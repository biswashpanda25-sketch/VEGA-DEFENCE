from pydantic import BaseModel, EmailStr
from typing import Optional, Any

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp: str | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_code: str = "ODISHA-DEMO"
    role: str = "analyst"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    organization_id: Optional[str] = None
    is_active: bool = True
    clearance: str = "INTERNAL"
    mfa_enabled: bool = False

class OrgCreate(BaseModel):
    name: str
    code: str
    type: str = "department"
    state: str = "Odisha"

class OrgOut(BaseModel):
    id: str
    name: str
    code: str
    type: str
    state: str
    is_active: bool

class DatasetCreate(BaseModel):
    name: str
    description: str = ""
    source_type: str = "file"
    source_org: str = ""
    classification: str = "INTERNAL"

class DatasetOut(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str
    source_type: str
    source_org: str
    classification: str
    record_count: int
    quality_score: float
    status: str

class EntityCreate(BaseModel):
    entity_type: str
    name: str
    classification: str = "INTERNAL"
    description: str = ""
    district: str = ""
    state: str = "Odisha"
    status: str = "active"
    confidence: float = 1.0
    attributes: dict = {}

class EntityOut(BaseModel):
    id: str
    organization_id: str
    entity_type: str
    name: str
    description: str
    district: str
    state: str
    status: str
    confidence: float
    is_synthetic: bool
    classification: str = "INTERNAL"

class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    rel_type: str
    provenance: str = "imported"
    confidence: float = 0.8
    evidence: str = ""
    source_ref: str = ""

class RelationshipOut(BaseModel):
    id: str
    organization_id: str
    source_id: str
    target_id: str
    rel_type: str
    provenance: str
    confidence: float
    evidence: str
    source_ref: str

class CaseCreate(BaseModel):
    title: str
    description: str = ""
    classification: str = "INTERNAL"

class CaseOut(BaseModel):
    id: str
    organization_id: str
    title: str
    description: str
    status: str
    classification: str
    created_by: str

class FindingCreate(BaseModel):
    title: str
    description: str = ""
    kind: str = "evidence"
    confidence: float = 0.5
    evidence_refs: list = []

class FindingOut(BaseModel):
    id: str
    case_id: str
    title: str
    description: str
    kind: str
    confidence: float
    evidence_refs: list
    reviewer_status: str

class AIQuestion(BaseModel):
    question: str
    case_id: Optional[str] = None

class AIAnswer(BaseModel):
    answer: str
    citations: list
    confidence: float
    insufficient_evidence: bool = False

class SearchResult(BaseModel):
    kind: str
    id: str
    title: str
    snippet: str
    organization_id: str

class ImpactEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    source_name: Optional[str] = ""
    target_name: Optional[str] = ""
    rel_type: str
    provenance: str
    confidence: float
    evidence: str
    source_ref: Optional[str] = ""
    is_hypothesis: bool = False

class ImpactNode(BaseModel):
    id: str
    name: str
    entity_type: str
    district: Optional[str] = ""
    state: Optional[str] = "Odisha"
    status: Optional[str] = "active"
    confidence: float = 1.0
    classification: str = "INTERNAL"
    attributes: Optional[dict] = {}
    hop_distance: int
    path: list[ImpactEdge] = []
    path_confidence: float = 1.0
    is_hypothesis: bool = False

class ImpactResponse(BaseModel):
    root_entity: dict
    depth: int
    direction: str = "downstream"
    total_affected: int
    nodes: list[ImpactNode]
    edges: list[ImpactEdge]
