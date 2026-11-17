"""Entity + relationship (knowledge graph) API with provenance and evidence enforcement."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..db import get_db
from ..models import Entity, Relationship, User
from ..schemas import EntityCreate, EntityOut, RelationshipCreate, RelationshipOut, ImpactResponse
from ..deps import get_current_user, require_role, audit
from ..policy import scope_query, redact, can_read, assert_can_read, AccessDenied, audit_purpose
from ..services import resolution, impact

router = APIRouter(prefix="/api/v1", tags=["graph"])
VALID_PROV = {"confirmed", "imported", "inferred", "unverified"}

def _tenant_scoped(db, model, current):
    """Tenant scope + classification clearance, applied before results leave the service."""
    return scope_query(db.query(model), model, current)

@router.get("/entities", response_model=list[EntityOut])
def list_entities(q: str | None = None, entity_type: str | None = None, district: str | None = None,
                  limit: int = Query(100, le=500), offset: int = 0,
                  current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = _tenant_scoped(db, Entity, current).filter(Entity.canonical_id.is_(None))
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Entity.name.ilike(like), Entity.description.ilike(like)))
    if entity_type: query = query.filter(Entity.entity_type == entity_type)
    if district: query = query.filter(Entity.district == district)
    if q and db.bind.dialect.name == "postgresql":
        # Trigram GiST distance ordering turns a 2.6 s worst case into ~0.2 s on 1M rows by walking
        # the index in similarity order instead of sorting every match (docs/scale_results.json).
        return query.order_by(Entity.name.op("<->")(q)).offset(offset).limit(limit).all()
    return query.order_by(Entity.name).offset(offset).limit(limit).all()

@router.post("/entities", response_model=EntityOut)
def create_entity(payload: EntityCreate,
                  current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")),
                  db: Session = Depends(get_db)):
    from ..policy import clearance_of, rank
    data = payload.model_dump()
    classification = data.pop("classification", "INTERNAL")
    if rank(classification) > clearance_of(current):
        raise HTTPException(403, "Cannot create a record above your clearance")
    e = Entity(organization_id=current.organization_id, is_synthetic=True,
               classification=classification, **data)
    db.add(e); db.commit(); db.refresh(e)
    audit(db, current, "entity.create", e.id, f"{e.entity_type}:{e.name}")
    return e

@router.get("/entities/{entity_id}")
def get_entity(entity_id: str, purpose: str | None = None,
               current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    e = _tenant_scoped(db, Entity, current).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(404, "Entity not found")
    assert_can_read(current, e.classification, e.organization_id)
    rels = db.query(Relationship).filter(
        Relationship.organization_id == e.organization_id,
        or_(Relationship.source_id == e.id, Relationship.target_id == e.id)).all()
    neighbor_ids = {r.source_id for r in rels} | {r.target_id for r in rels}
    neighbors = db.query(Entity).filter(Entity.id.in_(neighbor_ids)).all() if neighbor_ids else []
    names = {n.id: n.name for n in neighbors}
    audit(db, current, "entity.read", e.id, f"classification={e.classification}",
          purpose=audit_purpose(current, purpose))
    return {
        "entity": redact(current, {
            "id": e.id, "name": e.name, "entity_type": e.entity_type, "district": e.district,
            "state": e.state, "status": e.status, "description": e.description,
            "confidence": e.confidence, "is_synthetic": e.is_synthetic,
            "classification": e.classification,
            "attributes": e.attributes}, purpose=purpose),
        "relationships": [{"id": r.id, "source_id": r.source_id, "source_name": names.get(r.source_id, ""),
                           "target_id": r.target_id, "target_name": names.get(r.target_id, ""),
                           "rel_type": r.rel_type, "provenance": r.provenance,
                           "confidence": r.confidence, "evidence": r.evidence,
                           "source_ref": r.source_ref} for r in rels],
    }

@router.get("/entities/{entity_id}/impact", response_model=ImpactResponse)
def get_entity_impact(entity_id: str, depth: int = Query(3, ge=1, le=4),
                      direction: str = Query("downstream", pattern="^(downstream|upstream|both)$"),
                      purpose: str | None = None,
                      current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = impact.analyze_impact(
            db=db,
            root_entity_id=entity_id,
            user=current,
            max_depth=depth,
            direction=direction,
            purpose=purpose,
        )
    except AccessDenied:
        raise HTTPException(404, "Entity not found")
    audit(db, current, "entity.impact", entity_id,
          f"depth={depth} direction={direction} affected={result['total_affected']}",
          purpose=audit_purpose(current, purpose))
    return result

@router.get("/relationships", response_model=list[RelationshipOut])
def list_relationships(provenance: str | None = None, limit: int = Query(300, le=1000),
                       current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = _tenant_scoped(db, Relationship, current)
    if provenance: q = q.filter(Relationship.provenance == provenance)
    return q.limit(limit).all()

@router.post("/relationships", response_model=RelationshipOut)
def create_relationship(payload: RelationshipCreate,
                        current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")),
                        db: Session = Depends(get_db)):
    if payload.provenance not in VALID_PROV:
        raise HTTPException(400, f"provenance must be one of {sorted(VALID_PROV)}")
    if not payload.evidence.strip():
        raise HTTPException(400, "Relationships require evidence — inferred links must not be recorded as fact")
    src = _tenant_scoped(db, Entity, current).filter(Entity.id == payload.source_id).first()
    tgt = _tenant_scoped(db, Entity, current).filter(Entity.id == payload.target_id).first()
    if not src or not tgt: raise HTTPException(404, "Source or target entity not found in your organization")
    r = Relationship(organization_id=current.organization_id, **payload.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    audit(db, current, "relationship.create", r.id, f"{payload.rel_type} {payload.source_id}->{payload.target_id} ({payload.provenance})")
    return r

@router.get("/graph")
def graph(limit: int = Query(200, le=800), provenance: str | None = None,
          current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ents = _tenant_scoped(db, Entity, current).limit(limit).all()
    ids = {e.id for e in ents}
    q = _tenant_scoped(db, Relationship, current)
    if provenance: q = q.filter(Relationship.provenance == provenance)
    rels = [r for r in q.limit(limit * 3).all() if r.source_id in ids and r.target_id in ids]
    return {
        "nodes": [{"id": e.id, "label": e.name, "type": e.entity_type, "district": e.district,
                   "status": e.status, "confidence": e.confidence,
                   "created_at": e.created_at.isoformat() if e.created_at else None} for e in ents],
        "edges": [{"id": r.id, "source": r.source_id, "target": r.target_id, "type": r.rel_type,
                   "provenance": r.provenance, "confidence": r.confidence, "evidence": r.evidence,
                   "created_at": r.created_at.isoformat() if r.created_at else None} for r in rels],
    }


@router.get("/entities/{entity_id}/resolution-candidates")
def resolution_candidates(entity_id: str,
                          current: User = Depends(require_role("platform_admin", "org_admin", "data_admin", "analyst")),
                          db: Session = Depends(get_db)):
    e = _tenant_scoped(db, Entity, current).filter(Entity.id == entity_id).first()
    if not e:
        raise HTTPException(404, "Entity not found")
    cands = resolution.candidates(db, e)
    audit(db, current, "entity.resolution_candidates", e.id, f"candidates={len(cands)}")
    return {"entity_id": e.id, "name": e.name, "candidates": cands,
            "note": "Candidates are proposals for human review. No merge happens without an authorized decision."}


@router.post("/entities/merge")
def merge_entities(survivor_id: str, duplicate_id: str, reason: str,
                   current: User = Depends(require_role("platform_admin", "org_admin", "reviewer")),
                   db: Session = Depends(get_db)):
    if not reason.strip():
        raise HTTPException(400, "A merge requires a recorded reason")
    try:
        result = resolution.merge(db, survivor_id, duplicate_id,
                                  organization_id=current.organization_id,
                                  actor_email=current.email, reason=reason)
    except ValueError as e:
        raise HTTPException(400, str(e))
    audit(db, current, "entity.merge", survivor_id,
          f"merged {duplicate_id} into {survivor_id}: {reason}")
    return result
