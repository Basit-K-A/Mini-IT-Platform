"""
Security severity levels for alerts and dashboard rollups (SIEM-style).

Infrastructure events (devices) use EventSeverity in schemas/validators.py;
this enum is the canonical scale for security monitoring and alerts.
"""

from enum import Enum


class SecuritySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def normalize_event_severity(event_severity: str) -> SecuritySeverity:
    """Map stored event severities to dashboard security levels."""
    s = event_severity.lower()
    if s in ("critical",):
        return SecuritySeverity.CRITICAL
    if s in ("high", "warning"):
        return SecuritySeverity.HIGH
    if s in ("medium",):
        return SecuritySeverity.MEDIUM
    return SecuritySeverity.LOW
