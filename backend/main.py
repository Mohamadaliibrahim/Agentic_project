from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from contextlib import asynccontextmanager

from core.config import settings
from core.logger import app_logger, get_logger
from database.factory import initialize_database, close_database
from routes.basic import router as basic_router
from routes.users import router as users_router
from routes.messages import router as messages_router
from routes.documents import router as documents_router
from routes.orchestrator import router as orchestrator_router
from startup import startup_check_sync

# Initialize logging first
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Bot backend is starting up...")
    app_logger.log_startup()
    
    try:
        await initialize_database()
        logger.info(f"Server will be available at: http://{settings.HOST}:{settings.PORT}")
        logger.info(f"API documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
        logger.info("Backend startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}", exc_info=True)
        raise
    
    yield
    
    logger.info("Bot backend is shutting down...")
    try:
        await close_database()
        app_logger.log_shutdown()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)

app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(basic_router)
app.include_router(users_router)
app.include_router(messages_router)
app.include_router(documents_router)
app.include_router(orchestrator_router)

if __name__ == "__main__":
    logger.info("Bot Backend Server - Starting Pre-Flight Checks...")
    logger.info("=" * 60)
    
    try:
        if not startup_check_sync():
            logger.error("Startup failed due to health check errors!")
            logger.error("Please fix the above issues and try again.")
            sys.exit(1)
        
        logger.info("All systems ready! Starting FastAPI server...")
        logger.info("=" * 60)
        
        # Start server with logging to file
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            log_level="info",
            access_log=False,  # We handle access logs through our custom logger
            log_config=None    # Disable uvicorn's default logging config
        )
        
    except Exception as e:
        logger.error(f"Critical error starting server: {str(e)}", exc_info=True)
        sys.exit(1)
