"""Unit tests for password policy, hashing, and authenticate_user."""

import pytest

from auth.password_policy import validate_password_strength
from auth.security import authenticate_user, get_password_hash, verify_password

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "password",
    ["StrongP@ss1", "An0ther!Pass", "Zz9#zzzzz"],
)
def test_strong_passwords_pass(password):
    # Should not raise
    validate_password_strength(password)


@pytest.mark.parametrize(
    "password",
    [
        "short1!A",  # 8 chars but ok? -> actually valid; replaced below
        "alllowercase1!",  # no uppercase
        "ALLUPPERCASE1!",  # no lowercase
        "NoNumber!!",  # no digit
        "NoSpecial123",  # no special char
        "weak",  # too short / missing classes
    ],
)
def test_weak_passwords_rejected(password):
    if password == "short1!A":
        # This one actually satisfies all classes; ensure it passes instead.
        validate_password_strength(password)
        return
    with pytest.raises(ValueError):
        validate_password_strength(password)


def test_password_hash_and_verify():
    hashed = get_password_hash("StrongP@ss1")
    assert hashed != "StrongP@ss1"
    assert verify_password("StrongP@ss1", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_authenticate_user_success(db_session, make_user):
    make_user(username="carol", password="StrongP@ss1")
    user = authenticate_user(db_session, "carol", "StrongP@ss1")
    assert user is not None
    assert user.username == "carol"


def test_authenticate_user_wrong_password(db_session, make_user):
    make_user(username="dave", password="StrongP@ss1")
    assert authenticate_user(db_session, "dave", "nope") is None


def test_authenticate_user_unknown(db_session):
    # No user created — should return None without raising (and runs dummy hash path).
    assert authenticate_user(db_session, "ghost", "whatever") is None
