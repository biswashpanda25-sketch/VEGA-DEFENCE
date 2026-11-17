from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .security import decode_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)

def get_current_user(request: Request, token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def require_role(*roles):
    def checker(current: User = Depends(get_current_user)):
        if current.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current
    return checker

def audit(db: Session, user: User | None, action: str, resource: str = "", detail: str = "",
          org_id: str | None = None, ip: str = "", purpose: str = ""):
    """Append a hash-chained audit event (tamper-evident; append-only by construction)."""
    from .models import AuditEvent
    from sqlalchemy import func
    head_seq = db.query(func.max(AuditEvent.seq)).scalar() or 0
    last = db.query(AuditEvent).filter(AuditEvent.seq == head_seq).first()
    prev_hash = (last.row_hash if last and last.row_hash else "GENESIS")
    ev = AuditEvent(
        organization_id=org_id or (user.organization_id if user else None),
        user_id=user.id if user else None,
        action=action, resource=resource, detail=detail[:2000], ip_address=ip, purpose=purpose,
        seq=head_seq + 1, prev_hash=prev_hash,
    )
    db.add(ev)
    db.flush()
    ev.row_hash = compute_row_hash(ev)
    db.commit()


def _canonical_ts(value) -> str:
    """Timezone-normalised, microsecond-precision timestamp so hashes survive a database round trip."""
    if not value:
        return ""
    try:
        return value.replace(tzinfo=None).isoformat(timespec="microseconds")
    except (AttributeError, TypeError):
        return str(value)


def compute_row_hash(ev) -> str:
    """SHA-256 over the canonical fields of an audit row, chained to its predecessor."""
    import hashlib, json
    payload = "|".join([
        str(ev.seq or 0),
        str(ev.prev_hash or "GENESIS"),
        str(ev.organization_id or ""),
        str(ev.user_id or ""),
        str(ev.action or ""),
        str(ev.resource or ""),
        str(ev.detail or ""),
        str(ev.purpose or ""),
        str(ev.ip_address or ""),
        _canonical_ts(ev.created_at),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_audit_chain(db: Session, limit: int | None = None) -> dict:
    """Recompute the chain and report the first broken link, if any."""
    from .models import AuditEvent
    q = db.query(AuditEvent).order_by(AuditEvent.seq.asc())
    rows = q.all()
    if limit:
        rows = rows[-limit:]
    prev = rows[0].prev_hash if rows else "GENESIS"
    checked = 0
    for ev in rows:
        if ev.prev_hash != prev:
            return {"valid": False, "checked": checked, "broken_at": ev.id,
                    "reason": "prev_hash does not match predecessor row_hash"}
        expected = compute_row_hash(ev)
        if expected != ev.row_hash:
            return {"valid": False, "checked": checked, "broken_at": ev.id,
                    "reason": "row_hash does not match recomputed hash"}
        prev = ev.row_hash
        checked += 1
    return {"valid": True, "checked": checked, "head": prev, "tail": rows[0].row_hash if rows else None}
