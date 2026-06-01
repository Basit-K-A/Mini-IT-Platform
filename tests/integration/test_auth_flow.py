"""Integration tests for the authentication workflow (register → login → me → refresh)."""

import pytest

pytestmark = pytest.mark.integration


def _register(client, username="alice", password="StrongP@ss1"):
    return client.post(
        "/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )


def test_register_creates_viewer(client):
    resp = _register(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "alice"
    assert body["role"] == "viewer"
    assert "hashed_password" not in body


def test_register_duplicate_username_rejected(client):
    _register(client)
    resp = _register(client)
    assert resp.status_code == 400


def test_login_returns_token_pair(client):
    _register(client)
    resp = client.post("/token", data={"username": "alice", "password": "StrongP@ss1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_unauthorized(client):
    _register(client)
    resp = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401
    body = resp.json()
    # Standardized error envelope
    assert body["error"] is True
    assert "request_id" in body


def test_me_requires_token(client):
    resp = client.get("/users/me/")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    _register(client)
    token = client.post(
        "/token", data={"username": "alice", "password": "StrongP@ss1"}
    ).json()["access_token"]
    resp = client.get("/users/me/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_refresh_returns_new_tokens(client):
    _register(client)
    refresh_token = client.post(
        "/token", data={"username": "alice", "password": "StrongP@ss1"}
    ).json()["refresh_token"]
    resp = client.post("/token/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]
