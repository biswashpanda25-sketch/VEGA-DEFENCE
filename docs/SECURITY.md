# Security Architecture and Threat Model

> This document describes controls that **exist in this build** and the residual risk that remains. It is not a
> certification. No independent audit, penetration test or accreditation has been performed. Do not represent
> this system as compliant with any scheme (e.g. CERT-In directions, DPDP Act, ISO 27001) until a qualified
> reviewer has assessed it against the applicable requirements.

## 1. Assets

| Asset | Sensitivity | Where it lives |
|---|---|---|
| Institutional records & documents | High | Relational store, object store |
| Entity relationships and evidence | High | Relational store |
| Analytical findings, case notes | High | Relational store |
| Audit trail | High (integrity) | Relational store |
| Credentials, JWT signing key | Critical | Environment / secret store |
| Model prompts & retrieved context | High | In-process only; conversation rows persisted |

## 2. Trust boundaries

1. Browser ⇄ API (HTTPS in deployment; bearer JWT).
2. API ⇄ database (private network, credentials from environment).
3. API ⇄ model provider (optional, egress; may be a local model with no egress).
4. Uploaded files and ingested documents — **untrusted input**, always.

## 3. Threat model (STRIDE-oriented)

| ID | Threat | Control in this build | Residual risk |
|---|---|---|---|
| T1 | Unauthenticated access to records | JWT required on every non-public route; `get_current_user` rejects missing/expired/forged tokens | Token theft via XSS if a bug is introduced; no refresh-token rotation yet |
| T2 | Cross-tenant data access | Query-layer org filter; object reads return 404 across tenants; tests 02/02b/02c/12 | Postgres RLS not yet enabled as defence-in-depth |
| T3 | Privilege escalation via role change | Only `platform_admin`/`org_admin`; `org_admin` cannot grant `platform_admin`; every change audited | No approval workflow for role grants yet |
| T4 | Sensitive field exposure | Response schemas exclude hashes; connector config strips `password/token/api_key/secret`; test 03 | Field-level classification not enforced below record level |
| T5 | Malicious upload / parser exploitation | Extension allow-list, 25 MB cap, parser exceptions converted to 400 (**test 05**) | No antivirus/CDR sandbox before extraction — required before real document intake |
| T6 | SQL injection | ORM parameterisation throughout; no string-built SQL with user input | — |
| T7 | XSS | React auto-escaping; no `dangerouslySetInnerHTML` in application code; map popup HTML is built from a fixed template with escaped values | Map popup string interpolation is the one place to review when adding fields |
| T8 | Credential brute force | bcrypt hashes; login rate limit (20/min/IP) → 429 (**test 13b**) | Distributed attempts need edge/WAF rate limiting |
| T9 | Prompt injection via documents | Retrieved text is framed as untrusted data; system policy forbids following embedded instructions; citation validation; **test 10c** | Model behaviour is probabilistic when an external model is enabled — keep the deterministic path for sensitive deployments |
| T10 | AI data leakage across tenants | Retrieval scoped before generation; leakage measured at 0.00 in the eval harness | Would regress silently if a new corpus source forgets the tenant filter — covered by test 11 |
| T11 | Audit tampering | Hash-chained rows (`seq`, `prev_hash`, `row_hash`); `GET /audit/verify` detects any mutated or reordered row and reports `broken_at`; append-only by API design | A database superuser can delete the entire chain — tamper evidence, not tamper prevention. WORM export outstanding (KI-15) |
| T12 | Secret leakage in logs | Structured logs record method/path/status/duration only; audit detail excludes credentials | Add log scrubbing before shipping to a central platform |
| T13 | SSRF via connectors | Connector adapters take operator-supplied endpoints; only used by data-admin+ | Outbound allow-list/proxy required before enabling live connectors |
| T14 | Denial of service | Payload caps, pagination limits, graph node caps, sequential benchmark measured | No concurrency test yet; add edge rate limits per route class |

## 4. Authentication and session

- Passwords: bcrypt (cost from `bcrypt.gensalt()`), never logged, never returned.
- Tokens: HS256 JWT, 8-hour default expiry, `sub` = user id, claims include org and role for correlation only —
  **authorisation always re-derives role from the database**, never from the token claim.
- Logout writes an audit event; the client discards the token. Server-side token revocation (denylist) is not
  implemented — recorded in KNOWN_ISSUES.
- **MFA (TOTP): implemented and tested.** `POST /auth/mfa/enroll` returns a secret + `otpauth://` URI,
  `/auth/mfa/activate` verifies the first code and flips the account into enforcement, and login then requires
  `{password, totp}`. A wrong or stale code is rejected with 401; a password-only attempt on an MFA-enabled
  account is refused with an explicit "MFA required" detail rather than a generic failure. Enrolment, activation,
  wrong-code rejection and TOTP sign-in are all covered in `test_mfa_enrollment_and_login_enforcement`.
- **Failed-attempt throttling:** 20 failed sign-ins per client IP per 60 s (configurable via
  `LOGIN_MAX_FAILURES_PER_MIN`). Only *failures* are counted — a limiter that also punishes successful logins
  locks out legitimate operators during busy periods. In-process state; see KI-19 for the Redis requirement.
- OIDC and SAML federation: **not implemented** (KI-01).

## 5. Authorisation model

Roles (least privilege, enforced by `require_role`): `platform_admin`, `org_admin`, `data_admin`, `analyst`,
`reviewer`, `readonly`, `auditor`.

| Action | Required role(s) |
|---|---|
| Read entities/cases/search/AI | any authenticated user |
| Create dataset, ingest, upload document | data_admin, org_admin, analyst, platform_admin |
| Create entity/relationship | data_admin, org_admin, analyst, platform_admin |
| Create case/finding | analyst, reviewer, data_admin, org_admin, platform_admin |
| Approve/reject finding | reviewer, org_admin, platform_admin |
| Read audit log | auditor, org_admin, platform_admin |
| Manage users/roles, connectors | org_admin (own org), platform_admin |
| Create organization | platform_admin |

`readonly` users can read but hold no write role — they are refused on every mutating route.

### 5a. Attribute-based access control (clearance, purpose, compartment)

Roles alone cannot express "an analyst may see INTERNAL records, an org admin may see RESTRICTED, and the
PROTECTED register only reaches PROTECTED-cleared staff". `app/policy.py` adds that layer:

| Element | Behaviour |
|---|---|
| `CLASSIFICATION_RANK` | `INTERNAL (0) < RESTRICTED (1) < PROTECTED (2)` |
| Effective clearance | `max(role default, user.clearance)`; role defaults: platform_admin → PROTECTED, org_admin/data_admin/auditor → RESTRICTED, analyst → INTERNAL |
| Read scoping | `scope_query()` applies tenant filter **and** clearance filter to every entity query, including inside retrieval and analytics |
| Above-clearance access | `assert_can_read()` raises **404, not 403** — a 403 would confirm that the record exists |
| Field-level redaction | `RESTRICTED_FIELDS` (contact/telephone) are removed unless the caller supplies a `purpose` from `PERMITTED_PURPOSES` *and* holds ≥ RESTRICTED clearance; every purpose-gated read is audited with the stated purpose |
| Clearance administration | `PATCH /admin/users/{id}/clearance` is `platform_admin`-only and audited (`admin.clearance_change`) |
| Retrieval | Clearance filtering happens *before* ranking, so a summary cannot leak content through a citation |

## 6. Data protection

- Transport: TLS terminated at ingress/nginx in deployment (compose maps plain HTTP inside the network).
- At rest: delegated to the managed Postgres/object-store volume encryption; application-level envelope encryption
  is **not** implemented.
- Secrets: environment variables or Docker file secrets. No secret is committed; `.gitignore` excludes `.env` and
  `deploy/secrets/*.txt` (only a placeholder file ships for local runs).
- Classification: every dataset/document/entity carries a classification label; the UI labels synthetic data
  everywhere. Enforcement below record level is planned.
- Deletion/retention: retention policy fields and documentation exist; automated purge jobs are not implemented.

## 7. Auditability

Events recorded: `auth.login/logout/register`, `dataset.create/ingest/ingest_failed`, `document.upload`,
`entity.create`, `relationship.create`, `entity.merge`, `case.create`, `finding.create/review`, `search.query`,
`ai.query`, `admin.role_change`, `admin.clearance_change`, `auth.mfa_enroll/activate`. Each row stores org, user,
action, resource, detail, IP, purpose (where supplied), timestamp (UTC), and a monotonic `seq`.

**Integrity.** Each row's `row_hash` is SHA-256 over `seq | prev_hash | org | user | action | resource | detail |
ip | purpose | timestamp (UTC, microsecond precision)`. The timestamp is canonicalised before hashing so that a
database round trip (which drops the timezone marker) does not break verification — an early version failed its
own verifier for exactly that reason. `GET /audit/verify` walks the chain in `seq` order and returns
`{valid, checked, head, tail, broken_at, reason}`.

## 8. Security testing performed

- **61 automated tests on SQLite and 61 on PostgreSQL**, including the 16 mandated scenarios, 8 ABAC/MFA/
  audit-integrity cases and a 26-case route matrix (`docs/TESTING.md`).
- Tamper-detection drill: the audit chain verifies clean, then a single mutated row makes verification fail with
  the offending record identified.
- Scale suite executed at 1,000,000 entities (`docs/SCALE.md`).
- AI grounding and permission-leakage evaluation (`docs/EVALUATION.md`).
- Dependency audit and secret-pattern scan wired into CI (`pip-audit`, `npm audit`, grep gate).

**Not performed:** external penetration test, SAST tool run, DAST fuzzing campaign, backup restore drill on real
infrastructure, chaos/failover test. These are prerequisites for any production claim.
