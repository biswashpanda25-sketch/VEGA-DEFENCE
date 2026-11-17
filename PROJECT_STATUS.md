# PROJECT STATUS (root pointer)

The authoritative status record is **`docs/PROJECT_STATUS.md`**.

Quick state as of 2026-11-12:
- Phases 0–6 implemented and running; Phases 7–8 partial (see phase table).
- **61/61 tests passing on SQLite and 61/61 on PostgreSQL 17 + PostGIS**; 27/27 browser E2E checks; AI evaluation,
  API benchmark and a 1,000,000-row scale benchmark measured and recorded (`docs/SCALE.md`).
- Phase-A/B capabilities landed: ABAC clearance, TOTP MFA, hash-chained audit with verification, entity
  resolution + merge, connector job ledger with dead-letter, PostGIS KNN proximity.
- Synthetic Odisha demonstration dataset only.
- 21 tracked known issues; 1 of severity S1 (no OIDC/SAML IdP). Postgres execution and audit chaining are closed.
- **Re-measured capability index: 16.3%** (baseline 7.2%; Phase-A gate is 20.7%) — `docs/ROADMAP_TO_60.md` §1a.
