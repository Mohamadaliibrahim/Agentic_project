from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from database_factory import initialize_database, close_database
from routes_basic import router as basic_router
from routes_users import router as users_router
from routes_messages import router as messages_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Bot backend is starting up...")
    await initialize_database()
    print("Server will be available at: http://127.0.0.1:8012")
    print("API documentation available at: http://127.0.0.1:8012/docs")
    yield
    print("Bot backend is shutting down...")
    await close_database()

app = FastAPI(
    title="Bot API",
    description="A simple FastAPI bot backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(basic_router)
app.include_router(users_router)
app.include_router(messages_router)

if __name__ == "__main__":
    print("Starting Bot Backend Server...")
    print("=" * 50)
    # start up functions, logging, startup.py
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8012,
        reload=True,
        log_level="info"
    )
