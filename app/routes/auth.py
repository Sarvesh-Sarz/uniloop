"""
Authentication API Endpoints

Routes for:
- Student registration with university domain validation
- User login with password verification and JWT issuance
- Current user profile retrieval (/api/auth/me)
- Demo password reset simulation
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.utils import validate_university_email, UNIVERSITY_EMAIL_DOMAIN

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_student(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Registers a new student account.
    Validates that the email belongs to the configured university domain.
    """
    email_clean = user_data.email.strip().lower()

    # 1. Check university email domain
    if not validate_university_email(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration restricted to university students. Email must end with '{UNIVERSITY_EMAIL_DOMAIN}'."
        )

    # 2. Check if email is already registered
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this university email already exists. Please log in."
        )

    # 3. Create student with baseline trust score of 50
    new_user = User(
        name=user_data.name.strip(),
        email=email_clean,
        password_hash=hash_password(user_data.password),
        department=user_data.department.strip(),
        year=user_data.year.strip(),
        role="student",
        trust_score=50,  # All new students start at 50/100
        average_rating=5.0,
        rating_count=0,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Generate JWT access token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email, "role": new_user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer", "user": new_user}


@router.post("/login", response_model=Token)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user via email and password, returning a signed JWT token.
    """
    email_clean = login_data.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact an administrator."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and permissions.
    """
    return current_user


@router.post("/forgot-password")
def forgot_password_placeholder(payload: dict):
    """
    Simulated password reset flow for demo purposes without external SMTP requirements.
    """
    email = payload.get("email", "")
    return {
        "message": f"If an account exists for {email}, a secure password reset link has been dispatched to your campus inbox."
    }
