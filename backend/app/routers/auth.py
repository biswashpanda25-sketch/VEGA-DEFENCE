from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, Organization
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from ..security import hash_password, verify_password, create_access_token
from ..deps import get_current_user, audit
from ..auth_limits import is_throttled, record_failure, clear as clear_throttle
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.code == payload.organization_code).first()
    if not org:
        raise HTTPException(status_code=400, detail="Organization not found")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, full_name=payload.full_name,
                hashed_password=hash_password(payload.password),
                role=payload.role, organization_id=org.id)
    db.add(user); db.commit(); db.refresh(user)
    audit(db, user, "auth.register", user.id, f"Registered {payload.email}", org.id, request.client.host if request.client else "")
    token = create_access_token(user.id, {"org": org.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    key = request.client.host if request.client else "unknown"
    if is_throttled(key):
        raise HTTPException(status_code=429, detail="Too many failed sign-in attempts. Retry in one minute.")
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        record_failure(key)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    if user.mfa_enabled:
        import pyotp
        if not payload.totp:
            raise HTTPException(status_code=401,
                                detail="MFA required: resubmit with the current 6-digit authenticator code")
        if not pyotp.TOTP(user.mfa_secret or "").verify(payload.totp, valid_window=1):
            record_failure(key)
            audit(db, user, "auth.mfa_failed", user.id, "invalid TOTP at login",
                  user.organization_id, request.client.host if request.client else "")
            raise HTTPException(status_code=401, detail="Invalid authenticator code")
    clear_throttle(key)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    audit(db, user, "auth.login", user.id, f"Login {payload.email}", user.organization_id, request.client.host if request.client else "")
    token = create_access_token(user.id, {"org": user.organization_id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current

@router.post("/logout")
def logout(request: Request, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    audit(db, current, "auth.logout", current.id, "Logout", current.organization_id, request.client.host if request.client else "")
    return {"status": "logged out"}
