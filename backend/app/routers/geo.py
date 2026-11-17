from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from ..models import Entity, User
from ..deps import get_current_user
from ..services.geo import odisha_district_geojson, DISTRICTS

router = APIRouter(prefix="/api/v1/geo", tags=["geo"])

@router.get("/districts")
def districts():
    return odisha_district_geojson()

@router.get("/assets")
def asset_features(layer: str | None = None, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """GeoJSON of entity locations, anchored to district centroids with jitter for mapping."""
    q = db.query(Entity)
    if current.role != "platform_admin":
        q = q.filter(Entity.organization_id == current.organization_id)
    if layer:
        q = q.filter(Entity.entity_type == layer)
    centroids = {n.lower(): (lat, lon) for n, lat, lon in DISTRICTS}
    import hashlib
    feats = []
    for e in q.limit(1000).all():
        c = centroids.get((e.district or "").lower())
        if not c: continue
        h = hashlib.sha256(e.id.encode()).digest()
        lat = c[0] + ((h[0] / 255) - 0.5) * 0.18
        lon = c[1] + ((h[1] / 255) - 0.5) * 0.18
        feats.append({"type": "Feature", "id": e.id,
                      "properties": {"name": e.name, "entity_type": e.entity_type,
                                     "district": e.district, "status": e.status,
                                     "confidence": e.confidence, "synthetic": e.is_synthetic,
                                     "organization_id": e.organization_id},
                      "geometry": {"type": "Point", "coordinates": [round(lon, 5), round(lat, 5)]}})
    return {"type": "FeatureCollection", "features": feats,
            "metadata": {"source": "VEGA INDIA entity registry", "count": len(feats),
                         "note": "Positions are district-anchored approximations for synthetic records."}}

@router.get("/summary")
def district_summary(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Entity.district, func.count(Entity.id))
    if current.role != "platform_admin":
        q = q.filter(Entity.organization_id == current.organization_id)
    rows = q.group_by(Entity.district).all()
    return {"districts": [{"district": d or "Unassigned", "count": c} for d, c in sorted(rows, key=lambda r: -r[1])]}


@router.get("/nearby")
def nearby(lat: float, lon: float, radius_km: float = 50, limit: int = 50,
           current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Spatial proximity query.

    PostgreSQL path uses a GiST index on a geography expression plus KNN (`<->`) ordering, which
    returns the nearest N inside the radius without sorting the whole candidate set. Measured on
    1,000,000 entities: 1.05 ms p50 versus 351 ms for the equivalent `ORDER BY distance` form
    (docs/scale_results.json). The SQLite path is a haversine scan and is honest about it.
    """
    from fastapi import HTTPException
    from sqlalchemy import text
    from ..policy import CLASSIFICATION_RANK, clearance_of, scope_query

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(400, "coordinates out of range")
    if not (-180 <= lon <= 180):
        raise HTTPException(400, "longitude out of range")
    radius_m = max(1.0, min(radius_km, 1000.0)) * 1000.0
    limit = max(1, min(limit, 500))
    visible = [c for c, rank in CLASSIFICATION_RANK.items() if rank <= clearance_of(current)]

    if db.bind.dialect.name == "postgresql":
        geo = "ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography"
        pt = "ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography"
        # Latency guard: the planner prefers a parallel seq scan for wide radii, which costs ~200x
        # more than the ordered index scan for a nearest-N query.
        db.execute(text("SET LOCAL max_parallel_workers_per_gather = 0"))
        rows = db.execute(text(f"""
            SELECT id, name, entity_type, district, status, classification,
                   ({geo} <-> {pt}) / 1000.0 AS distance_km
            FROM entities
            WHERE canonical_id IS NULL
              AND latitude IS NOT NULL AND longitude IS NOT NULL
              AND (:is_admin OR organization_id = :org)
              AND "classification" = ANY(:classes)
              AND ST_DWithin({geo}, {pt}, :radius)
            ORDER BY {geo} <-> {pt}
            LIMIT :lim
        """), {"lat": lat, "lon": lon, "radius": radius_m, "lim": limit,
               "is_admin": current.role == "platform_admin",
               "org": current.organization_id,
               "classes": visible}).fetchall()
        engine_used = "postgis-gist-knn"
    else:
        import math
        q = scope_query(db.query(Entity), Entity, current).filter(Entity.canonical_id.is_(None))
        out = []
        for e in q.all():
            if e.latitude is None or e.longitude is None:
                continue
            d_lat = math.radians(e.latitude - lat)
            d_lon = math.radians(e.longitude - lon)
            a = (math.sin(d_lat / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(e.latitude)) * math.sin(d_lon / 2) ** 2)
            km = 6371.0 * 2 * math.asin(math.sqrt(a))
            if km <= radius_km:
                out.append((e, km))
        out.sort(key=lambda r: r[1])
        rows = [(e.id, e.name, e.entity_type, e.district, e.status, e.classification, km)
                for e, km in out[:limit]]
        engine_used = "haversine"

    return {"engine": engine_used, "centre": {"lat": lat, "lon": lon}, "radius_km": radius_km,
            "count": len(rows),
            "results": [{"id": r[0], "name": r[1], "entity_type": r[2], "district": r[3],
                         "status": r[4], "classification": r[5],
                         "distance_km": round(float(r[6]), 2)} for r in rows]}
