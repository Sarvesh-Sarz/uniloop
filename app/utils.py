"""
Utility Functions & Helpers

Contains helper functions for:
- University email domain validation
- Image/file uploads to local static storage (easily swappable for S3 later)
- Date formatting and helpers
"""

import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

UNIVERSITY_EMAIL_DOMAIN = os.getenv("UNIVERSITY_EMAIL_DOMAIN", "@university.edu").lower()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"}


def validate_university_email(email: str) -> bool:
    """
    Validates whether the provided email belongs to the configured university domain.
    E.g., if domain is '@university.edu', 'student@university.edu' is valid.
    """
    if not email:
        return False
    return email.strip().lower().endswith(UNIVERSITY_EMAIL_DOMAIN)


def save_upload_file(file: UploadFile) -> str:
    """
    Saves an uploaded file to the local uploads directory.
    Generates a unique filename using UUID to prevent collisions.
    Returns the relative URL path to access the file via static files.
    """
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Extract and validate file extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Write file stream to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return f"/uploads/{unique_name}"
