"""
Basic Routes
Root and health check endpoints
"""

from fastapi import APIRouter
from core.mistral_service import mistral_service

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

@router.get("/ai-health", tags=["Basic"])
async def ai_health_check():
    """
    AI service health check endpoint
    """
    ai_status = await mistral_service.health_check()
    return {
        "ai_service": "available" if ai_status else "unavailable",
        "model": mistral_service.model,
        "message": "AI service is ready" if ai_status else "AI service is not configured or unavailable"
    }
