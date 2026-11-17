# Implementation Plan (living)

Status legend: **DONE** · **PARTIAL** · **NEXT** · **BLOCKED (needs environment/credential)**

## Phase 0 — Audit
- DONE Environment + repository audit → `docs/AUDIT.md`
- DONE Risk register, ADR baseline → `docs/DECISIONS.md`

## Phase 1 — Foundation
- DONE Repo structure (`backend/`, `frontend/`, `deploy/`, `docs/`, CI)
- DONE FastAPI app factory, settings, structured logs, error envelope
- DONE SQLAlchemy models + Alembic baseline
- DONE bcrypt + JWT auth, rate limiting, `/auth/*`
- DONE Role model + `require_role` dependencies
- DONE Organization/tenant model + query-layer isolation
- DONE Append-only audit service
- DONE Login UI, session persistence, role-aware shell

## Phase 2 — Data foundation
- DONE CSV / JSON / XLSX ingestion with normalisation and schema aliasing
- DONE Duplicate detection (tenant + type + name)
- DONE Provenance retention on every record
- DONE Quality scoring (completeness/uniqueness/validity/provenance)
- DONE Document upload with type allow-list and size cap
- DONE Dataset + connector registry and health surface
- PARTIAL Connector SDK: file connectors complete; REST/Postgres adapters are interfaces only
- NEXT Queued ingestion worker with retry/backoff and dead-letter handling
- NEXT OCR pipeline (Tesseract / institutional service) with pre-extraction malware scan

## Phase 3 — Intelligence foundation
- DONE Entity model with attributes/provenance/confidence
- DONE Relationship model with mandatory evidence + provenance class
- DONE Graph API (nodes/edges, tenant-scoped, provenance filter)
- DONE Interactive graph explorer with evidence inspection
- DONE Lexical search with permission filtering + audit
- DONE Case workspace, typed findings, reviewer decisions
- PARTIAL Entity resolution: duplicate suppression at ingest; fuzzy matching/merge UI is NEXT
- NEXT Saved searches, search history server-side

## Phase 4 — Geospatial
- DONE District reference dataset (Odisha, 30 districts)
- DONE Entity feature collection + district summary endpoints
- DONE MapLibre explorer: clustering, heatmap, layer toggles, popups, legend, freshness
- PARTIAL PostGIS: provisioned in Compose, unexecuted here
- NEXT Load licensed administrative polygons; add spatial predicates (`ST_Within`, nearest-neighbour)

## Phase 5 — AI engine
- DONE Model abstraction (grounded-local | ollama | OpenAI-compatible)
- DONE Tenant-scoped retrieval with evidence-admission gate
- DONE Citation generation + validation; refusal path
- DONE Conversation persistence + audit
- DONE Evaluation harness with measured results
- NEXT Embeddings + pgvector hybrid retrieval; re-measure before switching default
- NEXT Grounded report drafting from selected case evidence

## Phase 6 — Operational intelligence
- DONE Asset/inventory posture, exception queue, availability ratio
- DONE Advisory capacity projection with explicit data basis/limitations
- DONE Notification stream + read state
- DONE Report generation (CSV/JSON/print-PDF) with metadata and classification
- PARTIAL Task assignment & approval workflows: findings review implemented; general workflow engine NEXT
- NEXT Threshold configuration UI, email/webhook delivery adapters

## Phase 7 — Enterprise security
- DONE RBAC + tenant isolation tests
- DONE Upload validation and parser hardening
- DONE Prompt-injection and AI-leakage tests
- DONE CI dependency audit + secret scan
- BLOCKED OIDC/SAML + MFA (needs an IdP)
- NEXT External penetration test, SAST/DAST campaign, hash-chained audit export

## Phase 8 — Production readiness
- DONE Dockerfiles, Compose (PostGIS/Redis/nginx), CI pipeline
- DONE Deployment, operations and runbook documentation
- DONE Latency benchmark with stated conditions
- NEXT Postgres-backed load/soak test, DR drill, observability stack (Prometheus/OTel/Grafana) wiring
