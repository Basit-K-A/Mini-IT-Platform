"""Unit tests for Device CRUD operations (business logic, no HTTP)."""

from types import SimpleNamespace

import pytest

from crud import device as device_crud
from schemas.device import DeviceCreate, DeviceUpdate

pytestmark = pytest.mark.unit


def _device_in(hostname="srv-01", ip="10.0.0.1", os_="Ubuntu 22.04", status="active",
               department="IT", owner_id=1):
    return DeviceCreate(
        hostname=hostname,
        ip_address=ip,
        operating_system=os_,
        status=status,
        department=department,
        owner_id=owner_id,
    )


def _list_params(**overrides):
    base = {
        "page": 1,
        "limit": 10,
        "sort_by": None,
        "sort_order": "desc",
        "status": None,
        "department": None,
        "owner_id": None,
        "operating_system": None,
        "hostname": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
def owner(make_user):
    return make_user(username="owner1", role="technician")


def test_create_device(db_session, owner):
    device = device_crud.create_device(db_session, _device_in(owner_id=owner.id))
    assert device.id is not None
    assert device.hostname == "srv-01"
    assert device.status == "active"
    assert device_crud.get_device(db_session, device.id) is not None


def test_update_device(db_session, owner):
    device = device_crud.create_device(db_session, _device_in(owner_id=owner.id))
    update = DeviceUpdate(
        hostname="srv-renamed",
        ip_address="10.0.0.2",
        operating_system="Debian 12",
        status="maintenance",
        department="Finance",
        owner_id=owner.id,
    )
    updated = device_crud.update_device(db_session, device, update)
    assert updated.hostname == "srv-renamed"
    assert updated.status == "maintenance"
    assert updated.department == "Finance"


def test_delete_device(db_session, owner):
    device = device_crud.create_device(db_session, _device_in(owner_id=owner.id))
    device_id = device.id
    device_crud.delete_device(db_session, device)
    assert device_crud.get_device(db_session, device_id) is None


def test_list_devices_pagination_and_filter(db_session, owner):
    for i in range(15):
        device_crud.create_device(
            db_session,
            _device_in(hostname=f"host-{i:02d}", owner_id=owner.id,
                       status="active" if i % 2 == 0 else "offline"),
        )

    items, meta = device_crud.list_devices(db_session, _list_params(page=1, limit=10))
    assert len(items) == 10
    assert meta.total_records == 15
    assert meta.total_pages == 2
    assert meta.current_page == 1

    # Filter by status
    active_items, active_meta = device_crud.list_devices(
        db_session, _list_params(status="active", limit=100)
    )
    assert active_meta.total_records == 8
    assert all(d.status == "active" for d in active_items)


def test_list_devices_sort_by_hostname(db_session, owner):
    for name in ["bbb", "aaa", "ccc"]:
        device_crud.create_device(db_session, _device_in(hostname=name, owner_id=owner.id))
    items, _ = device_crud.list_devices(
        db_session, _list_params(sort_by="hostname", sort_order="asc", limit=100)
    )
    hostnames = [d.hostname for d in items]
    assert hostnames == sorted(hostnames)
