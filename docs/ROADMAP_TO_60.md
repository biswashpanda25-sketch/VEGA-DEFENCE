# Roadmap to 60–70% of Gotham-Class Capability

**Date:** 2026-11-12 · **Baseline:** 7.2% weighted index (see `docs/ASSESSMENT_VS_GOTHAM.md`)
**Re-measured after Phase-A/B execution:** **16.3%** — see §1a for the per-area evidence behind each change
**Target:** 60–70% weighted index by month 36
**Realistic cost:** ~150–250 engineer-years — a 40–60 person programme over 3 years, **not** an extension of this
repository by a small team in a quarter.

---

## 1. What "60–70%" is measured against

A weighted capability index, because an unweighted average lets you pad the score with easy screens while the
things institutions actually buy — integration, security granularity, scale evidence — stay at zero.

| Capability area | Weight | Baseline | **Re-measured** | Why this weight |
|---|---|---|---|---|
| Data integration & pipelines | 18% | 3% | **12%** | The entire product value is connecting messy institutional systems |
| Ontology (types, actions, writeback) | 12% | 8% | **10%** | The step from *reading records* to *running operations* |
| Security, governance, audit integrity | 15% | 15% | **30%** | Procurement gate; also the hardest to retrofit |
| Scale & performance | 12% | 1% | **20%** | Determines whether it survives contact with real data |
| Graph analysis & entity resolution | 10% | 8% | **16%** | The analytic core analysts actually use |
| Geospatial | 7% | 8% | **22%** | High value, bounded scope — the easiest area to genuinely finish |
| Analytical workspaces & collaboration | 8% | 12% | **14%** | Where daily work happens |
| Operational workflows & tasking | 8% | 5% | **8%** | Converts insight into action, with accountability |
| AI (agents, tools, evals) | 6% | 8% | **14%** | Enormous leverage, small surface, high risk of dishonesty |
| Deployment, reliability, accreditation | 4% | 2% | **8%** | Capped by institutional trust, not engineering |

Weighted re-measured index: 0.18×12 + 0.12×10 + 0.15×30 + 0.12×20 + 0.10×16 + 0.07×22 + 0.08×14 + 0.08×8 +
0.06×14 + 0.04×8 = **16.3%** (was 7.2%).

**Trajectory if the plan below is executed:**

| Milestone | Weighted index |
|---|---|
| Baseline (first assessment) | 7.2% |
| **Re-measured 2026-11-12 (after Phase-A/B work)** | **16.3%** |
| End of Phase A (month 6) | 20.7% |
| End of Phase B (month 14) | 39.1% |
| End of Phase C (month 22) | 57.7% |
| End of Phase D (month 28) | 64.3% |
| End of Phase E (month 36) | **70.0%** |

The last 30% is deliberately excluded. It is 20 years of edge cases, petabyte-class engineering and national
accreditation — and no amount of roadmap reaches it without institutional trust that is earned in deployment,
not in code.

---

## 1a. Why each area moved — evidence, not intent

Scoring rule: an area only moves when the capability **executes and is verified in this repository**
(tests, migrations, or a measured benchmark). Anything specified but not running scores as before.

| Area | What now genuinely runs | What still caps it |
|---|---|---|
| Integration (3→12) | Connector catalogue with health checks; ingestion with provenance, quality scoring and duplicate detection; job ledger with attempts, exponential backoff and dead-letter; CSV/XLSX/JSON ingestion executed | No live partner system; ingestion synchronous; no CDC or schema-drift detection |
| Ontology (8→10) | Typed relationships require evidence and valid provenance; canonical-entity merge with reversible re-pointing | No source write-back, no ontology-as-data editor |
| Security (15→30) | Clearance ABAC (INTERNAL/RESTRICTED/PROTECTED) enforced on read paths; field-level redaction gated by purpose; hash-chained audit with `/audit/verify` tamper detection; TOTP MFA enrolment + login challenge; failed-attempt throttling; audited clearance administration | No OIDC/SAML IdP, no Postgres RLS, no WORM export, no token revocation/refresh rotation |
| Scale (1→20) | PostgreSQL 17 + PostGIS 3.5 executed; Alembic from empty → head; 1M-row load; published query and endpoint latencies; spatial KNN 1.05 ms; three scale defects found and fixed (`docs/SCALE.md`) | No partitioning, no pooler, no 10⁷ test, analytics overview still scans |
| Graph & ER (8→16) | Trigram-blocked candidate generation with scored match reasons; human-gated merge that re-points relationships, marks canonical records and is audited | No centrality/community/path algorithms |
| Geospatial (8→22) | GiST geography index + KNN radius search measured at 1M rows; district reference data; engine reported honestly (`postgis-gist-knn` vs `haversine`) | No authoritative boundaries, routing or tiling |
| Workspaces (12→14) | Cases, findings, reviewer approval, workspace notes, bounded retrieval | No real-time collaboration or comment threads |
| Workflows (5→8) | Notifications, severity, read-state, job attempts and dead-letter visibility | No assignment engine, SLA or escalation |
| AI (8→14) | Evidence-gated retrieval, `[E#]` citations that resolve, refusal on thin evidence, executed eval set, tenant + clearance scoping inside retrieval | No tool-calling agents, no external model measured, pgvector retrieval unwired |
| Deployment (2→8) | Migration chain, executed `pg_dump`/`pg_restore` drill with row parity, CI workflow with backend/frontend/E2E jobs | Docker unavailable here; containers written but not executed; no accreditation |

The honest reading: the index roughly doubled, and **still sits below the Phase-A gate (20.7%)** because the
identity and connector workstreams — SSO, real source systems — are untouched. Those are not code problems,
they are partnership problems.

---

## 2. The strategic decision that determines success

**Do not build a thin horizontal platform.** Gotham's breadth came from two decades of customer-funded depth.
A sovereign programme reaching 60–70% must pick **two or three mission areas** and become unambiguously excellent
there, then generalise.

Recommended wedge (matches the existing domain work and Odisha demonstration):
1. **Disaster response coordination** — highest public value, strong multi-agency data need, time-critical.
2. **Public infrastructure & logistics** — asset registers, maintenance, supply chain, geography.
3. *(Optional third)* **Defence-adjacent logistics/readiness** — only with an authorized sponsor and legal review.

Everything in the phases below is scoped to those missions. Features that serve no named mission do not get built.

**The single biggest unlock is not engineering: it is 2–3 institutional design partners supplying real,
non-classified data under a signed agreement.** Without them, Phases A and B cannot be validated and the index
stalls around 30%.

---

## 3. Phases, with exit gates that can fail

Each phase ends with **measured exit criteria**. If a gate fails, the phase does not close and the next phase does
not start. This is the difference between a roadmap and a wish list.

### Phase A — Trust & Data Spine (months 0–6) → 20.7%
*Rationale: you cannot deploy, demo to a ministry, or even safely pilot without this. It is also the cheapest
phase to do now and the most expensive to retrofit.*

| Workstream | Deliverables |
|---|---|
| Identity | OIDC/SAML against a real IdP (Keycloak/ADFS/Azure AD), MFA enrolment + enforcement, session revocation/refresh rotation, admin step-up auth |
| Authorisation | ABAC policy engine (purpose, clearance, compartment, org, time), **field-level marking enforcement** in the serialisation layer, Postgres RLS as defence-in-depth, cross-org sharing grants |
| Data spine | PostgreSQL + PostGIS + pgvector executed for real; partitioning; connection pooling; Alembic from empty → head in CI |
| Connectors | Two **real** connectors against partner systems (1 REST, 1 read-only DB), CDC/backfill, schema-drift detection, idempotent replay, dead-letter queue, worker queue (RQ/Celery) with retry/backoff |
| Audit integrity | Hash-chained audit rows, WORM export to immutable storage, retention enforcement job, audit query API for investigators |
| Security baseline | Threat model per release, SAST + dependency + container scanning in CI, secret manager, backup/restore drill executed |

**Exit gates:** 10⁶ records loaded from ≥2 real sources · restore drill completed inside stated RTO · external
pen-test with zero criticals · a read-only user provably cannot reach a field above their marking (automated test,
not a claim).

### Phase B — Ontology, Graph, Entity Resolution (months 4–14) → 39.1%
*Rationale: the ontology is the product. Everything else is a view onto it.*

| Workstream | Deliverables |
|---|---|
| Ontology | Object types and link types defined **as data, not code**; property types with validation; versioned ontology with migration of existing objects; per-object edit history |
| Actions | Action types with parameters, validation, side effects, and **approval gates**; writeback to source systems where the source permits; dry-run mode |
| Graph service | k-hop traversal, shortest path, neighbourhood analytics, query budgets and cost limits; precomputed materialisations; p95 targets by depth |
| Entity resolution | Blocking/indexing, probabilistic scoring, **human-supervised merge/split** with full audit and reversibility, resolution state visible on every link |
| Provenance v2 | Every property carries source, assertion time, confidence, and whether it was imported/inferred/confirmed — at property level, not just relationship level |

**Exit gates:** a new object type added to a running system with **no deployment** · 5×10⁶ objects and 3×10⁷ links
loaded · 3-hop query p95 < 2 s at that volume · 500 human resolution decisions executed with 100% audit
reconstruction · zero unapproved writes to a source system.

### Phase C — Analytical & Operational Surface (months 12–22) → 57.7%
*Rationale: this is where the platform stops being a viewer and starts running a mission.*

| Workstream | Deliverables |
|---|---|
| Workspaces | Shared cases with presence, comments/threads, tasking, assignment, notifications, per-object markup |
| Workflow engine | Configurable state machines, approvals, SLA/escalation, delegation, writeback via ontology actions, complete activity ledger |
| Geospatial | Authorized boundary polygons in PostGIS, spatial predicates (within/intersects/nearest), temporal playback, live feeds with freshness + staleness indicators, offline tile-free rendering retained |
| Reporting | Server-side PDF/Excel generation with templated classification markings, scheduled reports, distribution controls |
| Mission hardening | Two mission workflows rebuilt end-to-end with design partners; usability testing with real analysts |

**Exit gates:** a real analyst completes a full mission cycle (ingest → analyse → act → report) **without an
engineer in the loop** · every action traces to a person, a timestamp and a policy decision · zero unmarked
exports.

### Phase D — AI as an Agentic Layer (months 18–28) → 64.3%
*Rationale: AI is 6% of the index and the easiest place to destroy institutional trust. Do it after the ontology
is trustworthy, not before.*

| Workstream | Deliverables |
|---|---|
| Retrieval | Embeddings in pgvector, hybrid lexical+vector retrieval, re-ranking, measured before switching defaults |
| Tools/agents | Tool-calling over ontology **read** and **propose-action** APIs, hard permission inheritance, human approval gate for every consequential action, no autonomous permission changes |
| Evaluation | CI-gated eval suite (groundedness, citation accuracy, leakage, refusal correctness) with regression thresholds; adversarial/red-team corpus; per-release published numbers |
| Governance | Model registry, prompt versioning, per-org model config, usage/cost dashboards, disable switch per tenant |

**Exit gates:** agents complete 5 named mission workflows · ≥95% citation accuracy · **0** permission leaks across
an adversarial suite of ≥200 probes · every agent-initiated action carries recorded human approval.

### Phase E — Scale, Reliability, Accreditation (months 24–36) → 70.0%
*Rationale: this is the phase that decides whether any of the above may be used.*

| Workstream | Deliverables |
|---|---|
| Scale evidence | Load/soak at 10⁷–10⁸ objects and 500+ concurrent analysts, **published with conditions**; horizontal scaling; read replicas; columnar/Parquet lake for analytics; caching layer with correctness tests |
| Reliability | Multi-AZ, RPO/RTO defined, quarterly restore + failover drills with recorded timings, chaos experiments, SLOs with error budgets |
| Supply chain | SBOM, signed images, reproducible builds, dependency policy, air-gapped installable bundle with offline model weights |
| Accreditation support | Threat model + control mapping for the sponsoring authority, independent security assessment, documentation pack for legal/privacy review (DPDP, CERT-In directions, procurement rules) |

**Exit gates:** 99.9% availability over 90 consecutive days · restore inside RTO in a live drill · zero open
critical/high findings from an independent assessment · a fresh air-gapped install completed by someone who is not
on the engineering team.

---

## 4. Team shape (steady state, ~48 people)

| Function | Headcount | Notes |
|---|---|---|
| Platform/backend | 10 | Ontology, graph, workflow engine |
| Data engineering | 8 | Connectors, pipelines, CDC, drift |
| Frontend | 7 | Dense analytical UX is a specialism |
| Security engineering | 5 | ABAC, crypto, pen-test remediation |
| SRE/Infra | 5 | Postgres at scale, K8s, DR, observability |
| AI/ML | 3 | Retrieval, evals, red-teaming |
| QA/automation | 4 | Contract tests, E2E, performance harness |
| Product + design | 3 | Mission scoping with partners |
| Domain analysts (seconded from partners) | 2–3 | Non-negotiable; they define correctness |
| Program/security-compliance | 2 | Accreditation is a full-time job |

Minimum credible variant: **12–15 people, 18 months → ~35–40%**. Below that, the integration and security
workstreams cannot run in parallel and the index plateaus.

---

## 5. What this plan deliberately does NOT do

- **No dedicated graph database** until measured traversal latency at 10⁷ objects justifies it (ADR-002 stands).
- **No rewrite.** The existing ontology/graph/audit/AI core evolves in place; the migration path is additive.
- **No surveillance, targeting, or individual-tracking capability** — the boundary holds regardless of sponsor
  pressure. It is both a legal and an ethical constraint, and it is written into the code, not just the docs.
- **No multi-tenant SaaS sprawl.** Fewer, deeper institutional deployments beat many shallow ones.
- **No AI-first repositioning.** The ontology and audit trail earn trust; AI spends it.

---

## 6. Risks that could sink this (and the honest mitigation)

| Risk | Severity | Mitigation |
|---|---|---|
| No institutional design partner with real data | **Fatal** | Secure ≥2 partners *before* Phase A closes; without them the index caps near 30% |
| Accreditation timeline is political, not technical | High | Start control-mapping in month 3, not month 30; assume 12–18 month authority cycle |
| Security granularity retrofitted late | High | Phase A does ABAC/field-level first for exactly this reason |
| Team growth outpaces architecture | Medium | Ontology-as-data + contract tests + ADRs; no parallel bespoke services |
| AI credibility collapse from one hallucinated claim | Medium | CI-gated eval thresholds; deterministic grounded mode always available as fallback |
| Scale surprises beyond 10⁷ objects | Medium | Phase B and E include explicit load gates; publish failures, not just successes |

**Kill criteria.** I would recommend stopping or re-scoping if, by month 9: fewer than 2 real sources are
connected; there is no design partner providing live data; or the Phase A security gates cannot be passed without
a full rewrite. Sunk-cost at that point is smaller than at month 18.

---

## 7. One-paragraph answer

Reaching 60–70% is a **three-year, ~50-person, ~200 engineer-year programme** with two institutional data partners
and an accreditation track running in parallel — sequenced identity-and-policy → ontology-and-resolution →
workspaces-and-workflow → agentic AI → scale-and-accreditation, with hard measured gates between each. Roughly
half the distance (to ~40%) is achievable in 14 months with 15 people **if and only if** real data and real
security requirements arrive early. The remaining gap to Gotham itself is not technical ambition — it is
integration surface, measured scale, and institutional trust, each of which is bought with years and partnerships
rather than code.
