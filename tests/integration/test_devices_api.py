"""Integration tests for Device API: create/update/delete + DB persistence."""

import pytest

pytestmark = pytest.mark.integration


def _device_body(owner_id, hostname="srv-01"):
    return {
        "hostname": hostname,
        "ip_address": "10.0.1.20",
        "operating_system": "Ubuntu 22.04",
        "status": "active",
        "department": "IT",
        "owner_id": owner_id,
    }


def test_admin_can_create_and_list_device(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    headers = auth_header(admin.username)

    create = client.post("/devices", json=_device_body(admin.id), headers=headers)
    assert create.status_code == 201
    created = create.json()
    assert created["hostname"] == "srv-01"
    device_id = created["id"]

    listing = client.get("/devices", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["pagination"]["total_records"] == 1
    assert body["data"][0]["id"] == device_id


def test_create_device_unknown_owner_404(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    resp = client.post(
        "/devices", json=_device_body(owner_id=9999), headers=auth_header(admin.username)
    )
    assert resp.status_code == 404


def test_update_device(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    headers = auth_header(admin.username)
    device_id = client.post(
        "/devices", json=_device_body(admin.id), headers=headers
    ).json()["id"]

    update = _device_body(admin.id, hostname="srv-updated")
    update["status"] = "maintenance"
    resp = client.put(f"/devices/{device_id}", json=update, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["hostname"] == "srv-updated"
    assert resp.json()["status"] == "maintenance"


def test_delete_device(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    headers = auth_header(admin.username)
    device_id = client.post(
        "/devices", json=_device_body(admin.id), headers=headers
    ).json()["id"]

    resp = client.delete(f"/devices/{device_id}", headers=headers)
    assert resp.status_code == 204

    listing = client.get("/devices", headers=headers).json()
    assert listing["pagination"]["total_records"] == 0


def test_create_device_invalid_payload_422(client, make_user, auth_header):
    admin = make_user(username="admin", role="admin")
    bad = _device_body(admin.id)
    bad["ip_address"] = "not-an-ip"
    resp = client.post("/devices", json=bad, headers=auth_header(admin.username))
    assert resp.status_code == 422
