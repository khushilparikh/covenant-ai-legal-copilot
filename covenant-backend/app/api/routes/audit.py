from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.db import models
from app.db.database import get_db

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])


@router.get("/{contract_id}")
def get_audit_trail(contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contract = get_owned_contract(db, contract_id, user)
    logs = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.contract_id == contract.id)
        .order_by(models.AuditLog.timestamp.asc())
        .all()
    )
    return [
        {"action": l.action, "details": l.details, "user_id": l.user_id, "timestamp": l.timestamp}
        for l in logs
    ]
