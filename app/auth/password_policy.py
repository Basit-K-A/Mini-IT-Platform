"""
Password strength rules for registration — reduces weak-credential risk.
"""

import re

# At least 8 chars, one upper, one lower, one digit, one special character
_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>_\-\[\]\\/]).{8,128}$"
)


def validate_password_strength(password: str) -> None:
    """
    Raise ValueError with a user-safe message if the password is too weak.

    Checks: length 8–128, uppercase, lowercase, digit, special character.
    """
    if _PASSWORD_PATTERN.match(password):
        return
    raise ValueError(
        "Password must be 8–128 characters and include uppercase, lowercase, "
        "a number, and a special character"
    )
