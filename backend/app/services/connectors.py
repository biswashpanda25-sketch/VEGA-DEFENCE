"""Connector SDK — the reusable interface every authorized data source implements.

Design contract (each connector):
    validate_config() -> None | raises ConnectorConfigError
    discover_schema() -> SchemaDescriptor
    extract()         -> Iterable[dict]     (raw source rows)
    transform(row)    -> dict               (canonical entity shape)
    health_check()    -> HealthReport

A connector NEVER bypasses authentication, rate limits or access controls, and never claims a successful
integration without a verified call. Connectors that need institutional endpoints or credentials raise
`ConnectorNotConfigured` until those are supplied — which is surfaced to operators as `error`, not
papered over as healthy.
"""
from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable

from .ingestion import normalize, KNOWN_TYPES


class ConnectorConfigError(ValueError):
    """Configuration is invalid or incomplete."""


class ConnectorNotConfigured(RuntimeError):
    """The connector requires credentials or an endpoint that has not been supplied."""


@dataclass
class SchemaDescriptor:
    name: str
    fields: list[dict[str, str]]
    sample: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HealthReport:
    healthy: bool
    detail: str
    verified: bool = False  # True only after a successful authenticated call


class BaseConnector(ABC):
    kind: str = "base"
    required_config: tuple[str, ...] = ()

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    # -- configuration -------------------------------------------------------------------
    def validate_config(self) -> None:
        missing = [k for k in self.required_config if not self.config.get(k)]
        if missing:
            raise ConnectorConfigError(f"{self.kind} connector missing configuration: {', '.join(missing)}")

    # -- pipeline stages -----------------------------------------------------------------
    @abstractmethod
    def extract(self) -> Iterable[dict]:
        raise NotImplementedError

    def discover_schema(self) -> SchemaDescriptor:
        rows = list(self.extract())
        fields = [{"name": k, "type": type(v).__name__} for k, v in (rows[0].items() if rows else [])]
        return SchemaDescriptor(name=self.kind, fields=fields, sample=rows[:3])

    def transform(self, row: dict) -> dict:
        n = normalize(row)
        if not n["name"]:
            raise ConnectorConfigError("row has no resolvable name field")
        if n["entity_type"] not in KNOWN_TYPES:
            n["entity_type"] = "asset"
        return n

    def load(self) -> list[dict]:
        out = []
        for row in self.extract():
            try:
                out.append(self.transform(row))
            except ConnectorConfigError:
                continue  # unparseable rows are counted out, never silently invented
        return out

    # -- health --------------------------------------------------------------------------
    def health_check(self) -> HealthReport:
        try:
            self.validate_config()
            rows = list(self.extract())
            return HealthReport(healthy=True, detail=f"extracted {len(rows)} rows", verified=True)
        except ConnectorNotConfigured as e:
            return HealthReport(healthy=False, detail=str(e), verified=False)
        except ConnectorConfigError as e:
            return HealthReport(healthy=False, detail=str(e), verified=False)
        except Exception as e:  # source fault — reported, not raised to the caller
            return HealthReport(healthy=False, detail=f"{type(e).__name__}: {e}", verified=False)


# ---------------------------------------------------------------------------------------
# Implemented connectors
# ---------------------------------------------------------------------------------------
class CsvConnector(BaseConnector):
    kind = "csv"
    required_config = ("content",)

    def extract(self):
        raw = self.config["content"]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig", errors="replace")
        return [dict(r) for r in csv.DictReader(io.StringIO(raw))]


class JsonConnector(BaseConnector):
    kind = "json"
    required_config = ("content",)

    def extract(self):
        raw = self.config["content"]
        data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
        if isinstance(data, dict):
            data = data.get("records") or data.get("data") or [data]
        return [r for r in data if isinstance(r, dict)]


class ExcelConnector(BaseConnector):
    kind = "excel"
    required_config = ("content",)

    def extract(self):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(self.config["content"]), read_only=True, data_only=True)
        rows = list(wb.active.iter_rows(values_only=True))
        if not rows:
            return []
        header = [str(h) if h is not None else f"col{i}" for i, h in enumerate(rows[0])]
        return [dict(zip(header, r)) for r in rows[1:] if any(c is not None for c in r)]


class RestConnector(BaseConnector):
    """Authorized REST API connector. Requires an institutional endpoint and credentials.

    Deliberately blocked until configured: no anonymous scraping, no auth bypass, no retry storm.
    """
    kind = "rest"
    required_config = ("base_url", "endpoint")

    def validate_config(self) -> None:
        super().validate_config()
        if not self.config.get("auth_token") and not self.config.get("service_account"):
            raise ConnectorNotConfigured(
                "REST connector requires an authorized credential (auth_token or service_account); "
                "no integration is claimed operational until a verified call succeeds"
            )

    def extract(self):
        import httpx
        url = self.config["base_url"].rstrip("/") + "/" + self.config["endpoint"].lstrip("/")
        headers = {"Authorization": f"Bearer {self.config['auth_token']}"} if self.config.get("auth_token") else {}
        with httpx.Client(timeout=float(self.config.get("timeout_s", 20))) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
        if isinstance(data, dict):
            data = data.get("records") or data.get("data") or []
        return [x for x in data if isinstance(x, dict)]


class PostgresConnector(BaseConnector):
    """Authorized read-only database connector (no DDL, no writes, no credential elevation)."""
    kind = "postgres"
    required_config = ("dsn", "query")

    def validate_config(self) -> None:
        super().validate_config()
        if not str(self.config["query"]).strip().lower().startswith("select"):
            raise ConnectorConfigError("only read-only SELECT statements are permitted")
        if not self.config.get("dsn"):
            raise ConnectorNotConfigured("Postgres connector requires an authorized read-only DSN")

    def extract(self):
        try:
            import psycopg  # optional dependency; absent in the reference environment
        except ImportError as e:  # pragma: no cover - environment dependent
            raise ConnectorNotConfigured(f"psycopg not installed: {e}")
        with psycopg.connect(self.config["dsn"]) as conn, conn.cursor() as cur:
            cur.execute(self.config["query"])
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


REGISTRY: dict[str, type[BaseConnector]] = {
    c.kind: c for c in (CsvConnector, JsonConnector, ExcelConnector, RestConnector, PostgresConnector)
}


def get_connector(kind: str, config: dict[str, Any] | None = None) -> BaseConnector:
    if kind not in REGISTRY:
        raise ConnectorConfigError(f"unsupported connector kind '{kind}'; available: {sorted(REGISTRY)}")
    return REGISTRY[kind](config)


def catalog() -> list[dict]:
    """Advertise the connector catalogue with an honest implementation status."""
    status = {"csv": "implemented", "json": "implemented", "excel": "implemented",
              "rest": "requires_credentials", "postgres": "requires_credentials"}
    return [{"kind": k, "status": status[k], "required_config": list(v.required_config),
             "class": v.__name__} for k, v in sorted(REGISTRY.items())]
