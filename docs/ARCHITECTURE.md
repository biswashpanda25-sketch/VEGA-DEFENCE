# GOTHAM INDIA — System Architecture

## 1. Purpose and boundaries

GOTHAM INDIA is a sovereign intelligence and decision-support platform for authorized Indian institutions:
ingest authorized records, resolve them into an entity graph, analyse them geographically and analytically,
and produce evidence-grounded assessments under human review.

**Out of scope by design** (and by policy in the code): targeting, strike planning, autonomous decisions about
individuals, covert tracking, interception, credential theft, or any unauthorised access. The platform analyses
institutional records about assets, organizations and events — not people.

## 2. Logical architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Web console (React 19 + TS + Vite)                                         │
│  Shell · Universal search · Graph explorer · Map · Workspaces · Assistant   │
│  Reports · Admin · Audit        TanStack Query (server state) · Zustand     │
└───────────────▲────────────────────────────────────────────────────────────┘
                │ REST /api/v1 (JSON, bearer JWT)
┌───────────────┴────────────────────────────────────────────────────────────┐
│ API service (FastAPI)                                                      │
│  auth · organizations · datasets · entities · relationships · cases        │
│  connector SDK (csv/json/excel implemented; rest/postgres credential-gated)│
│  search · geo · ai · ops · notifications · audit · admin                   │
│  ── cross-cutting: JWT authN, RBAC authZ, tenant scoping, audit, validation │
└───────────────▲────────────────────────────────────────────────────────────┘
                │ SQLAlchemy 2.1 ORM
┌───────────────┴───────────────┐   ┌──────────────────┐   ┌─────────────────┐
│ Relational store              │   │ Object store     │   │ Model providers │
│ Postgres (+ PostGIS, pgvector)│   │ S3/MinIO (docs)  │   │ Ollama / OpenAI │
│ SQLite in dev/test            │   │ dev: DB column   │   │ compatible      │
└───────────────────────────────┘   └──────────────────┘   └─────────────────┘
```

## 3. Module dependency map

```
config ─▶ db ─▶ models ─▶ deps(security+audit) ─▶ routers ─▶ main
                                 │
                                 ├─▶ services/ingestion   (datasets router)
                                 ├─▶ services/retrieval   (search, ai)
                                 ├─▶ services/ai          (ai router)
                                 └─▶ services/geo         (geo router)

frontend: main.tsx ─▶ App(shell, routing, guards)
                        ├─▶ pages/*  ─▶ api.ts ─▶ store.ts (auth session)
                        └─▶ components/{ui,charts,icons}
```

Rules: routers never touch raw SQL; services hold domain logic; models own persistence shape; `deps.py`
is the only place that resolves identity, roles and audit writes for a request.

## 4. Data model (implemented)

```
organizations ──1:N── users
      │                  
      ├──1:N── datasets ──1:N── documents
      ├──1:N── connectors
      ├──1:N── entities ──┬──1:N── relationships (source_id, target_id, provenance, evidence)
      │                   └──N:M── findings (via evidence_refs JSON)
      ├──1:N── cases ──1:N── findings
      ├──1:N── notifications
      ├──1:N── ai_conversations
      └──1:N── audit_events
```

Key invariants enforced in code:
- every tenant-owned row carries `organization_id`;
- `relationships.evidence` must be non-empty and `provenance ∈ {confirmed, imported, inferred, unverified}`;
- `findings` of kind `evidence`/`conclusion` must reference at least one entity **in the same organization**;
- `documents` are type-allow-listed and size-capped before storage.

## 5. Request lifecycle (security-critical path)

1. Bearer JWT decoded → user loaded → `is_active` checked (401 otherwise).
2. Role dependency applied per route (`require_role(...)`).
3. Query built with tenant filter unless caller is `platform_admin`.
4. Input validated by Pydantic; uploads validated by extension, size and parser integrity.
5. Mutation commits, then `audit()` writes an append-only event.
6. Response serialised through an explicit schema — password hashes and secrets never leave the service.

## 6. AI architecture

```
question ─▶ Retriever(tenant-scoped corpus)
              ├─ BM25-style scoring over entity/document/case records
              └─ evidence-admission gate (query-term coverage ≥ 0.30)
                    │
                    ▼
        Grounded composer (default) ── OR ── external model (Ollama / OpenAI-compatible)
                    │                              │
                    │                              ▼
                    │                    citation validator ([E#] must resolve)
                    ▼                              │
              answer + citations ◀─────────────────┘ (uncited output rejected)
                    │
                    ▼
        AIConversation row (question, answer, citations) + audit event
```

Safety properties: retrieval is permission-filtered before generation; retrieved document text is delimited as
untrusted data; the model cannot alter permissions or trigger workflows; refusal is a first-class outcome.

## 7. Deployment topology

| Environment | Shape |
|---|---|
| Developer | `uvicorn` + `vite dev` (proxy `/api`), SQLite file |
| Evaluation | `docker compose`: PostGIS, Redis, API (alembic upgrade on boot), nginx-served SPA |
| Institutional | Kubernetes or VM fleet behind an ingress, managed Postgres + PostGIS + pgvector, S3-compatible object store, OIDC IdP, central logging/metrics |

Air-gapped operation is supported by design: no runtime dependency on external tile servers, CDNs or SaaS
endpoints. Models may be local (Ollama/vLLM) with no egress.

## 8. Scale-up path (evidence-driven, not aspirational)

1. **Search**: lexical → hybrid (pgvector embeddings) once document volume justifies it; keep BM25 as fallback.
2. **Graph**: Postgres adjacency is adequate for tens of millions of edges with the right indexes; introduce a
   dedicated graph store only after measured traversal latency breaches target.
3. **Ingestion**: synchronous → queued worker with idempotency keys and retry/backoff.
4. **Serving**: single uvicorn → multiple workers behind ingress with Redis-backed cache and rate limits.
