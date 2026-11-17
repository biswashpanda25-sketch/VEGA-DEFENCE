from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..deps import get_current_user, audit
from ..services.retrieval import Retriever

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("")
def search(q: str = Query(..., min_length=1), kind: str | None = None, limit: int = Query(20, le=100),
           current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hits = Retriever(db, current).search(q, k=limit * 2)
    if kind:
        hits = [h for h in hits if h["kind"] == kind]
    hits = hits[:limit]
    audit(db, current, "search.query", "search", f"q_len={len(q)} results={len(hits)}")
    return {"query": q, "count": len(hits), "results": hits}
