# Known Issues and Limitations

Severity: **S1** blocks production · **S2** material gap · **S3** cosmetic/limited.
**Last reviewed:** 2026-11-12, after the Phase-A/B execution pass.

| ID | Sev | Issue | Impact | Workaround / next step |
|---|---|---|---|---|
| KI-01 | S1 | No OIDC/SAML identity provider. Local passwords + TOTP MFA only. | Institutional SSO, group sync and central de-provisioning are impossible. | TOTP MFA is now implemented and tested (`/auth/mfa/*`); the remaining work is IdP federation (Keycloak/ADFS/Azure AD) — see Roadmap Phase A. |
| ~~KI-02~~ | — | ~~Postgres/PostGIS paths unexecuted~~ **CLOSED 2026-11-12**: PostgreSQL 17 + PostGIS 3.5 + pg_trgm + pgvector run locally; the full suite passes against it (61/61), Alembic builds the schema from empty → head, and a 1,000,000-row dataset is benchmarked (`docs/SCALE.md`). Docker remains unavailable, so *container* execution is still unproven. | — | Remaining gap split into KI-14 (containers). |
| KI-03 | S2 | No antivirus/CDR scanning before document extraction. | Malicious uploads could reach the extractor. | Allow-list + 25 MB cap only; add ClamAV or an institutional scanning service first. |
| KI-04 | S2 | Ingestion is synchronous in the request path. | A large file blocks a request; retry semantics exist but the caller waits. | Every ingest is wrapped in a `ConnectorJob` ledger with attempts, backoff and dead-letter (`GET /admin/jobs`). Next step: move execution to an RQ/Celery worker — the ledger is already the durable state a worker needs. |
| KI-05 | S2 | No server-side token revocation or refresh rotation. | A stolen JWT stays valid until expiry. | Short expiry; logout clears the client token. Add a denylist keyed by `jti` plus refresh-token rotation. |
| KI-06 | S2 | Field-level classification is enforced for *sensitive contact fields* only (`RESTRICTED_FIELDS`), not as a general per-field marking scheme. | Mixed-classification records cannot be partially released field by field. | `policy.redact()` + purpose gating exist and are tested; a general marking model needs a field-metadata table. |
| ~~KI-07~~ | — | ~~Audit rows are not hash-chained~~ **CLOSED 2026-11-12**: every audit row carries `seq`, `prev_hash` and `row_hash` (SHA-256 over canonical fields); `GET /audit/verify` walks the chain and reports `broken_at` on tampering, proven by a test that mutates a row. | — | WORM export to immutable storage remains outstanding (KI-15). |
| KI-08 | S2 | No frontend unit/component tests. | UI logic is covered only by the 27-check browser smoke test. | Add Vitest component tests for critical widgets. |
| KI-09 | S2 | External model path unmeasured. | Enabling `AI_PROVIDER=ollama` changes answer quality without local evidence. | Re-run `tests/eval_ai.py` against the target model before enabling; the eval harness and thresholds already exist. |
| KI-10 | S3 | OCR disabled; PDF text extraction is raw byte-decoding. | Scanned PDFs yield poor text. | Documented in the UI; add an OCR service. |
| KI-11 | S3 | District geometry is centroid anchors, not boundaries. | Map shows approximations, no area fills. | Labelled in-product; load licensed Survey of India polygons into PostGIS. |
| KI-12 | S3 | Email/webhook notification channels unimplemented. | Only in-app delivery works. | UI states "not configured"; add adapters when endpoints exist. |
| KI-13 | S3 | `@app.on_event("startup")` is deprecated in FastAPI. | Warning noise; future breakage. | Migrate to a lifespan handler (behaviour is covered by tests either way). |
| KI-14 | S2 | Containers are written but never executed — Docker is unavailable in this environment. | `docker-compose.yml`, Dockerfiles and nginx config are reviewed but unproven. | Run `docker compose up` on a Docker host and record the result in `docs/DEPLOYMENT.md`. |
| KI-15 | S2 | No WORM / immutable audit export and no retention-enforcement job. | An attacker with database superuser access can delete the whole chain, tamper-evidence notwithstanding. | Ship `audit_events` to append-only object storage with object-lock, and run a nightly retention job. |
| KI-16 | S2 | `analytics/overview` performs a full tenant scan — 504 ms p50 at 1,000,000 entities. | Dashboards at large tenants pay a per-request aggregate cost. | Serve from a rollup table or materialized view refreshed on a schedule (`docs/SCALE.md` §5). |
| KI-17 | S2 | Broad-term entity search is slow: 196 ms p50 / 477 ms p95 for a term matching ~39% of 1M rows. | A search box with a very common term feels sluggish at scale. | Keyset + `tsvector` ranking, or an external search engine for broad queries. Selective terms are 46 ms. |
| KI-18 | S3 | Offset pagination degrades linearly (100 ms at offset 50,000 on 1M rows). | Deep page navigation is slow. | Move to keyset pagination. |
| KI-19 | S3 | Login throttling is in-process memory, keyed by client IP. | Does not survive a restart, is per-node, and NAT clusters share a bucket. | Move the counter to Redis and key on (IP, account). Limit is configurable via `LOGIN_MAX_FAILURES_PER_MIN` (default 20/min, failed attempts only). |
| KI-20 | S3 | No partitioning, no connection pooler, no read replicas. | 1,000,000 rows is comfortable and measured; 10,000,000 is untested. | Declarative partitioning by organization + PgBouncer before any multi-worker deployment. |
| KI-21 | S3 | `pgvector` is installed but retrieval is lexical (BM25) only. | Semantic recall is not available. | The candidate pre-filter interface is the seam; add embeddings + `ivfflat`/`hnsw` index behind `Retriever`. |

## Notes on honesty

- KI-16/KI-17 are published *because* they were measured, not because they were suspected. Both are
  reproducible with `tests/bench_scale.py`.
- Closing a row requires an executed test or benchmark, not a code change that "should" work. Two rows closed
  twice in this project (Postgres, hash-chained audit) with the evidence recorded in `docs/TESTING.md`.
- Nothing in the table is a silent failure: each is surfaced in the interface, the test suite, or the
  documentation.
