"""Endpoint-level benchmark against the 1,000,000-row PostgreSQL database.

Complements `tests/scale.py` (raw query paths) with real HTTP request timing through the FastAPI stack,
so the numbers include serialisation, authorisation and policy filtering.

Prerequisite: `python -m tests.scale --rows 1000000 --dba-psql ...`

    DATABASE_URL=postgresql+psycopg://gotham:gotham_dev_pw@127.0.0.1:5432/gotham_scale \
        python -m tests.bench_scale
"""
import json
import os
import statistics
import time
from pathlib import Path

os.environ.setdefault("SEED_DEMO", "false")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://gotham:gotham_dev_pw@127.0.0.1:5432/gotham_scale")

from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import create_access_token  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

N = int(os.getenv("BENCH_N", "15"))


def pct(samples, p):
    s = sorted(samples)
    return round(s[max(0, int(len(s) * p) - 1)], 2)


def main() -> dict:
    db = SessionLocal()
    user = db.query(User).filter(User.role == "platform_admin").first()
    if user is None:
        raise SystemExit("run tests/scale.py first: no platform_admin in the scale database")
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    db.close()

    probes = [
        ("GET /health", "/api/v1/health", {}),
        ("GET /entities?page=1", "/api/v1/entities?page=1&page_size=50", {}),
        ("GET /entities?q=Khordha", "/api/v1/entities?q=Khordha&page=1", {}),
        ("GET /search?q=warehouse", "/api/v1/search?q=warehouse%20Khordha", {}),
        ("GET /geo/nearby (50km)", "/api/v1/geo/nearby?lat=20.18&lon=85.62&radius_km=50&limit=50", {}),
        ("GET /analytics/overview", "/api/v1/analytics/overview", {}),
        ("POST /ai/ask", "/api/v1/ai/ask", {"json": {"question": "Which warehouses are degraded in Khordha?"}}),
    ]

    out = {
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "conditions": {
            "database": os.environ["DATABASE_URL"],
            "client": "FastAPI TestClient (in-process), single client",
            "note": "in-process transport removes network cost; treat as a lower bound for real HTTP",
            "n": N,
        },
        "endpoints": [],
    }

    with TestClient(app) as client:
        for label, url, kw in probes:
            samples, status = [], None
            method = client.post if kw.get("json") is not None else client.get
            for _ in range(N):
                t = time.perf_counter()
                r = method(url, headers=headers, **kw)
                samples.append((time.perf_counter() - t) * 1000)
                status = r.status_code
            row = {"endpoint": label, "status": status, "p50_ms": pct(samples, 0.50),
                   "p95_ms": pct(samples, 0.95), "max_ms": round(max(samples), 2), "n": N}
            out["endpoints"].append(row)
            print(f"  {label:32s} {status}  p50={row['p50_ms']:8.2f}ms  p95={row['p95_ms']:8.2f}ms")

    path = Path(__file__).resolve().parents[2] / "docs" / "scale_endpoint_bench.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\nwritten -> {path}")
    return out


if __name__ == "__main__":
    main()
