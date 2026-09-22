"""
User Profile & Public Info Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.listing import Listing
from app.models.rental import Rental
from app.schemas.user import UserResponse, UserProfileUpdate
from app.auth import get_current_user
from app.services.trust_service import get_trust_tier

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/{user_id}/public")
def get_public_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Returns public student profile information:
    trust tier, ratings, successful rentals, and listed items.
    Does not expose private information like email or role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    trust_info = get_trust_tier(user.trust_score)

    # Count successful on-time rentals
    successful_rentals = db.query(Rental).filter(
        (Rental.borrower_id == user_id) | (Rental.owner_id == user_id),
        Rental.status == "COMPLETED"
    ).count()

    # Active listings
    listings = db.query(Listing).filter(
        Listing.owner_id == user_id,
        Listing.status == "available"
    ).all()

    return {
        "id": user.id,
        "name": user.name,
        "department": user.department,
        "year": user.year,
        "trust_score": user.trust_score,
        "trust_tier": trust_info["tier"],
        "trust_badge_color": trust_info["color"],
        "trust_description": trust_info["description"],
        "average_rating": user.average_rating,
        "rating_count": user.rating_count,
        "profile_image": user.profile_image,
        "successful_rentals": successful_rentals,
        "items_count": len(listings),
        "created_at": user.created_at
    }


@router.put("/me", response_model=UserResponse)
def update_profile(
    update_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated student's profile information.
    """
    if update_data.name:
        current_user.name = update_data.name.strip()
    if update_data.department:
        current_user.department = update_data.department.strip()
    if update_data.year:
        current_user.year = update_data.year.strip()
    if update_data.profile_image is not None:
        current_user.profile_image = update_data.profile_image

    db.commit()
    db.refresh(current_user)
    return current_user
