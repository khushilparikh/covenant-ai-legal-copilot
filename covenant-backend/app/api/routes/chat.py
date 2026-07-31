from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.db import models
from app.db.database import get_db
from app.schemas.contract import ChatMessageOut, ChatRequest
from app.services.chat_service import ask_contract

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("/ask")
def ask(payload: ChatRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contract = get_owned_contract(db, payload.contract_id, user)
    return ask_contract(db, contract, payload.question)


@router.get("/{contract_id}/history", response_model=list[ChatMessageOut])
def history(contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    contract = get_owned_contract(db, contract_id, user)
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.contract_id == contract.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
