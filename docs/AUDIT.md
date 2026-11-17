# Phase 0 — Repository and Environment Audit

**Date:** 2026-11-12 · **Auditor:** engineering agent · **Scope:** `/home/user` workspace

## 1. Repository findings

- The workspace was **empty** — no prior source, configuration or build artefacts. No risk of overwriting earlier work.
- No version control history existed in the workspace; the project was initialised as a fresh tree at `gotham-india/`.

## 2. Runtime inventory (measured, not assumed)

| Component | Finding | Consequence |
|---|---|---|
| OS | Debian 13 (trixie), Linux x86_64 | Standard target; glibc wheels available |
| Python | 3.13.16, pip 26.2.2 | FastAPI/SQLAlchemy/Pydantic 2 all supported |
| Node.js | 20.20.2, npm 10.8.2 | Vite 8 / React 19 supported |
| PostgreSQL | **not installed** | PostGIS/pgvector cannot be exercised here |
| Docker | **not installed** | Compose stack authored and lint-checked, not executed |
| SQLite | available via Python stdlib | Chosen as the development/test store |
| OpenSSL / CA | present, `NODE_OPTIONS=--use-openssl-ca` | npm installs succeed |

## 3. Configuration and dependency state

- Python environment had `pydantic`, `pytest`, `httpx`, `pandas`, `openpyxl` but **no FastAPI, SQLAlchemy, uvicorn, alembic** — installed during Phase 1.
- No service credentials, API keys, or institutional endpoints were present. **No external integration was attempted or claimed.**
- No outbound dependency on a specific cloud; nothing in the code assumes a public cloud.

## 4. Deployment constraints discovered

1. **No container runtime** → the stack is delivered as Docker assets + a native dev path (`uvicorn` + `vite`) that actually runs here.
2. **No Postgres** → models are written to be Postgres-portable (no SQLite-only types; JSON columns; string UUID PKs), migrations generated with Alembic, and the Postgres path is provisioned in Compose but **unverified**. This is recorded as a known limitation.
3. **Preview environment** serves the app through an HTTPS proxy with an iframe sandbox → the map had to work **without external tile servers**. MapLibre is configured with a self-contained style and platform GeoJSON only.
4. **Single always-on process budget** → no background worker broker in this environment; ingestion is synchronous and documented as such.

## 5. Architectural risks identified

| # | Risk | Mitigation adopted |
|---|---|---|
| R1 | Sandbox DB (SQLite) diverges from production Postgres | Portable column types, Alembic baseline, no SQLite-specific SQL in application code |
| R2 | Large graph rendering performance in-browser | Deterministic force layout computed once per node-set, SVG with caps; server clamps graph size |
| R3 | AI plausibility vs. evidence | Retrieval gate + citation validation + refusal path; every assertion carries `[E#]` |
| R4 | Tenant leakage through search/aggregates | Every collection endpoint filters by `organization_id` unless `platform_admin`; covered by tests 02, 02b, 02c, 11, 12 |
| R5 | Untrusted document text as prompt injection | Retrieved text is never treated as instructions; injection test 10c asserts behaviour |
| R6 | Secrets in transit or logs | Secrets via env/file, never logged; audit `detail` explicitly excludes credentials |
| R7 | Single dev secret key | `SECRET_KEY` required from environment; compose refuses to start without it |

## 6. Decisions taken as a result

See `docs/DECISIONS.md` — ADR-001 (SQLite dev / Postgres target), ADR-002 (Postgres-native graph instead of Neo4j), ADR-003 (lexical-first retrieval), ADR-004 (MapLibre with self-contained style), ADR-005 (no Tailwind build, hand-authored design system).
