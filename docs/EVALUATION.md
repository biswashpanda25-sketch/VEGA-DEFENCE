# AI and Data Quality Evaluation

## 1. How it is measured

`backend/tests/eval_ai.py` runs a labelled synthetic question set (11 cases, 8 answerable, 3 that must be refused)
against the live application with two distinct tenant identities and computes:

| Metric | Definition |
|---|---|
| Retrieval precision | share of expected evidence families recovered per question (mean) |
| Retrieval recall | whether *any* expected evidence was cited (mean) |
| Citation coverage | fraction of answers carrying ≥1 citation |
| Groundedness | share of cited records that belong to the expected evidence family |
| Unsupported-claim rate | answers asserting content with zero citations |
| Refusal accuracy | share of unanswerable / out-of-tenant questions refused |
| Permission leakage rate | citations whose `organization_id` ≠ caller's organization |
| Latency p50/p95 | end-to-end `/api/v1/ai/ask` |

## 2. Executed results — 2026-11-12

Environment: Python 3.13.16, `AI_PROVIDER=grounded-local` (no external model), synthetic dataset
(2 organizations, 20 entities, 14 relationships, 2 documents).

```json
{
  "cases": 11,
  "retrieval_precision": 0.812,
  "retrieval_recall": 1.0,
  "citation_coverage": 1.0,
  "groundedness": 0.729,
  "unsupported_claim_rate": 0.0,
  "refusal_accuracy": 1.0,
  "permission_leakage_rate": 0.0,
  "latency_ms_p50": 8.6,
  "latency_ms_p95": 9.0,
  "total_citations": 13
}
```

Raw output: `docs/ai_eval_results.json`.

### Interpretation, including what this does *not* prove

- **Refusal correctness is the headline result.** All three out-of-evidence questions (a fabricated location, a
  cross-tenant question, and nonsense) returned `insufficient_evidence` with zero citations.
- **Groundedness 0.73** means roughly a quarter of cited records were contextually relevant but outside the
  labelled expected set (e.g. a warehouse cited when the question concerned its stock batch). This is a labelling
  artefact of a small set as much as a retrieval defect; it is reported as measured, not rounded up.
- These figures measure **retrieval and citation discipline**, not prose quality. The default composer is
  deterministic; fluency metrics are meaningless for it.

## 3. Threshold tuning (same dataset, same day)

The evidence-admission gate requires a retrieved record to cover a share of the query's distinct content terms.
The threshold was selected by measurement, not intuition:

| min_coverage | precision | recall | groundedness | refusal accuracy | citations |
|---|---|---|---|---|---|
| 0.30 | 0.812 | 1.000 | 0.729 | 1.000 | 13 |
| 0.40 | 0.688 | 0.875 | 0.604 | 1.000 | 12 |
| 0.50 | 0.562 | 0.625 | 0.500 | 1.000 | 7 |
| 0.60 | 0.375 | 0.375 | 0.312 | 1.000 | 5 |

0.30 was adopted: maximum recall at perfect refusal accuracy on this set. A larger, harder labelled set is required
before this threshold is treated as tuned for production.

## 4. Data quality metrics

Computed live by `services/ingestion.quality_report` over the caller's organization:

| Dimension | Weight | Method |
|---|---|---|
| Completeness | 40% | records with name + district + type |
| Uniqueness | 30% | distinct (name, type) pairs / records |
| Validity | 20% | entity_type within the controlled vocabulary |
| Provenance coverage | 10% | records carrying a source file reference |

Composite score is surfaced on each dataset row (`quality_score`) and in the Data Sources screen.

## 5. Known evaluation gaps

- Single-tenant-answerable questions dominate; adversarial paraphrases are under-represented.
- No human-graded relevance judgements; no inter-annotator agreement.
- External model path (`AI_PROVIDER=ollama`) is implemented but unmeasured — no model was available in this
  environment. Any deployment using it must re-run this harness with the exact model and prompt version.
