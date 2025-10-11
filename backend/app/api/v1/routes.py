from fastapi import APIRouter, Depends

from .endpoints import request_logs
from app.core.auth import require_api_key

api_router = APIRouter()

api_router.include_router(
    request_logs.router,
    prefix="/logs",
    tags=["Request Logs & Monitoring"],
    dependencies=[Depends(require_api_key)],
)
