"""
Ratings & Reviews API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.rental import Rental
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse
from app.auth import get_current_user
from app.services.trust_service import update_user_ratings_and_trust
from app.services.notification_service import notify_rating_received

router = APIRouter(prefix="", tags=["Ratings"])


@router.post("/api/ratings", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def submit_rating(
    payload: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a 1-5 star review after a rental is completed.
    Borrower rates Owner, or Owner rates Borrower.
    Prevents multiple ratings for the same completed rental.
    """
    rental = db.query(Rental).filter(Rental.id == payload.rental_id).first()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found.")

    if rental.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviews can only be submitted after the rental has been marked as COMPLETED."
        )

    # Determine who is being reviewed
    if current_user.id == rental.borrower_id:
        reviewed_user_id = rental.owner_id
    elif current_user.id == rental.owner_id:
        reviewed_user_id = rental.borrower_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You were not a participant in this rental."
        )

    # Check for existing rating by this reviewer for this rental
    existing_rating = db.query(Rating).filter(
        Rating.rental_id == rental.id,
        Rating.reviewer_id == current_user.id
    ).first()

    if existing_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a rating for this rental."
        )

    # Create new rating
    rating_record = Rating(
        rental_id=rental.id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
        rating=payload.rating,
        review=payload.review.strip() if payload.review else None
    )
    db.add(rating_record)
    db.commit()
    db.refresh(rating_record)

    # Automatically recalculate target user's average rating and trust score
    update_user_ratings_and_trust(db, reviewed_user_id, payload.rating)

    # Send in-app notification
    notify_rating_received(db, reviewed_user_id, current_user.name, payload.rating)

    return rating_record


@router.get("/api/users/{user_id}/ratings", response_model=List[RatingResponse])
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    """
    Returns all public peer reviews received by a student.
    """
    ratings = db.query(Rating).filter(
        Rating.reviewed_user_id == user_id
    ).order_by(desc(Rating.created_at)).all()
    return ratings
