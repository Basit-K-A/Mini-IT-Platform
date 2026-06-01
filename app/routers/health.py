"""
Health endpoints for load balancers, Docker health checks, and monitoring.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from core.limiter import limiter
from core.redis_client import is_redis_available
from database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.exempt
async def health_liveness(request: Request):
    """Process is up — does not check the database."""
    return {
        "status": "ok",
        "service": "nexventory-api",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cache": "redis" if is_redis_available() else "disabled",
    }


@router.get("/health/ready")
@limiter.exempt
async def health_readiness(request: Request, db: Session = Depends(get_db)):
    """API can serve traffic and reach PostgreSQL (and optionally Redis)."""
    try:
        await run_in_threadpool(db.execute, text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )

    # Redis is optional — degraded cache, not a hard failure
    return {
        "status": "ok",
        "database": "connected",
        "redis": "connected" if is_redis_available() else "unavailable",
    }
