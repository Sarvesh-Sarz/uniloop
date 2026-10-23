"""
Database Configuration & Session Management

This module sets up SQLAlchemy ORM:
- Creates the database engine connecting to PostgreSQL (or SQLite local fallback).
- Configures SessionLocal for database transaction management.
- Provides the get_db() dependency for FastAPI endpoints.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Database connection URL from environment, defaulting to local SQLite for instant setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uniloop.db")

# SQLite requires 'check_same_thread: False' to allow multiple threads to interact with the database
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine
# pool_pre_ping checks the connection liveness before executing queries
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True if not DATABASE_URL.startswith("sqlite") else False
)

# Each instance of SessionLocal is a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy database models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a transactional database session per request.
    Closes the session automatically when the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
