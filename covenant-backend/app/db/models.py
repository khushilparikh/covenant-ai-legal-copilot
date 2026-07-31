import enum
import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, DateTime, Enum, Float, ForeignKey,
                         Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    USER = "user"


class ReviewStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --------------------------------------------------------------------- #
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    plan: Mapped[str] = mapped_column(String, default="free")  # "free" | "premium"

    # Profile fields
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    job_title: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contracts: Mapped[list["Contract"]] = relationship(back_populates="uploaded_by")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    display_code: Mapped[str] = mapped_column(String, unique=True, index=True)  # e.g. CV-2026-0142
    title: Mapped[str] = mapped_column(String, nullable=False)
    contract_type: Mapped[str] = mapped_column(String, default="General")  # MSA/NDA/Vendor/Employment/Lease...
    counterparty: Mapped[str | None] = mapped_column(String, nullable=True)

    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    page_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.DRAFT)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)

    effective_date: Mapped[str | None] = mapped_column(String, nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String, nullable=True)
    governing_law: Mapped[str | None] = mapped_column(String, nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String, nullable=True)
    parties: Mapped[list | None] = mapped_column(JSON, nullable=True)
    monetary_values: Mapped[list | None] = mapped_column(JSON, nullable=True)

    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Versioning, for Module 9 (Contract Comparison)
    version_group_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    version_label: Mapped[str | None] = mapped_column(String, nullable=True)

    uploaded_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    uploaded_by: Mapped["User"] = relationship(back_populates="contracts")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    clauses: Mapped[list["Clause"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    compliance_results: Mapped[list["ComplianceResult"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="contract", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)

    clause_number: Mapped[str] = mapped_column(String)   # e.g. "8.3"
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    clause_type: Mapped[str] = mapped_column(String, index=True)   # Module 4 output
    classification_confidence: Mapped[float] = mapped_column(Float)

    risk_score: Mapped[int] = mapped_column(Integer, default=0)     # Module 7 output
    risk_severity: Mapped[RiskSeverity] = mapped_column(Enum(RiskSeverity), default=RiskSeverity.LOW)

    contract: Mapped["Contract"] = relationship(back_populates="clauses")
    risk_flags: Mapped[list["RiskFlag"]] = relationship(back_populates="clause", cascade="all, delete-orphan")


class RiskFlag(Base):
    __tablename__ = "risk_flags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    clause_id: Mapped[str] = mapped_column(ForeignKey("clauses.id"), index=True)
    severity: Mapped[RiskSeverity] = mapped_column(Enum(RiskSeverity))
    reason: Mapped[str] = mapped_column(String)

    clause: Mapped["Clause"] = relationship(back_populates="risk_flags")


class PlaybookRule(Base):
    """Module 6: corporate playbook rules that contracts are checked against."""
    __tablename__ = "playbook_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    applies_to_clause_type: Mapped[str] = mapped_column(String)  # e.g. "Liability"
    rule_kind: Mapped[str] = mapped_column(String)  # "min_notice_days" | "requires_cap" | "max_notice_days" | ...
    threshold_value: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("playbook_rules.id"))
    status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus))
    reasoning: Mapped[str] = mapped_column(Text)
    related_clause_id: Mapped[str | None] = mapped_column(String, nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="compliance_results")


class ChatMessage(Base):
    """Module 11: Chat With Contract history."""
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # "user" | "ai"
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[list | None] = mapped_column(JSON, nullable=True)  # clause numbers cited
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contract: Mapped["Contract"] = relationship(back_populates="chat_messages")


class AuditLog(Base):
    """Module 14: Audit Trail — user actions, AI decisions, generated reports."""
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    contract_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)   # "uploaded" | "status_changed" | "ai_classified" | ...
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Order/payment tracking for the Premium upgrade flow.

    IMPORTANT: this is a fully SIMULATED payment gateway for educational
    purposes — no real payment provider (Razorpay, PayPal, Stripe, etc.)
    is involved anywhere in this flow. No real money ever moves. See
    billing_service.py for the simulated authorization logic."""
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    amount_inr: Mapped[int] = mapped_column(Integer)
    billing_cycle: Mapped[str] = mapped_column(String)    # "monthly" | "yearly"
    method: Mapped[str] = mapped_column(String, default="card")  # card | upi | netbanking | qr
    detail: Mapped[str | None] = mapped_column(String, nullable=True)  # masked card/UPI id/bank name
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | paid | declined
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
