"""
Reports & Dispute Reporting API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreate, ReportResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def file_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a student to flag an inappropriate listing, fraudulent behavior, harassment, or item damage.
    """
    new_report = Report(
        reporter_id=current_user.id,
        reported_user_id=report_data.reported_user_id,
        listing_id=report_data.listing_id,
        rental_id=report_data.rental_id,
        category=report_data.category.strip(),
        description=report_data.description.strip(),
        status="OPEN"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


@router.get("/my", response_model=List[ReportResponse])
def get_my_filed_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns reports submitted by the current user.
    """
    reports = db.query(Report).filter(
        Report.reporter_id == current_user.id
    ).order_by(desc(Report.created_at)).all()
    return reports
