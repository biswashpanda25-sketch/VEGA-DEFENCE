"""Administration: users, connectors, connector SDK, health, model + AI usage monitoring."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Connector, Dataset, Entity, AIConversation, Organization
from ..schemas import OrgCreate
from ..deps import get_current_user, require_role, audit
from ..services import connectors as connector_sdk
from ..services import jobs as job_service

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/users")
def list_users(current: User = Depends(require_role("platform_admin", "org_admin")), db: Session = Depends(get_db)):
    q = db.query(User)
    if current.role != "platform_admin":
        q = q.filter(User.organization_id == current.organization_id)
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role,
             "is_active": u.is_active, "organization_id": u.organization_id,
             "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None} for u in q.all()]

@router.patch("/users/{user_id}/role")
def set_role(user_id: str, role: str, current: User = Depends(require_role("platform_admin", "org_admin")),
             db: Session = Depends(get_db)):
    valid = {"platform_admin", "org_admin", "data_admin", "analyst", "reviewer", "readonly", "auditor"}
    if role not in valid: raise HTTPException(400, f"role must be one of {sorted(valid)}")
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404, "User not found")
    if current.role != "platform_admin" and u.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    if current.role == "org_admin" and role == "platform_admin":
        raise HTTPException(403, "Only a platform administrator may grant platform_admin")
    u.role = role; db.commit()
    audit(db, current, "admin.role_change", u.id, f"{u.email} -> {role}")
    return {"id": u.id, "role": u.role}

@router.get("/connectors")
def list_connectors(current: User = Depends(require_role("platform_admin", "org_admin", "data_admin")),
                    db: Session = Depends(get_db)):
    q = db.query(Connector)
    if current.role != "platform_admin":
        q = q.filter(Connector.organization_id == current.organization_id)
    return [{"id": c.id, "name": c.name, "kind": c.kind, "status": c.status,
             "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None,
             "last_error": c.last_error, "config": {k: v for k, v in (c.config or {}).items()
                                                    if k not in {"password", "token", "api_key", "secret"}}} for c in q.all()]

@router.get("/system-health")
def system_health(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import platform, os
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"database": "ok" if db_ok else "error",
            "api": "ok", "runtime": f"python {platform.python_version()}",
            "ai_provider": os.getenv("AI_PROVIDER", "grounded-local"),
            "counts": {"users": db.query(User).count(), "organizations": db.query(Organization).count(),
                       "datasets": db.query(Dataset).count(), "entities": db.query(Entity).count()}}

@router.get("/ai-usage")
def ai_usage(current: User = Depends(require_role("platform_admin", "org_admin", "auditor")),
             db: Session = Depends(get_db)):
    q = db.query(AIConversation)
    if current.role != "platform_admin":
        q = q.filter(AIConversation.organization_id == current.organization_id)
    rows = q.all()
    cited = sum(1 for r in rows if r.citations)
    return {"queries": len(rows),
            "queries_with_citations": cited,
            "citation_coverage": round(cited / len(rows), 3) if rows else 0.0,
            "note": "External model tokens are only recorded when AI_PROVIDER is not grounded-local."}


@router.get("/connector-catalog")
def connector_catalog(current: User = Depends(get_current_user)):
    """Connector SDK catalogue with honest implementation status per kind."""
    return {"connectors": connector_sdk.catalog(),
            "note": "Kinds marked requires_credentials refuse to run until an authorized endpoint and "
                    "credential are supplied; they are never reported healthy without a verified call."}


@router.post("/connectors/{connector_id}/health-check")
def connector_health(connector_id: str,
                     current: User = Depends(require_role("platform_admin", "org_admin", "data_admin")),
                     db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    c = db.query(Connector).filter(Connector.id == connector_id).first()
    if not c:
        raise HTTPException(404, "Connector not found")
    if current.role != "platform_admin" and c.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    try:
        impl = connector_sdk.get_connector(c.kind, c.config or {})
        report = impl.health_check()
    except connector_sdk.ConnectorConfigError as e:
        raise HTTPException(400, str(e))
    c.status = "healthy" if report.healthy and report.verified else "error"
    c.last_error = None if report.healthy else report.detail
    c.last_run_at = datetime.now(timezone.utc)
    db.commit()
    audit(db, current, "connector.health_check", c.id, f"{c.kind}: {report.detail}")
    return {"connector_id": c.id, "kind": c.kind, "status": c.status,
            "detail": report.detail, "verified": report.verified}


@router.get("/jobs")
def list_jobs(status: str | None = None, limit: int = 100,
              current: User = Depends(require_role("platform_admin", "org_admin", "data_admin")),
              db: Session = Depends(get_db)):
    """Ingestion job ledger: attempts, retries and dead-lettered payloads."""
    org = None if current.role == "platform_admin" else current.organization_id
    rows = job_service.list_jobs(db, org, status, limit)
    return [{"id": j.id, "status": j.status, "attempts": j.attempts, "max_attempts": j.max_attempts,
             "dataset_id": j.dataset_id, "payload_ref": j.payload_ref, "last_error": j.last_error,
             "result": j.result, "created_at": j.created_at.isoformat()} for j in rows]
