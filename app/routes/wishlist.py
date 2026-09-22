"""
Wishlist & Saved Items API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.wishlist import Wishlist
from app.models.listing import Listing
from app.models.user import User
from app.schemas.wishlist import WishlistResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


@router.get("", response_model=List[WishlistResponse])
def get_user_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all items bookmarked by the current student.
    """
    items = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id
    ).order_by(desc(Wishlist.created_at)).all()
    return items


@router.get("/check/{listing_id}")
def check_is_wishlisted(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks whether the specified listing is in the user's wishlist.
    """
    exists = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.listing_id == listing_id
    ).first() is not None
    return {"saved": exists}


@router.post("/{listing_id}", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a listing to the user's wishlist.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.listing_id == listing_id
    ).first()

    if existing:
        return {"message": "Item already in your wishlist."}

    entry = Wishlist(user_id=current_user.id, listing_id=listing_id)
    db.add(entry)
    db.commit()
    return {"message": "Saved to your wishlist."}


@router.delete("/{listing_id}", status_code=status.HTTP_200_OK)
def remove_from_wishlist(
    listing_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a listing from the user's wishlist.
    """
    deleted = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.listing_id == listing_id
    ).delete()
    db.commit()

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item was not in your wishlist.")

    return {"message": "Removed from wishlist."}
