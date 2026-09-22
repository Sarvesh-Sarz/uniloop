"""
Trust Score & Rating Service

Implements a transparent, rule-based algorithm for student trust scores:
- Every student starts with 50 / 100.
- Score is always bounded between 0 and 100.

Positive events:
  +5 : On-time completed rental
  +3 : Positive rating (4 or 5 stars)
  +2 : Clean, successful item return

Negative events:
  -5 : Late return
  -3 : Cancelled approved rental
  -10: Confirmed damage or dispute

Trust tiers:
  80 - 100 : Highly Reliable (Badge: Green)
  60 - 79  : Reliable (Badge: Blue)
  40 - 59  : New / Building Trust (Badge: Yellow/Amber)
  0  - 39  : Low Trust (Badge: Red)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.rating import Rating


def get_trust_tier(score: int) -> dict:
    """
    Returns the human-friendly label, color badge class, and description for a trust score.
    """
    score = max(0, min(100, score))
    if score >= 80:
        return {
            "tier": "Highly Reliable",
            "badge_class": "badge-success",
            "color": "#10b981",
            "description": "Consistently returns items on time in excellent condition."
        }
    elif score >= 60:
        return {
            "tier": "Reliable",
            "badge_class": "badge-primary",
            "color": "#3b82f6",
            "description": "Good track record of peer sharing and positive reviews."
        }
    elif score >= 40:
        return {
            "tier": "Building Trust",
            "badge_class": "badge-warning",
            "color": "#f59e0b",
            "description": "New member or actively establishing campus reputation."
        }
    else:
        return {
            "tier": "Low Trust",
            "badge_class": "badge-danger",
            "color": "#ef4444",
            "description": "Multiple late returns, cancellations, or damage incidents."
        }


def adjust_trust_score(db: Session, user_id: int, delta: int) -> int:
    """
    Applies a positive or negative delta to the user's trust score.
    Clamps the result strictly between 0 and 100.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 50

    new_score = user.trust_score + delta
    user.trust_score = max(0, min(100, new_score))
    db.commit()
    db.refresh(user)
    return user.trust_score


def update_user_ratings_and_trust(db: Session, reviewed_user_id: int, new_star_rating: int) -> None:
    """
    Recalculates the user's average rating and total rating count,
    and applies a trust score bonus (+3 for >= 4 stars).
    """
    user = db.query(User).filter(User.id == reviewed_user_id).first()
    if not user:
        return

    # Calculate average rating and count directly from database
    result = db.query(
        func.avg(Rating.rating),
        func.count(Rating.id)
    ).filter(Rating.reviewed_user_id == reviewed_user_id).first()

    avg_rating = round(float(result[0]), 2) if result and result[0] is not None else 5.0
    count = int(result[1]) if result and result[1] is not None else 0

    user.average_rating = avg_rating
    user.rating_count = count

    # Trust bonus: +3 for 4-star or 5-star rating
    if new_star_rating >= 4:
        user.trust_score = max(0, min(100, user.trust_score + 3))

    db.commit()
