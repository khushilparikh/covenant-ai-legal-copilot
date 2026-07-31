from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.database import get_db
from app.ml.llm_client import OllamaUnavailableError, generate_redline, is_ollama_available

router = APIRouter(prefix="/api/redline", tags=["Redline"])


class RedlineOut(BaseModel):
    clause_id: str
    original_text: str
    suggested_text: str
    reason: str
    source: str  # "llm" | "unavailable"


@router.post("/{clause_id}", response_model=RedlineOut)
def suggest_redline(clause_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    clause = (
        db.query(models.Clause)
        .join(models.Contract, models.Clause.contract_id == models.Contract.id)
        .filter(models.Clause.id == clause_id, models.Contract.uploaded_by_id == user.id)
        .first()
    )
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")

    flag_reasons = [f.reason for f in clause.risk_flags] or [
        f"General {clause.risk_severity.value}-risk clause of type {clause.clause_type}."
    ]

    if not is_ollama_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama isn't reachable at the configured OLLAMA_BASE_URL. "
                   "Start it locally with `ollama serve` and ensure the model is pulled.",
        )

    try:
        result = generate_redline(clause.text, flag_reasons)
    except OllamaUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    db.add(models.AuditLog(
        contract_id=clause.contract_id, user_id=user.id, action="redline_suggested",
        details={"clause_id": clause.id, "clause_number": clause.clause_number},
    ))
    db.commit()

    return RedlineOut(
        clause_id=clause.id,
        original_text=clause.text,
        suggested_text=result.get("suggested_text", ""),
        reason=result.get("reason", ""),
        source="llm",
    )
