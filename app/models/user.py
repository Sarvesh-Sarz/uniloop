"""
User Database Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    year = Column(String(50), nullable=False)
    role = Column(String(20), default="student", nullable=False)  # "student" or "admin"
    trust_score = Column(Integer, default=50, nullable=False)    # 0 to 100, default 50
    average_rating = Column(Float, default=5.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    profile_image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    listings = relationship("Listing", back_populates="owner", cascade="all, delete-orphan")
    rental_requests = relationship("RentalRequest", back_populates="borrower", cascade="all, delete-orphan")
    borrowed_rentals = relationship("Rental", foreign_keys="Rental.borrower_id", back_populates="borrower")
    lent_rentals = relationship("Rental", foreign_keys="Rental.owner_id", back_populates="owner")
    ratings_given = relationship("Rating", foreign_keys="Rating.reviewer_id", back_populates="reviewer")
    ratings_received = relationship("Rating", foreign_keys="Rating.reviewed_user_id", back_populates="reviewed_user")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    filed_reports = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
