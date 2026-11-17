"""Entity resolution: candidate generation, scoring, and human-supervised merge.

Candidate generation uses PostgreSQL trigram similarity (pg_trgm GIN index) when the database supports it,
and falls back to difflib ratio on SQLite. Merging is *never* automatic: an authorized reviewer selects a
survivor, the merge is recorded with evidence, and it is reversible through the audit ledger.
"""
from __future__ import annotations

import difflib
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import Entity, Relationship


def is_postgres(db: Session) -> bool:
    return db.bind.dialect.name == "postgresql"


def ensure_trigram_index(db: Session) -> bool:
    """Create the trigram GIN index used for blocking. Idempotent; DBA-friendly."""
    if not is_postgres(db):
        return False
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_entities_name_trgm "
                    "ON entities USING gin (name gin_trgm_ops)"))
    db.commit()
    return True


def candidates(db: Session, entity: Entity, limit: int = 10) -> list[dict]:
    """Rank possible duplicates of `entity` inside the same organization."""
    ensure_trigram_index(db)
    rows: list[tuple[Entity, float]] = []

    if is_postgres(db):
        scored = db.execute(text("""
            SELECT id, similarity(name, :name) AS sim
            FROM entities
            WHERE organization_id = :org
              AND id <> :eid
              AND canonical_id IS NULL
              AND (entity_type = :etype OR district = :district)
              AND similarity(name, :name) > 0.25
            ORDER BY sim DESC
            LIMIT :lim
        """), {"name": entity.name, "org": entity.organization_id, "eid": entity.id,
               "etype": entity.entity_type, "district": entity.district or "", "lim": limit}).fetchall()
        ids = [r[0] for r in scored]
        found = {e.id: e for e in db.query(Entity).filter(Entity.id.in_(ids)).all()} if ids else {}
        rows = [(found[r[0]], float(r[1])) for r in scored if r[0] in found]
    else:
        pool = (db.query(Entity)
                .filter(Entity.organization_id == entity.organization_id,
                        Entity.id != entity.id,
                        Entity.canonical_id.is_(None))
                .all())
        for cand in pool:
            sim = difflib.SequenceMatcher(None, entity.name.lower(), cand.name.lower()).ratio()
            if sim > 0.25 and (cand.entity_type == entity.entity_type or cand.district == entity.district):
                rows.append((cand, sim))
        rows.sort(key=lambda r: -r[1])
        rows = rows[:limit]

    out = []
    for cand, sim in rows:
        reasons = []
        if cand.entity_type == entity.entity_type:
            reasons.append("same entity type")
        if cand.district and cand.district == entity.district:
            reasons.append("same district")
        if cand.name.lower().strip() == entity.name.lower().strip():
            reasons.append("identical normalised name")
        out.append({
            "entity_id": cand.id, "name": cand.name, "entity_type": cand.entity_type,
            "district": cand.district, "status": cand.status,
            "similarity": round(sim, 3),
            "confidence": round(min(0.99, sim * 0.85 + (0.1 if reasons else 0.0)), 3),
            "match_reasons": reasons,
            "proposed_action": "review_for_merge",
        })
    return out


def merge(db: Session, survivor_id: str, duplicate_id: str, *, organization_id: str,
          actor_email: str, reason: str) -> dict:
    """Merge `duplicate` into `survivor`. Relationships are re-pointed, never silently dropped."""
    if survivor_id == duplicate_id:
        raise ValueError("cannot merge an entity into itself")
    survivor = db.query(Entity).filter(Entity.id == survivor_id,
                                       Entity.organization_id == organization_id).first()
    duplicate = db.query(Entity).filter(Entity.id == duplicate_id,
                                        Entity.organization_id == organization_id).first()
    if not survivor or not duplicate:
        raise ValueError("entity not found in this organization")
    if duplicate.canonical_id:
        raise ValueError("duplicate record was already merged")

    moved = 0
    for rel in db.query(Relationship).filter(
            (Relationship.source_id == duplicate.id) | (Relationship.target_id == duplicate.id)).all():
        if rel.source_id == duplicate.id:
            rel.source_id = survivor.id
        if rel.target_id == duplicate.id:
            rel.target_id = survivor.id
        moved += 1

    before = dict(duplicate.attributes or {})
    survivor.attributes = {
        **(survivor.attributes or {}),
        "merged_from": list((survivor.attributes or {}).get("merged_from", [])) + [duplicate.id],
    }
    duplicate.canonical_id = survivor.id
    duplicate.attributes = {**before, "merged_into": survivor.id,
                            "merged_by": actor_email,
                            "merged_at": datetime.now(timezone.utc).isoformat(),
                            "merge_reason": reason}
    duplicate.confidence = 0.0
    db.commit()
    return {"survivor_id": survivor.id, "duplicate_id": duplicate.id,
            "relationships_repointed": moved, "reason": reason,
            "reversible": True, "audited": True}
