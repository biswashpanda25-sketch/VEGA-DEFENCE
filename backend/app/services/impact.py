"""Impact analysis service: breadth-first traversal, cycle-safe, clearance- and tenant-scoped."""
from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models import Entity, Relationship, User
from ..policy import scope_query, assert_can_read, redact, AccessDenied

MAX_DEPTH_LIMIT = 4


def analyze_impact(
    db: Session,
    root_entity_id: str,
    user: User,
    max_depth: int = 3,
    direction: str = "downstream",
    purpose: str | None = None,
) -> dict[str, Any]:
    """Perform breadth-first impact analysis starting from root_entity_id.

    Traverses relationships up to min(max_depth, 4) hops.
    Cycle-safe via visited set tracking.
    Strictly enforces tenant isolation and classification clearance:
    records above clearance or across tenants are never traversed, counted, or disclosed.
    Inferred edges are marked as hypotheses.
    """
    bounded_depth = min(max(1, max_depth), MAX_DEPTH_LIMIT)

    # 1. Fetch and authorize root entity
    root = (
        scope_query(db.query(Entity), Entity, user)
        .filter(Entity.id == root_entity_id, Entity.canonical_id.is_(None))
        .first()
    )
    if not root:
        raise AccessDenied("not found")
    assert_can_read(user, root.classification, root.organization_id)

    # 2. BFS state
    visited: set[str] = {root.id}
    paths: dict[str, list[dict[str, Any]]] = {root.id: []}
    current_level: list[str] = [root.id]

    impacted_nodes: list[dict[str, Any]] = []
    impacted_edges_map: dict[str, dict[str, Any]] = {}
    known_names: dict[str, str] = {root.id: root.name}

    for hop in range(1, bounded_depth + 1):
        if not current_level:
            break

        current_set = set(current_level)

        # Query relationships connected to the current frontier within the tenant
        rel_query = db.query(Relationship)
        if getattr(user, "role", None) != "platform_admin":
            rel_query = rel_query.filter(Relationship.organization_id == user.organization_id)

        if direction == "downstream":
            rel_query = rel_query.filter(Relationship.source_id.in_(current_level))
        elif direction == "upstream":
            rel_query = rel_query.filter(Relationship.target_id.in_(current_level))
        elif direction == "both":
            rel_query = rel_query.filter(
                or_(
                    Relationship.source_id.in_(current_level),
                    Relationship.target_id.in_(current_level)
                )
            )
        else:
            rel_query = rel_query.filter(Relationship.source_id.in_(current_level))

        # Order by confidence desc to prioritize higher confidence paths
        rels = rel_query.order_by(Relationship.confidence.desc()).all()

        candidate_edges: list[tuple[str, str, Relationship]] = []
        candidate_next_ids: set[str] = set()

        for r in rels:
            if direction == "downstream":
                curr_id, next_id = r.source_id, r.target_id
            elif direction == "upstream":
                curr_id, next_id = r.target_id, r.source_id
            else:  # "both"
                if r.source_id in current_set:
                    curr_id, next_id = r.source_id, r.target_id
                else:
                    curr_id, next_id = r.target_id, r.source_id

            if next_id in visited:
                continue
            candidate_edges.append((curr_id, next_id, r))
            candidate_next_ids.add(next_id)

        if not candidate_next_ids:
            break

        # Authorize candidate next nodes: apply tenant and classification clearance filters
        visible_next = (
            scope_query(db.query(Entity), Entity, user)
            .filter(Entity.id.in_(candidate_next_ids), Entity.canonical_id.is_(None))
            .all()
        )
        visible_map = {e.id: e for e in visible_next}
        for e in visible_next:
            known_names[e.id] = e.name

        next_level: list[str] = []

        for curr_id, next_id, r in candidate_edges:
            # If the neighbor is not visible under user clearance or tenant, skip completely
            if next_id not in visible_map:
                continue
            # If already visited during this hop from another branch, skip
            if next_id in visited:
                continue

            visited.add(next_id)
            next_level.append(next_id)

            ent = visible_map[next_id]
            parent_path = paths[curr_id]

            is_hypo = (r.provenance == "inferred")
            edge_dict = {
                "id": r.id,
                "source_id": r.source_id,
                "source_name": known_names.get(r.source_id, ent.name if r.source_id == ent.id else ""),
                "target_id": r.target_id,
                "target_name": known_names.get(r.target_id, ent.name if r.target_id == ent.id else ""),
                "rel_type": r.rel_type,
                "provenance": r.provenance,
                "confidence": round(float(r.confidence), 3),
                "evidence": r.evidence or "",
                "source_ref": r.source_ref or "",
                "is_hypothesis": is_hypo,
            }
            impacted_edges_map[r.id] = edge_dict

            node_path = parent_path + [edge_dict]
            paths[next_id] = node_path

            # Cumulative path confidence (product of confidences along path)
            cum_conf = 1.0
            for edge in node_path:
                cum_conf *= edge["confidence"]
            cum_conf = round(cum_conf, 3)

            path_is_hypothesis = any(edge["is_hypothesis"] for edge in node_path)

            impacted_nodes.append({
                "id": ent.id,
                "name": ent.name,
                "entity_type": ent.entity_type,
                "district": ent.district or "",
                "state": ent.state or "Odisha",
                "status": ent.status or "active",
                "confidence": round(float(ent.confidence), 3),
                "classification": ent.classification,
                "attributes": redact(user, ent.attributes or {}, purpose=purpose, model="entity"),
                "hop_distance": hop,
                "path": node_path,
                "path_confidence": cum_conf,
                "is_hypothesis": path_is_hypothesis,
            })

        current_level = next_level

    # Sort impacted nodes by hop distance, then descending path confidence, then name
    impacted_nodes.sort(key=lambda n: (n["hop_distance"], -n["path_confidence"], n["name"]))

    # Resolve any missing names in impacted_edges_map
    for e in impacted_edges_map.values():
        if not e["source_name"] and e["source_id"] in known_names:
            e["source_name"] = known_names[e["source_id"]]
        if not e["target_name"] and e["target_id"] in known_names:
            e["target_name"] = known_names[e["target_id"]]

    root_payload = redact(user, {
        "id": root.id,
        "name": root.name,
        "entity_type": root.entity_type,
        "district": root.district or "",
        "state": root.state or "Odisha",
        "status": root.status or "active",
        "confidence": round(float(root.confidence), 3),
        "classification": root.classification,
        "attributes": root.attributes or {},
    }, purpose=purpose, model="entity")

    return {
        "root_entity": root_payload,
        "depth": bounded_depth,
        "direction": direction,
        "total_affected": len(impacted_nodes),
        "nodes": impacted_nodes,
        "edges": list(impacted_edges_map.values()),
    }
