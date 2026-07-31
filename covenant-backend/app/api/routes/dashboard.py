from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.database import get_db

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contracts = db.query(models.Contract).filter(models.Contract.uploaded_by_id == user.id).all()
    total = len(contracts)

    status_counts = Counter(c.status.value for c in contracts)
    compliant_or_approved = status_counts.get("approved", 0) + status_counts.get("reviewed", 0)
    compliance_rate = round((compliant_or_approved / total) * 100, 1) if total else 0.0
    avg_risk = round(sum(c.risk_score for c in contracts) / total, 1) if total else 0.0

    risk_bands = Counter()
    for c in contracts:
        if c.risk_score >= 61:
            risk_bands["high"] += 1
        elif c.risk_score >= 31:
            risk_bands["medium"] += 1
        else:
            risk_bands["low"] += 1

    clause_type_counts = Counter()
    for c in contracts:
        for cl in c.clauses:
            clause_type_counts[cl.clause_type] += 1

    return {
        "contracts_reviewed": total,
        "compliance_rate": compliance_rate,
        "average_risk_score": avg_risk,
        "pending_review": status_counts.get("pending_review", 0),
        "status_breakdown": dict(status_counts),
        "risk_distribution": dict(risk_bands),
        "clause_distribution": dict(clause_type_counts.most_common(10)),
    }
