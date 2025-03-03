"""
API V1 Package

This package contains the V1 API routers and handlers for the application.
"""

from fastapi import APIRouter

# Create the main v1 router
v1_router = APIRouter(prefix="/api/v1")

# Import and include the individual routers
from .scheduler import router as scheduler_router

# Include the routers in the main router
v1_router.include_router(scheduler_router)
