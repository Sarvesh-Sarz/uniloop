"""
Peer Message Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class MessageCreate(BaseModel):
    receiver_id: int
    listing_id: Optional[int] = None
    message: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    listing_id: Optional[int] = None
    message: str
    is_read: bool
    created_at: datetime
    sender: Optional[UserPublic] = None
    receiver: Optional[UserPublic] = None

    class Config:
        from_attributes = True
