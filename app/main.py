"""
CampusShare — Main Application Entry Point

Full-Stack Campus Resource Sharing & Peer-to-Peer Rental Hub
Built with FastAPI, SQLAlchemy ORM, and modern Vanilla HTML/CSS/JS.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.routes import (
    auth_router,
    users_router,
    listings_router,
    rentals_router,
    ratings_router,
    messages_router,
    notifications_router,
    wishlist_router,
    reports_router,
    admin_router,
)

# 1. Initialize Database Tables automatically
Base.metadata.create_all(bind=engine)

# 2. Ensure directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

# 3. Create FastAPI Application
app = FastAPI(
    title="CampusShare API",
    description="Hyperlocal campus resource sharing and peer-to-peer rental hub for university students.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 4. Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Include API Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(listings_router)
app.include_router(rentals_router)
app.include_router(ratings_router)
app.include_router(messages_router)
app.include_router(notifications_router)
app.include_router(wishlist_router)
app.include_router(reports_router)
app.include_router(admin_router)


# 6. Health Check Endpoint
@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "CampusShare API",
        "version": "1.0.0"
    }


# 7. Static file mounts
# Serve user-uploaded listing images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve frontend HTML, CSS, and JS files with html=True so / points to index.html
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
