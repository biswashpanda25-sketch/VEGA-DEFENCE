"""Ingestion job ledger with bounded retries and dead-letter handling.

In this build the worker runs in-request (no broker available), but the *semantics* are those of a queue:
every attempt is recorded, transient failures are retried with exponential backoff, exhausted jobs move to
`dead_letter` and are replayable by an operator. Wrapping `execute` in RQ/Celery later requires no change to
the callers.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import ConnectorJob

BACKOFF_BASE_S = 0.05  # deliberately short in-request; a real worker uses seconds-to-minutes


def create_job(db: Session, *, organization_id: str, connector_id: str | None, dataset_id: str | None,
               payload_ref: str = "", max_attempts: int = 3) -> ConnectorJob:
    job = ConnectorJob(organization_id=organization_id, connector_id=connector_id,
                       dataset_id=dataset_id, payload_ref=payload_ref,
                       status="queued", max_attempts=max_attempts)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def execute(db: Session, job: ConnectorJob, fn):
    """Run `fn()` with retries. Returns (result, job). Raises the final exception when dead-lettered."""
    last_error: Exception | None = None
    for attempt in range(1, (job.max_attempts or 3) + 1):
        job.attempts = attempt
        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        try:
            result = fn()
            job.status = "succeeded"
            job.result = result if isinstance(result, dict) else {"result": str(result)}
            job.last_error = ""
            db.commit()
            return result, job
        except Exception as e:  # noqa: BLE001 - every failure is recorded, none are swallowed
            last_error = e
            job.last_error = f"{type(e).__name__}: {e}"[:500]
            job.status = "retrying" if attempt < (job.max_attempts or 3) else "dead_letter"
            db.commit()
            if attempt < (job.max_attempts or 3):
                time.sleep(BACKOFF_BASE_S * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error


def list_jobs(db: Session, organization_id: str | None, status: str | None = None, limit: int = 100):
    q = db.query(ConnectorJob)
    if organization_id:
        q = q.filter(ConnectorJob.organization_id == organization_id)
    if status:
        q = q.filter(ConnectorJob.status == status)
    return q.order_by(ConnectorJob.created_at.desc()).limit(limit).all()
