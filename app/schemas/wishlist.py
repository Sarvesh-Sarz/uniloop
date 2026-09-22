"""
Wishlist Pydantic Schemas
"""

from datetime import datetime
from pydantic import BaseModel

from app.schemas.listing import ListingResponse


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    listing_id: int
    created_at: datetime
    listing: ListingResponse

    class Config:
        from_attributes = True
