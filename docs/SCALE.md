# Scale Evidence — 1,000,000 entities on PostgreSQL 17 + PostGIS 3.5

**Measured:** 2026-11-12 · **Machine:** this sandbox (shared CI-class CPU, local NVMe) · **Client:** in-process
**Reproduce:** `cd backend && python -m tests.scale --rows 1000000 --dba-psql "sudo -u postgres /usr/lib/postgresql/17/bin/psql"` then `DATABASE_URL=postgresql+psycopg://…/gotham_scale python -m tests.bench_scale`

Every number below was printed by a script in this repository. Raw output: `docs/scale_results.json`
(query paths) and `docs/scale_endpoint_bench.json` (HTTP endpoints). Nothing here is extrapolated from a
small dataset, and nothing was tuned after the numbers were taken without re-running the harness.

---

## 1. Dataset and load

| Property | Value |
|---|---|
| Rows | 1,000,000 entities (verified `reltuples` 999,950 at measurement time) |
| Relationships | 300,000 |
| Data | Synthetic, labelled `is_synthetic = true`; district-clustered coordinates across 18 Odisha districts |
| Schema | Created by `alembic upgrade head` — the same migration chain as production, not a bespoke DDL script |
| Load method | `COPY FROM STDIN`, 39,173 rows/s (25.5 s) |
| Index build | 14.1 s for GiST (geography), GIN (trigram ×2), GiST (trigram), b-tree composites |

## 2. Query paths

| Query | p50 | p95 | Notes |
|---|---|---|---|
| Paginated list, page 1 | **0.14 ms** | 0.45 ms | Composite `(organization_id, entity_type)` b-tree |
| Paginated list, offset 50,000 | 100.8 ms | 119.4 ms | Offset pagination degrades linearly — see §5 |
| Trigram search, broad term ("Khordha", ~39% of rows) | 633 ms | 664 ms | Pathological selectivity; GIN is the wrong tool here |
| Trigram search, selective token | **46.5 ms** | 49.3 ms | The realistic case for a search box |
| District aggregate over the full tenant | 121 ms | 140 ms | One sequential scan is the floor |
| Two-hop relationship join | 58.8 ms | 75.0 ms | `UNION ALL` of two indexed lookups (the naive `OR` join was 655 ms) |
| **PostGIS radius 50 km, KNN ordering** | **1.05 ms** | 2.66 ms | GiST geography expression + `<->` ordering |
| PostGIS radius 50 km, distance-sorted (naive) | 350.6 ms | 419.6 ms | Same predicate, `ORDER BY ST_Distance` — 334× slower |
| PostGIS count within 2 km | 19.1 ms | 23.4 ms | Selective radius, index scan |

## 3. Endpoints (full HTTP stack, in-process TestClient)

| Endpoint | Status | p50 | p95 |
|---|---|---|---|
| `GET /api/v1/health` | 200 | 2.9 ms | 6.8 ms |
| `GET /api/v1/entities?page=1` | 200 | 8.6 ms | 9.3 ms |
| `GET /api/v1/entities?q=Khordha` | 200 | 196 ms | 477 ms |
| `GET /api/v1/search?q=warehouse` | 200 | 28.4 ms | 58.5 ms |
| `GET /api/v1/geo/nearby` (50 km) | 200 | **9.4 ms** | 11.2 ms |
| `GET /api/v1/analytics/overview` | 200 | 504 ms | 554 ms |
| `POST /api/v1/ai/ask` | 200 | 59.4 ms | 66.8 ms |

The in-process client removes network cost, so treat these as lower bounds for real HTTP. Response sizes are
small (≤50 records), so serialisation is not the bottleneck on any row above.

## 4. What the measurement changed in the product

Three defects were only visible at scale, and each one was fixed and re-measured rather than documented as a
limitation:

1. **JIT compilation was adding ~180 ms to every interactive query.** A 9 ms spatial query took 262 ms; the
   server log showed 181.8 ms in "JIT: Optimization". The first fix attempt (`SET jit = off` inside a
   connection event) silently did nothing because the `SET` ran inside a transaction that was rolled back.
   Correct fix: `-c jit=off` in the connection options, applied at connection establishment.
2. **PostGIS predicates were not using an index.** The original query cast `ST_MakePoint(lon, lat)` to
   `geography` per row, which no index can serve, and a parallel sequential scan was chosen for wide radii.
   Fix: a GiST index on a matching geography expression, KNN `<->` ordering instead of sorting by distance,
   and a per-query latency guard that disables parallel gather on the nearest-N path.
3. **Retrieval loaded the whole corpus into Python.** BM25 over every entity is fine for 20 rows and fatal for
   1M. Candidate selection now runs in the database (trigram pre-filter, capped at 500) with the same
   in-process re-ranking, so small corpora behave identically and large ones stay bounded.

Two secondary improvements: `(source_id, target_id)` indexes on relationships (the graph endpoint had no
index on either endpoint of an edge), and a single-scan overview aggregate.

## 5. Known limits at this scale — stated, not hidden

| Limit | Measurement | Intended fix |
|---|---|---|
| `analytics/overview` scans the tenant | 504 ms p50 | Rollup table or materialized view refreshed on a schedule; the dashboard already labels every figure as a live count |
| Broad-term entity search | 196 ms p50 (477 p95) for a term matching ~39% of rows | Keyset + `tsvector` full-text ranking, or an external search engine for broad queries |
| Offset pagination | 100 ms at offset 50,000 | Keyset pagination (`WHERE name > :last ORDER BY name`) |
| No partitioning | 1M rows is comfortable; 10⁷ is untested | Declarative partitioning by organization on `entities` |
| No connection pooler | Single-process pool only | PgBouncer in transaction mode before multi-worker deployment |

**10⁷ objects is untested in this environment.** PostGIS, trigram and b-tree behaviour above one million
rows is an extrapolation, and this repository does not claim otherwise.

## 6. Reproducing honestly

- The harness drops and recreates `gotham_scale` on each run, so results are not contaminated by prior state.
- Extensions are installed by the DBA role (`--dba-psql`), exactly as a real deployment would; the
  application role cannot create extensions.
- Index presence is verified against `pg_indexes` and printed, because an earlier version of the script
  reported "indexed in 7.9 s" while a rollback had silently discarded every index.
- A figure that cannot be reproduced is a bug in the documentation, not a marketing number.
