from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Organization, User
from ..schemas import OrgCreate, OrgOut
from ..deps import get_current_user, require_role

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])

@router.get("", response_model=list[OrgOut])
def list_orgs(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Platform admins see all; others see own org only (tenant isolation)
    if current.role == "platform_admin":
        return db.query(Organization).all()
    return db.query(Organization).filter(Organization.id == current.organization_id).all()

@router.post("", response_model=OrgOut)
def create_org(payload: OrgCreate, current: User = Depends(require_role("platform_admin")), db: Session = Depends(get_db)):
    if db.query(Organization).filter(Organization.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Code already exists")
    org = Organization(name=payload.name, code=payload.code, type=payload.type, state=payload.state)
    db.add(org); db.commit(); db.refresh(org)
    return org

@router.get("/{org_id}", response_model=OrgOut)
def get_org(org_id: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    if current.role != "platform_admin" and org.id != current.organization_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
    return org
