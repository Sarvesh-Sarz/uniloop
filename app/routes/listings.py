"""
Listings & Marketplace API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.database import get_db
from app.models.listing import Listing, ListingImage
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse
from app.auth import get_current_user
from app.utils import save_upload_file

router = APIRouter(prefix="/api/listings", tags=["Listings"])


@router.get("", response_model=List[ListingResponse])
def get_listings(
    search: Optional[str] = Query(None, description="Search by title, description or category"),
    category: Optional[str] = Query(None, description="Filter by category"),
    condition: Optional[str] = Query(None, description="Filter by item condition"),
    rental_type: Optional[str] = Query(None, description="'paid' or 'free'"),
    pickup_location: Optional[str] = Query(None, description="Filter by campus location"),
    department: Optional[str] = Query(None, description="Filter by owner's university department"),
    is_semester_resource: Optional[bool] = Query(None, description="Semester featured items"),
    sort: Optional[str] = Query("newest", description="Sorting: newest, price_asc, price_desc, rating_desc"),
    db: Session = Depends(get_db)
):
    """
    Retrieves marketplace listings with multi-attribute filtering, search, and sorting.
    Only shows 'available' listings by default.
    """
    query = db.query(Listing).join(User, Listing.owner_id == User.id).filter(Listing.status == "available")

    # Full text / keyword search
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Listing.title.ilike(search_term),
                Listing.description.ilike(search_term),
                Listing.category.ilike(search_term),
                Listing.pickup_location.ilike(search_term)
            )
        )

    # Category filter
    if category and category != "All":
        query = query.filter(Listing.category == category)

    # Condition filter
    if condition and condition != "All":
        query = query.filter(Listing.condition == condition)

    # Rental type filter (Paid vs Free Borrow)
    if rental_type and rental_type != "All":
        query = query.filter(Listing.rental_type == rental_type)

    # Campus location filter
    if pickup_location and pickup_location != "All":
        query = query.filter(Listing.pickup_location == pickup_location)

    # Department filter (joined on User)
    if department and department != "All":
        query = query.filter(User.department == department)

    # Semester resource filter
    if is_semester_resource is not None:
        query = query.filter(Listing.is_semester_resource == is_semester_resource)

    # Sorting options
    if sort == "price_asc":
        query = query.order_by(asc(Listing.price_per_day))
    elif sort == "price_desc":
        query = query.order_by(desc(Listing.price_per_day))
    elif sort == "rating_desc":
        query = query.order_by(desc(User.average_rating), desc(Listing.created_at))
    else:  # "newest" by default
        query = query.order_by(desc(Listing.created_at))

    return query.all()


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing_by_id(listing_id: int, db: Session = Depends(get_db)):
    """
    Retrieves complete details for a single listing including owner reputation and gallery images.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")
    return listing


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
def create_listing(
    listing_data: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new campus resource listing authored by the authenticated student.
    """
    new_listing = Listing(
        owner_id=current_user.id,
        title=listing_data.title.strip(),
        description=listing_data.description.strip(),
        category=listing_data.category,
        condition=listing_data.condition,
        rental_type=listing_data.rental_type,
        price_per_day=listing_data.price_per_day if listing_data.rental_type == "paid" else 0.0,
        price_per_week=listing_data.price_per_week if listing_data.rental_type == "paid" else 0.0,
        security_deposit=listing_data.security_deposit,
        max_duration_days=listing_data.max_duration_days,
        pickup_location=listing_data.pickup_location.strip(),
        is_semester_resource=listing_data.is_semester_resource,
        status="available"
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)

    # Save images
    if listing_data.images:
        for idx, img_url in enumerate(listing_data.images):
            image_record = ListingImage(
                listing_id=new_listing.id,
                image_url=img_url,
                is_primary=(idx == 0)
            )
            db.add(image_record)
        db.commit()
        db.refresh(new_listing)

    return new_listing


@router.put("/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: int,
    update_data: ListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates an existing listing. Only the listing owner or an administrator can perform this.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    if listing.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this listing."
        )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        if field == "images" and value is not None:
            # Clear old images and insert new ones
            db.query(ListingImage).filter(ListingImage.listing_id == listing.id).delete()
            for idx, img_url in enumerate(value):
                db.add(ListingImage(listing_id=listing.id, image_url=img_url, is_primary=(idx == 0)))
        else:
            setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_200_OK)
def delete_listing(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a listing. Sets status to 'removed' or deletes.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    if listing.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this listing."
        )

    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted successfully."}


@router.post("/upload-image")
def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a photo for a resource listing. Stored locally in uploads/ (S3-ready).
    """
    image_url = save_upload_file(file)
    return {"image_url": image_url}
