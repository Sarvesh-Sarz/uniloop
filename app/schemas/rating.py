"""
Rating & Review Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class RatingCreate(BaseModel):
    rental_id: int
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)


class RatingResponse(BaseModel):
    id: int
    rental_id: int
    reviewer_id: int
    reviewed_user_id: int
    rating: int
    review: Optional[str] = None
    created_at: datetime
    reviewer: Optional[UserPublic] = None

    class Config:
        from_attributes = True
