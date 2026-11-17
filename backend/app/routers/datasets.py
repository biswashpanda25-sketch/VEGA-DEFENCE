"""Datasets + ingestion (CSV/JSON/Excel) with provenance, validation and duplicate detection."""
import csv, io, json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Dataset, User, Entity, Document
from ..schemas import DatasetCreate, DatasetOut
from ..deps import get_current_user, require_role, audit
from ..services.ingestion import ingest_tabular, quality_report
from ..services import jobs as job_service

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

@router.get("", response_model=list[DatasetOut])
def list_datasets(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Dataset)
    if current.role != "platform_admin":
        q = q.filter(Dataset.organization_id == current.organization_id)
    return q.order_by(Dataset.created_at.desc()).all()

@router.post("", response_model=DatasetOut)
def create_dataset(payload: DatasetCreate, current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")), db: Session = Depends(get_db)):
    ds = Dataset(organization_id=current.organization_id, **payload.model_dump(),
                 provenance={"created_by": current.email, "source": payload.source_type,
                             "ingested_at": datetime.now(timezone.utc).isoformat()})
    db.add(ds); db.commit(); db.refresh(ds)
    audit(db, current, "dataset.create", ds.id, f"Created dataset {ds.name}")
    return ds

@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    if current.role != "platform_admin" and ds.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    return ds

@router.post("/{dataset_id}/ingest")
async def ingest_file(dataset_id: str, file: UploadFile = File(...),
                      current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")),
                      db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    if current.role != "platform_admin" and ds.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 25MB limit")
    job = job_service.create_job(db, organization_id=ds.organization_id, connector_id=None,
                                 dataset_id=ds.id, payload_ref=file.filename or "upload",
                                 max_attempts=3)
    try:
        result, job = job_service.execute(
            db, job, lambda: _as_dict(ingest_tabular(db, ds, file.filename or "upload", raw, current)))
    except ValueError as e:
        audit(db, current, "dataset.ingest_failed", ds.id,
              f"{file.filename}: {e} (job {job.id}, attempts={job.attempts})")
        raise HTTPException(400, f"Ingestion error: {e}")
    rows, created, skipped = result["rows"], result["entities_created"], result["duplicates_skipped"]
    ds.record_count = db.query(Entity).filter(Entity.organization_id == ds.organization_id).count()
    ds.quality_score = quality_report(db, ds.organization_id)
    ds.updated_at = datetime.now(timezone.utc)
    db.commit()
    audit(db, current, "dataset.ingest", ds.id,
          f"{file.filename} rows={rows} created={created} dup={skipped} job={job.id}")
    return {"rows": rows, "entities_created": created, "duplicates_skipped": skipped,
            "quality_score": round(ds.quality_score, 3), "provenance": ds.provenance,
            "job_id": job.id, "attempts": job.attempts}

@router.post("/{dataset_id}/documents")
async def upload_document(dataset_id: str, file: UploadFile = File(...), title: str = Form(""),
                          current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")),
                          db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    if current.role != "platform_admin" and ds.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024: raise HTTPException(413, "File too large")
    name = (file.filename or "").lower()
    if not name.endswith((".pdf", ".txt", ".md")):
        raise HTTPException(400, "Unsupported document type (pdf, txt, md)")
    text = ""
    if name.endswith(".pdf"):
        text = raw.decode("latin-1", errors="ignore")  # extraction hook; see KNOWN_ISSUES
    else:
        text = raw.decode("utf-8", errors="ignore")
    doc = Document(organization_id=ds.organization_id, dataset_id=ds.id,
                   title=title or file.filename or "Untitled", filename=file.filename or "",
                   doc_type=name.rsplit(".", 1)[-1], content_text=text[:200000], is_synthetic=True)
    db.add(doc); db.commit(); db.refresh(doc)
    audit(db, current, "document.upload", doc.id, f"{doc.filename} bytes={len(raw)}")
    return {"id": doc.id, "title": doc.title, "chars_extracted": len(text), "document": doc.id}

def _as_dict(result):
    rows, created, skipped = result
    return {"rows": rows, "entities_created": created, "duplicates_skipped": skipped}


@router.get("/{dataset_id}/quality")
def quality(dataset_id: str, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds: raise HTTPException(404, "Dataset not found")
    if current.role != "platform_admin" and ds.organization_id != current.organization_id:
        raise HTTPException(403, "Cross-tenant access denied")
    return quality_report(db, ds.organization_id, detailed=True)
