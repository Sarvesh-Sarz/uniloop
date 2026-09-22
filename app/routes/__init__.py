"""
API Routes Package
"""

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.listings import router as listings_router
from app.routes.rentals import router as rentals_router
from app.routes.ratings import router as ratings_router
from app.routes.messages import router as messages_router
from app.routes.notifications import router as notifications_router
from app.routes.wishlist import router as wishlist_router
from app.routes.reports import router as reports_router
from app.routes.admin import router as admin_router

__all__ = [
    "auth_router",
    "users_router",
    "listings_router",
    "rentals_router",
    "ratings_router",
    "messages_router",
    "notifications_router",
    "wishlist_router",
    "reports_router",
    "admin_router",
]
