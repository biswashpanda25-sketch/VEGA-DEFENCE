# Release Notes

## v1.2 — 2026-11-12 · Phase-A/B execution pass

**Verified capability added**
- **ABAC clearance** (INTERNAL/RESTRICTED/PROTECTED) on every read path, including retrieval and analytics;
  above-clearance reads return 404 rather than 403 so existence is not disclosed.
- **TOTP multi-factor authentication** — enrolment, activation and an enforced login challenge.
- **Hash-chained audit trail** with `GET /api/v1/audit/verify`; a test proves that mutating one row breaks
  verification and identifies the record.
- **Entity resolution and merge** — trigram-blocked candidates with scored match reasons; merge is
  human-gated, reversible, re-points relationships and is audited.
- **Connector job ledger** — attempt history, exponential backoff, dead-letter, `GET /api/v1/admin/jobs`.
- **PostGIS proximity** (`GET /api/v1/geo/nearby`) with GiST KNN and an honest engine field.
- **Bounded, clearance-aware retrieval** — candidate selection pushed into the database, capped at 500.

**Measured, not estimated**
- PostgreSQL 17 + PostGIS 3.5 + pg_trgm + pgvector executed locally; suite green on both backends (61/61).
- 1,000,000-entity benchmark: spatial KNN 1.05 ms p50, list page 0.14 ms, `/search` 28 ms, `/ai/ask` 59 ms.
  Known slow paths published too: `analytics/overview` 504 ms, broad-term search 196 ms.
- Three scale defects found and fixed: JIT overhead (~180 ms per interactive query), PostGIS index not used,
  full-corpus retrieval. Full write-up in `docs/SCALE.md`.

**Fixed**
- Graph endpoint 500 when scoping relationships (now covered by a schema-derived route matrix test).
- Login throttling counted successful logins, locking out legitimate users under load; now counts failures only.
- Audit verification failed against its own rows because timestamps lost their timezone on round trip; hashing
  now canonicalises before hashing.
- Backup drill compared org-scoped API counts against whole-database restore counts; parity baseline is now
  taken from the database at dump time.

**Honest status:** re-measured capability index **16.3%** (was 7.2%). Still below the Phase-A gate (20.7%) —
identity federation and real source-system connectors are untouched.


## 1.0.0 — 2026-11-12

First integrated release candidate of the GOTHAM INDIA demonstration platform. All data synthetic.

### Added
- **Foundation** — FastAPI service with JWT auth, bcrypt hashing, login rate limiting; RBAC across seven roles;
  organization/tenant model with query-layer isolation; append-only audit service; Alembic migration baseline.
- **Data** — dataset and connector registry; CSV/JSON/XLSX ingestion with schema normalisation, duplicate detection,
  provenance retention and weighted data-quality scoring; document upload with type allow-list and 25 MB cap.
- **Intelligence** — entity graph with mandatory-evidence relationships and four provenance classes; interactive
  force-directed explorer with evidence inspection; BM25-style permission-filtered search.
- **Analysis** — case workspaces; typed findings (evidence/assumption/hypothesis/conclusion); reviewer approval
  workflow with immutable audit events.
- **Geospatial** — MapLibre explorer with clustering, heatmap, layer toggles, district reference geography and
  freshness indicators; district summary endpoint.
- **AI** — tenant-scoped retrieval with an evidence-admission gate; citation-only composition and refusal path;
  optional Ollama / OpenAI-compatible provider with citation validation; evaluation harness.
- **Operations** — asset posture and exception queue, advisory capacity projection with stated limitations,
  notifications, CSV/JSON/PDF reporting with classification metadata.
- **Console** — dark enterprise shell, 14 functional screens, universal search, contextual side panel.
- **Delivery** — Dockerfiles, Compose (PostGIS, Redis, nginx), CI pipeline with migrations, tests, AI evaluation,
  dependency audit and secret scan; full documentation set.

### Measured
- 25/25 automated tests passing, covering all 16 mandated scenarios.
- AI: precision 0.81, recall 1.00, groundedness 0.73, unsupported-claim rate 0.00, permission-leakage 0.00, p50 8.6 ms.
- API: p50 1.3–9.5 ms across seven endpoints (sequential single client; not a capacity test).

### Known limitations at release
No MFA/OIDC/SAML; Postgres/PostGIS/pgvector paths unexecuted here; no AV scanning on uploads; synchronous ingestion;
no frontend E2E suite; external model path unmeasured. Full list in `docs/KNOWN_ISSUES.md`.

### Not claimed
No security certification, no compliance attestation, no production-readiness claim, no live external integration.
