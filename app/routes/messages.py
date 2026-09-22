"""
Peer-to-Peer Messaging API Endpoints

Simple HTTP REST messaging between students regarding listings/rentals.
Avoids WebSockets for simplicity and ease of interview explanation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.auth import get_current_user
from app.services.notification_service import create_notification

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.get("", response_model=List[MessageResponse])
def get_messages_thread(
    other_user_id: int = Query(..., description="ID of the user to view conversation with"),
    listing_id: Optional[int] = Query(None, description="Optional filter by listing"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the chronological message thread between the current user and another student.
    Marks received messages as read.
    """
    query = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
            and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id)
        )
    )

    if listing_id:
        query = query.filter(Message.listing_id == listing_id)

    messages = query.order_by(Message.created_at.asc()).all()

    # Automatically mark incoming unread messages as read
    unread_ids = [m.id for m in messages if m.receiver_id == current_user.id and not m.is_read]
    if unread_ids:
        db.query(Message).filter(Message.id.in_(unread_ids)).update({Message.is_read: True}, synchronize_session=False)
        db.commit()

    return messages


@router.get("/conversations")
def get_active_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns an inbox summary of all students with whom the current user has chatted,
    including the last message snippet, timestamp, and unread count.
    """
    # Fetch all messages where current user is sender or receiver
    all_msgs = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).order_by(desc(Message.created_at)).all()

    conversations = {}
    for m in all_msgs:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        if other_id not in conversations:
            other_user = db.query(User).filter(User.id == other_id).first()
            if not other_user:
                continue

            unread_count = db.query(Message).filter(
                Message.sender_id == other_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()

            conversations[other_id] = {
                "other_user": {
                    "id": other_user.id,
                    "name": other_user.name,
                    "department": other_user.department,
                    "profile_image": other_user.profile_image
                },
                "last_message": m.message,
                "last_message_at": m.created_at,
                "listing_id": m.listing_id,
                "unread_count": unread_count
            }

    return list(conversations.values())


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends a direct message to another student.
    """
    if payload.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot message yourself."
        )

    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient user not found.")

    new_msg = Message(
        sender_id=current_user.id,
        receiver_id=payload.receiver_id,
        listing_id=payload.listing_id,
        message=payload.message.strip(),
        is_read=False
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # In-app notification to receiver
    create_notification(
        db=db,
        user_id=receiver.id,
        title="New Message",
        message=f"{current_user.name} sent you a message: '{new_msg.message[:40]}...'",
        link=f"/messages.html?user_id={current_user.id}"
    )

    return new_msg
