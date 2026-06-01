"""
CRUD helpers for Device — database access only, no HTTP logic.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.query import apply_exact_filters, apply_ilike_filters, apply_sort, paginate
from dependencies.list_params import DeviceListParams
from models.device import Device
from schemas.device import DeviceCreate, DeviceUpdate
from schemas.pagination import PaginationMeta

_DEVICE_SORT_COLUMNS = {
    "id": Device.id,
    "hostname": Device.hostname,
    "status": Device.status,
    "department": Device.department,
    "owner_id": Device.owner_id,
    "created_at": Device.created_at,
    "ip_address": Device.ip_address,
    "operating_system": Device.operating_system,
}


def get_device(db: Session, device_id: int) -> Device | None:
    return db.query(Device).filter(Device.id == device_id).first()


def list_devices(
    db: Session,
    params: DeviceListParams,
) -> tuple[list[Device], PaginationMeta]:
    query = db.query(Device)
    query = apply_exact_filters(
        query,
        Device,
        {
            "status": params.status,
            "department": params.department,
            "owner_id": params.owner_id,
            "operating_system": params.operating_system,
        },
    )
    query = apply_ilike_filters(query, Device, {"hostname": params.hostname})

    try:
        query = apply_sort(
            query,
            allowed_columns=_DEVICE_SORT_COLUMNS,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            default_column=Device.created_at,
            default_desc=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return paginate(query, page=params.page, limit=params.limit)


def create_device(db: Session, device_in: DeviceCreate) -> Device:
    db_device = Device(
        hostname=device_in.hostname,
        ip_address=device_in.ip_address,
        operating_system=device_in.operating_system,
        status=device_in.status.value,
        department=device_in.department,
        owner_id=device_in.owner_id,
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def update_device(db: Session, device: Device, device_in: DeviceUpdate) -> Device:
    device.hostname = device_in.hostname
    device.ip_address = device_in.ip_address
    device.operating_system = device_in.operating_system
    device.status = device_in.status.value
    device.department = device_in.department
    device.owner_id = device_in.owner_id
    db.commit()
    db.refresh(device)
    return device
