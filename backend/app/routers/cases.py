"""Analytical workspaces / cases with findings, evidence refs and reviewer workflow."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Case, Finding, User, Entity
from ..schemas import CaseCreate, CaseOut, FindingCreate, FindingOut
from ..deps import get_current_user, require_role, audit

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
VALID_KINDS = {"evidence", "assumption", "hypothesis", "conclusion"}

def _scoped(db, current):
    q = db.query(Case)
    if current.role != "platform_admin":
        q = q.filter(Case.organization_id == current.organization_id)
    return q

@router.get("", response_model=list[CaseOut])
def list_cases(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _scoped(db, current).order_by(Case.updated_at.desc()).all()

@router.post("", response_model=CaseOut)
def create_case(payload: CaseCreate,
                current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst", "reviewer")),
                db: Session = Depends(get_db)):
    c = Case(organization_id=current.organization_id, created_by=current.email, **payload.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    audit(db, current, "case.create", c.id, c.title)
    return c

@router.get("/{case_id}")
def get_case(case_id: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = _scoped(db, current).filter(Case.id == case_id).first()
    if not c: raise HTTPException(404, "Case not found")
    findings = db.query(Finding).filter(Finding.case_id == c.id).order_by(Finding.created_at).all()
    return {"case": {"id": c.id, "title": c.title, "description": c.description, "status": c.status,
                     "classification": c.classification, "created_by": c.created_by,
                     "created_at": c.created_at.isoformat()},
            "findings": [{"id": f.id, "title": f.title, "description": f.description, "kind": f.kind,
                          "confidence": f.confidence, "evidence_refs": f.evidence_refs,
                          "reviewer_status": f.reviewer_status, "created_by": f.created_by,
                          "created_at": f.created_at.isoformat()} for f in findings]}

@router.post("/{case_id}/findings", response_model=FindingOut)
def add_finding(case_id: str, payload: FindingCreate,
                current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst", "reviewer")),
                db: Session = Depends(get_db)):
    c = _scoped(db, current).filter(Case.id == case_id).first()
    if not c: raise HTTPException(404, "Case not found")
    if payload.kind not in VALID_KINDS:
        raise HTTPException(400, f"kind must be one of {sorted(VALID_KINDS)}")
    # Evidence enforcement: non-assumption findings must cite at least one entity in-tenant
    if payload.kind in {"evidence", "conclusion"} and not payload.evidence_refs:
        raise HTTPException(400, "Evidence and conclusion findings require at least one evidence reference")
    for ref in payload.evidence_refs:
        ok = db.query(Entity).filter(Entity.id == ref, Entity.organization_id == c.organization_id).first()
        if not ok:
            raise HTTPException(400, f"Evidence reference {ref} not found in case organization")
    f = Finding(case_id=c.id, organization_id=c.organization_id, created_by=current.email, **payload.model_dump())
    db.add(f); db.commit(); db.refresh(f)
    audit(db, current, "finding.create", f.id, f"{payload.kind}: {payload.title}")
    return f

@router.post("/{case_id}/findings/{finding_id}/review")
def review_finding(case_id: str, finding_id: str, decision: str = "approved",
                   current: User = Depends(require_role("platform_admin", "org_admin", "reviewer")),
                   db: Session = Depends(get_db)):
    if decision not in {"approved", "rejected", "needs_revision"}:
        raise HTTPException(400, "decision must be approved|rejected|needs_revision")
    f = db.query(Finding).filter(Finding.id == finding_id, Finding.case_id == case_id).first()
    if not f: raise HTTPException(404, "Finding not found")
    if current.role != "platform_admin" and f.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    f.reviewer_status = decision
    db.commit()
    audit(db, current, "finding.review", f.id, f"{decision} by {current.email}")
    return {"id": f.id, "reviewer_status": f.reviewer_status}
