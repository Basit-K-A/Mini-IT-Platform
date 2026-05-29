"""
Health endpoints for load balancers, Docker health checks, and monitoring.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.limiter import limiter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
@limiter.exempt
def health_liveness(request: Request):
    """Process is up — does not check the database."""
    return {
        "status": "ok",
        "service": "nexventory-api",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.get("/health/ready")
@limiter.exempt
def health_readiness(request: Request, db: Session = Depends(get_db)):
    """API can serve traffic and reach PostgreSQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        )
    return {"status": "ok", "database": "connected"}
