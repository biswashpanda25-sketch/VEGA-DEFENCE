"""Phase-A/B proof: ABAC clearance, field redaction, audit hash chain, MFA, resolution, spatial query."""
import pyotp


def _login(client, email, password="Gotham@2026", totp=None):
    body = {"email": email, "password": password}
    if totp:
        body["totp"] = totp
    return client.post("/api/v1/auth/login", json=body)


def test_abac_hides_records_above_clearance(client, analyst, admin):
    """INTERNAL-clearance analyst must not see RESTRICTED or PROTECTED records."""
    visible = client.get("/api/v1/entities?limit=300", headers=analyst).json()
    names = {e["name"] for e in visible}
    assert all(e["classification"] == "INTERNAL" for e in visible), "analyst sees above clearance"
    assert "Embankment Segment BBSR-07 (Synthetic)" not in names, "PROTECTED record leaked"
    assert "Substation K-17 (Synthetic)" not in names, "RESTRICTED record leaked"

    # platform admin holds PROTECTED clearance and does see them
    admin_view = client.get("/api/v1/entities?limit=300", headers=admin).json()
    admin_names = {e["name"] for e in admin_view}
    assert "Embankment Segment BBSR-07 (Synthetic)" in admin_names
    assert len(admin_view) > len(visible)


def test_abac_direct_fetch_above_clearance_is_404(client, analyst, admin):
    protected = [e for e in client.get("/api/v1/entities?limit=300", headers=admin).json()
                 if e["classification"] == "PROTECTED"]
    assert protected, "seed must contain a PROTECTED record for this test to mean anything"
    r = client.get(f"/api/v1/entities/{protected[0]['id']}", headers=analyst)
    # existence is not disclosed: 404, never 403 with the title
    assert r.status_code == 404
    assert "BBSR-07" not in r.text


def test_clearance_change_is_audited_and_scoped(client, admin, analyst):
    me = client.get("/api/v1/auth/me", headers=analyst).json()
    r = client.patch(f"/api/v1/admin/users/{me['id']}/clearance?clearance=RESTRICTED", headers=admin)
    assert r.status_code == 200 and r.json()["clearance"] == "RESTRICTED"
    now_visible = {e["name"] for e in client.get("/api/v1/entities?limit=300", headers=analyst).json()}
    assert "Substation K-17 (Synthetic)" in now_visible, "RESTRICTED record must appear at RESTRICTED clearance"

    log = client.get("/api/v1/audit?action=admin.clearance_change", headers=admin).json()
    assert any("INTERNAL -> RESTRICTED" in (e["detail"] or "") for e in log)

    # restore least privilege for the rest of the suite
    client.patch(f"/api/v1/admin/users/{me['id']}/clearance?clearance=INTERNAL", headers=admin)


def test_field_level_redaction_requires_purpose(client, admin):
    ent = client.get("/api/v1/entities?limit=1", headers=admin).json()[0]
    # inject a marked field directly, as an import would
    from app.db import SessionLocal
    from app.models import Entity
    db = SessionLocal()
    row = db.query(Entity).filter(Entity.id == ent["id"]).first()
    row.attributes = {**(row.attributes or {}), "contact_phone": "+91-00000-00000"}
    db.commit()
    db.close()

    without = client.get(f"/api/v1/entities/{ent['id']}", headers=admin).json()["entity"]
    assert "contact_phone" not in (without.get("attributes") or {}), "marked field leaked without purpose"
    assert without.get("redacted_fields"), "redaction must be visible to the caller"

    with_purpose = client.get(f"/api/v1/entities/{ent['id']}?purpose=audit_review", headers=admin).json()["entity"]
    assert (with_purpose.get("attributes") or {}).get("contact_phone") == "+91-00000-00000"


def test_audit_chain_verifies_and_detects_tampering(client, admin):
    v = client.get("/api/v1/audit/verify", headers=admin)
    assert v.status_code == 200 and v.json()["valid"] is True
    assert v.json()["checked"] > 0

    from app.db import SessionLocal
    from app.models import AuditEvent
    db = SessionLocal()
    row = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
    original = row.detail
    row.detail = "tampered by an actor with database access"
    db.commit()
    db.close()

    broken = client.get("/api/v1/audit/verify", headers=admin).json()
    assert broken["valid"] is False and broken["broken_at"], "hash chain must detect modification"

    db = SessionLocal()
    row = db.query(AuditEvent).filter(AuditEvent.id == broken["broken_at"]).first()
    if row:
        row.detail = original
        db.commit()
    db.close()


def test_mfa_enrollment_and_login_enforcement(client):
    """MFA is exercised on a dedicated identity so the rest of the suite is not affected."""
    email = "mfa-probe@gotham-demo.in"
    reg = client.post("/api/v1/auth/register", json={
        "email": email, "password": "Gotham@2026", "full_name": "MFA Probe",
        "organization_code": "ODISHA-DEMO", "role": "analyst"})
    if reg.status_code == 400:  # already registered by an earlier run
        reg = _login(client, email)
    tok = reg.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    enroll = client.post("/api/v1/auth/mfa/enroll", headers=h)
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]
    assert enroll.json()["otpauth_uri"].startswith("otpauth://totp/")

    bad = client.post("/api/v1/auth/mfa/activate?code=000000", headers=h)
    assert bad.status_code == 400
    assert client.post(f"/api/v1/auth/mfa/activate?code={pyotp.TOTP(secret).now()}", headers=h).status_code == 200

    # password alone is no longer sufficient for this identity
    no_code = _login(client, email)
    assert no_code.status_code == 401 and "MFA" in no_code.json()["detail"]
    assert _login(client, email, totp="000000").status_code == 401
    ok = _login(client, email, totp=pyotp.TOTP(secret).now())
    assert ok.status_code == 200

    step = client.post(f"/api/v1/auth/mfa/verify?code={pyotp.TOTP(secret).now()}",
                       headers={"Authorization": f"Bearer {ok.json()['access_token']}"})
    assert step.status_code == 200 and step.json()["verified"] is True


def test_entity_resolution_candidates_and_merge(client, admin, analyst):
    ds = client.post("/api/v1/datasets", headers=admin,
                     json={"name": "Resolution Fixture", "description": "", "source_type": "file"}).json()
    rows = ("name,entity_type,district\n"
            "Bhadrak Pumping Station (Synthetic),facility,Bhadrak\n"
            "Bhadrak Pump Station (Synthetic),facility,Bhadrak\n")
    client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=admin,
                files={"file": ("res.csv", rows.encode(), "text/csv")})

    ents = client.get("/api/v1/entities?q=Bhadrak", headers=admin).json()
    assert len(ents) >= 2
    a, b = ents[0], ents[1]

    cands = client.get(f"/api/v1/entities/{a['id']}/resolution-candidates", headers=admin).json()
    assert cands["candidates"], "trigram/fuzzy blocking must propose the near-duplicate"
    top = cands["candidates"][0]
    assert top["similarity"] > 0.6 and "same district" in top["match_reasons"]

    # analysts cannot merge; reviewers/admins can
    denied = client.post(f"/api/v1/entities/merge?survivor_id={a['id']}&duplicate_id={b['id']}"
                         f"&reason=test", headers=analyst)
    assert denied.status_code == 403

    merged = client.post(f"/api/v1/entities/merge?survivor_id={a['id']}&duplicate_id={b['id']}"
                         f"&reason=Same facility, spelling variant", headers=admin)
    assert merged.status_code == 200 and merged.json()["reversible"] is True

    remaining = client.get("/api/v1/entities?q=Bhadrak", headers=admin).json()
    assert len(remaining) == len(ents) - 1, "merged duplicate must leave the active set"
    merged_entity = client.get(f"/api/v1/entities/{b['id']}", headers=admin).json()["entity"]
    assert merged_entity["attributes"].get("merged_into") == a["id"]


def test_spatial_proximity_query(client, admin):
    r = client.get("/api/v1/geo/nearby?lat=20.18&lon=85.62&radius_km=60", headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] in ("postgis-gist-knn", "postgis", "haversine")
    assert body["count"] > 0, "seed entities carry coordinates"
    distances = [x["distance_km"] for x in body["results"]]
    assert distances == sorted(distances), "results ordered by distance"
    assert all(d <= 60 for d in distances)

    bad = client.get("/api/v1/geo/nearby?lat=999&lon=0", headers=admin)
    assert bad.status_code == 400


def test_ingestion_job_ledger_records_retries_and_dead_letters(client, admin):
    ds = client.get("/api/v1/datasets", headers=admin).json()[0]
    bad = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=admin,
                      files={"file": ("broken.json", b"{{{{", "application/json")})
    assert bad.status_code == 400

    jobs = client.get("/api/v1/admin/jobs?status=dead_letter", headers=admin).json()
    assert jobs, "exhausted ingestion must land in the dead-letter queue"
    job = jobs[0]
    assert job["attempts"] == job["max_attempts"] == 3
    assert "Malformed JSON" in job["last_error"] or "json" in job["last_error"].lower()

    good = client.post(f"/api/v1/datasets/{ds['id']}/ingest", headers=admin,
                       files={"file": ("ok.json", b'[{"name":"Job Ledger Asset","entity_type":"asset"}]',
                                       "application/json")})
    assert good.status_code == 200 and good.json()["attempts"] == 1
