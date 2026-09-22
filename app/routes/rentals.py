"""
Rentals & Rental Requests API Endpoints

Implements the complete rental lifecycle:
REQUESTED -> APPROVED -> ACTIVE -> RETURN_REQUESTED -> COMPLETED
(Also REJECTED, CANCELLED, OVERDUE, DISPUTED)

Enforces:
- Backend price calculation
- Security deposit state handling
- Late fee generation on overdue items
- Damage reporting and dispute resolution
- Trust score recalculation on returns
"""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.database import get_db
from app.models.rental import Rental, RentalRequest
from app.models.listing import Listing
from app.models.user import User
from app.schemas.rental import (
    RentalQuoteRequest,
    RentalQuoteResponse,
    RentalRequestCreate,
    RentalRequestResponse,
    RentalResponse,
    ReturnRequest,
    DisputeResolution,
)
from app.auth import get_current_user
from app.services.rental_service import (
    calculate_rental_quote,
    calculate_late_fee,
    get_countdown_details,
    sync_overdue_rentals,
)
from app.services.trust_service import adjust_trust_score
from app.services.notification_service import (
    notify_rental_requested,
    notify_rental_approved,
    notify_rental_rejected,
    notify_rental_returned,
    notify_rental_completed,
)

router = APIRouter(prefix="", tags=["Rentals"])


# ==============================================================================
# 1. RENTAL QUOTE (ESTIMATOR / AUTHORITATIVE PRICING)
# ==============================================================================
@router.post("/api/rentals/quote", response_model=RentalQuoteResponse)
def get_rental_quote(payload: RentalQuoteRequest, db: Session = Depends(get_db)):
    """
    Authoritative backend calculation of rental cost, security deposit, and total.
    The frontend calls this whenever dates change to display an accurate breakdown.
    """
    listing = db.query(Listing).filter(Listing.id == payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    quote = calculate_rental_quote(
        price_per_day=listing.price_per_day,
        price_per_week=listing.price_per_week,
        security_deposit=listing.security_deposit,
        rental_type=listing.rental_type,
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    return quote


# ==============================================================================
# 2. RENTAL REQUESTS LIFECYCLE
# ==============================================================================
@router.post("/api/rental-requests", response_model=RentalRequestResponse, status_code=status.HTTP_201_CREATED)
def create_rental_request(
    req: RentalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Student submits a request to rent or borrow an item.
    Validations:
    - User cannot rent their own item
    - Item must be currently 'available'
    - End date must be on or after start date
    """
    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    if listing.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot rent or borrow your own listing."
        )

    if listing.status != "available":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is currently not available for rental."
        )

    # Check max duration
    days = max(1, (req.end_date - req.start_date).days)
    if days > listing.max_duration_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested rental duration ({days} days) exceeds maximum allowed ({listing.max_duration_days} days)."
        )

    rental_request = RentalRequest(
        listing_id=listing.id,
        borrower_id=current_user.id,
        start_date=req.start_date,
        end_date=req.end_date,
        message=req.message,
        status="REQUESTED"
    )
    db.add(rental_request)
    db.commit()
    db.refresh(rental_request)

    # Send in-app notification to the listing owner
    notify_rental_requested(
        db=db,
        owner_id=listing.owner_id,
        item_title=listing.title,
        borrower_name=current_user.name
    )

    return rental_request


@router.get("/api/rental-requests", response_model=List[RentalRequestResponse])
def get_rental_requests(
    role: Optional[str] = Query("all", description="'borrower', 'owner', or 'all'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists rental requests involving the current student.
    """
    query = db.query(RentalRequest).join(Listing, RentalRequest.listing_id == Listing.id)

    if role == "borrower":
        query = query.filter(RentalRequest.borrower_id == current_user.id)
    elif role == "owner":
        query = query.filter(Listing.owner_id == current_user.id)
    else:
        query = query.filter(
            or_(
                RentalRequest.borrower_id == current_user.id,
                Listing.owner_id == current_user.id
            )
        )

    return query.order_by(desc(RentalRequest.created_at)).all()


@router.put("/api/rental-requests/{request_id}/approve", response_model=RentalResponse)
def approve_rental_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Owner approves a rental request.
    Creates an ACTIVE Rental record, sets deposit to HELD, marks listing rented.
    """
    req = db.query(RentalRequest).filter(RentalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental request not found.")

    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if listing.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can approve this request.")

    if req.status != "REQUESTED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request is already {req.status}.")

    # Calculate authoritative pricing
    quote = calculate_rental_quote(
        price_per_day=listing.price_per_day,
        price_per_week=listing.price_per_week,
        security_deposit=listing.security_deposit,
        rental_type=listing.rental_type,
        start_date=req.start_date,
        end_date=req.end_date
    )

    # 1. Update Request status
    req.status = "APPROVED"

    # 2. Mark listing as rented
    listing.status = "rented"

    # 3. Create active rental
    rental = Rental(
        listing_id=listing.id,
        owner_id=listing.owner_id,
        borrower_id=req.borrower_id,
        request_id=req.id,
        start_date=req.start_date,
        end_date=req.end_date,
        rental_cost=quote["rental_cost"],
        security_deposit=quote["security_deposit"],
        late_fee=0.0,
        deposit_status="HELD",
        status="ACTIVE",
        damage_reported=False
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)

    # Notify borrower
    notify_rental_approved(db, req.borrower_id, listing.title)

    # Attach countdown info
    info = get_countdown_details(rental)
    rental.days_remaining = info["days_remaining"]
    rental.countdown_text = info["countdown_text"]

    return rental


@router.put("/api/rental-requests/{request_id}/reject", response_model=RentalRequestResponse)
def reject_rental_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Owner declines a rental request.
    """
    req = db.query(RentalRequest).filter(RentalRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental request not found.")

    listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
    if listing.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    req.status = "REJECTED"
    db.commit()
    db.refresh(req)

    notify_rental_rejected(db, req.borrower_id, listing.title)
    return req


# ==============================================================================
# 3. ACTIVE RENTALS & MANAGEMENT
# ==============================================================================
@router.get("/api/rentals", response_model=List[RentalResponse])
def get_rentals(
    tab: Optional[str] = Query("all", description="'borrowed', 'lent', 'completed', 'overdue', or 'all'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves user rentals across tabs with dynamic countdown calculations.
    Automatically identifies and marks overdue items.
    """
    # 1. Sync overdue items dynamically
    sync_overdue_rentals(db)

    query = db.query(Rental)

    if tab == "borrowed":
        query = query.filter(
            Rental.borrower_id == current_user.id,
            Rental.status.in_(["ACTIVE", "RETURN_REQUESTED", "OVERDUE", "DISPUTED"])
        )
    elif tab == "lent":
        query = query.filter(
            Rental.owner_id == current_user.id,
            Rental.status.in_(["ACTIVE", "RETURN_REQUESTED", "OVERDUE", "DISPUTED"])
        )
    elif tab == "completed":
        query = query.filter(
            or_(Rental.borrower_id == current_user.id, Rental.owner_id == current_user.id),
            Rental.status == "COMPLETED"
        )
    elif tab == "overdue":
        query = query.filter(
            or_(Rental.borrower_id == current_user.id, Rental.owner_id == current_user.id),
            Rental.status == "OVERDUE"
        )
    else:
        query = query.filter(
            or_(Rental.borrower_id == current_user.id, Rental.owner_id == current_user.id)
        )

    rentals = query.order_by(desc(Rental.created_at)).all()

    # Decorate with live countdown information
    for r in rentals:
        info = get_countdown_details(r)
        r.days_remaining = info["days_remaining"]
        r.countdown_text = info["countdown_text"]

    return rentals


@router.get("/api/rentals/{rental_id}", response_model=RentalResponse)
def get_rental_by_id(
    rental_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves complete rental details including live late fee calculation and countdown.
    """
    sync_overdue_rentals(db)

    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")

    if (rental.borrower_id != current_user.id and
        rental.owner_id != current_user.id and
        current_user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    info = get_countdown_details(rental)
    rental.days_remaining = info["days_remaining"]
    rental.countdown_text = info["countdown_text"]

    return rental


@router.put("/api/rentals/{rental_id}/return", response_model=RentalResponse)
def request_item_return(
    rental_id: int,
    payload: ReturnRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Borrower initiates item return.
    States:
    - 'good': Marks status=RETURN_REQUESTED, deposit=REFUNDABLE, awards +2 trust bonus
    - 'damaged': Marks status=DISPUTED, deposit=HELD, penalizes -10 trust score
    """
    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")

    if rental.borrower_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the borrower can initiate return.")

    if rental.status not in ["ACTIVE", "OVERDUE"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot return rental in {rental.status} state.")

    today = date.today()
    rental.actual_return_date = today

    # Check if late
    if today > rental.end_date:
        _, late_fee = calculate_late_fee(rental.end_date, today)
        rental.late_fee = late_fee
        # Penalty for late return: -5
        adjust_trust_score(db, rental.borrower_id, -5)

    if payload.return_condition == "good":
        rental.status = "RETURN_REQUESTED"
        rental.deposit_status = "REFUNDABLE"
        rental.damage_reported = False
        # Reward on-time clean return attempt: +2
        adjust_trust_score(db, rental.borrower_id, 2)
    else:
        rental.status = "DISPUTED"
        rental.damage_reported = True
        rental.damage_notes = payload.damage_notes
        rental.damage_image = payload.damage_image
        rental.deposit_status = "PARTIALLY_DEDUCTED"
        # Confirmed damage penalty: -10
        adjust_trust_score(db, rental.borrower_id, -10)

    db.commit()
    db.refresh(rental)

    # Notify owner
    listing = db.query(Listing).filter(Listing.id == rental.listing_id).first()
    item_title = listing.title if listing else "Item"
    notify_rental_returned(db, rental.owner_id, item_title, payload.return_condition)

    info = get_countdown_details(rental)
    rental.days_remaining = info["days_remaining"]
    rental.countdown_text = info["countdown_text"]

    return rental


@router.put("/api/rentals/{rental_id}/complete", response_model=RentalResponse)
def finalize_rental_completion(
    rental_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Owner (or Admin) inspects the returned item and finalizes completion.
    Releases deposit to REFUNDED, makes listing available again,
    and awards borrower +5 trust score for on-time completion.
    """
    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")

    if rental.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can complete this rental.")

    if rental.status not in ["RETURN_REQUESTED", "ACTIVE", "OVERDUE", "DISPUTED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Rental is already {rental.status}.")

    rental.status = "COMPLETED"
    if rental.deposit_status in ["REFUNDABLE", "HELD"]:
        rental.deposit_status = "REFUNDED"
    
    if not rental.actual_return_date:
        rental.actual_return_date = date.today()

    # Reset listing to available
    listing = db.query(Listing).filter(Listing.id == rental.listing_id).first()
    if listing:
        listing.status = "available"

    # Reward on-time completion if returned on or before end_date: +5
    if rental.actual_return_date <= rental.end_date and not rental.damage_reported:
        adjust_trust_score(db, rental.borrower_id, 5)

    db.commit()
    db.refresh(rental)

    # Notify borrower
    item_title = listing.title if listing else "Item"
    notify_rental_completed(db, rental.borrower_id, item_title)

    info = get_countdown_details(rental)
    rental.days_remaining = info["days_remaining"]
    rental.countdown_text = info["countdown_text"]

    return rental


@router.put("/api/rentals/{rental_id}/resolve-dispute", response_model=RentalResponse)
def resolve_dispute(
    rental_id: int,
    payload: DisputeResolution,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin or owner settles a damage/dispute report with custom deposit disposition.
    """
    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")

    if rental.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    rental.status = payload.status
    rental.deposit_status = payload.deposit_status
    if payload.resolution_notes:
        rental.damage_notes = f"{rental.damage_notes or ''}\nResolution: {payload.resolution_notes}".strip()

    # Make listing available again
    listing = db.query(Listing).filter(Listing.id == rental.listing_id).first()
    if listing:
        listing.status = "available"

    db.commit()
    db.refresh(rental)

    info = get_countdown_details(rental)
    rental.days_remaining = info["days_remaining"]
    rental.countdown_text = info["countdown_text"]

    return rental
