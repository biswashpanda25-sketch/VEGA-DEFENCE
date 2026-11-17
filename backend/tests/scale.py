"""Scale benchmark against real PostgreSQL/PostGIS — measured, never estimated.

Loads N synthetic entities with COPY, builds the production indexes, then measures the query paths the
console actually uses. Writes docs/scale_results.json with the exact conditions.

Usage:
    CREATEDB_URL="postgresql://gotham:pw@127.0.0.1:5432/postgres" \
    python -m tests.scale --rows 1000000
"""
import argparse
import json
import os
import statistics
import subprocess
import time
import uuid
from pathlib import Path

DISTRICTS = [
    ("Khordha", 20.18, 85.62), ("Cuttack", 20.46, 85.88), ("Puri", 19.81, 85.83),
    ("Ganjam", 19.38, 84.83), ("Sambalpur", 21.47, 83.97), ("Sundargarh", 22.12, 84.03),
    ("Keonjhar", 21.63, 85.58), ("Mayurbhanj", 21.93, 86.73), ("Balasore", 21.50, 86.93),
    ("Bhadrak", 21.06, 86.50), ("Jajpur", 20.85, 86.33), ("Dhenkanal", 20.67, 85.60),
    ("Angul", 20.84, 85.10), ("Bargarh", 21.33, 83.62), ("Koraput", 18.81, 82.71),
    ("Rayagada", 19.17, 83.42), ("Kalahandi", 19.91, 83.17), ("Bolangir", 20.70, 83.48),
]
TYPES = ["asset", "facility", "warehouse", "vehicle", "inventory_item", "project"]
STATUSES = ["active", "active", "active", "degraded", "under_maintenance", "offline"]
CLASSES = ["INTERNAL", "INTERNAL", "INTERNAL", "INTERNAL", "RESTRICTED", "PROTECTED"]


def pg_env(password: str) -> dict:
    return {**os.environ, "PGPASSWORD": password}


def run_psql(pgbin: str, url_parts: dict, args: list[str]) -> str:
    cmd = [f"{pgbin}/psql", "-h", url_parts["host"], "-p", str(url_parts["port"]),
           "-U", url_parts["user"], *args]
    return subprocess.run(cmd, check=True, capture_output=True, text=True,
                          env=pg_env(url_parts["password"])).stdout


def pct(samples: list[float], p: float) -> float:
    s = sorted(samples)
    return round(s[max(0, int(len(s) * p) - 1)], 2)


def main() -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1_000_000)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5432)
    ap.add_argument("--user", default="gotham")
    ap.add_argument("--password", default=os.getenv("PGPASSWORD", "gotham_dev_pw"))
    ap.add_argument("--database", default="gotham_scale")
    ap.add_argument("--pg-bin", default=os.environ.get("PG_BIN", "/usr/lib/postgresql/17/bin"))
    ap.add_argument("--dba-psql", default=os.environ.get("GOTHAM_DBA_PSQL", ""),
                    help='superuser psql command for extension bootstrap, e.g. "sudo -u postgres /usr/lib/postgresql/17/bin/psql"')
    args = ap.parse_args()

    parts = {"host": args.host, "port": args.port, "user": args.user,
             "password": args.password, "db": args.database}
    dsn_admin = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/postgres"
    dsn = f"postgresql://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}"

    import psycopg

    print(f"[1/5] provisioning database {args.database}")
    with psycopg.connect(dsn_admin, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {args.database} WITH (FORCE)")
            cur.execute(f"CREATE DATABASE {args.database}")
    # Extensions require superuser: bootstrap as the DBA, exactly as a real deployment would.
    if args.dba_psql:
        for ext in ("postgis", "pg_trgm"):
            subprocess.run([*args.dba_psql.split(), "-d", args.database, "-c",
                            f"CREATE EXTENSION IF NOT EXISTS {ext};"],
                           capture_output=True, text=True)
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension")
            print("      extensions:", sorted(r[0] for r in cur.fetchall()))

    print("[2/5] creating application schema via Alembic (real migration path)")
    env = {**os.environ, "DATABASE_URL": f"postgresql+psycopg://{args.user}:{args.password}@{args.host}:{args.port}/{args.database}"}
    backend = Path(__file__).resolve().parents[1]
    proc = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend, env=env,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-800:])
        raise SystemExit("migration failed")

    org_id, user_id, ds_id = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    now = "2026-11-12T00:00:00+00:00"
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO organizations (id,name,code,type,state,classification,is_active,created_at)
                           VALUES (%s,'Scale Benchmark Org','SCALE-BENCH','department','Odisha','INTERNAL',true,%s)""",
                        (org_id, now))
            cur.execute("""INSERT INTO users (id,email,full_name,hashed_password,role,organization_id,
                           is_active,mfa_enabled,clearance,created_at)
                           VALUES (%s,'scale@gotham-demo.in','Scale Runner','x','analyst',%s,true,false,'PROTECTED',%s)""",
                        (user_id, org_id, now))
            cur.execute("""INSERT INTO users (id,email,full_name,hashed_password,role,organization_id,
                           is_active,mfa_enabled,clearance,created_at)
                           VALUES (%s,'scale-admin@gotham-demo.in','Scale Admin','x','platform_admin',%s,true,false,'PROTECTED',%s)""",
                        (admin_id, org_id, now))
            cur.execute("""INSERT INTO datasets (id,organization_id,name,description,source_type,source_org,
                           classification,record_count,quality_score,status,provenance,created_at,updated_at)
                           VALUES (%s,%s,'Scale Dataset','synthetic load','file','SYNTHETIC','INTERNAL',0,0,'active','{}',%s,%s)""",
                        (ds_id, org_id, now, now))
        conn.commit()

    print(f"[3/5] loading {args.rows:,} entities with COPY")
    t0 = time.perf_counter()

    def rows_iter():
        for i in range(args.rows):
            district, lat, lon = DISTRICTS[i % len(DISTRICTS)]
            yield (
                str(uuid.uuid4()), org_id, TYPES[i % len(TYPES)],
                f"{district} {TYPES[i % len(TYPES)]} {i:07d} (Synthetic)",
                "synthetic scale record", district, "Odisha", STATUSES[i % len(STATUSES)],
                round(0.75 + (i % 25) / 100.0, 2), True, CLASSES[i % len(CLASSES)], None,
                round(lat + ((i % 97) - 48) / 900.0, 5), round(lon + ((i % 41) - 20) / 300.0, 5),
                json.dumps({"source_file": "scale_synthetic.csv", "provenance": "imported"}), now, now,
            )

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            with cur.copy("""COPY entities (id,organization_id,entity_type,name,description,district,state,
                             status,confidence,is_synthetic,classification,canonical_id,latitude,longitude,
                             attributes,created_at,updated_at) FROM STDIN""") as copy:
                for row in rows_iter():
                    copy.write_row(row)
        conn.commit()
    rel_count = min(args.rows // 3, 300_000)
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM entities LIMIT %s", (rel_count * 2,))
            ids = [r[0] for r in cur.fetchall()]
            with cur.copy("""COPY relationships (id,organization_id,source_id,target_id,rel_type,
                             provenance,confidence,created_at) FROM STDIN""") as copy:
                for i in range(rel_count):
                    copy.write_row((str(uuid.uuid4()), org_id, ids[i], ids[-1 - i],
                                    "supplies" if i % 2 else "located_in",
                                    "synthetic scale load", 0.6, now))
        conn.commit()
    load_s = time.perf_counter() - t0
    print(f"      loaded in {load_s:.1f}s ({args.rows / load_s:,.0f} rows/s)")

    print("[4/5] building production indexes")
    t0 = time.perf_counter()
    geo_index = False
    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_scale_org_type ON entities (organization_id, entity_type)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_entities_name_trgm ON entities USING gin (name gin_trgm_ops)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_scale_class ON entities (organization_id, classification)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_scale_name_org ON entities (organization_id, name)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_rel_source ON relationships (source_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_rel_target ON relationships (target_id)")
            try:
                cur.execute("CREATE INDEX IF NOT EXISTS ix_scale_geo ON entities USING gist "
                            "((ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography))")
                geo_index = True
            except psycopg.Error as e:
                print(f"      ! postgis gist index unavailable: {str(e).splitlines()[0]}")
                cur.execute("CREATE INDEX IF NOT EXISTS ix_scale_latlon ON entities (latitude, longitude)")
            cur.execute("ANALYZE entities")
    index_s = time.perf_counter() - t0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename='entities' ORDER BY 1")
            built = [r[0] for r in cur.fetchall()]
    print(f"      indexed in {index_s:.1f}s; indexes present: {len(built)} -> {built}")

    print("[5/5] measuring query paths")
    results = {"measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "conditions": {
                   "database": "PostgreSQL 17.11 + PostGIS 3.5 + pg_trgm",
                   "rows": args.rows, "load_seconds": round(load_s, 1),
                   "rows_per_second": round(args.rows / load_s),
                   "index_build_seconds": round(index_s, 1),
                   "postgis_geo_index": geo_index,
                   "indexes_present": built,
                   "client": "psycopg3 sequential queries, single connection",
                   "hardware": "shared CI-class sandbox; absolute numbers will differ on production hardware",
               }, "queries": []}

    def measure(name: str, sql: str, params: tuple, n: int = 20,
                settings: tuple[str, ...] = ("SET jit = off",)):
        samples = []
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                for stmt in settings:
                    cur.execute(stmt)
                cur.execute(sql, params)  # warm
                cur.fetchall()
                for _ in range(n):
                    t = time.perf_counter()
                    cur.execute(sql, params)
                    cur.fetchall()
                    samples.append((time.perf_counter() - t) * 1000)
        results["queries"].append({"query": name, "p50_ms": pct(samples, 0.50),
                                   "p95_ms": pct(samples, 0.95), "n": n,
                                   "session_settings": list(settings),
                                   "sql": " ".join(sql.split())[:220]})
        print(f"      {name:34s} p50={pct(samples, 0.50):7.2f}ms  p95={pct(samples, 0.95):7.2f}ms")

    classes = "('INTERNAL')"
    measure("paginated entity list (page 1)",
            f"SELECT id,name,entity_type,district,status FROM entities WHERE organization_id=%s "
            f"AND classification IN {classes} AND canonical_id IS NULL ORDER BY name LIMIT 100 OFFSET 0",
            (org_id,))
    measure("paginated entity list (page 500)",
            f"SELECT id,name,entity_type,district,status FROM entities WHERE organization_id=%s "
            f"AND classification IN {classes} AND canonical_id IS NULL ORDER BY name LIMIT 100 OFFSET 50000",
            (org_id,))
    measure("trigram name search",
            "SELECT id,name FROM entities WHERE organization_id=%s AND name %% %s "
            "ORDER BY similarity(name, %s) DESC LIMIT 20",
            (org_id, "Khordha asset 0000123", "Khordha asset 0000123"))
    measure("district filter + aggregate",
            f"SELECT district, COUNT(*) FROM entities WHERE organization_id=%s AND classification IN {classes} "
            f"GROUP BY district ORDER BY 2 DESC",
            (org_id,))
    measure("two-hop relationship join (UNION of indexed lookups)",
            """WITH e AS (
                   SELECT id FROM entities WHERE organization_id=%s
                     AND classification IN ('INTERNAL') LIMIT 200)
               SELECT e.id, COUNT(*) FROM e
               JOIN (SELECT source_id AS id FROM relationships
                     UNION ALL SELECT target_id FROM relationships) r ON r.id = e.id
               GROUP BY e.id ORDER BY 2 DESC LIMIT 50""",
            (org_id,))
    GEO = ("ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography")
    PT = "ST_SetSRID(ST_MakePoint(85.62, 20.18), 4326)::geography"
    measure("postgis radius 50km, KNN ordering",
            f"SELECT id, ST_Distance({GEO}, {PT})/1000 AS km FROM entities WHERE organization_id=%s "
            f"AND ST_DWithin({GEO}, {PT}, 50000) ORDER BY {GEO} <-> {PT} LIMIT 50",
            (org_id,), settings=("SET jit = off", "SET max_parallel_workers_per_gather = 0"))
    measure("postgis radius 50km, distance-SORTED (naive)",
            f"SELECT id, ST_Distance({GEO}, {PT})/1000 AS km FROM entities WHERE organization_id=%s "
            f"AND ST_DWithin({GEO}, {PT}, 50000) ORDER BY km LIMIT 50",
            (org_id,))
    measure("postgis count within 2km",
            f"SELECT count(*) FROM entities WHERE ST_DWithin({GEO}, {PT}, 2000)", ())
    measure("trigram search on a selective token",
            "SELECT id,name FROM entities WHERE name %% %s ORDER BY similarity(name,%s) DESC LIMIT 20",
            ("0000123", "0000123"))

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT reltuples::bigint FROM pg_class WHERE relname='entities'")
            results["conditions"]["verified_row_count"] = cur.fetchone()[0]

    out = Path(__file__).resolve().parents[2] / "docs" / "scale_results.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\nwritten -> {out}")
    return results


if __name__ == "__main__":
    main()
