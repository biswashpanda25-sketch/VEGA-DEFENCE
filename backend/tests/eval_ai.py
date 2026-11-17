"""Offline AI evaluation harness for GOTHAM INDIA.

Measures, against a labelled synthetic question set:
  - retrieval precision / recall
  - citation coverage (answers carrying >=1 citation)
  - groundedness (fraction of cited records that are in the expected evidence set)
  - unsupported-claim rate (answers that assert content with no citation)
  - permission leakage rate (citations outside the caller's tenant)
  - refusal correctness on unanswerable questions
  - latency (p50/p95)

Run:  python -m tests.eval_ai
"""
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp(prefix='gotham-eval-')}/eval.db"
os.environ["SEED_DEMO"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

# Labelled set. `expected` = substrings that MUST appear in retrieved/cited titles.
CASES = [
    {"q": "Summarise the maintenance and condition of Bridge Mahanadi-03",
     "expected": ["Bridge Mahanadi-03"], "tenant": "analyst"},
    {"q": "What is the condition of Embankment Segment BBSR-07?",
     "expected": ["Embankment Segment BBSR-07"], "tenant": "analyst"},
    {"q": "Where are relief tarpaulin stocks held?",
     "expected": ["Tarpaulin", "Warehouse"], "tenant": "analyst"},
    {"q": "Which organization manages Substation K-17?",
     "expected": ["Substation K-17", "Works Department"], "tenant": "analyst"},
    {"q": "Summarise the coastal readiness case and its findings",
     "expected": ["Cyclone Season Readiness"], "tenant": "analyst"},
    {"q": "What does the monsoon preparedness advisory say?",
     "expected": ["Monsoon Preparedness"], "tenant": "analyst"},
    {"q": "Identify suppliers linked to the Mahanadi bridge",
     "expected": ["Mahanadi Fabrication", "Bridge Mahanadi-03"], "tenant": "analyst"},
    {"q": "Describe the coastal shelter cluster in Puri",
     "expected": ["Coastal Shelter Cluster"], "tenant": "analyst"},
    # unanswerable / out-of-tenant — must be refused
    {"q": "What is the embankment status near Rourkela steel plant?",
     "expected": [], "tenant": "analyst", "should_refuse_or_no_citation": True},
    {"q": "Summarise Embankment Segment BBSR-07 readiness",
     "expected": [], "tenant": "disaster", "should_refuse_or_no_citation": True},
    {"q": "quantum entanglement in relief logistics 4471",
     "expected": [], "tenant": "analyst", "should_refuse_or_no_citation": True},
]


def login(c: TestClient, email: str) -> dict:
    r = c.post("/api/v1/auth/login", json={"email": email, "password": "Gotham@2026"})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def main() -> dict:
    with TestClient(app) as client:
        tokens = {
            "analyst": login(client, "analyst@gotham-demo.in"),
            "disaster": login(client, "disaster@gotham-demo.in"),
        }
        me = {t: client.get("/api/v1/auth/me", headers=h).json() for t, h in tokens.items()}

        latencies, precisions, recalls, grounded, unsupported, refused_ok = [], [], [], [], [], []
        leakage = 0
        citations_total = 0

        for case in CASES:
            t0 = time.perf_counter()
            r = client.post("/api/v1/ai/ask", headers=tokens[case["tenant"]], json={"question": case["q"]})
            latencies.append((time.perf_counter() - t0) * 1000)
            body = r.json()
            cited = body.get("citations", [])
            citations_total += len(cited)
            titles = [c["title"] for c in cited]

            # permission leakage: every citation must belong to the caller's organisation
            for c in cited:
                if c.get("organization_id") != me[case["tenant"]]["organization_id"]:
                    leakage += 1

            if case.get("should_refuse_or_no_citation"):
                refused_ok.append(body["insufficient_evidence"] or len(cited) == 0)
                continue

            exp = case["expected"]
            matched = [e for e in exp if any(e.lower() in t.lower() for t in titles)]
            precisions.append(len(matched) / len(exp) if exp else 1.0)
            recalls.append(1.0 if matched else 0.0)
            # groundedness: fraction of cited records that match an expected evidence family
            groundable = sum(1 for t in titles if any(e.lower() in t.lower() for e in exp))
            grounded.append(groundable / len(titles) if titles else 0.0)
            # unsupported claim: non-refusal answer with zero citations
            unsupported.append(1.0 if (not cited and not body["insufficient_evidence"]) else 0.0)

        n = len(CASES)
        result = {
            "harness": "gotham-ai-eval",
            "prompt_version": "gotham-rag-v1",
            "provider": os.getenv("AI_PROVIDER", "grounded-local"),
            "cases": n,
            "retrieval_precision": round(statistics.mean(precisions), 3) if precisions else 0.0,
            "retrieval_recall": round(statistics.mean(recalls), 3) if recalls else 0.0,
            "citation_coverage": round(sum(1 for p in recalls if p > 0) / max(len(recalls), 1), 3),
            "groundedness": round(statistics.mean(grounded), 3) if grounded else 0.0,
            "unsupported_claim_rate": round(statistics.mean(unsupported), 3) if unsupported else 0.0,
            "refusal_accuracy": round(statistics.mean(refused_ok), 3) if refused_ok else 0.0,
            "permission_leakage_rate": round(leakage / citations_total, 4) if citations_total else 0.0,
            "latency_ms_p50": round(statistics.median(latencies), 1),
            "latency_ms_p95": round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 1),
            "total_citations": citations_total,
            "notes": "Deterministic grounded composer; no external model invoked. "
                     "Metrics measure retrieval + citation discipline, not language fluency.",
        }
        return result


if __name__ == "__main__":
    res = main()
    print(json.dumps(res, indent=2))
    out = Path(__file__).resolve().parents[2] / "docs" / "ai_eval_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    print(f"\nwritten -> {out}")
