# Data Governance

## 1. Principles

1. **Provenance before insight.** Every record carries its source, ingestion time, validation state and
   transformation history. A record with no provenance is a liability, not an asset.
2. **Evidence before assertion.** Relationships require evidence text; findings require typed intent and, for
   evidence/conclusion, resolvable references.
3. **Classification is explicit.** Datasets, documents and cases carry a classification label; synthetic data is
   labelled in every surface, not just in the database.
4. **Least data.** Only authorized institutional records related to assets, organizations and events. No profiling
   or tracking of private individuals is implemented anywhere in the platform.
5. **Tenant sovereignty.** Records belong to an organization. Cross-organization access is refused by default at
   the query layer.

## 2. Canonical model and fidelity

Incoming rows are normalised into a canonical entity shape (`name`, `entity_type`, `district`, `state`, `status`)
while `attributes.extras` preserves every original field that was not mapped, alongside `source_file`,
`dataset_id`, `ingested_at`, `source_org`, `provenance` and `validation`. Source information is therefore never
destroyed by normalisation.

## 3. Relationship provenance classes

| Class | Meaning | Allowed to state as fact? |
|---|---|---|
| `confirmed` | Stated in a source record and corroborated | Yes, with the citation |
| `imported` | Asserted by a source, not independently verified | Yes, attributed to the source |
| `inferred` | Derived by the platform from patterns | **No** — presented as hypothesis |
| `unverified` | Referenced once, not corroborated | **No** |

The interface encodes this visually (solid / dashed / dotted edges) so a reader cannot mistake an inference for a
finding.

## 4. Retention and lifecycle

- Classification labels: `INTERNAL`, `RESTRICTED`, `PROTECTED` (configurable per organization).
- Retention: demonstration default 90 days for audit; record retention is organization-configurable. Automated
  purge jobs are **not implemented** (see KNOWN_ISSUES).
- Deletion: secure-deletion procedures must be defined by the deploying institution; the platform provides
  scoped deletion only through database administration at present.

## 5. Export control

Report exports include classification, generation timestamp, generating user, record count and data basis.
Exports are audited. Field-level export restriction is planned (KI-06).

## 6. Legal and regulatory posture

Applicable Indian requirements — including privacy, cybersecurity directions, procurement rules and
information-security classifications — **must be identified and assessed by qualified institutional reviewers**
before deployment. Technical controls in this repository do not constitute compliance. The platform is designed
to be *assessable*: it labels data, records who did what, and refuses actions it cannot justify.
