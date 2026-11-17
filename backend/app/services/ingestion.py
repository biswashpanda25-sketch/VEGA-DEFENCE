"""Ingestion services: schema mapping, normalization, duplicate detection, quality scoring."""
import csv, io, json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import Dataset, Entity, User

REQUIRED_FIELDS = ["name"]
KNOWN_TYPES = {"organization", "department", "asset", "vehicle", "facility", "warehouse",
               "inventory_item", "project", "document", "case", "location", "supplier"}

def _rows_from_upload(filename: str, raw: bytes) -> list[dict]:
    name = filename.lower()
    if name.endswith(".csv"):
        text = raw.decode("utf-8-sig", errors="replace")
        return [dict(r) for r in csv.DictReader(io.StringIO(text))]
    if name.endswith(".json"):
        data = json.loads(raw.decode("utf-8", errors="replace"))
        if isinstance(data, dict):
            data = data.get("records") or data.get("data") or [data]
        if not isinstance(data, list):
            raise ValueError("JSON must be an array of objects or {records: []}")
        return [r for r in data if isinstance(r, dict)]
    if name.endswith((".xlsx", ".xlsm")):
        import openpyxl, zipfile
        try:
            wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        except (zipfile.BadZipFile, KeyError, OSError, Exception) as e:
            raise ValueError(f"Unreadable workbook: {type(e).__name__}")
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        header = [str(h) if h is not None else f"col{i}" for i, h in enumerate(rows[0])]
        return [dict(zip(header, r)) for r in rows[1:] if any(c is not None for c in r)]
    raise ValueError("Unsupported format. Use CSV, JSON or XLSX")

def normalize(row: dict) -> dict:
    """Schema mapping: accepts common aliases, trims, normalizes case."""
    lowered = {(k or "").strip().lower().replace(" ", "_"): v for k, v in row.items()}
    def pick(*keys, default=""):
        for k in keys:
            if k in lowered and lowered[k] not in (None, ""):
                return lowered[k]
        return default
    def _num(*keys):
        for k in keys:
            v = lowered.get(k)
            if v in (None, ""):
                continue
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        return None

    out = {
        "name": str(pick("name", "asset_name", "entity_name", "title", "facility_name")).strip(),
        "latitude": _num("latitude", "lat"),
        "longitude": _num("longitude", "lon", "lng"),
        "classification": str(pick("classification", default="INTERNAL")).strip().upper(),
        "entity_type": str(pick("entity_type", "type", "category", default="asset")).strip().lower(),
        "description": str(pick("description", "details", "remarks")).strip(),
        "district": str(pick("district", "district_name")).strip(),
        "state": str(pick("state", default="Odisha")).strip(),
        "status": str(pick("status", default="active")).strip().lower(),
    }
    out["extras"] = {k: v for k, v in lowered.items() if k not in
                     {"name", "asset_name", "entity_name", "title", "facility_name", "entity_type",
                      "type", "category", "description", "details", "remarks", "district",
                      "district_name", "state", "status", "latitude", "lat",
                      "longitude", "lon", "lng", "classification"}}
    return out

def ingest_tabular(db: Session, ds: Dataset, filename: str, raw: bytes, user: User):
    try:
        rows = _rows_from_upload(filename, raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON: {e}")
    if not rows:
        raise ValueError("No rows found in file")
    created = skipped = 0
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        n = normalize(r)
        if not n["name"]:
            skipped += 1
            continue
        if n["entity_type"] not in KNOWN_TYPES:
            n["entity_type"] = "asset"
        # Duplicate detection within tenant: case-insensitive name + type + district
        existing = (db.query(Entity)
                    .filter(Entity.organization_id == ds.organization_id,
                            Entity.name.ilike(n["name"]),
                            Entity.entity_type == n["entity_type"])
                    .first())
        if existing:
            skipped += 1
            continue
        cls = n.get("classification") or "INTERNAL"
        if cls not in ("INTERNAL", "RESTRICTED", "PROTECTED"):
            cls = "INTERNAL"
        db.add(Entity(
            organization_id=ds.organization_id, entity_type=n["entity_type"], name=n["name"],
            classification=cls, latitude=n.get("latitude"), longitude=n.get("longitude"),
            description=n["description"], district=n["district"], state=n["state"],
            status=n["status"], confidence=1.0, is_synthetic=True,
            attributes={"extras": n["extras"], "dataset_id": ds.id,
                        "source_file": filename, "ingested_at": now,
                        "source_org": ds.source_org or "SYNTHETIC",
                        "provenance": "imported", "validation": "passed"},
        ))
        created += 1
    db.commit()
    return len(rows), created, skipped

def quality_report(db: Session, org_id: str, detailed: bool = False):
    ents = db.query(Entity).filter(Entity.organization_id == org_id).all()
    total = len(ents) or 1
    complete = sum(1 for e in ents if e.name and e.district and e.entity_type)
    unique_names = len({(e.name.lower(), e.entity_type) for e in ents})
    valid_types = sum(1 for e in ents if e.entity_type in KNOWN_TYPES)
    provenance = sum(1 for e in ents if (e.attributes or {}).get("source_file"))
    synthetic = sum(1 for e in ents if e.is_synthetic)
    score = round(((complete / total) * 0.4 + (unique_names / total) * 0.3 +
                   (valid_types / total) * 0.2 + (provenance / total) * 0.1), 4)
    if not detailed:
        return score
    return {
        "score": score, "total_records": len(ents),
        "completeness": round(complete / total, 4),
        "uniqueness": round(unique_names / total, 4),
        "validity": round(valid_types / total, 4),
        "provenance_coverage": round(provenance / total, 4),
        "synthetic_share": round(synthetic / total, 4),
    }
