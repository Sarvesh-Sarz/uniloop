"""
In-App Notification Dispatcher Service
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    link: Optional[str] = None
) -> Notification:
    """
    Creates an in-app notification entry for the specified user.
    """
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        link=link,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def notify_rental_requested(db: Session, owner_id: int, item_title: str, borrower_name: str):
    return create_notification(
        db,
        user_id=owner_id,
        title="New Rental Request",
        message=f"{borrower_name} has requested to borrow/rent '{item_title}'.",
        link="/rentals.html?tab=lent"
    )


def notify_rental_approved(db: Session, borrower_id: int, item_title: str):
    return create_notification(
        db,
        user_id=borrower_id,
        title="Rental Request Approved!",
        message=f"Your request for '{item_title}' has been approved by the owner.",
        link="/rentals.html?tab=borrowed"
    )


def notify_rental_rejected(db: Session, borrower_id: int, item_title: str):
    return create_notification(
        db,
        user_id=borrower_id,
        title="Rental Request Declined",
        message=f"Your request for '{item_title}' was declined.",
        link="/marketplace.html"
    )


def notify_rental_returned(db: Session, owner_id: int, item_title: str, condition: str):
    return create_notification(
        db,
        user_id=owner_id,
        title="Item Return Submitted",
        message=f"The borrower has submitted return for '{item_title}' (Condition: {condition.upper()}). Please review and finalize.",
        link="/rentals.html?tab=lent"
    )


def notify_rental_completed(db: Session, borrower_id: int, item_title: str):
    return create_notification(
        db,
        user_id=borrower_id,
        title="Rental Completed & Deposit Released",
        message=f"Rental for '{item_title}' has been marked complete. Your security deposit status has been updated.",
        link="/rentals.html?tab=completed"
    )


def notify_rating_received(db: Session, user_id: int, reviewer_name: str, rating: int):
    return create_notification(
        db,
        user_id=user_id,
        title="New Peer Review Received",
        message=f"{reviewer_name} gave you a {rating}-star rating! Your profile and trust score have been updated.",
        link="/profile.html"
    )
