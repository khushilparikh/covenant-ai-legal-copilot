from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.db import models
from app.db.database import get_db
from app.schemas.contract import ComplianceResultOut
from app.services.compliance_service import run_compliance_audit

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


@router.post("/{contract_id}/run", response_model=list[ComplianceResultOut])
def run_audit(contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contract = get_owned_contract(db, contract_id, user)

    results = run_compliance_audit(db, contract)
    rule_map = {r.id: r.name for r in db.query(models.PlaybookRule).all()}
    return [
        ComplianceResultOut(rule_name=rule_map.get(r.rule_id, "Unknown rule"), status=r.status.value, reasoning=r.reasoning)
        for r in results
    ]


@router.get("/{contract_id}", response_model=list[ComplianceResultOut])
def get_audit_results(contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contract = get_owned_contract(db, contract_id, user)

    results = db.query(models.ComplianceResult).filter(models.ComplianceResult.contract_id == contract.id).all()
    rule_map = {r.id: r.name for r in db.query(models.PlaybookRule).all()}
    return [
        ComplianceResultOut(rule_name=rule_map.get(r.rule_id, "Unknown rule"), status=r.status.value, reasoning=r.reasoning)
        for r in results
    ]
