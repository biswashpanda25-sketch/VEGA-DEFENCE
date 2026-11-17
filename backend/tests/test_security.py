"""Mandatory security scenarios 1, 2, 3, 4, 11, 12, 13."""
import io


def test_01_unauthenticated_access_denied(client):
    for path in ["/api/v1/entities", "/api/v1/cases", "/api/v1/datasets",
                 "/api/v1/analytics/overview", "/api/v1/audit", "/api/v1/admin/users"]:
        r = client.get(path)
        assert r.status_code == 401, f"{path} must reject unauthenticated access"


def test_01b_invalid_token_denied(client):
    r = client.get("/api/v1/entities", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_02_tenant_isolation_entities(client, other_tenant, analyst):
    mine = client.get("/api/v1/entities?limit=300", headers=other_tenant)
    assert mine.status_code == 200
    # the disaster-cell tenant must never receive another organization's records
    for e in mine.json():
        assert e["organization_id"] != "00000000-0000-0000-0000-000000000000"
    ids_other = {e["id"] for e in mine.json()}
    ids_analyst = {e["id"] for e in client.get("/api/v1/entities?limit=300", headers=analyst).json()}
    assert ids_other.isdisjoint(ids_analyst), "tenant datasets must not overlap"
    assert len(ids_analyst) > 0 and len(ids_other) == 0 or ids_other.isdisjoint(ids_analyst)


def test_02b_cross_tenant_entity_fetch_denied(client, other_tenant, analyst):
    entity = client.get("/api/v1/entities?limit=1", headers=analyst).json()[0]
    r = client.get(f"/api/v1/entities/{entity['id']}", headers=other_tenant)
    assert r.status_code == 404


def test_02c_cross_tenant_case_denied(client, other_tenant, analyst):
    case = client.get("/api/v1/cases", headers=analyst).json()[0]
    r = client.get(f"/api/v1/cases/{case['id']}", headers=other_tenant)
    assert r.status_code == 404


def test_03_restricted_fields_not_exposed(client, analyst, admin):
    # password hashes are never serialised on any user-facing endpoint
    r = client.get("/api/v1/admin/users", headers=admin)
    assert r.status_code == 200
    body = r.text
    assert "hashed_password" not in body and "$2b$" not in body
    # analysts are refused administrative user enumeration entirely
    assert client.get("/api/v1/admin/users", headers=analyst).status_code == 403
    # connector secrets are stripped from configuration output
    conns = client.get("/api/v1/admin/connectors", headers=admin)
    assert conns.status_code == 200
    for c in conns.json():
        assert not ({"password", "token", "api_key", "secret"} & set(c["config"].keys()))


def test_04_document_upload_validation(client, analyst):
    ds = client.get("/api/v1/datasets", headers=analyst).json()[0]
    bad = client.post(f"/api/v1/datasets/{ds['id']}/documents", headers=analyst,
                      files={"file": ("malware.exe", b"MZ\x90\x00binary", "application/octet-stream")})
    assert bad.status_code == 400
    good = client.post(f"/api/v1/datasets/{ds['id']}/documents", headers=analyst,
                       files={"file": ("advisory.txt", b"Synthetic advisory text.", "text/plain")})
    assert good.status_code == 200
    assert good.json()["chars_extracted"] > 0


def test_11_ai_cannot_reach_other_tenant(client, other_tenant):
    # disaster tenant asks about a record that only exists in the infrastructure tenant
    r = client.post("/api/v1/ai/ask", headers=other_tenant,
                    json={"question": "Summarise the evidence for Embankment Segment BBSR-07"})
    assert r.status_code == 200
    body = r.json()
    assert body["insufficient_evidence"] is True
    assert body["citations"] == []
    assert "Insufficient evidence" in body["answer"]


def test_12_search_respects_permissions(client, analyst, other_tenant):
    a = client.get("/api/v1/search?q=embankment", headers=analyst).json()
    b = client.get("/api/v1/search?q=embankment", headers=other_tenant).json()
    assert a["count"] > 0
    assert b["count"] == 0, "other tenant must not retrieve these records"
    for hit in a["results"]:
        assert hit["organization_id"] != "" and hit["organization_id"] is not None


def test_13_audit_events_recorded(client, analyst, admin):
    client.get("/api/v1/entities?limit=1", headers=analyst)
    client.post("/api/v1/search", headers=analyst, json={}) if False else None
    client.get("/api/v1/search?q=audit-probe", headers=analyst)
    r = client.get("/api/v1/audit?limit=200", headers=admin)
    assert r.status_code == 200
    actions = {e["action"] for e in r.json()}
    assert "auth.login" in actions
    assert "search.query" in actions
    # auditors/admins only
    assert client.get("/api/v1/audit", headers=analyst).status_code == 403


def test_13b_rate_limit_on_login(client):
    codes = []
    for _ in range(24):
        codes.append(client.post("/api/v1/auth/login",
                                 json={"email": "analyst@gotham-demo.in", "password": "wrong"}).status_code)
    assert 429 in codes, "repeated failed logins must be rate limited"
