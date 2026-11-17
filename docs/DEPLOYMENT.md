# Deployment Guide

## 1. Local development (no Docker)

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./gotham.db SECRET_KEY=$(openssl rand -hex 32)
python -m alembic upgrade head          # or rely on startup create_all in dev
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# frontend (second terminal)
cd frontend
npm ci
npm run dev                             # http://localhost:5173, proxies /api -> :8000
```

OpenAPI: `/api/docs`. Health: `/api/v1/health`.

Demo identities (password `Gotham@2026`, synthetic data only):
`analyst@gotham-demo.in`, `reviewer@gotham-demo.in`, `admin@gotham-demo.in`, `disaster@gotham-demo.in`.

## 2. Docker Compose evaluation stack

```bash
cp .env.example .env                 # set SECRET_KEY and DB_PASSWORD
export SECRET_KEY=... DB_PASSWORD=...
docker compose up --build
# web  http://localhost:8080   (nginx serves SPA + proxies /api)
# api  http://localhost:8000
```

Services: `db` (postgis/postgis:16-3.4, extensions postgis/pg_trgm/vector), `cache` (redis), `api`
(alembic upgrade on boot), `web` (nginx). Database password is provided via Docker secret file.

## 3. Institutional deployment checklist

| Area | Requirement |
|---|---|
| Hosting | Private cloud, government-approved cloud, or on-premises. Architecture assumes no public-cloud dependency. |
| Database | Managed PostgreSQL 16 with PostGIS and pgvector; encrypted volumes; PITR backups |
| Object storage | S3-compatible (MinIO acceptable) with versioning and lifecycle rules |
| Identity | OIDC/SAML IdP with MFA enforced (**not yet implemented in-app — KI-01**) |
| Transport | TLS 1.2+ at ingress; HSTS; internal mTLS optional |
| Secrets | Vault/KMS or platform secret manager; rotate `SECRET_KEY` on a schedule |
| Model hosting | Local (Ollama/vLLM) inside the network for sensitive deployments; no egress |
| Observability | Central logs, Prometheus metrics, OpenTelemetry traces, alerting on error rate and latency |
| Network | API not internet-facing; analyst access through VPN/zero-trust proxy |
| Backup | Nightly base backup + WAL archiving; quarterly restore drill with recorded timing |

## 4. Configuration reference

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./gotham.db` |
| `SECRET_KEY` | JWT signing key (32+ bytes) | dev placeholder — **must override** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session lifetime | `480` |
| `SEED_DEMO` | Seed synthetic dataset at startup | `true` |
| `AI_PROVIDER` | `grounded-local` \| `ollama` \| `openai-compatible` | `grounded-local` |
| `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY` | External model endpoint | unset |
| `REDIS_URL` | Cache/queue target (reserved) | unset |

## 5. Release procedure

1. CI green: migrations, 25 tests, AI evaluation, frontend typecheck/build, dependency audit.
2. `alembic upgrade head` against staging; verify schema diff is empty.
3. Smoke: login, ingest a CSV, open graph, ask the assistant, verify citations, check audit entries.
4. Measure: run `tests/bench.py` against staging before promoting.
5. Tag release; update `docs/RELEASE_NOTES.md` and `docs/PROJECT_STATUS.md`.

## 6. Rollback

Application rollback is image-tag based. Schema rollback uses `alembic downgrade -1` only where the migration is
reversible; destructive migrations require a tested backup restore instead (see `OPERATIONS.md`).
