from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from contextlib import asynccontextmanager

from core.config import settings
from database.factory import initialize_database, close_database
from routes.basic import router as basic_router
from routes.users import router as users_router
from routes.messages import router as messages_router
from startup import startup_check_sync

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Bot backend is starting up...")
    await initialize_database()
    print(f"Server will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"API documentation available at: http://{settings.HOST}:{settings.PORT}/docs")
    yield
    print("Bot backend is shutting down...")
    await close_database()

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

if __name__ == "__main__":
    print("Bot Backend Server - Starting Pre-Flight Checks...")
    print("=" * 60)
    
    if not startup_check_sync():
        print("\nStartup failed due to health check errors!")
        print("Please fix the above issues and try again.")
        sys.exit(1)
    
    print("\nAll systems ready! Starting FastAPI server...")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL
    )
