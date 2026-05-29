"""
Device API routes.

Uses Depends(get_db) so each request gets its own SQLAlchemy session.
RBAC: read = any authenticated user; write = admin or technician.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth.roles import require_any_role
from auth.security import get_current_active_user
from constants.audit_actions import AuditAction
from constants.roles import ROLE_ADMIN, ROLE_TECHNICIAN
from crud import device as device_crud
from crud import user as user_crud
from database import get_db
from models.user import User
from schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate
from services.audit import log_audit

router = APIRouter(prefix="/devices", tags=["devices"])

# Reusable RBAC dependencies for this router
RequireDeviceWrite = require_any_role(ROLE_ADMIN, ROLE_TECHNICIAN)


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    device_in: DeviceCreate,
    request: Request,
    current_user: Annotated[User, Depends(RequireDeviceWrite)],
    db: Session = Depends(get_db),
):
    if not user_crud.get_user_by_id(db, device_in.owner_id):
        raise HTTPException(status_code=404, detail="Owner user not found")
    device = device_crud.create_device(db, device_in)
    log_audit(
        db,
        request,
        action=AuditAction.DEVICE_CREATED,
        status_code=status.HTTP_201_CREATED,
        user_id=current_user.id,
        details=f"device_id={device.id} hostname={device.hostname}",
    )
    return device


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    _current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Read-only: all authenticated roles (viewer, analyst, technician, admin)."""
    return device_crud.get_devices(db, skip=skip, limit=limit)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: int,
    device_in: DeviceUpdate,
    request: Request,
    current_user: Annotated[User, Depends(RequireDeviceWrite)],
    db: Session = Depends(get_db),
):
    device = device_crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not user_crud.get_user_by_id(db, device_in.owner_id):
        raise HTTPException(status_code=404, detail="Owner user not found")
    updated = device_crud.update_device(db, device, device_in)
    log_audit(
        db,
        request,
        action=AuditAction.DEVICE_UPDATED,
        status_code=status.HTTP_200_OK,
        user_id=current_user.id,
        details=f"device_id={device_id} hostname={updated.hostname}",
    )
    return updated
