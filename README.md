# GOTHAM INDIA

**Sovereign Intelligence & Decision Support Platform** — an indigenous, modular platform for authorized Indian
institutions to integrate records, resolve entities, analyse geography, and produce evidence-grounded assessments
under human review.

> **Demonstration build.** Every record in the running system is **synthetic** (Odisha public-infrastructure and
> disaster-coordination scenario). No classified, personal or operational data is present. This is not certified for
> production use — see `docs/KNOWN_ISSUES.md` and `docs/SECURITY.md`.

---

## What actually runs

| Layer | Implementation |
|---|---|
| API | FastAPI + SQLAlchemy 2.1 + Pydantic 2, JWT auth, RBAC, tenant isolation, append-only audit |
| Data | Dataset/connector registry, connector SDK (CSV/JSON/Excel implemented; REST/Postgres credential-gated), ingestion with normalisation, duplicate detection, quality scoring, provenance retention |
| Intelligence | Entity graph with evidence-bearing relationships, provenance classes, interactive exploration |
| Analysis | Case workspaces, typed findings (evidence/assumption/hypothesis/conclusion), reviewer decisions |
| Geospatial | MapLibre GL explorer — clustering, heatmap, district reference geography, feature inspection |
| AI | Tenant-scoped retrieval with an evidence-admission gate, citation-only composition, refusal path, measured evaluation |
| Ops | Asset posture, exception queue, notifications, CSV/JSON/PDF reporting, administration, audit explorer |
| Delivery | Docker, Compose (PostGIS + Redis + nginx), Alembic migrations, GitHub Actions CI |

## Quick start (this environment)

```bash
# terminal 1 — API
cd backend && pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# terminal 2 — console
cd frontend && npm install && npm run dev     # http://localhost:5173
```

Demo sign-in (synthetic data, shared password `Gotham@2026`):

| Email | Role |
|---|---|
| `analyst@gotham-demo.in` | Analyst — Infrastructure Directorate |
| `reviewer@gotham-demo.in` | Reviewer — approval authority |
| `admin@gotham-demo.in` | Platform Administrator |
| `disaster@gotham-demo.in` | Analyst — second tenant (Disaster Coordination Cell) |

API docs at `/api/docs`.

## Verify it yourself

```bash
cd backend
python -m pytest tests -q        # 61 passed on SQLite — all 16 mandated scenarios + ABAC/MFA/audit/route matrix
# same suite against PostgreSQL 17 + PostGIS:
GOTHAM_TEST_DB_URL="postgresql+psycopg://gotham:gotham_dev_pw@127.0.0.1:5432/gotham_test" python -m pytest tests -q   # 61 passed
python -m tests.eval_ai          # AI grounding evaluation, measured
python -m tests.bench --n 40     # latency benchmark against the running API
cd ../frontend && npm run typecheck && npm run build && npm run e2e   # 27/27 browser checks
```

Measured in this environment: **61 backend tests passing on both SQLite and PostgreSQL, 27/27 browser checks passing** · retrieval recall 1.00, groundedness 0.73, unsupported-claim
rate 0.00, permission-leakage 0.00, AI p50 8.6 ms · API p50 1.3–9.5 ms (sequential, single client).

## Repository layout

```
gotham-india/
├── backend/
│   ├── app/
│   │   ├── main.py          app factory, middleware, rate limit, static hosting
│   │   ├── models.py        SQLAlchemy schema (13 tables)
│   │   ├── deps.py          auth, RBAC, tenant guards, audit writer
│   │   ├── routers/         auth, orgs, datasets, entities, cases, search, geo, ai, ops, admin
│   │   ├── services/        ingestion, connectors (SDK), retrieval, ai, geo
│   │   └── seed.py          synthetic Odisha demonstration dataset
│   ├── migrations/          Alembic baseline
│   └── tests/               25 tests + AI evaluation + benchmark
├── frontend/
│   └── src/                 shell, 15 screens, design system, charts, map
├── deploy/                  DB bootstrap, secret files
├── docs/                    architecture, security, testing, evaluation, operations, guides
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Documentation

| Document | Contents |
|---|---|
| `docs/AUDIT.md` | Phase 0 repository and environment audit |
| `docs/ARCHITECTURE.md` | System design, module dependency map, data model, scale-up path |
| `docs/DECISIONS.md` | Architecture decision records (8 decisions with consequences) |
| `docs/SECURITY.md` | Controls, threat model, residual risk, what was *not* tested |
| `docs/DATA_GOVERNANCE.md` | Provenance, classification, retention, legal posture |
| `docs/TESTING.md` | Test strategy mapped to the 16 mandated scenarios, executed results |
| `docs/EVALUATION.md` | AI metrics, threshold tuning table, honest interpretation |
| `docs/API.md` | Endpoint reference and guarantees |
| `docs/DEPLOYMENT.md` | Local, Compose and institutional deployment |
| `docs/OPERATIONS.md` | Runbook, backup/restore, incident response |
| `docs/USER_GUIDE.md` / `docs/ADMIN_GUIDE.md` | Operator documentation |
| `docs/PROJECT_STATUS.md` | Implemented / simulated / planned, phase by phase |
| `docs/IMPLEMENTATION_PLAN.md` | Living task checklist |
| `docs/KNOWN_ISSUES.md` | 13 tracked limitations with severity and path forward |

## Boundaries

This platform performs authorized institutional record analysis, infrastructure and logistics management, disaster
coordination, public-source research and evidence-based administrative workflows. It does **not** implement
targeting, strike planning, weapon guidance, covert tracking, interception, or automated consequential decisions
about individuals — and the API refuses to record a relationship or a conclusion without supporting evidence.
