# User Guide

## Getting in

Sign in with your institutional email and password. Sessions survive a refresh; **Sign out** from the user menu at the
top right. Access is logged. Demo identities and the shared demo password are listed on the sign-in screen.

## The frame

- **Left rail** — sections grouped as Analyse / Data / Decide / Govern. Your role governs what each section will let
  you do; pages fail safe with an explanatory banner rather than silently hiding data.
- **Top bar** — universal search with type-ahead, notifications, and your identity/role.
- **Right panel** — contextual detail for whatever you inspect. It opens when you click a record, a citation or a
  map feature, and stays out of the way otherwise.
- **Bottom-left** — classification ceiling for the workspace (INTERNAL · synthetic) and build identity.

## Typical analytical loop

1. **Ingest** — Data Sources → pick a dataset → choose a CSV/JSON/XLSX → Run ingestion. You get parsed rows,
   records created, duplicates skipped, quality score and the provenance retained.
2. **Assess quality** — the Data Quality card shows completeness, uniqueness, validity and provenance coverage.
3. **Explore** — Data Catalog lists canonical records; **Inspect** opens the record, its provenance and its
   relationships.
4. **Map relationships** — Knowledge Graph draws entities and links. Green solid = confirmed, blue = imported,
   amber dashed = inferred, red dotted = unverified. Click a node to read the evidence behind each edge.
5. **Search** — Universal Search ranks entities, documents and cases; every result respects your organization.
6. **Locate** — Geospatial Explorer clusters assets by district, offers a density heatmap, layer toggles and a
   region summary. Positions are district-anchored approximations.
7. **Investigate** — Analytical Workspaces → create a case → attach evidence by adding findings. Choose the kind
   honestly: evidence, assumption, hypothesis or conclusion. Evidence and conclusion findings require references.
8. **Review** — a Reviewer approves, rejects or returns findings. That decision is an immutable audit event.
9. **Ask** — AI Assistant answers from records you are allowed to see and cites each one. If it cannot support an
   answer it says so; that is the product working.
10. **Report** — Reports → choose the extract → Export CSV/JSON or Print/PDF. Exports carry classification,
    generation time, generating user and record count.

## Reading the intelligence honestly

- A **citation** is a pointer to a record, not a truth guarantee: open it and check.
- An **inferred** relationship is a hypothesis. The platform will not let it be filed as evidence without you
  supplying the evidence.
- A **forecast** shows its data basis and limitations. Treat it as a conversation starter.
- Anything labelled **SYNTHETIC** is demonstration data. Nothing in this build is live institutional data.

## Roles at a glance

| Role | Can do |
|---|---|
| Read-only | Read pages, search, view map and graph |
| Analyst | Everything read-only plus ingest, create entities/relationships, open cases, add findings, use the assistant |
| Reviewer | Analyst capabilities plus approve/reject/return findings |
| Data admin | Dataset and connector administration |
| Organization admin | User and role administration within the organization, audit access |
| Security auditor | Audit and AI-usage review |
| Platform admin | Cross-organization administration |

## If something looks wrong

Report the exact page, the record id and the time (IST). The audit log records your searches and actions, so an
investigation can reconstruct what happened without guesswork.


## Governance console

Available to every signed-in user from the sidebar (`Govern` → `Governance`); individual panels degrade to an
explanatory banner when the role lacks the privilege, and the refusal is audited.

- **Audit chain integrity** — shows the current chain head/tail and row count. *Verify now* recomputes the chain:
  a single edited, deleted or reordered row makes the check fail and names the offending record.
- **Data clearances** — platform administrators can see every user's clearance and change it. A clearance change
  is audited and takes effect on the user's next request.
- **Multi-factor authentication** — begin enrolment, add the `otpauth://` URI to an authenticator app and enter
  the 6-digit code. After activation, sign-in requires the current code. Enrol a throwaway identity if you are
  demonstrating the platform, because the shared demo logins will then need a code.
- **Connector job ledger** — every ingest attempt with its status, attempt count and last error; exhausted jobs
  appear as `dead_letter` rather than disappearing.
