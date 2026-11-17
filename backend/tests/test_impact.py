"""Tests for impact analysis service and endpoint:
- multi-hop traversal and relationship path
- cycle safety and duplicate prevention
- classification clearance filtering (ABAC) and no existence disclosure
- cross-tenant isolation and 404 denial
- depth limits and direction parameter handling
"""
import pytest
from app.db import SessionLocal
from app.models import Entity, Relationship, User


def _create_ent(db, org_id, name, entity_type="asset", classification="INTERNAL") -> str:
    e = Entity(
        organization_id=org_id,
        name=name,
        entity_type=entity_type,
        classification=classification,
        status="active",
        confidence=1.0,
        is_synthetic=True,
    )
    db.add(e)
    db.commit()
    return str(e.id)


def _create_rel(db, org_id, src_id, tgt_id, rel_type="supplied_by", provenance="confirmed", confidence=0.9, evidence="test evidence") -> str:
    r = Relationship(
        organization_id=org_id,
        source_id=src_id,
        target_id=tgt_id,
        rel_type=rel_type,
        provenance=provenance,
        confidence=confidence,
        evidence=evidence,
        source_ref="test_suite_ref",
    )
    db.add(r)
    db.commit()
    return str(r.id)


def _cleanup(ent_ids: list[str], rel_ids: list[str]):
    db = SessionLocal()
    try:
        if rel_ids:
            db.query(Relationship).filter(Relationship.id.in_(rel_ids)).delete(synchronize_session=False)
        if ent_ids:
            db.query(Entity).filter(Entity.id.in_(ent_ids)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_impact_multi_hop_result(client, analyst):
    """Multi-hop breadth-first traversal up to depth N with hop distance, evidence and hypothesis marking."""
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    org_id = me["organization_id"]

    db = SessionLocal()
    ent_ids, rel_ids = [], []
    try:
        r_id = _create_ent(db, org_id, "Impact Root Alpha")
        h1_id = _create_ent(db, org_id, "Impact Hop1 Beta")
        h2_id = _create_ent(db, org_id, "Impact Hop2 Gamma")
        h3_id = _create_ent(db, org_id, "Impact Hop3 Delta")
        h4_id = _create_ent(db, org_id, "Impact Hop4 Epsilon")
        ent_ids = [r_id, h1_id, h2_id, h3_id, h4_id]

        r1 = _create_rel(db, org_id, r_id, h1_id, rel_type="supplies", provenance="confirmed", confidence=0.95, evidence="Direct feed line A->B")
        r2 = _create_rel(db, org_id, h1_id, h2_id, rel_type="powers", provenance="imported", confidence=0.90, evidence="Distribution grid log B->C")
        r3 = _create_rel(db, org_id, h2_id, h3_id, rel_type="serves", provenance="inferred", confidence=0.70, evidence="Inferred service coupling C->D")
        r4 = _create_rel(db, org_id, h3_id, h4_id, rel_type="coordinates", provenance="confirmed", confidence=0.85, evidence="Telemetry channel D->E")
        rel_ids = [r1, r2, r3, r4]

        # 1 Hop
        res1 = client.get(f"/api/v1/entities/{r_id}/impact?depth=1", headers=analyst)
        assert res1.status_code == 200, res1.text
        data1 = res1.json()
        assert data1["total_affected"] == 1
        assert data1["depth"] == 1
        assert len(data1["nodes"]) == 1
        assert data1["nodes"][0]["id"] == h1_id
        assert data1["nodes"][0]["hop_distance"] == 1
        assert len(data1["nodes"][0]["path"]) == 1
        assert data1["nodes"][0]["path"][0]["provenance"] == "confirmed"
        assert data1["nodes"][0]["path"][0]["is_hypothesis"] is False
        assert data1["nodes"][0]["is_hypothesis"] is False

        # 2 Hops
        res2 = client.get(f"/api/v1/entities/{r_id}/impact?depth=2", headers=analyst)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["total_affected"] == 2
        hop_map2 = {n["id"]: n for n in data2["nodes"]}
        assert h1_id in hop_map2 and hop_map2[h1_id]["hop_distance"] == 1
        assert h2_id in hop_map2 and hop_map2[h2_id]["hop_distance"] == 2

        # 3 Hops (default depth in endpoint)
        res3 = client.get(f"/api/v1/entities/{r_id}/impact?depth=3", headers=analyst)
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["total_affected"] == 3
        node_ids = [n["id"] for n in data3["nodes"]]
        assert node_ids == [h1_id, h2_id, h3_id]

        delta_node = [n for n in data3["nodes"] if n["id"] == h3_id][0]
        assert delta_node["hop_distance"] == 3
        assert len(delta_node["path"]) == 3
        assert delta_node["is_hypothesis"] is True, "Path containing inferred edge must be marked as hypothesis"
        assert delta_node["path"][2]["is_hypothesis"] is True
        assert delta_node["path"][2]["provenance"] == "inferred"
        assert delta_node["path"][2]["confidence"] == 0.70
        assert delta_node["path"][2]["evidence"] == "Inferred service coupling C->D"
        assert delta_node["path_confidence"] == round(0.95 * 0.90 * 0.70, 3)

        # 4 Hops (maximum depth limit)
        res4 = client.get(f"/api/v1/entities/{r_id}/impact?depth=4", headers=analyst)
        assert res4.status_code == 200
        data4 = res4.json()
        assert data4["total_affected"] == 4
        assert any(n["id"] == h4_id and n["hop_distance"] == 4 for n in data4["nodes"])
    finally:
        db.close()
        _cleanup(ent_ids, rel_ids)


def test_impact_cycle_safe(client, analyst):
    """Cycles in the graph must not cause infinite loops, duplicate nodes, or distorted hop distances."""
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    org_id = me["organization_id"]

    db = SessionLocal()
    ent_ids, rel_ids = [], []
    try:
        r_id = _create_ent(db, org_id, "Cycle Root")
        n1_id = _create_ent(db, org_id, "Cycle Node 1")
        n2_id = _create_ent(db, org_id, "Cycle Node 2")
        n3_id = _create_ent(db, org_id, "Cycle Node 3")
        ent_ids = [r_id, n1_id, n2_id, n3_id]

        # Root -> 1 -> 2 -> 3 -> 1 (cycle)
        # and 3 -> Root (cycle back to root)
        # and 2 -> 2 (self loop)
        r1 = _create_rel(db, org_id, r_id, n1_id, rel_type="connected_to", evidence="cycle link 1")
        r2 = _create_rel(db, org_id, n1_id, n2_id, rel_type="connected_to", evidence="cycle link 2")
        r3 = _create_rel(db, org_id, n2_id, n3_id, rel_type="connected_to", evidence="cycle link 3")
        r4 = _create_rel(db, org_id, n3_id, n1_id, rel_type="connected_to", evidence="back to 1")
        r5 = _create_rel(db, org_id, n3_id, r_id, rel_type="connected_to", evidence="back to root")
        r6 = _create_rel(db, org_id, n2_id, n2_id, rel_type="connected_to", evidence="self loop")
        rel_ids = [r1, r2, r3, r4, r5, r6]

        res = client.get(f"/api/v1/entities/{r_id}/impact?depth=4", headers=analyst)
        assert res.status_code == 200
        data = res.json()

        # The traversal must be cycle-safe
        assert data["total_affected"] == 3
        returned_ids = [n["id"] for n in data["nodes"]]
        assert len(returned_ids) == len(set(returned_ids)), "No node should be duplicated"
        assert r_id not in returned_ids, "Root entity should not appear in affected nodes"

        hop_map = {n["id"]: n["hop_distance"] for n in data["nodes"]}
        assert hop_map[n1_id] == 1
        assert hop_map[n2_id] == 2
        assert hop_map[n3_id] == 3
    finally:
        db.close()
        _cleanup(ent_ids, rel_ids)


def test_impact_clearance_filtering(client, analyst, admin):
    """Clearance filtering (ABAC): nodes above user clearance must not be returned, traversed, or revealed in totals."""
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    org_id = me["organization_id"]

    db = SessionLocal()
    ent_ids, rel_ids = [], []
    try:
        root_id = _create_ent(db, org_id, "Clearance Root Public", classification="INTERNAL")
        internal_child_id = _create_ent(db, org_id, "Internal Dependent", classification="INTERNAL")
        restricted_child_id = _create_ent(db, org_id, "Restricted Sensitive Node", classification="RESTRICTED")
        protected_grandchild_id = _create_ent(db, org_id, "Protected Secret Node", classification="PROTECTED")
        ent_ids = [root_id, internal_child_id, restricted_child_id, protected_grandchild_id]

        # Root -> Internal Child
        r1 = _create_rel(db, org_id, root_id, internal_child_id, rel_type="supplies", evidence="Public feed")
        # Root -> Restricted Child -> Protected Grandchild
        r2 = _create_rel(db, org_id, root_id, restricted_child_id, rel_type="supplies", evidence="Classified feed")
        r3 = _create_rel(db, org_id, restricted_child_id, protected_grandchild_id, rel_type="controls", evidence="Secret link")
        rel_ids = [r1, r2, r3]

        # Analyst has clearance INTERNAL: must not see RESTRICTED or PROTECTED records
        res_analyst = client.get(f"/api/v1/entities/{root_id}/impact?depth=3", headers=analyst)
        assert res_analyst.status_code == 200
        data_analyst = res_analyst.json()

        assert data_analyst["total_affected"] == 1, "Totals must NEVER reveal existence of classified nodes"
        assert len(data_analyst["nodes"]) == 1
        assert data_analyst["nodes"][0]["id"] == internal_child_id
        node_names = {n["name"] for n in data_analyst["nodes"]}
        assert "Restricted Sensitive Node" not in node_names
        assert "Protected Secret Node" not in node_names

        # Edges must not reveal the classified relationships
        edge_targets = {e["target_id"] for e in data_analyst["edges"]}
        assert restricted_child_id not in edge_targets
        assert protected_grandchild_id not in edge_targets

        # Admin holds PROTECTED clearance: can see the full graph
        res_admin = client.get(f"/api/v1/entities/{root_id}/impact?depth=3", headers=admin)
        assert res_admin.status_code == 200
        data_admin = res_admin.json()
        assert data_admin["total_affected"] == 3
        admin_node_ids = {n["id"] for n in data_admin["nodes"]}
        assert {internal_child_id, restricted_child_id, protected_grandchild_id} <= admin_node_ids

        # Querying impact on a node above caller's clearance must return 404, not 403 (no existence disclosure)
        denied = client.get(f"/api/v1/entities/{restricted_child_id}/impact", headers=analyst)
        assert denied.status_code == 404, "Access to node above clearance must return 404"
    finally:
        db.close()
        _cleanup(ent_ids, rel_ids)


def test_impact_cross_tenant_denial(client, analyst, other_tenant):
    """Tenant isolation: cross-tenant entity fetch returns 404, and cross-tenant edges are never traversed."""
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    other_me = client.get("/api/v1/auth/me", headers=other_tenant).json()
    org1_id = me["organization_id"]
    org2_id = other_me["organization_id"]

    db = SessionLocal()
    ent_ids, rel_ids = [], []
    try:
        t1_root_id = _create_ent(db, org1_id, "Tenant 1 Facility")
        t1_dep_id = _create_ent(db, org1_id, "Tenant 1 Dependent")
        t2_node_id = _create_ent(db, org2_id, "Tenant 2 Installation")
        ent_ids = [t1_root_id, t1_dep_id, t2_node_id]

        r1 = _create_rel(db, org1_id, t1_root_id, t1_dep_id, evidence="intra-tenant link")
        # Attempt an illicit cross-tenant relationship
        r2 = _create_rel(db, org1_id, t1_root_id, t2_node_id, evidence="cross-tenant link")
        rel_ids = [r1, r2]

        # other_tenant attempts to query impact of t1_root: must get 404
        r_denied = client.get(f"/api/v1/entities/{t1_root_id}/impact", headers=other_tenant)
        assert r_denied.status_code == 404

        # Analyst queries impact of t1_root: must only see Tenant 1 records
        r_analyst = client.get(f"/api/v1/entities/{t1_root_id}/impact?depth=3", headers=analyst)
        assert r_analyst.status_code == 200
        data = r_analyst.json()
        assert data["total_affected"] == 1
        assert data["nodes"][0]["id"] == t1_dep_id
        assert all(n["id"] != t2_node_id for n in data["nodes"])
    finally:
        db.close()
        _cleanup(ent_ids, rel_ids)


def test_impact_depth_limits_and_direction(client, analyst):
    """Validation: depth must be between 1 and 4, direction parameter supports downstream, upstream, both."""
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    org_id = me["organization_id"]

    db = SessionLocal()
    ent_ids, rel_ids = [], []
    try:
        p1_id = _create_ent(db, org_id, "Direction Node P1")
        p2_id = _create_ent(db, org_id, "Direction Node P2")
        p3_id = _create_ent(db, org_id, "Direction Node P3")
        ent_ids = [p1_id, p2_id, p3_id]

        r1 = _create_rel(db, org_id, p1_id, p2_id, evidence="P1 -> P2")
        r2 = _create_rel(db, org_id, p2_id, p3_id, evidence="P2 -> P3")
        rel_ids = [r1, r2]

        # Depth validation
        assert client.get(f"/api/v1/entities/{p2_id}/impact?depth=0", headers=analyst).status_code == 422
        assert client.get(f"/api/v1/entities/{p2_id}/impact?depth=5", headers=analyst).status_code == 422

        # Direction downstream from P2: should see P3
        down = client.get(f"/api/v1/entities/{p2_id}/impact?depth=2&direction=downstream", headers=analyst).json()
        assert down["total_affected"] == 1
        assert down["nodes"][0]["id"] == p3_id

        # Direction upstream from P2: should see P1
        up = client.get(f"/api/v1/entities/{p2_id}/impact?depth=2&direction=upstream", headers=analyst).json()
        assert up["total_affected"] == 1
        assert up["nodes"][0]["id"] == p1_id

        # Direction both from P2: should see P1 and P3
        both = client.get(f"/api/v1/entities/{p2_id}/impact?depth=2&direction=both", headers=analyst).json()
        assert both["total_affected"] == 2
        both_ids = {n["id"] for n in both["nodes"]}
        assert both_ids == {p1_id, p3_id}
    finally:
        db.close()
        _cleanup(ent_ids, rel_ids)
