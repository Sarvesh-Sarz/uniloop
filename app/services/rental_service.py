"""
Rental Service & Business Logic

Core business logic for:
- Authoritative rental cost calculations (per-day and per-week)
- Late fee calculation (days overdue * daily_late_fee)
- Real-time countdown tracking (days remaining, due tomorrow, overdue)
- Automatic overdue detection without external background workers
- Rental lifecycle state transitions (REQUESTED -> APPROVED -> ACTIVE -> RETURN_REQUESTED -> COMPLETED)
"""

import os
from datetime import date, datetime
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models.rental import Rental, RentalRequest
from app.models.listing import Listing
from app.models.user import User

load_dotenv()
DEFAULT_DAILY_LATE_FEE = float(os.getenv("DAILY_LATE_FEE", "25.0"))


# ==============================================================================
# 1. RENTAL COST CALCULATION
# ==============================================================================
def calculate_rental_quote(
    price_per_day: float,
    price_per_week: float,
    security_deposit: float,
    rental_type: str,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """
    Calculates the exact rental cost and total amount.
    Duration is calculated inclusive of days: (end_date - start_date).days (minimum 1 day).
    Free borrows have zero rental cost but may still hold a deposit if configured.
    """
    days = max(1, (end_date - start_date).days)
    
    if rental_type == "free":
        rental_cost = 0.0
        deposit = 0.0
    else:
        # If weekly price exists and duration >= 7 days, provide optimal bundle price
        if price_per_week > 0 and days >= 7:
            weeks = days // 7
            rem_days = days % 7
            bundled_cost = (weeks * price_per_week) + (rem_days * price_per_day)
            daily_cost = days * price_per_day
            rental_cost = round(min(bundled_cost, daily_cost), 2)
        else:
            rental_cost = round(days * price_per_day, 2)
        
        deposit = round(security_deposit, 2)

    total_amount = round(rental_cost + deposit, 2)

    return {
        "days": days,
        "price_per_day": price_per_day,
        "price_per_week": price_per_week,
        "rental_cost": rental_cost,
        "security_deposit": deposit,
        "total_amount": total_amount,
        "rental_type": rental_type
    }


# ==============================================================================
# 2. LATE FEE CALCULATION
# ==============================================================================
def calculate_late_fee(
    end_date: date,
    return_date: Optional[date] = None,
    daily_late_fee: float = DEFAULT_DAILY_LATE_FEE
) -> Tuple[int, float]:
    """
    Calculates overdue days and corresponding late fee:
    late_fee = late_days * daily_late_fee
    Returns: (late_days, late_fee)
    """
    compare_date = return_date if return_date else date.today()
    if compare_date > end_date:
        late_days = (compare_date - end_date).days
        late_fee = round(late_days * daily_late_fee, 2)
        return late_days, late_fee
    return 0, 0.0


# ==============================================================================
# 3. COUNTDOWN AND REMAINING DAYS
# ==============================================================================
def get_countdown_details(rental: Rental) -> Dict[str, Any]:
    """
    Computes countdown information relative to today's date for UI display.
    """
    today = date.today()
    if rental.status in ["COMPLETED", "CANCELLED", "REJECTED"]:
        return {"days_remaining": 0, "countdown_text": rental.status.capitalize()}

    if today > rental.end_date:
        overdue_days = (today - rental.end_date).days
        return {
            "days_remaining": -overdue_days,
            "countdown_text": f"Overdue by {overdue_days} day{'s' if overdue_days != 1 else ''}"
        }
    elif today == rental.end_date:
        return {"days_remaining": 0, "countdown_text": "Due today"}
    else:
        diff = (rental.end_date - today).days
        if diff == 1:
            return {"days_remaining": 1, "countdown_text": "Due tomorrow"}
        return {"days_remaining": diff, "countdown_text": f"{diff} days remaining"}


# ==============================================================================
# 4. AUTOMATIC OVERDUE DETECTION
# ==============================================================================
def sync_overdue_rentals(db: Session) -> None:
    """
    Checks active rentals whose end_date has passed and dynamically updates
    their status to OVERDUE and updates their late fee.
    Called when rentals endpoints are accessed - avoids Celery / Redis.
    """
    today = date.today()
    overdue_active = db.query(Rental).filter(
        Rental.status.in_(["ACTIVE", "RETURN_REQUESTED"]),
        Rental.end_date < today
    ).all()

    for rental in overdue_active:
        rental.status = "OVERDUE"
        late_days, fee = calculate_late_fee(rental.end_date, today)
        rental.late_fee = fee

    if overdue_active:
        db.commit()
