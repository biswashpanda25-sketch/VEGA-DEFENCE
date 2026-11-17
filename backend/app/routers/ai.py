from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User, AIConversation
from ..schemas import AIQuestion
from ..deps import get_current_user, audit
from ..services import ai as ai_service

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

@router.post("/ask")
def ask(payload: AIQuestion, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payload.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    if len(payload.question) > 2000:
        raise HTTPException(400, "Question too long (max 2000 chars)")
    result = ai_service.answer(db, current, payload.question, payload.case_id)
    conv = AIConversation(organization_id=current.organization_id, user_id=current.id,
                          question=payload.question, answer=result["answer"],
                          citations=result["citations"])
    db.add(conv); db.commit()
    audit(db, current, "ai.query", conv.id,
          f"q_len={len(payload.question)} cited={len(result['citations'])} insufficient={result['insufficient_evidence']}")
    return {**result, "conversation_id": conv.id}

@router.get("/history")
def history(limit: int = 25, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(AIConversation)
    if current.role != "platform_admin":
        q = q.filter(AIConversation.organization_id == current.organization_id)
    rows = q.order_by(AIConversation.created_at.desc()).limit(limit).all()
    return [{"id": r.id, "question": r.question, "answer": r.answer,
             "citations": r.citations, "created_at": r.created_at.isoformat()} for r in rows]

@router.get("/config")
def config(current: User = Depends(get_current_user)):
    import os
    return {"provider": os.getenv("AI_PROVIDER", "grounded-local"),
            "model": os.getenv("AI_MODEL", "none (deterministic grounded composer)"),
            "prompt_version": ai_service.PROMPT_VERSION,
            "external_model_configured": bool(os.getenv("AI_BASE_URL"))}
