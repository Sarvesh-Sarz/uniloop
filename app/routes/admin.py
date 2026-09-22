"""
Admin Moderation & Analytics Endpoints

Accessible exclusively by users with role='admin'.
Provides:
- Platform KPIs and statistics
- User management and suspension
- Listing moderation and 'Semester Resources' curation
- Dispute and report resolution
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.user import User
from app.models.listing import Listing
from app.models.rental import Rental
from app.models.report import Report
from app.schemas.user import UserResponse
from app.schemas.listing import ListingResponse
from app.schemas.report import ReportResponse, ReportStatusUpdate
from app.schemas.rental import RentalResponse
from app.auth import get_current_admin
from app.services.rental_service import sync_overdue_rentals, get_countdown_details

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/dashboard")
def get_admin_dashboard_metrics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Returns platform-wide metrics and KPIs for the administrator dashboard.
    """
    sync_overdue_rentals(db)

    total_students = db.query(User).filter(User.role == "student").count()
    total_listings = db.query(Listing).count()
    active_rentals = db.query(Rental).filter(Rental.status.in_(["ACTIVE", "RETURN_REQUESTED"])).count()
    overdue_rentals = db.query(Rental).filter(Rental.status == "OVERDUE").count()
    completed_rentals = db.query(Rental).filter(Rental.status == "COMPLETED").count()
    open_reports = db.query(Report).filter(Report.status.in_(["OPEN", "REVIEWING"])).count()
    
    # Calculate estimated money saved by students on campus
    total_value_shared = db.query(func.sum(Rental.rental_cost)).scalar() or 0.0

    return {
        "total_students": total_students,
        "total_listings": total_listings,
        "active_rentals": active_rentals,
        "overdue_rentals": overdue_rentals,
        "completed_rentals": completed_rentals,
        "open_reports": open_reports,
        "total_value_shared": round(float(total_value_shared), 2)
    }


@router.get("/users")
def get_all_users(
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Lists registered users on the platform with reputation score and active state.
    """
    query = db.query(User)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.name.ilike(s)) | (User.email.ilike(s)) | (User.department.ilike(s)))

    users = query.order_by(desc(User.created_at)).all()
    
    result = []
    for u in users:
        listings_count = db.query(Listing).filter(Listing.owner_id == u.id).count()
        rentals_count = db.query(Rental).filter((Rental.borrower_id == u.id) | (Rental.owner_id == u.id)).count()
        result.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "department": u.department,
            "year": u.year,
            "role": u.role,
            "trust_score": u.trust_score,
            "average_rating": u.average_rating,
            "is_active": u.is_active,
            "listings_count": listings_count,
            "rentals_count": rentals_count,
            "created_at": u.created_at
        })
    return result


@router.put("/users/{user_id}/toggle-suspend")
def toggle_user_suspension(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Suspends or reactivates a user account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot suspend yourself.")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    status_str = "activated" if user.is_active else "suspended"
    return {"message": f"User {user.name} has been {status_str}.", "is_active": user.is_active}


@router.get("/listings", response_model=List[ListingResponse])
def get_all_listings_admin(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Lists all platform listings for administrative moderation.
    """
    return db.query(Listing).order_by(desc(Listing.created_at)).all()


@router.put("/listings/{listing_id}/toggle-semester")
def toggle_semester_resource(
    listing_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Marks or unmarks a listing as 'Popular This Semester' for homepage highlight.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    listing.is_semester_resource = not listing.is_semester_resource
    db.commit()
    db.refresh(listing)

    state = "featured in Semester Resources" if listing.is_semester_resource else "unfeatured"
    return {"message": f"Listing '{listing.title}' is now {state}.", "is_semester_resource": listing.is_semester_resource}


@router.delete("/listings/{listing_id}")
def remove_listing_admin(
    listing_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Moderator action to remove an inappropriate listing.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    db.delete(listing)
    db.commit()
    return {"message": f"Listing '{listing.title}' removed by admin."}


@router.get("/reports", response_model=List[ReportResponse])
def get_all_reports(
    status_filter: Optional[str] = Query(None, description="OPEN, REVIEWING, RESOLVED, REJECTED"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Lists all dispute and moderation reports filed by students.
    """
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    return query.order_by(desc(Report.created_at)).all()


@router.put("/reports/{report_id}", response_model=ReportResponse)
def update_report_status(
    report_id: int,
    payload: ReportStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Updates the resolution status and notes of a filed report.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    report.status = payload.status
    if payload.resolution_notes:
        report.resolution_notes = payload.resolution_notes.strip()

    db.commit()
    db.refresh(report)
    return report


@router.get("/rentals", response_model=List[RentalResponse])
def get_all_rentals_admin(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Returns all campus rentals with live overdue checks and countdown details.
    """
    sync_overdue_rentals(db)
    rentals = db.query(Rental).order_by(desc(Rental.created_at)).all()

    for r in rentals:
        info = get_countdown_details(r)
        r.days_remaining = info["days_remaining"]
        r.countdown_text = info["countdown_text"]

    return rentals
