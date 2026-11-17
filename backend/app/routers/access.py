"""Access-control surface: audit-chain verification, clearance administration, MFA enrolment."""
import io
import base64
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pyotp

from ..db import get_db
from ..models import User
from ..deps import get_current_user, require_role, audit, verify_audit_chain
from ..policy import CLASSIFICATION_RANK

router = APIRouter(prefix="/api/v1", tags=["access"])


@router.get("/audit/verify")
def verify_chain(current: User = Depends(require_role("platform_admin", "org_admin", "auditor")),
                 db: Session = Depends(get_db)):
    """Recompute the SHA-256 hash chain over the audit log and report the first broken link."""
    result = verify_audit_chain(db)
    audit(db, current, "audit.verify", "audit_events",
          f"valid={result['valid']} checked={result['checked']}")
    return result


@router.get("/admin/clearances")
def list_clearances(current: User = Depends(require_role("platform_admin", "org_admin")),
                    db: Session = Depends(get_db)):
    q = db.query(User)
    if current.role != "platform_admin":
        q = q.filter(User.organization_id == current.organization_id)
    return {
        "levels": list(CLASSIFICATION_RANK.keys()),
        "users": [{"id": u.id, "email": u.email, "role": u.role,
                   "clearance": u.clearance or "INTERNAL", "mfa_enabled": u.mfa_enabled} for u in q.all()],
    }


@router.patch("/admin/users/{user_id}/clearance")
def set_clearance(user_id: str, clearance: str,
                  current: User = Depends(require_role("platform_admin", "org_admin")),
                  db: Session = Depends(get_db)):
    if clearance not in CLASSIFICATION_RANK:
        raise HTTPException(400, f"clearance must be one of {list(CLASSIFICATION_RANK)}")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    if current.role != "platform_admin" and u.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    if current.role == "org_admin" and clearance == "PROTECTED":
        raise HTTPException(403, "Only a platform administrator may grant PROTECTED clearance")
    previous = u.clearance
    u.clearance = clearance
    db.commit()
    audit(db, current, "admin.clearance_change", u.id, f"{u.email}: {previous} -> {clearance}")
    return {"id": u.id, "clearance": u.clearance}


@router.post("/auth/mfa/enroll")
def mfa_enroll(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Begin TOTP enrolment. The secret is returned once, for the authenticator app."""
    user = db.query(User).filter(User.id == current.id).first()
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="VEGA INDIA")
    audit(db, current, "auth.mfa_enroll_started", user.id, "TOTP secret issued")
    return {"secret": secret, "otpauth_uri": uri,
            "next": "POST /api/v1/auth/mfa/activate with a valid 6-digit code from your authenticator"}


@router.post("/auth/mfa/activate")
def mfa_activate(code: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current.id).first()
    if not user.mfa_secret:
        raise HTTPException(400, "Start enrolment first")
    if not pyotp.TOTP(user.mfa_secret).verify(code, valid_window=1):
        audit(db, current, "auth.mfa_activate_failed", user.id, "invalid TOTP code")
        raise HTTPException(400, "Invalid code")
    user.mfa_enabled = True
    db.commit()
    audit(db, current, "auth.mfa_activated", user.id, "MFA enforced for this account")
    return {"mfa_enabled": True}


@router.post("/auth/mfa/verify")
def mfa_verify(code: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Step-up re-verification for sensitive actions (e.g. clearance changes, exports)."""
    user = db.query(User).filter(User.id == current.id).first()
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(400, "MFA is not enabled for this account")
    if not pyotp.TOTP(user.mfa_secret).verify(code, valid_window=1):
        audit(db, current, "auth.mfa_stepup_failed", user.id, "invalid TOTP code")
        raise HTTPException(401, "Invalid code")
    audit(db, current, "auth.mfa_stepup", user.id, "step-up verification passed")
    return {"verified": True}
