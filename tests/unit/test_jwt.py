"""Unit tests for JWT generation/validation and authentication helpers."""

import time

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from auth.jwt_handler import (
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_access_token,
    validate_refresh_token,
)

pytestmark = pytest.mark.unit


def test_access_token_roundtrip():
    token = create_access_token({"sub": "alice"})
    assert validate_access_token(token) == "alice"
    payload = decode_token(token)
    assert payload["typ"] == "access"
    assert payload["sub"] == "alice"


def test_refresh_token_roundtrip():
    token = create_refresh_token("bob")
    assert validate_refresh_token(token) == "bob"
    assert decode_token(token)["typ"] == "refresh"


def test_access_token_rejected_as_refresh():
    access = create_access_token({"sub": "alice"})
    with pytest.raises(InvalidTokenError):
        validate_refresh_token(access)


def test_refresh_token_rejected_as_access():
    refresh = create_refresh_token("alice")
    with pytest.raises(InvalidTokenError):
        validate_access_token(refresh)


def test_expired_token_is_invalid():
    from datetime import timedelta

    token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        validate_access_token(token)


def test_tampered_signature_is_invalid():
    token = create_access_token({"sub": "alice"})
    forged = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    with pytest.raises(InvalidTokenError):
        decode_token(forged)


def test_token_missing_subject_is_invalid():
    # Manually sign a token without a `sub` but with the access type.
    bad = jwt.encode(
        {"typ": "access", "exp": int(time.time()) + 60}, SECRET_KEY, algorithm="HS256"
    )
    with pytest.raises(InvalidTokenError):
        validate_access_token(bad)
