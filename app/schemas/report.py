"""
Report Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class ReportCreate(BaseModel):
    reported_user_id: Optional[int] = None
    listing_id: Optional[int] = None
    rental_id: Optional[int] = None
    category: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)


class ReportStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(OPEN|REVIEWING|RESOLVED|REJECTED)$")
    resolution_notes: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    reported_user_id: Optional[int] = None
    listing_id: Optional[int] = None
    rental_id: Optional[int] = None
    category: str
    description: str
    status: str
    resolution_notes: Optional[str] = None
    created_at: datetime
    reporter: Optional[UserPublic] = None
    reported_user: Optional[UserPublic] = None

    class Config:
        from_attributes = True
