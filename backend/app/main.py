from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import api_router
from app.core.config import settings
from app.middleware import RequestLoggingMiddleware, SecurityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan events
    """
    yield


app = FastAPI(title="Anonymous Chat API", lifespan=lifespan)

allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    RequestLoggingMiddleware,
    log_health_checks=False,  # Don't log health checks in production
    enable_async_logging=True,  # Use async logging for better performance
    log_request_body=True,  # Enable request body logging for payload capture
)

app.add_middleware(
    SecurityMiddleware,
    enable_path_blocking=True,
    enable_rate_limiting=True,
    enable_pattern_detection=True,
    rate_limit_requests=100,
    rate_limit_window=60,
    suspicious_threshold=5,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Anonymous Chat API"}
