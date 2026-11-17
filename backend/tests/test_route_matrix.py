"""Route matrix: every registered GET endpoint must answer without a 5xx.

Rationale: the graph endpoint returned HTTP 500 for a week of development because no test exercised
it after `scope_query` learned about classification. A schema-level sweep is cheap insurance against
whole endpoints silently breaking.

Endpoints that need a concrete record ID are skipped here (they have dedicated tests); everything
without path parameters is exercised with the analyst identity.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def _gettable_routes():
    """Enumerate from the OpenAPI schema: independent of the internal router-tree representation."""
    schema = app.openapi()
    out = []
    for path, ops in schema.get("paths", {}).items():
        if "get" not in ops or "{" in path or not path.startswith("/api/v1"):
            continue
        if path in ("/api/v1/health",):
            continue
        out.append(path)
    return sorted(set(out))


@pytest.mark.parametrize("path", _gettable_routes())
def test_get_endpoint_returns_no_server_error(client: TestClient, path: str):
    from tests.conftest import _login
    token = _login(client, "analyst@gotham-demo.in")
    r = client.get(path, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code < 500, f"{path} -> {r.status_code}: {r.text[:300]}"
