# Operational Runbook

## 1. Service checks

| Check | Command | Expected |
|---|---|---|
| API liveness | `curl -fsS http://api:8000/api/v1/health` | `{"status":"ok"}` |
| DB connectivity | `GET /api/v1/admin/system-health` (authenticated) | `"database":"ok"` |
| Migration state | `python -m alembic current` | head revision |
| Connector health | Administration → System & connectors | status per connector |
| AI posture | `GET /api/v1/ai/config` | provider + prompt version |

## 2. Common incidents

**Ingestion failures spike.** Check `GET /api/v1/audit?action=dataset` for `dataset.ingest_failed` detail.
Typical causes: unexpected column set, encoding, unsupported format, file > 25 MB. Re-ingest is safe — duplicate
detection prevents double-counting.

**Suspected cross-tenant access.** Query audit for the user id, compare returned `organization_id` values against
the user's org. The query layer is the enforcement point; if a violation is observed it is a code defect — capture
the request id and open a security incident. Do not "fix" by hiding fields in the UI.

**AI answers without citations.** Treat as a defect. The composer must refuse or cite. Check `AI_PROVIDER` and the
`ai.query` audit rows (they record citation counts).

**Database growth.** Entities/documents dominate. Check `system-health` counts, then `pg_total_relation_size`.
Retention policy is organization-configurable; automated purge is not implemented (KI-04 adjacent).

**High latency.** Compare against `docs/benchmark_results.json` conditions. Look for unbounded `limit` parameters
(server caps at 500), missing indexes on new filter columns, or an external model with a long timeout.

## 3. Backup and restore

```bash
# logical backup (Postgres)
pg_dump --format=custom --no-owner "$DATABASE_URL" > gotham-$(date +%F).dump

# restore into a scratch database and verify before any production restore
createdb gotham_verify && pg_restore --no-owner -d gotham_verify gotham-$(date +%F).dump
psql gotham_verify -c "select count(*) from entities; select count(*) from audit_events;"
```

SQLite development equivalent (exercised by `test_15_backup_and_restore`):
```python
import sqlite3; sqlite3.connect("gotham.db").backup(sqlite3.connect("backup.db"))
```

**Restore drill cadence:** quarterly. Record: backup age, restore duration, row-count parity, audit continuity.
A backup that has never been restored is an assumption, not a control.

## 4. Secret rotation

1. Generate a new `SECRET_KEY`; deploy alongside the old one during a rolling window (dual-accept requires a code
   change — currently single-key, so rotation invalidates sessions; schedule it as maintenance).
2. Rotate DB credentials in the secret store, restart API pods, verify health.
3. Rotate model API keys; confirm `ai.query` events still succeed.

## 5. Capacity planning inputs

Track monthly: entity count, relationship count, document bytes, AI queries, ingestion volume, p95 latency,
DB size. These five drive the scale-up decisions in `ARCHITECTURE.md §8`.

## 6. On-call first 10 minutes

1. Confirm scope: which tenants, which functions.
2. Check `/api/v1/health`, then `system-health`, then the audit stream for the last 30 minutes.
3. If ingestion-related: pause the connector (status → paused) before debugging payloads.
4. If security-related: preserve audit rows and logs, do not rotate evidence away.
5. Escalate with: symptoms, tenant ids, time window (IST), request ids, and what was tried.
