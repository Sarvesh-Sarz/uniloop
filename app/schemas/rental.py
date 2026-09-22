"""
Rental & RentalRequest Pydantic Schemas
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.listing import ListingResponse
from app.schemas.user import UserPublic


class RentalQuoteRequest(BaseModel):
    listing_id: int
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("Rental end date cannot be earlier than the start date.")
        return v


class RentalQuoteResponse(BaseModel):
    days: int
    price_per_day: float
    price_per_week: float
    rental_cost: float
    security_deposit: float
    total_amount: float
    rental_type: str


class RentalRequestCreate(BaseModel):
    listing_id: int
    start_date: date
    end_date: date
    message: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("Rental end date cannot be earlier than start date.")
        return v


class RentalRequestResponse(BaseModel):
    id: int
    listing_id: int
    borrower_id: int
    start_date: date
    end_date: date
    message: Optional[str] = None
    status: str
    created_at: datetime
    listing: Optional[ListingResponse] = None
    borrower: Optional[UserPublic] = None

    class Config:
        from_attributes = True


class ReturnRequest(BaseModel):
    return_condition: str = Field(..., pattern="^(good|damaged)$")
    damage_notes: Optional[str] = None
    damage_image: Optional[str] = None


class DisputeResolution(BaseModel):
    deposit_status: str = Field(..., pattern="^(REFUNDED|PARTIALLY_DEDUCTED|DEDUCTED)$")
    status: str = Field(default="COMPLETED")
    resolution_notes: Optional[str] = None


class RentalResponse(BaseModel):
    id: int
    listing_id: int
    owner_id: int
    borrower_id: int
    request_id: Optional[int] = None
    start_date: date
    end_date: date
    actual_return_date: Optional[date] = None
    rental_cost: float
    security_deposit: float
    late_fee: float
    deposit_status: str
    status: str
    damage_reported: bool
    damage_notes: Optional[str] = None
    damage_image: Optional[str] = None
    created_at: datetime
    days_remaining: Optional[int] = None
    countdown_text: Optional[str] = None
    listing: Optional[ListingResponse] = None
    owner: Optional[UserPublic] = None
    borrower: Optional[UserPublic] = None

    class Config:
        from_attributes = True
