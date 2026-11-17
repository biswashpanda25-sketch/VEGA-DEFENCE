# Architecture Decision Records

Format: context → decision → consequences. Only decisions that materially shape the system are recorded.

---

## ADR-001 — SQLite for development, PostgreSQL for production

**Context.** The sandbox has no PostgreSQL or Docker. The platform nevertheless needs a real relational schema,
transactions and referential integrity.

**Decision.** Use SQLAlchemy 2.1 with portable column types (`String`, `JSON`, `DateTime`) and string UUID primary
keys. Default `DATABASE_URL` is a SQLite file; Compose provisions `postgis/postgis:16-3.4`. Alembic owns schema
creation in deployed environments; `Base.metadata.create_all` is used only at development startup.

**Consequences.** (+) The whole platform runs and is tested here. (+) Migration baseline generated and applied.
(−) PostGIS/pgvector execution paths are unverified — recorded as a limitation, not claimed as working.

---

## ADR-002 — Graph in PostgreSQL rather than a dedicated graph database

**Context.** Palantir-style platforms are often assumed to need Neo4j. The demonstration workload is 20 entities
and 14 relationships; the design target is institutional registers, i.e. low-degree, high-cardinality entity data.

**Decision.** Model entities and relationships as first-class relational tables with `organization_id`, indexed
`source_id`/`target_id`, provenance and evidence columns. Graph queries are recursive CTEs / two-hop joins when needed.

**Consequences.** (+) One database to operate, back up and audit; tenant isolation is trivial. (+) No dual-write
consistency problem. (−) Deep traversals (5+ hops) will need measured optimisation or a graph store later — the
trigger is a measured latency breach, not fashion.

---

## ADR-003 — Lexical-first retrieval with an evidence-admission gate

**Context.** An LLM answer without verifiable grounding is worse than no answer in an institutional context.

**Decision.** Ship a deterministic retrieval + composition path as the default (`AI_PROVIDER=grounded-local`).
Retrieval is BM25-style over tenant-scoped records; a hit is only admissible as *evidence* if it covers ≥30% of the
query's distinct content terms. An external model may be enabled, but its output is rejected unless every `[E#]`
citation resolves to a retrieved record.

**Consequences.** (+) Groundedness and permission-leakage are measurable and measured (see `EVALUATION.md`).
(+) Works air-gapped with no model at all. (−) Composed prose is templated, not conversational; the gate trades
recall on loosely-worded questions for refusal correctness. Threshold tuned empirically: 0.30 gave recall 1.00 /
refusal accuracy 1.00; 0.50 dropped recall to 0.63.

---

## ADR-004 — MapLibre with a self-contained style

**Context.** The preview surface runs in a sandboxed iframe; external tile or glyph servers may be unreachable, and
an institutional deployment may be air-gapped.

**Decision.** Configure MapLibre GL with no external sources: a background layer plus platform GeoJSON (district
anchors, entity features). Clustering, heatmap and interaction are native MapLibre capabilities.

**Consequences.** (+) The map always renders, online or offline, with no third-party data leaving the deployment.
(−) Raster basemaps and search-geocoding require licensed providers; boundary polygons must be loaded from an
authorised administrative-geography source before operational use — stated in-product.

---

## ADR-005 — Hand-authored design system instead of a utility-CSS framework

**Context.** The brief calls for a dense, dark, institutional interface that must not look like a generic SaaS
template, and the build must stay reproducible in a constrained sandbox.

**Decision.** Author a CSS design-token system (`src/styles.css`) with a small React primitive layer
(`components/ui.tsx`). No Tailwind build step, no component library dependency.

**Consequences.** (+) Full control of density, typography and tone; zero CSS framework churn; bundle is CSS-only cost.
(−) Contributors must learn the token set; there is no utility vocabulary to lean on.

---

## ADR-006 — Evidence is mandatory on relationships; findings are typed

**Context.** The single most dangerous failure mode in analytical software is an inference silently becoming "fact".

**Decision.** The API refuses relationships without evidence text and a valid provenance class. Findings must declare
`evidence | assumption | hypothesis | conclusion`; evidence and conclusion kinds require resolvable in-tenant
evidence references. Reviewer approval is a separate, audited action by a reviewer-role user.

**Consequences.** (+) The product cannot be used to launder speculation into assessment. (−) More friction for
analysts — intentional.

---

## ADR-007 — Tenant isolation at the query layer, not in the UI

**Context.** Row-level security in Postgres is attractive but unavailable in SQLite dev; hiding data in the client
is not a control.

**Decision.** Every collection endpoint constructs its query with an organization filter unless the caller is
`platform_admin`. Object-level reads return 404 (not 403) for cross-tenant IDs to avoid existence disclosure.
Postgres RLS is a planned defence-in-depth layer, not a substitute.

**Consequences.** (+) One enforcement point, covered by tests 02/02b/02c/11/12. (−) New endpoints must remember the
scoping helper; enforced by code review and the test suite.

---

## ADR-008 — Synchronous ingestion in this build

**Context.** Production ingestion should be queued, retried and observable. No broker is available in the sandbox.

**Decision.** Ingest synchronously with explicit error surfacing (400 + audit `dataset.ingest_failed`) and an
idempotent duplicate check. The pipeline stages are isolated in `services/ingestion.py` so a worker can wrap the same
functions without change.

**Consequences.** (+) Real end-to-end behaviour, honest error handling, no lost jobs. (−) Large files block the
request; 25 MB cap documented; queueing is on the roadmap.

---

## ADR-009 — Disable PostgreSQL JIT for the API session

**Context.** The 1,000,000-row benchmark showed every interactive query carrying ~180 ms of fixed latency. Server
logs attributed 181.8 ms of a 181.4 ms query to "JIT: Optimization" — a 1–9 ms spatial query was spending 95% of its
time compiling code that ran for microseconds.

**Decision.** Set `-c jit=off` in the psycopg connection options for every API connection, and keep a
`statement_timeout` guard alongside it. First attempt used a SQLAlchemy `connect` event executing `SET jit = off`;
that silently did nothing because the `SET` ran inside a transaction that was later rolled back. Connection options
are applied at establishment and cannot be rolled back.

**Consequences.** (+) Interactive latency becomes stable and predictable; the same setting is applied everywhere
instead of per query. (−) Long analytical scans that would benefit from JIT run slower; a reporting role can opt back
in with a session override when intra-day analytics matter more than latency.

---

## ADR-010 — KNN ordering and a latency guard for spatial nearest-N queries

**Context.** `/geo/nearby` originally cast `ST_MakePoint(lon, lat)` to `geography` per row and ordered by the computed
distance. No index can serve that cast, and for wide radii the planner preferred a parallel sequential scan: 950 ms
p50 at 1M rows, and 351 ms even after the index existed.

**Decision.** Index a *matching* expression (`GiST (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography)`),
order by the KNN operator `<->` instead of sorting by distance, and set
`max_parallel_workers_per_gather = 0` for that query so the planner takes the ordered index path. The engine label in
the response names the path that actually ran (`postgis-gist-knn` vs `haversine`).

**Consequences.** (+) 1.05 ms p50 at 1M rows, 334× faster than the distance-sorted form. (−) The expression index
must match the query text exactly, which is easy to break silently — the benchmark therefore prints the indexes
actually present in `pg_indexes` rather than assuming its DDL worked (a rollback once discarded all of them).

---

## ADR-011 — Bounded, clearance-aware retrieval instead of full-corpus scoring

**Context.** BM25 over every entity is transparent and easy to audit, and it is also O(corpus) per query. At 1M rows
`/search` would have been unusable, and worse, the corpus was assembled without a clearance filter — a citation could
have surfaced content above the caller's clearance.

**Decision.** Keep BM25 scoring but bound the candidate set: PostgreSQL does a trigram pre-filter (capped at 500 rows),
SQLite scans a capped window; on small corpora the cap exceeds the corpus so behaviour is unchanged. Clearance
filtering is applied in SQL *before* ranking, and absorbed (`canonical_id`) records are excluded.

**Consequences.** (+) `/search` is 28 ms p50 at 1M rows, and retrieval can no longer leak above clearance.
(−) Recall is now bounded by the pre-filter for very broad terms; `pgvector` embeddings are the intended next step
behind the same seam.
