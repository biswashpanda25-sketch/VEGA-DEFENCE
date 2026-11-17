# API Reference (v1)

Base URL: `https://<host>/api/v1` · Interactive docs: `/api/docs` · Schema: `/api/openapi.json`
Auth: `Authorization: Bearer <JWT>` on every route except `POST /auth/login`, `POST /auth/register`, `GET /health`.

Standard error envelope: `{"detail": "<human readable>"}` with 400 (validation/domain), 401 (unauthenticated),
403 (role), 404 (not found **or cross-tenant**), 413 (payload), 422 (schema), 429 (rate limit), 500.

## Authentication

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/login` | `{email, password}` → `{access_token, token_type}`; 20 req/min/IP |
| POST | `/auth/register` | Self-registration within an existing organization (disable in production) |
| GET | `/auth/me` | Current identity + role |
| POST | `/auth/logout` | Records an audit event |

## Organizations

`GET /organizations` (own org, or all for platform admin) · `POST /organizations` (platform admin) · `GET /organizations/{id}`

## Datasets & ingestion

| Method | Path | Notes |
|---|---|---|
| GET | `/datasets` | Tenant-scoped list with record counts and quality scores |
| POST | `/datasets` | Create dataset (analyst+) |
| GET | `/datasets/{id}` | Detail |
| POST | `/datasets/{id}/ingest` | multipart `file`: CSV, JSON, XLSX → `{rows, entities_created, duplicates_skipped, quality_score, provenance}` |
| POST | `/datasets/{id}/documents` | multipart `file` + `title`: pdf/txt/md, ≤25 MB |
| GET | `/datasets/{id}/quality` | Completeness / uniqueness / validity / provenance coverage |

## Entities & relationships

| Method | Path | Notes |
|---|---|---|
| GET | `/entities?q=&entity_type=&district=&limit=&offset=` | Tenant-scoped, paginated |
| POST | `/entities` | Create entity |
| GET | `/entities/{id}` | Entity + all relationships with evidence |
| GET | `/entities/{id}/impact?depth=3&direction=downstream` | Breadth-first dependency traversal (max depth 4, cycle-safe); returns affected nodes by hop distance, relationship paths, and link evidence. Inferred edges marked as hypotheses. Scoped to caller tenant and clearance (never counts or leaks hidden records). |
| GET | `/relationships?provenance=` | Filter by provenance class |
| POST | `/relationships` | **Requires** `evidence`; `provenance ∈ confirmed\|imported\|inferred\|unverified` |
| GET | `/graph?limit=&provenance=` | `{nodes, edges}` for the explorer |

## Cases and findings

| Method | Path | Notes |
|---|---|---|
| GET/POST | `/cases` | List / create analytical workspace |
| GET | `/cases/{id}` | Case + findings |
| POST | `/cases/{id}/findings` | `kind ∈ evidence\|assumption\|hypothesis\|conclusion`; evidence/conclusion require `evidence_refs` |
| POST | `/cases/{id}/findings/{fid}/review?decision=` | reviewer/org_admin only: `approved\|rejected\|needs_revision` |

## Search

`GET /search?q=&kind=&limit=` → ranked `{results:[{kind,id,title,snippet,classification,synthetic,score}], count}`.
Ranking is BM25-style; results are tenant-filtered before scoring; the query is audited.

## Geospatial

`GET /geo/districts` (reference GeoJSON) · `GET /geo/assets?layer=` (entity features, district-anchored) ·
`GET /geo/summary` (counts per district).

## AI

`POST /ai/ask` `{question, case_id?}` → `{answer, citations[], confidence, insufficient_evidence, meta}`.
`GET /ai/history` · `GET /ai/config`.
Guarantees: retrieval scoped to caller's organization; every factual sentence carries `[E#]`; refusals are explicit;
model output is rejected if citations do not resolve.

## Operations / analytics

`GET /analytics/overview` · `GET /analytics/asset-health` · `GET /notifications` · `POST /notifications/{id}/read`

## Audit and administration

`GET /audit?action=&limit=` (auditor/org_admin/platform_admin) ·
`GET /admin/users` · `PATCH /admin/users/{id}/role?role=` · `GET /admin/connectors` ·
`GET /admin/system-health` · `GET /admin/ai-usage` · `GET /admin/jobs`

## Governance (ABAC, MFA, audit integrity, resolution, spatial)

| Endpoint | Access | Behaviour |
|---|---|---|
| `GET /audit/verify` | auditor, org_admin, platform_admin | Walks the hash chain in `seq` order → `{valid, checked, head, tail, broken_at, reason}` |
| `GET /admin/clearances` | platform_admin | Available clearance levels + every user's role, clearance and MFA state |
| `PATCH /admin/users/{id}/clearance?clearance=` | platform_admin | Sets a clearance; audited as `admin.clearance_change` |
| `POST /auth/mfa/enroll` | any authenticated | Returns `{secret, otpauth_uri}` once; stores the secret, not the code |
| `POST /auth/mfa/activate?code=` | any authenticated | Verifies the first code and enables enforcement (400 on a wrong code) |
| `POST /auth/mfa/verify?code=` | any authenticated | Step-up verification for the current session |
| `POST /auth/login` | public | With MFA enabled, requires `{email, password, totp}`; password-only returns 401 `MFA required` |
| `GET /entities/{id}/resolution-candidates` | any authenticated | Trigram-blocked candidates with `score` and `match_reasons` |
| `POST /entities/merge` | reviewer, org_admin, platform_admin | Re-points relationships, sets `canonical_id`, reversible, audited as `entity.merge` |
| `GET /geo/nearby?lat=&lon=&radius_km=&limit=` | any authenticated | PostGIS GiST + KNN, or haversine on SQLite; `engine` reports which path ran |

### Access-control semantics worth knowing

- A record above the caller's clearance returns **404, not 403** — a 403 confirms the record exists.
- `RESTRICTED_FIELDS` (contact/telephone) are omitted unless the caller passes a `purpose` from
  `PERMITTED_PURPOSES` *and* holds ≥ RESTRICTED clearance; the purpose is written to the audit row.
- Merge results set `canonical_id` on the absorbed record; list, search, retrieval and spatial endpoints all
  exclude absorbed records so a merged entity cannot be double-counted.

## Conventions

- Dates are UTC ISO-8601 in transit; the console renders IST (`Asia/Kolkata`).
- Lists are paginated (`limit` capped server-side; default 100–300 depending on resource).
- IDs are UUID strings.
- `X-Process-Time-Ms` is returned on every response for client-side latency observation.
