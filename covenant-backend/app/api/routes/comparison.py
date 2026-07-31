from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.db import models
from app.db.database import get_db
from app.schemas.contract import ComparisonRequest, ComparisonResult
from app.services.comparison_service import compare_contracts

router = APIRouter(prefix="/api/comparison", tags=["Comparison"])


@router.post("", response_model=ComparisonResult)
def compare(payload: ComparisonRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    a = get_owned_contract(db, payload.contract_a_id, user)
    b = get_owned_contract(db, payload.contract_b_id, user)
    return compare_contracts(a, b)
