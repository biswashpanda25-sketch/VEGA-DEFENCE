"""Measured performance benchmark against the running platform (no invented figures).

Usage:  python -m tests.bench --base http://127.0.0.1:8000 --n 40
Writes docs/benchmark_results.json with the exact test conditions.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx


def timed(client, method, path, headers, n, **kw):
    samples, statuses = [], []
    for _ in range(n):
        t0 = time.perf_counter()
        r = client.request(method, path, headers=headers, **kw)
        samples.append((time.perf_counter() - t0) * 1000)
        statuses.append(r.status_code)
    samples.sort()
    return {
        "endpoint": f"{method} {path}",
        "n": n,
        "status": sorted(set(statuses)),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(samples[max(0, int(n * 0.95) - 1)], 2),
        "min_ms": round(samples[0], 2),
        "max_ms": round(samples[-1], 2),
        "mean_ms": round(statistics.mean(samples), 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--n", type=int, default=40)
    args = ap.parse_args()

    with httpx.Client(base_url=args.base, timeout=30) as c:
        health = c.get("/api/v1/health")
        login = c.post("/api/v1/auth/login", json={"email": "analyst@gotham-demo.in", "password": "Gotham@2026"})
        login.raise_for_status()
        h = {"Authorization": f"Bearer {login.json()['access_token']}"}

        results = [
            timed(c, "GET", "/api/v1/health", {}, args.n),
            timed(c, "GET", "/api/v1/entities?limit=50", h, args.n),
            timed(c, "GET", "/api/v1/analytics/overview", h, args.n),
            timed(c, "GET", "/api/v1/graph", h, max(10, args.n // 2)),
            timed(c, "GET", "/api/v1/search?q=embankment%20relief", h, max(10, args.n // 2)),
            timed(c, "POST", "/api/v1/ai/ask", h, max(10, args.n // 2),
                  json={"question": "Summarise the condition of Bridge Mahanadi-03"}),
            timed(c, "GET", "/api/v1/geo/assets", h, max(10, args.n // 2)),
        ]

    payload = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "conditions": {
            "base_url": args.base,
            "runtime": sys.version.split()[0],
            "server": "uvicorn (single worker), SQLAlchemy 2.1 + SQLite (development store)",
            "dataset": "synthetic demo dataset: 2 organizations, 20 entities, 14 relationships, 2 documents",
            "client": "httpx sequential requests, no concurrency (latency floor, not throughput ceiling)",
            "note": "Sequential single-client measurement. Not a load test; concurrency and Postgres results "
                    "must be measured separately before capacity claims are made.",
        },
        "results": results,
    }
    out = Path(__file__).resolve().parents[2] / "docs" / "benchmark_results.json"
    out.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
