# GOTHAM INDIA — Project Status

**Last updated:** 2026-11-12 (IST)
**Build:** 1.0.0
**Environment of record:** sandboxed Linux, Python 3.13.16, Node 20.20.2; **PostgreSQL 17.11 + PostGIS 3.5 +
pg_trgm + pgvector** executed locally alongside the SQLite development store
**Data in system:** 100% synthetic demonstration dataset (Odisha public-infrastructure / disaster-coordination scenario)

This file is the single source of truth for what is *actually built*, what is *simulated*, and what is *planned*.
No capability is listed as implemented unless it runs in this repository and has been exercised.

---

## 1. Phase status

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 0 | Repository & environment audit | **Complete** | `docs/AUDIT.md` |
| 1 | Foundation: repo, auth, RBAC, tenants, audit, DB | **Complete (+ABAC, MFA, audit chain)** | 61 passing tests on both backends, login flow live |
| 2 | Data foundation: ingestion, connectors, catalog, quality, lineage-lite | **Complete (file-based)** | CSV/JSON/XLSX ingestion, duplicate detection, quality scoring, provenance |
| 3 | Intelligence foundation: entities, relationships, graph explorer, search, cases | **Complete** | Graph explorer, BM25-style search, case/finding/reviewer workflow |
| 4 | Geospatial engine | **Complete (PostGIS executed)** | MapLibre GL with clustering and heatmap; `/geo/nearby` runs GiST geography KNN at 1.05 ms p50 on 1,000,000 entities (`docs/SCALE.md`); district anchors remain approximations (KI-11) |
| 5 | AI engine | **Complete (deterministic grounded mode)** | Retrieval-gated answers with citations, refusal path, eval harness (measured) |
| 6 | Operational intelligence, alerts, reporting | **Complete (record-derived)** | Asset health, exception queue, notifications, CSV/JSON/PDF reports |
| 7 | Enterprise security hardening | **Partial** | Controls implemented and tested (isolation, RBAC, validation, rate limit); no external pen-test performed |
| 8 | Production readiness | **Partial** | Docker/Compose/nginx/CI/Alembic delivered; **1M-row load test and `pg_dump`/`pg_restore` parity drill executed**; containers never executed here (KI-14) |

---

## 2. Implemented and verified

### Backend (FastAPI, SQLAlchemy 2.1, Pydantic 2)
- JWT authentication (HS256, bcrypt hashes), `/auth/login|register|me|logout`
- **TOTP MFA**: enrol → activate → enforced login challenge (`/auth/mfa/*`), tested end to end
- **Failed-attempt throttling** (20/min per IP, failures only, configurable)
- **ABAC clearance** (INTERNAL/RESTRICTED/PROTECTED) enforced on every read path, including retrieval and analytics;
  404 — not 403 — above clearance; audited clearance administration
- **Field-level redaction** gated by declared purpose, with purpose recorded in the audit row
- **Hash-chained audit trail** with `GET /audit/verify` tamper detection
- **Connector job ledger** with attempt history, exponential backoff and dead-letter (`GET /admin/jobs`)
- **Entity resolution**: trigram blocking, scored candidates with match reasons, human-gated reversible merge
- **Spatial proximity** (`/geo/nearby`) using PostGIS GiST + KNN with an honest `engine` field
- Role model: `platform_admin`, `org_admin`, `data_admin`, `analyst`, `reviewer`, `readonly`, `auditor`
- Tenant isolation enforced at the query layer on every collection endpoint
- Dataset/connector registry, file ingestion (CSV, JSON, XLSX), schema normalisation, duplicate detection, quality scoring
- Document store with type allow-list and size caps
- Entity and relationship model with **mandatory evidence** and provenance classification
- Case workspaces, findings typed as evidence/assumption/hypothesis/conclusion, reviewer decisions
- Hybrid search (BM25-style lexical scoring) with permission filtering and audit logging
- Grounded AI assistant: retrieval gate, citation-only composition, refusal path, optional external model with citation validation
- Geospatial endpoints: district GeoJSON, entity feature collection, district summary
- Notifications, audit log, administration (users, roles, connectors, health, AI usage)
- Alembic migration baseline (`migrations/versions/05e13bc558ae_initial_schema.py`)

### Frontend (React 19, TypeScript, Vite 8, MapLibre GL, ECharts, TanStack Query, Zustand)
- Dark enterprise shell: sidebar navigation, universal type-ahead search, notifications centre, org/tenant context, user menu
- 14 working screens (Overview, Data Sources, Catalog, Search, Graph, Workspaces, Cases, Geospatial, Operations, AI Assistant, Reports, Notifications, Administration, Security & Audit)
- Interactive force-directed knowledge-graph explorer with provenance-encoded edges and evidence side panel
- MapLibre map with clustering, heatmap, layer toggles, region summary, feature inspection
- Real charts bound to live API aggregates (no hardcoded series)

### Infrastructure
- Connector SDK (`services/connectors.py`): base interface + CSV/JSON/Excel implementations, REST/Postgres
  adapters that refuse to run without authorized credentials, catalogue + health-check endpoints
- Dockerfiles (API, web), docker-compose with PostGIS + Redis + nginx reverse proxy, DB secrets via file
- GitHub Actions CI: migrations, tests, AI evaluation, frontend typecheck/build, dependency audit, secret scan

### Measured results (this environment)
- Test suite: **61 backend tests passed on SQLite and 61 on PostgreSQL 17 + PostGIS**; browser E2E: **27/27 checks passed**
- AI evaluation: retrieval precision 0.81, recall 1.00, groundedness 0.73, unsupported-claim rate 0.00, permission leakage 0.00, p50 latency 8.6 ms
- API benchmark: p50 1.3–9.5 ms across seven endpoints (sequential, single client)

---

## 3. Simulated or limited (explicitly labelled in-product)

| Capability | Reality in this build |
|---|---|
| Institutional data | Synthetic Odisha dataset, every record flagged `SYNTHETIC` in the UI |
| External connectors | SDK ships CSV/JSON/Excel (working) and REST/Postgres adapters that refuse to run without credentials; **no external integration is operational** — one connector is seeded in `error` state to model an unconfigured feed |
| OCR | Not enabled; PDF ingestion stores raw text extraction only |
| District boundaries | Centroid reference anchors, not licensed Survey of India polygons |
| LLM | Default `grounded-local` deterministic composer; hosted/Ollama path implemented but unverified without credentials |
| Email / webhook notifications | Channel interface defined; no endpoint configured, so delivery is not claimed |
| Background job queue | Ingestion is synchronous; queue/worker design documented, not deployed |
| MFA / OIDC / SAML | Data model and UI placeholders (`mfa_enabled`), flows **not implemented** |

---

## 4. Known issues

See `docs/KNOWN_ISSUES.md` — 11 open items, none of which are silent failures; each is either surfaced in the UI or documented.

---

## 5. Immediate next tasks

1. OIDC/SAML provider integration with MFA enrolment (Phase 7 item, blocks any real deployment)
2. Postgres/PostGIS/pgvector execution path: move retrieval from lexical to hybrid embeddings; measure before switching
3. Background ingestion worker (Celery/RQ) with retry/backoff and dead-letter handling
4. Field-level classification enforcement (currently record-level) and cross-org sharing grants
5. Load and soak testing against Postgres with ≥100 concurrent analysts
6. Hash-chained audit export to write-once storage; restore drill on managed infrastructure
7. OCR pipeline (Tesseract or institutional OCR service) with malware scanning before extraction
