# Honest Assessment: GOTHAM INDIA vs. Palantir Gotham

**Date:** 2026-11-12 · **Subject:** what this repository actually is, measured against the publicly documented
capability space of Palantir Gotham · **Author:** the engineer who built it

> This is a self-assessment, deliberately unflattering. Nothing here relies on Palantir source code or internal
> knowledge; the comparison is against capability categories that are publicly described (ontology/workflows,
> dynamic data integration, link analysis, geospatial analysis, object-level security, collaborative operations,
> AI assistance, accredited deployment).

---

## 1. Scale of what exists

| Metric | This build | Order of magnitude for Gotham |
|---|---|---|
| Application code | ~4,650 lines (1,910 backend + 2,736 frontend) | tens of millions of lines across the platform |
| Database tables | 12 | ontology-backed, schema-per-object-type, tenant-partitioned |
| API endpoints | 43 | thousands of public/internal operations |
| Data under management in the demo | 20 entities, 14 relationships, 2 documents | petabytes, millions of objects |
| Engineer-years | effectively ~1 working day | ~20 years, thousands of engineers |
| Deployment accreditations | none | multiple national-security accreditations |
| Live enterprise integrations | **zero** | hundreds, including mission-critical systems |

## 2. Capability-by-capability scorecard

Percentages estimate **functional depth + robustness at scale**, not lines of code or screens present.

| Capability area | Gotham's publicly described depth | What exists here | Honest share |
|---|---|---|---|
| **Ontology / object model** | Dynamic object types, properties, links, actions, writeback, per-object versioning, ontology branching | Fixed canonical entity table + JSON attributes; no action types, no writeback, no ontology editing | **~8%** |
| **Data integration / pipelines** | Streaming, CDC, batch orchestration, hundreds of connectors, schema drift handling, lineage to column level | File ingestion (CSV/JSON/XLSX) + a connector SDK whose REST/Postgres adapters are deliberately inert without credentials | **~3%** |
| **Entity resolution** | Probabilistic matching, human-in-the-loop merge/split, resolution history | Case-insensitive name+type duplicate suppression at ingest | **~5%** |
| **Link analysis / graph** | Deep traversal, pathfinding, temporal graph, ego-network analytics at 10⁸-edge scale | 1-hop adjacency, force-directed visualisation, provenance-typed edges | **~10%** |
| **Geospatial** | Live tracks, geofences, temporal playback, boundary analytics, terrain/raster layers | Static district-anchored points, clustering, heatmap, no polygons, no time dimension | **~8%** |
| **Analytical workspace / cases** | Shared apps, notebooks, tasking, comments, fine-grained per-object markup | Cases, typed findings, evidence refs, reviewer approval; no comments, no co-editing | **~12%** |
| **Access control** | Purpose-based, cell-level, per-row/column markings, multi-org coalition controls, classification enforcement | RBAC (7 roles) + tenant scope + record-level classification label; no field-level enforcement, no ABAC policy engine | **~15%** |
| **Audit & governance** | Tamper-evident, WORM-backed, regulatory export, purpose binding | Append-only table with role-restricted read; no hash chain, no WORM export | **~15%** |
| **Operational workflows** | Tasking, approvals, resource allocation, simulation, operator apps with writeback | Advisory exception queue and read-only dashboards; **no workflow engine, no tasking, no writeback** | **~5%** |
| **AI (AIP-class)** | Tool-using agents over the ontology, permission-aware retrieval, model evals, human approval gates, deployed agent workflows | Single grounded question→answer path with citation validation and refusal; no tools, no agents, no ontology writes | **~8%** |
| **Scale & performance** | Cluster-scale compute, sub-second queries over billions of objects, thousands of concurrent analysts | Benchmarked p50 1.4–8.8 ms on **20 records**, single-process, single client | **~1%** |
| **Deployment / accreditation** | Air-gapped accredited installs, FedRAMP/IL-class controls, HA, DR drills | Docker Compose + CI authored, never executed; SQLite; no MFA/IdP; no HA or DR drill | **~2%** |

**Unweighted mean ≈ 8%. Weighted by what actually determines institutional value (integration, scale, security
granularity, accreditation) it is lower — comfortably under 10%.**

## 3. What is genuinely *not* trivial here

Being honest cuts both ways. A one-day build that scored 0% would not have been worth the effort:

- **The conceptual spine is correct.** Ontology-shaped entities, evidence-bearing relationships, provenance
  classes, typed findings, human review gates, append-only audit — these are the architectural choices that make
  Gotham-class software trustworthy, and they are present as working code, not slides.
- **The refusals are real and tested.** The API rejects evidence-free relationships, evidence-free conclusions,
  cross-tenant reads, uncited AI output, and unsupported AI questions. Six of the 26 tests assert a refusal.
  Most prototypes cannot do this because they never modelled the distinction.
- **The AI grounding discipline is defensible.** A measured 0.00 unsupported-claim rate and 0.00 permission
  leakage on a labelled set, with a threshold tuned by measurement rather than vibes. The external-model path is
  rejected unless citations resolve.
- **It is genuinely runnable end-to-end.** 61 backend tests (both backends) + 27 browser checks, real persistence, real auth,
  real migrations. Nothing on a screen is a static image.

## 4. What is missing that matters most

Ranked by how badly it blocks institutional use:

1. **No real integration.** The entire value of Gotham is connecting messy institutional systems. We have file
   uploads. The hardest, least glamorous 60% of the work is untouched.
2. **No identity federation or MFA.** Password-only auth disqualifies any government deployment immediately.
3. **No field-level / purpose-based security.** A single record either is or is not visible. Gotham's core security
   claim — the same record, different views by clearance and purpose — is absent.
4. **Zero scale evidence.** 20 rows in SQLite. Every performance number in the repo is a latency floor on a toy
   dataset and is labelled as such.
5. **No writeback or workflow.** Analysts can read and annotate; they cannot *act* in the system. Operational
   decision support is descriptive, not operational.
6. **No entity resolution workflow.** Duplicate suppression is a name match. Real resolution is a probabilistic,
   human-supervised discipline.
7. **PostGIS/pgvector never executed.** Spatial and vector capability is provisioned and documented, unproven.

## 5. The honest one-paragraph answer

We built roughly **8–10% of the publicly documented Gotham capability space by functional depth**, and **close to
100% of its conceptual shape** — ontology-style entities, graph with provenance, geospatial view, evidence-bound
analysis, human review, audit, grounded AI — implemented as a working, tested, documented system rather than a
mock. In institutional terms that is a credible *architectural reference implementation and demonstration*, and
it is nowhere near a deployable Gotham competitor. The gap is not in ideas; it is in integration surface,
security granularity, scale evidence, and accreditation — the parts that take years and real institutional
partnerships, not additional coding.

## 6. If the goal were a serious sovereign alternative

Sequence that would actually close the gap, in order:

1. **Identity & policy layer** — OIDC/SAML, MFA, ABAC policy engine, field-level markings, purpose binding.
2. **Two real connectors** with a live institutional partner, including schema drift and backfill.
3. **Postgres + PostGIS + pgvector executed**, then load-test at 10⁷ rows and 100 concurrent analysts; publish
   the numbers or the failure.
4. **Ontology with action types and writeback** — the step from reading records to running operations.
5. **Entity resolution with human-supervised merge/split** and resolution audit.
6. **External security assessment** and a real DR drill before any pilot conversation.
