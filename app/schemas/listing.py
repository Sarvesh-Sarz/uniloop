"""
Listing Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class ListingImageResponse(BaseModel):
    id: int
    image_url: str
    is_primary: bool

    class Config:
        from_attributes = True


class ListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: str = Field(...)  # Textbooks, Electronics, Lab Equipment, Tools, Lab Coats, Calculators, Other
    condition: str = Field(...)  # New, Like New, Good, Used, Heavily Used
    rental_type: str = Field(default="paid")  # "paid" or "free"
    price_per_day: float = Field(default=0.0, ge=0)
    price_per_week: float = Field(default=0.0, ge=0)
    security_deposit: float = Field(default=0.0, ge=0)
    max_duration_days: int = Field(default=30, ge=1, le=180)
    pickup_location: str = Field(..., min_length=2, max_length=100)
    is_semester_resource: bool = False


class ListingCreate(ListingBase):
    images: List[str] = []  # List of image URLs


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    rental_type: Optional[str] = None
    price_per_day: Optional[float] = None
    price_per_week: Optional[float] = None
    security_deposit: Optional[float] = None
    max_duration_days: Optional[int] = None
    pickup_location: Optional[str] = None
    status: Optional[str] = None
    is_semester_resource: Optional[bool] = None
    images: Optional[List[str]] = None


class ListingResponse(ListingBase):
    id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    owner: UserPublic
    images: List[ListingImageResponse] = []

    class Config:
        from_attributes = True
