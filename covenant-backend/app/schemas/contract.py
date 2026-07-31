from datetime import datetime

from pydantic import BaseModel


class RiskFlagOut(BaseModel):
    severity: str
    reason: str

    class Config:
        from_attributes = True


class ClauseOut(BaseModel):
    id: str
    clause_number: str
    page_number: int | None
    text: str
    clause_type: str
    classification_confidence: float
    risk_score: int
    risk_severity: str
    risk_flags: list[RiskFlagOut] = []

    class Config:
        from_attributes = True


class ContractSummary(BaseModel):
    id: str
    display_code: str
    title: str
    contract_type: str
    counterparty: str | None
    status: str
    risk_score: int
    page_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ContractDetail(ContractSummary):
    effective_date: str | None
    expiry_date: str | None
    governing_law: str | None
    payment_terms: str | None
    parties: list | None
    monetary_values: list | None
    executive_summary: str | None
    clauses: list[ClauseOut] = []

    class Config:
        from_attributes = True


class ContractStatusUpdate(BaseModel):
    status: str  # draft | pending_review | reviewed | approved | rejected


class ComplianceResultOut(BaseModel):
    rule_name: str
    status: str
    reasoning: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    contract_id: str
    question: str


class ChatMessageOut(BaseModel):
    role: str
    content: str
    sources: list | None
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonRequest(BaseModel):
    contract_a_id: str
    contract_b_id: str


class ComparisonResult(BaseModel):
    added: list[str]
    removed: list[str]
    modified: list[dict]
