"""
CRUD helpers for Device — database access only, no HTTP logic.
"""

from sqlalchemy.orm import Session

from models.device import Device
from schemas.device import DeviceCreate, DeviceUpdate


def get_device(db: Session, device_id: int) -> Device | None:
    return db.query(Device).filter(Device.id == device_id).first()


def get_devices(db: Session, skip: int = 0, limit: int = 100) -> list[Device]:
    return db.query(Device).offset(skip).limit(limit).all()


def create_device(db: Session, device_in: DeviceCreate) -> Device:
    db_device = Device(
        hostname=device_in.hostname,
        ip_address=device_in.ip_address,
        operating_system=device_in.operating_system,
        status=device_in.status.value,
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
    device.owner_id = device_in.owner_id
    db.commit()
    db.refresh(device)
    return device
