"""Mandatory scenarios 5, 6, 7, 8, 9 and the end-to-end workflow (16)."""
import io
import json
import csv


def _csv_bytes(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode()


def test_05_malformed_files_do_not_crash(client, analyst):
    ds = client.get("/api/v1/datasets", headers=analyst).json()[0]
    cases = [
        ("bad.json", b"{not valid json,,,}"),
        ("bad.csv", b""),
        ("bad.xlsx", b"PK\x03\x04notreallyazip"),
        ("bad.xml", b"<x>unsupported</x>"),
    ]
    for name, payload in cases:
        r = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                        files={"file": (name, payload, "application/octet-stream")})
        assert r.status_code in (400, 422), f"{name} should be rejected cleanly, got {r.status_code}: {r.text[:200]}"
    # the API is still healthy after the malformed batch
    assert client.get("/api/v1/health").status_code == 200


def test_06_connector_failure_and_recovery(client, analyst):
    ds = client.post("/api/v1/datasets", headers=analyst,
                     json={"name": f"Recovery Test {__name__}", "description": "failure recovery",
                           "source_type": "file", "source_org": "SYNTHETIC"}).json()
    bad = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                      files={"file": ("broken.json", b"{{{{", "application/json")})
    assert bad.status_code == 400
    good = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                       files={"file": ("ok.json", json.dumps([{"name": "Recovery Test Asset", "entity_type": "asset",
                                                               "district": "Khordha"}]).encode(), "application/json")})
    assert good.status_code == 200, good.text
    assert good.json()["entities_created"] == 1
    # failed attempt is recorded for diagnosis
    audit = client.get("/api/v1/audit?action=dataset&limit=50", headers=analyst)
    assert audit.status_code == 403  # analysts cannot read the audit log
    admin_audit = client.get("/api/v1/audit?limit=200", headers=client_admin(client))
    assert any(e["action"] == "dataset.ingest_failed" for e in admin_audit.json())


def client_admin(client):
    from tests.conftest import _login
    return _login(client, "admin@gotham-demo.in")


def test_07_duplicate_detection(client, analyst):
    rows = [{"name": "Dup Test Pump", "entity_type": "asset", "district": "Cuttack"}]
    ds = client.post("/api/v1/datasets", headers=analyst,
                     json={"name": "Duplicate Test Dataset", "description": "dup", "source_type": "file"}).json()
    first = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                        files={"file": ("dup.csv", _csv_bytes(rows), "text/csv")}).json()
    second = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                         files={"file": ("dup.csv", _csv_bytes(rows), "text/csv")}).json()
    assert first["entities_created"] == 1
    assert second["entities_created"] == 0 and second["duplicates_skipped"] == 1


def test_08_provenance_preserved(client, analyst):
    rows = [{"name": "Provenance Bridge", "entity_type": "asset", "district": "Puri", "status": "active"}]
    ds = client.post("/api/v1/datasets", headers=analyst,
                     json={"name": "Provenance Test Dataset", "description": "prov",
                           "source_type": "file", "source_org": "SYNTHETIC"}).json()
    client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                files={"file": ("prov.csv", _csv_bytes(rows), "text/csv")})
    ent = [e for e in client.get("/api/v1/entities?q=Provenance%20Bridge", headers=analyst).json()
           if e["name"] == "Provenance Bridge"][0]
    detail = client.get(f"/api/v1/entities/{ent['id']}", headers=analyst).json()
    attrs = detail["entity"]["attributes"]
    assert attrs["source_file"] == "prov.csv"
    assert attrs["provenance"] == "imported"
    assert attrs["validation"] == "passed"
    assert attrs["ingested_at"]
    assert attrs["dataset_id"] == ds["id"]


def test_09_relationships_require_evidence(client, analyst):
    ents = client.get("/api/v1/entities?limit=5", headers=analyst).json()
    a, b = ents[0]["id"], ents[1]["id"]
    r = client.post("/api/v1/relationships", headers=analyst,
                    json={"source_id": a, "target_id": b, "rel_type": "associated_with",
                          "provenance": "inferred", "confidence": 0.6, "evidence": ""})
    assert r.status_code == 400, "evidence-free relationships must be refused"
    ok = client.post("/api/v1/relationships", headers=analyst,
                     json={"source_id": a, "target_id": b, "rel_type": "associated_with",
                           "provenance": "inferred", "confidence": 0.6,
                           "evidence": "Co-occurrence in synthetic register", "source_ref": "test"})
    assert ok.status_code == 200
    assert ok.json()["provenance"] == "inferred"
    assert ok.json()["evidence"]


def test_09b_invalid_provenance_rejected(client, analyst):
    ents = client.get("/api/v1/entities?limit=2", headers=analyst).json()
    r = client.post("/api/v1/relationships", headers=analyst,
                    json={"source_id": ents[0]["id"], "target_id": ents[1]["id"],
                          "rel_type": "connected_to", "provenance": "certain", "evidence": "x"})
    assert r.status_code == 400


def test_16_end_to_end_analytical_workflow(client):
    from tests.conftest import _login
    analyst = _login(client, "analyst@gotham-demo.in")
    reviewer = _login(client, "reviewer@gotham-demo.in")

    ds = client.post("/api/v1/datasets", headers=analyst,
                     json={"name": "E2E Workflow Dataset", "description": "end to end",
                           "source_type": "file", "source_org": "SYNTHETIC"}).json()
    rows = [{"name": "E2E Shelter Site", "entity_type": "facility", "district": "Ganjam"},
            {"name": "E2E Supply Depot", "entity_type": "warehouse", "district": "Ganjam"}]
    ing = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=analyst,
                      files={"file": ("e2e.csv", _csv_bytes(rows), "text/csv")}).json()
    assert ing["entities_created"] == 2

    ents = client.get("/api/v1/entities?q=E2E", headers=analyst).json()
    ids = {e["name"]: e["id"] for e in ents}
    rel = client.post("/api/v1/relationships", headers=analyst,
                      json={"source_id": ids["E2E Supply Depot"], "target_id": ids["E2E Shelter Site"],
                            "rel_type": "connected_to", "provenance": "confirmed", "confidence": 0.9,
                            "evidence": "E2E fixture linkage", "source_ref": "e2e.csv"})
    assert rel.status_code == 200

    case = client.post("/api/v1/cases", headers=analyst,
                       json={"title": "E2E Readiness Case", "description": "workflow verification",
                             "classification": "INTERNAL"}).json()
    finding = client.post(f"/api/v1/cases/{case['id']}/findings", headers=analyst,
                          json={"title": "Depot serves shelter site", "description": "linked in fixture",
                                "kind": "evidence", "confidence": 0.85,
                                "evidence_refs": [ids["E2E Supply Depot"], ids["E2E Shelter Site"]]})
    assert finding.status_code == 200, finding.text
    fid = finding.json()["id"]

    rev = client.post(f"/api/v1/cases/{case['id']}/findings/{fid}/review?decision=approved", headers=reviewer)
    assert rev.status_code == 200 and rev.json()["reviewer_status"] == "approved"

    ai = client.post("/api/v1/ai/ask", headers=analyst,
                     json={"question": "What is the relationship between the E2E supply depot and shelter site?",
                           "case_id": case["id"]}).json()
    assert ai["citations"], "AI answer must cite retrieved records"
    assert any("E2E" in c["title"] for c in ai["citations"])

    case_detail = client.get(f"/api/v1/cases/{case['id']}", headers=analyst).json()
    assert case_detail["findings"][0]["reviewer_status"] == "approved"


def test_connector_sdk_catalog_and_honest_health(client, analyst, admin):
    """Connector SDK: implemented kinds work, credential-bound kinds refuse rather than fake success."""
    cat = client.get("/api/v1/admin/connector-catalog", headers=analyst)
    assert cat.status_code == 200
    kinds = {c["kind"]: c["status"] for c in cat.json()["connectors"]}
    assert kinds["csv"] == "implemented" and kinds["rest"] == "requires_credentials"

    from app.services import connectors as sdk
    csv_c = sdk.get_connector("csv", {"content": "name,entity_type,district\nSDK Asset,asset,Puri\n"})
    rows = csv_c.load()
    assert rows and rows[0]["name"] == "SDK Asset" and rows[0]["district"] == "Puri"
    schema = csv_c.discover_schema()
    assert any(f["name"] == "name" for f in schema.fields)
    assert csv_c.health_check().verified is True

    rest = sdk.get_connector("rest", {"base_url": "https://example.invalid", "endpoint": "/x"})
    report = rest.health_check()
    assert report.healthy is False and report.verified is False
    assert "credential" in report.detail.lower()

    pg = sdk.get_connector("postgres", {"dsn": "postgresql://x", "query": "DELETE FROM users"})
    assert pg.health_check().healthy is False  # write statements are refused outright
