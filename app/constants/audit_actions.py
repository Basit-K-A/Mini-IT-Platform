"""
Named audit actions — use these strings in code so logs stay consistent for reporting.
"""


class AuditAction:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    DEVICE_CREATED = "DEVICE_CREATED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    EVENT_CREATED = "EVENT_CREATED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
