"""GOTHAM INDIA — SQLAlchemy models. Postgres-ready; SQLite for local dev."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base

def uid():
    return str(uuid.uuid4())

def now():
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=uid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    type = Column(String, default="department")  # department, agency, institution
    state = Column(String, default="Odisha")
    classification = Column(String, default="INTERNAL")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)
    users = relationship("User", back_populates="organization")
    datasets = relationship("Dataset", back_populates="organization")
    entities = relationship("Entity", back_populates="organization")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=uid)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # platform_admin, org_admin, data_admin, analyst, reviewer, readonly, auditor
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    clearance = Column(String, default="INTERNAL")  # INTERNAL < RESTRICTED < PROTECTED
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)
    organization = relationship("Organization", back_populates="users")

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    source_type = Column(String, default="file")  # file, api, database, manual
    source_org = Column(String, default="")
    classification = Column(String, default="INTERNAL")
    record_count = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    status = Column(String, default="active")  # active, paused, error
    provenance = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    organization = relationship("Organization", back_populates="datasets")

class Connector(Base):
    __tablename__ = "connectors"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)  # csv, excel, json, xml, pdf, rest, postgres, webhook
    config = Column(JSON, default=dict)
    status = Column(String, default="configured")  # configured, healthy, error, paused
    last_run_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)

class ConnectorJob(Base):
    __tablename__ = "connector_jobs"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    connector_id = Column(String, ForeignKey("connectors.id"), nullable=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True, index=True)
    status = Column(String, default="queued")   # queued, running, succeeded, retrying, dead_letter
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    payload_ref = Column(String, default="")
    last_error = Column(Text, default="")
    result = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now, index=True)
    updated_at = Column(DateTime, default=now, onupdate=now)


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    title = Column(String, nullable=False)
    filename = Column(String, default="")
    doc_type = Column(String, default="pdf")
    classification = Column(String, default="INTERNAL")
    content_text = Column(Text, default="")
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)

class Entity(Base):
    __tablename__ = "entities"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, default="")
    district = Column(String, default="", index=True)
    state = Column(String, default="Odisha")
    status = Column(String, default="active")
    confidence = Column(Float, default=1.0)
    is_synthetic = Column(Boolean, default=True)
    classification = Column(String, default="INTERNAL", index=True)
    canonical_id = Column(String, nullable=True, index=True)   # set when merged into another record
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    attributes = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    organization = relationship("Organization", back_populates="entities")

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    source_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    target_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)
    rel_type = Column(String, nullable=False)  # belongs_to, managed_by, located_at, supplied_by, connected_to, maintained_by, referenced_in, derived_from, associated_with
    provenance = Column(String, default="imported")  # confirmed, imported, inferred, unverified
    confidence = Column(Float, default=0.8)
    evidence = Column(Text, default="")
    source_ref = Column(String, default="")
    created_at = Column(DateTime, default=now)

class Case(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="open")  # open, in_review, closed
    classification = Column(String, default="INTERNAL")
    created_by = Column(String, default="")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)

class Finding(Base):
    __tablename__ = "findings"
    id = Column(String, primary_key=True, default=uid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    kind = Column(String, default="evidence")  # evidence, assumption, hypothesis, conclusion
    confidence = Column(Float, default=0.5)
    evidence_refs = Column(JSON, default=list)
    reviewer_status = Column(String, default="pending")
    created_by = Column(String, default="")
    created_at = Column(DateTime, default=now)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    message = Column(Text, default="")
    severity = Column(String, default="info")  # info, warning, critical
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, nullable=True, index=True)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    resource = Column(String, default="")
    detail = Column(Text, default="")
    ip_address = Column(String, default="")
    purpose = Column(String, default="")
    seq = Column(Integer, default=0, index=True)   # monotonic ordering for chain verification
    prev_hash = Column(String, default="")
    row_hash = Column(String, default="", index=True)
    created_at = Column(DateTime, default=now, index=True)

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(String, primary_key=True, default=uid)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, default="")
    citations = Column(JSON, default=list)
    created_at = Column(DateTime, default=now)
