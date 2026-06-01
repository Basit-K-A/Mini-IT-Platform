"""Integration tests for the health endpoints."""

import pytest

pytestmark = pytest.mark.integration


def test_health_overall(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "nexventory-api"


def test_health_live(client):
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}


def test_health_ready_with_db(client):
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_request_id_header_present(client):
    resp = client.get("/health/live")
    assert "x-request-id" in {k.lower() for k in resp.headers}
