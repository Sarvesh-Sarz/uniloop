"""
RentalRequest & Rental Database Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class RentalRequest(Base):
    __tablename__ = "rental_requests"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(30), default="REQUESTED", nullable=False)  # "REQUESTED", "APPROVED", "REJECTED", "CANCELLED"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="rental_requests")
    borrower = relationship("User", back_populates="rental_requests")
    rental = relationship("Rental", back_populates="request", uselist=False)


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    borrower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_id = Column(Integer, ForeignKey("rental_requests.id", ondelete="SET NULL"), nullable=True)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    actual_return_date = Column(Date, nullable=True)
    
    rental_cost = Column(Float, default=0.0, nullable=False)
    security_deposit = Column(Float, default=0.0, nullable=False)
    late_fee = Column(Float, default=0.0, nullable=False)
    
    deposit_status = Column(String(30), default="HELD", nullable=False)
    # HELD, REFUNDABLE, REFUNDED, PARTIALLY_DEDUCTED, DEDUCTED
    
    status = Column(String(30), default="ACTIVE", nullable=False)
    # ACTIVE, RETURN_REQUESTED, COMPLETED, OVERDUE, DISPUTED, CANCELLED
    
    damage_reported = Column(Boolean, default=False, nullable=False)
    damage_notes = Column(Text, nullable=True)
    damage_image = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    listing = relationship("Listing", back_populates="rentals")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="lent_rentals")
    borrower = relationship("User", foreign_keys=[borrower_id], back_populates="borrowed_rentals")
    request = relationship("RentalRequest", back_populates="rental")
    ratings = relationship("Rating", back_populates="rental", cascade="all, delete-orphan")
