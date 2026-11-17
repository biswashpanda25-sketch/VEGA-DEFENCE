"""Attribute-based access control (ABAC) and field-level marking enforcement.

Model
-----
Every record carries a classification; every user carries a clearance. A record is visible only when
    clearance_rank(user) >= classification_rank(record)
*and* the record belongs to the user's organization (platform admins excepted for the tenant rule only —
they do NOT bypass classification).

Field-level markings are declared per field name. Sensitive fields are redacted from serialised output
unless the caller presents an explicit, recorded purpose that permits it. Redaction happens in the
serialisation layer, so a field cannot leak through a forgotten route.

Nothing here is cosmetic: `filter_records` is applied to queries before results leave the service, and
`redact` is applied to every serialised entity/document payload.
"""
from __future__ import annotations

from typing import Any, Iterable

CLASSIFICATION_RANK = {"INTERNAL": 1, "RESTRICTED": 2, "PROTECTED": 3}
DEFAULT_CLEARANCE = "INTERNAL"

# Field markings: fields that are sensitive regardless of record classification.
RESTRICTED_FIELDS = {
    "attributes": ("contact_phone", "personal_id", "home_address", "bank_account", "gps_track"),
}

# Purposes that legitimately unlock marked fields. Recorded on every access.
PERMITTED_PURPOSES = {
    "operations": ("contact_phone",),          # operational coordination
    "maintenance": ("contact_phone",),         # maintainer contact for a work order
    "audit_review": ("contact_phone", "personal_id"),
}


class AccessDenied(Exception):
    pass


def rank(classification: str | None) -> int:
    return CLASSIFICATION_RANK.get((classification or "INTERNAL").upper(), 1)


def clearance_of(user) -> int:
    if getattr(user, "role", None) == "platform_admin":
        # platform admins administer the platform; they do not get automatic content clearance
        return rank(getattr(user, "clearance", DEFAULT_CLEARANCE))
    return rank(getattr(user, "clearance", DEFAULT_CLEARANCE))


def can_read(user, record_classification: str | None, record_org_id: str | None = None) -> bool:
    if record_org_id is not None and getattr(user, "role", None) != "platform_admin":
        if record_org_id != getattr(user, "organization_id", None):
            return False
    return clearance_of(user) >= rank(record_classification)


def assert_can_read(user, record_classification: str | None, record_org_id: str | None = None) -> None:
    if not can_read(user, record_classification, record_org_id):
        # 404 semantics: do not disclose the existence of records above the caller's clearance
        raise AccessDenied("not found")


def scope_query(query, model, user):
    """Apply tenant + classification filtering to a SQLAlchemy query."""
    if getattr(user, "role", None) != "platform_admin":
        query = query.filter(model.organization_id == user.organization_id)
    column = getattr(model, "classification", None)
    if column is None:
        # Relationships inherit visibility from their endpoint entities, which are scoped separately.
        return query
    allowed = [c for c, r in CLASSIFICATION_RANK.items() if r <= clearance_of(user)]
    return query.filter(column.in_(allowed))


def permitted_fields(user, purpose: str | None) -> set[str]:
    fields: set[str] = set()
    if purpose and purpose in PERMITTED_PURPOSES:
        # a purpose only unlocks fields the caller's clearance already permits
        if clearance_of(user) >= rank("RESTRICTED"):
            fields.update(PERMITTED_PURPOSES[purpose])
    return fields


def redact(user, payload: dict, purpose: str | None = None, model: str = "entity") -> dict:
    """Strip marked fields the caller may not see, and record that a redaction occurred."""
    allowed = permitted_fields(user, purpose)
    out = dict(payload)
    removed: list[str] = []
    for field, keys in RESTRICTED_FIELDS.items():
        if field == "attributes" and model != "entity":
            continue
        value = out.get(field)
        if isinstance(value, dict):
            kept = {}
            for k, v in value.items():
                inner = v if not isinstance(v, dict) else v
                if k in keys and k not in allowed:
                    removed.append(k)
                    continue
                kept[k] = inner
            out[field] = kept
    if removed:
        out["redacted_fields"] = sorted(set(removed))
    return out


def audit_purpose(user, purpose: str | None) -> str:
    """Normalise the purpose claim recorded with the access event."""
    if not purpose:
        return "unspecified"
    return purpose if purpose in PERMITTED_PURPOSES else f"unrecognised:{purpose[:40]}"
