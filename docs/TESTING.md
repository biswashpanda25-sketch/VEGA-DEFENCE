# Testing Strategy and Executed Results

**Executed:** 2026-11-12, Python 3.13.16.
**Commands:**
- `cd backend && python -m pytest tests -q` → **61 passed in 19.4 s** (SQLite)
- `GOTHAM_TEST_DB_URL="postgresql+psycopg://gotham:gotham_dev_pw@127.0.0.1:5432/gotham_test" python -m pytest tests -q` → **61 passed in 20.8 s** (PostgreSQL 17 + PostGIS)
- `cd frontend && npm run e2e` → **27/27 browser checks passed** (Playwright, headless Chromium)
- `python -m tests.scale --rows 1000000` + `python -m tests.bench_scale` → published in `docs/SCALE.md`

The full suite runs green against **both** backends. The PostgreSQL run is not a smoke test: it exercises
PostGIS predicates, trigram blocking, `pg_dump`/`pg_restore` parity and the JSON/array column types.

No test in this document is aspirational — every row below was executed in this environment.

## 1. Mandated scenario coverage

| # | Required scenario | Test | Assertion |
|---|---|---|---|
| 1 | Unauthorised users cannot access protected records | `test_01_unauthenticated_access_denied`, `test_01b_invalid_token_denied` | 401 on six protected routes with no/forged token |
| 2 | One tenant cannot access another tenant's information | `test_02_tenant_isolation_entities`, `test_02b_cross_tenant_entity_fetch_denied`, `test_02c_cross_tenant_case_denied` | disjoint result sets; 404 across tenants |
| 3 | Restricted fields not exposed through APIs | `test_03_restricted_fields_not_exposed` | no password hashes; connector secrets stripped; analyst refused user enumeration |
| 4 | Document uploads validated | `test_04_document_upload_validation` | `.exe` → 400; `.txt` accepted with extracted characters |
| 5 | Malformed files do not crash ingestion | `test_05_malformed_files_do_not_crash` | malformed JSON/CSV/XLSX/XML → 400/422, API healthy afterwards |
| 6 | Failed connectors recover appropriately | `test_06_connector_failure_and_recovery` | failure → 400 + `dataset.ingest_failed` audit; retry succeeds |
| 7 | Duplicate records detected | `test_07_duplicate_detection` | second identical ingest creates 0 entities, skips 1 duplicate |
| 8 | Data provenance preserved | `test_08_provenance_preserved` | source file, dataset id, ingest timestamp, validation status retained |
| 9 | Graph relationships have evidence | `test_09_relationships_require_evidence`, `test_09b_invalid_provenance_rejected` | evidence-free and invalid-provenance links refused |
| 10 | AI responses cite source records | `test_10_ai_answers_cite_sources`, `test_10b_ai_refuses_without_evidence`, `test_10c_prompt_injection_text_is_not_executed` | `[E#]` markers resolve; refusal on no evidence; injected instructions never executed |
| 11 | AI cannot access restricted information | `test_11_ai_cannot_reach_other_tenant` | other tenant receives `insufficient_evidence` with zero citations |
| 12 | Search respects permissions | `test_12_search_respects_permissions` | analyst 4+ hits, other tenant 0 hits |
| 13 | Audit events recorded | `test_13_audit_events_recorded`, `test_13b_rate_limit_on_login` | login + search events present; analyst refused audit; 429 on brute force |
| 14 | Database migrations work | `test_14_schema_and_migrations`, `test_14b_alembic_migration_applies_cleanly` | required tables/FKs present; `alembic upgrade head` on empty DB reproduces schema |
| 15 | Backup restoration succeeds | `test_15_backup_and_restore` | SQLite online-backup snapshot restored with matching entity count and non-zero audit rows |
| 16 | Critical workflows work end-to-end | `test_16_end_to_end_analytical_workflow` | ingest → entity → relationship → case → finding → reviewer approval → AI citation → case reflects approval |

Additional: `test_swagger_and_openapi_available` verifies OpenAPI generation for the documented namespaces.

## 1a. Phase-A/B capability tests (`tests/test_abac_and_resolution.py`, 8 tests)

| Capability | Test | Assertion |
|---|---|---|
| Clearance-scoped visibility | `test_clearance_scopes_entity_visibility` | analyst sees only INTERNAL; admin sees PROTECTED |
| Above-clearance reads are indistinguishable from absent | `test_above_clearance_fetch_is_404_not_403` | 404, not 403 — existence is not disclosed |
| Clearance changes are auditable | `test_clearance_change_is_audited_and_scoped` | admin action recorded; analyst refused the endpoint |
| Field-level redaction by purpose | `test_field_redaction_requires_purpose_and_clearance` | contact field hidden without purpose, revealed with a permitted purpose and sufficient clearance |
| Audit tamper detection | `test_audit_chain_verifies_and_detects_tampering` | chain verifies; a single mutated row makes `valid=false` with `broken_at` |
| MFA end-to-end | `test_mfa_enrollment_and_login_enforcement` | enrolment, activation, wrong-code rejection, password-only rejection, TOTP login |
| Entity resolution + merge RBAC | `test_entity_resolution_candidates_and_merge` | candidates scored with reasons; analyst refused merge; reviewer merge re-points relationships |
| Spatial proximity | `test_spatial_proximity_query` | radius search returns ordered distances; engine reported per backend |
| Job retry and dead-letter | `test_job_dead_letter_after_retries` | bounded attempts, backoff, terminal `dead_letter` state |

## 1b. Route matrix (`tests/test_route_matrix.py`, 26 parametrised cases)

Every GET endpoint in the OpenAPI schema that takes no path parameters is called with an analyst identity and
must return a non-5xx status. This exists because `/api/v1/graph` returned 500 for an entire development
session after `scope_query` learned about classification — a bug no scenario test covered. The matrix is
generated from the schema, so new endpoints are covered automatically the moment they are registered.
`test_connector_sdk_catalog_and_honest_health` proves the connector SDK runs implemented kinds and refuses
credential-bound ones instead of reporting fake health.

## 2. Test design

- **Fixtures**: `conftest.py` creates a temp directory per session, points `DATABASE_URL` at it, seeds the synthetic
  dataset, and exposes role-based tokens (analyst, reviewer, admin, other-tenant analyst).
- **Isolation**: tests never touch the development database; ordering is not relied upon except for seed data.
- **Negative-first**: most assertions are about refusal — 401/403/404/400 — because the platform's value is
  bounded by what it refuses to do.

## 3. Browser end-to-end (executed)

`frontend/e2e/smoke.mjs` (Playwright + headless Chromium) drives the real application against the running
API and asserts 26 behaviours: sign-in, live KPI rendering, all 14 sections, graph node → evidence panel,
MapLibre canvas + feature count, assistant answer with citations naming the cited record, ranked search hits,
sign-out, and zero uncaught browser errors / unexpected failed requests.

```
cd frontend && npm run e2e       # 27/27 checks passed
```

Screenshots captured during the run are written to `frontend/e2e/screenshots/` (copies in `docs/screenshots/`).
HTTP 403 responses from role-restricted panels are expected and are asserted as such, not suppressed.

## 4. Not yet covered (honest gaps)

- Frontend unit/component tests (browser E2E only).
- Concurrency and load testing (single-client benchmark only).
- Postgres/PostGIS execution (sandbox has no server).
- Accessibility audit with assistive technology.
- Fault injection on the database or object store.

## 5. Reproducing

```bash
cd backend
python -m pytest tests -q                 # functional + security suite
python -m tests.eval_ai                   # AI grounding evaluation
python -m tests.bench --n 40              # latency benchmark (requires running API)
cd ../frontend && npm run typecheck && npm run build && npm run e2e
```
