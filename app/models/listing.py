"""
Listing & ListingImage Database Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    condition = Column(String(50), nullable=False)
    rental_type = Column(String(20), default="paid", nullable=False)  # "paid" or "free"
    price_per_day = Column(Float, default=0.0, nullable=False)
    price_per_week = Column(Float, default=0.0, nullable=False)
    security_deposit = Column(Float, default=0.0, nullable=False)
    max_duration_days = Column(Integer, default=30, nullable=False)
    pickup_location = Column(String(100), nullable=False)
    status = Column(String(30), default="available", nullable=False)  # "available", "rented", "removed"
    is_semester_resource = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="listings")
    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    rental_requests = relationship("RentalRequest", back_populates="listing", cascade="all, delete-orphan")
    rentals = relationship("Rental", back_populates="listing", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="listing", cascade="all, delete-orphan")


class ListingImage(Base):
    __tablename__ = "listing_images"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    listing = relationship("Listing", back_populates="images")
