"""
Report & Dispute Database Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="SET NULL"), nullable=True)
    rental_id = Column(Integer, ForeignKey("rentals.id", ondelete="SET NULL"), nullable=True)
    
    category = Column(String(100), nullable=False)
    # Categories: "Scam / suspicious", "Incorrect information", "Damaged item", "Harassment", "Other"
    
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN", nullable=False)
    # Statuses: "OPEN", "REVIEWING", "RESOLVED", "REJECTED"
    
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="filed_reports")
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    listing = relationship("Listing")
    rental = relationship("Rental")
