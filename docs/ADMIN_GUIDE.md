# Administrator Guide

## Daily posture check
1. **Administration → System & connectors** — API/database health, user and entity counts, connector status.
2. **Security & Audit** — scan the last 24 hours for `auth.*` anomalies, `admin.role_change`, `dataset.ingest_failed`.
3. **Notifications** — data-quality warnings and status changes awaiting action.
4. **AI governance** — citation coverage; any query without citations is a defect worth investigating.

## User and role management
Administration → Users & roles. Changing a role is immediate and audited (`admin.role_change`). Only a platform
administrator can grant `platform_admin`; an organization administrator is confined to their own organization.
Grant the least role that allows the work: analysts analyse, reviewers approve, auditors read the log — never combine
review authority with data-modification authority in one person where policy forbids it.

## Connector management
Connectors belong to an organization and carry a kind (`csv`, `excel`, `json`, `xml`, `pdf`, `rest`, `postgres`,
`webhook`) and a status (`configured`, `healthy`, `error`, `paused`). Secrets are stripped from API responses.
A connector in `error` with "No credentials configured" is the honest state of an unverified integration — do not
flip it to healthy without a successful authenticated run.

## Data quality
Each dataset exposes completeness, uniqueness, validity and provenance coverage. Investigate drops in
**provenance coverage** first: records without a source reference cannot be defended.

## Classification and retention
Classification labels travel with datasets, documents and cases. Retention defaults: 90 days for audit events in
this build; set institutional values before deployment and record them in the data-governance annexure.

## Exports
Exports are audited. Before releasing any export outside the organization, confirm the classification and the
recipient's authorization — the platform records who exported what, not who was entitled to receive it.

## Escalation
Security incident → preserve logs and audit rows, do not delete, notify the designated security officer with tenant
id, user id, time window and request ids. Reliability incident → follow `docs/OPERATIONS.md §6`.
