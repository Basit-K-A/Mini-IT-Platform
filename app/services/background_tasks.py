"""
Background task framework — defers non-critical work from HTTP request lifecycle.

Uses FastAPI BackgroundTasks today; tasks receive their own DB session.
Designed so Celery/RQ workers can call the same task functions later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import BackgroundTasks

from database import SessionLocal

logger = logging.getLogger("nexventory.tasks")


@dataclass
class AuditTaskPayload:
    action: str
    endpoint: str
    ip_address: str
    status_code: int
    user_id: int | None = None
    details: str | None = None


def run_with_db(task_name: str, fn, *args, **kwargs) -> None:
    """Execute a callable with a fresh SQLAlchemy session."""
    db = SessionLocal()
    try:
        fn(db, *args, **kwargs)
    except Exception:
        logger.exception("Background task failed: %s", task_name)
    finally:
        db.close()


def _persist_audit_log(db, payload: AuditTaskPayload) -> None:
    from crud import audit as audit_crud
    from services.cache import invalidate_audit_summaries

    audit_crud.create_audit_log(
        db,
        action=payload.action,
        endpoint=payload.endpoint,
        ip_address=payload.ip_address,
        status_code=payload.status_code,
        user_id=payload.user_id,
        details=payload.details,
    )
    invalidate_audit_summaries()


def schedule_audit_log(
    background_tasks: BackgroundTasks,
    payload: AuditTaskPayload,
) -> None:
    """Queue audit persistence and cache invalidation after response is sent."""
    background_tasks.add_task(
        run_with_db,
        "audit_log",
        _persist_audit_log,
        payload,
    )


def schedule_cache_invalidation(
    background_tasks: BackgroundTasks,
    invalidator: str,
) -> None:
    """Run cache invalidation after response (inventory vs audit namespaces)."""
    from services import cache as cache_svc

    def _run() -> None:
        if invalidator == "inventory":
            cache_svc.invalidate_inventory()
        elif invalidator == "audit":
            cache_svc.invalidate_audit_summaries()
        elif invalidator == "dashboard":
            cache_svc.invalidate_dashboard()

    background_tasks.add_task(_run)


def schedule_placeholder(
    background_tasks: BackgroundTasks,
    task_name: str,
    **context: Any,
) -> None:
    """
    Hook for future exports / email notifications.

    Logs intent today without blocking the request path.
    """
    def _log() -> None:
        logger.info("Background task queued (stub): %s context=%s", task_name, context)

    background_tasks.add_task(_log)
