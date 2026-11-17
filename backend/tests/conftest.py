import os
import sys
import tempfile
from pathlib import Path

# Isolated test database — never touches the development database.
# Set GOTHAM_TEST_DB_URL to run the identical suite against PostgreSQL/PostGIS/pgvector.
_external = os.environ.get("GOTHAM_TEST_DB_URL")
if _external:
    os.environ["DATABASE_URL"] = _external
    IS_POSTGRES = True
else:
    _tmpdir = tempfile.mkdtemp(prefix="gotham-test-")
    os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
    IS_POSTGRES = False
os.environ.setdefault("SEED_DEMO", "true")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-gotham-india-0123456789")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    if IS_POSTGRES:
        # Extensions are provisioned once by a DBA (see deploy/postgres-bootstrap.sql).
        # Tests only rebuild the application tables, leaving shared extension objects intact.
        from app.db import Base, engine
        from app import models  # noqa: F401 — ensure every table is registered before dropping
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    from app.main import app
    with TestClient(app) as c:
        yield c


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "Gotham@2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def analyst(client):
    return _login(client, "analyst@gotham-demo.in")


@pytest.fixture(scope="session")
def reviewer(client):
    return _login(client, "reviewer@gotham-demo.in")


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "admin@gotham-demo.in")


@pytest.fixture(scope="session")
def other_tenant(client):
    return _login(client, "disaster@gotham-demo.in")
