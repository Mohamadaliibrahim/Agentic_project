"""
Basic Routes
Root and health check endpoints
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/", tags=["Basic"])
def read_root():
    """
    Root endpoint - returns a welcome message
    """
    return {"message": "Welcome to Bot API", "status": "running"}

@router.get("/health", tags=["Basic"])
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "Bot backend is running successfully"}
