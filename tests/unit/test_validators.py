"""Unit tests for input validation logic (schemas/validators + Pydantic schemas)."""

import pytest

from schemas.device import DeviceCreate
from schemas.user import UserCreate
from schemas.validators import (
    DeviceStatus,
    validate_hostname,
    validate_ip_address,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("hostname", ["srv-01", "db.internal.example", "host123"])
def test_valid_hostnames(hostname):
    assert validate_hostname(hostname) == hostname


@pytest.mark.parametrize("hostname", ["-bad", "bad-", "white space", "x" * 256])
def test_invalid_hostnames(hostname):
    with pytest.raises(ValueError):
        validate_hostname(hostname)


@pytest.mark.parametrize("ip", ["10.0.0.1", "192.168.1.255", "::1", "2001:db8::1"])
def test_valid_ip_addresses(ip):
    assert validate_ip_address(ip) == ip


@pytest.mark.parametrize("ip", ["999.1.1.1", "not-an-ip", "10.0.0"])
def test_invalid_ip_addresses(ip):
    with pytest.raises(ValueError):
        validate_ip_address(ip)


def test_device_create_schema_valid():
    device = DeviceCreate(
        hostname="srv-db-01",
        ip_address="10.0.1.15",
        operating_system="Ubuntu 22.04",
        status="active",
        department="IT",
        owner_id=1,
    )
    assert device.status == DeviceStatus.active
    assert device.owner_id == 1


def test_device_create_rejects_bad_ip():
    with pytest.raises(ValueError):
        DeviceCreate(
            hostname="srv-db-01",
            ip_address="not-an-ip",
            operating_system="Ubuntu 22.04",
            owner_id=1,
        )


def test_device_create_rejects_nonpositive_owner():
    with pytest.raises(ValueError):
        DeviceCreate(
            hostname="srv-db-01",
            ip_address="10.0.1.15",
            operating_system="Ubuntu 22.04",
            owner_id=0,
        )


def test_user_create_defaults_and_role_validation():
    user = UserCreate(username="newuser", email="new@example.com", password="StrongP@ss1")
    assert user.role == "viewer"


def test_user_create_rejects_invalid_role():
    with pytest.raises(ValueError):
        UserCreate(
            username="newuser",
            email="new@example.com",
            password="StrongP@ss1",
            role="superadmin",
        )


def test_user_create_rejects_weak_password():
    with pytest.raises(ValueError):
        UserCreate(username="newuser", email="new@example.com", password="weak")
