from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import models
from app.db.database import get_db
from app.services.billing_service import create_fake_order, get_billing_status, pay_fake_order

router = APIRouter(prefix="/api/billing", tags=["Billing"])


class CreateOrderRequest(BaseModel):
    billing_cycle: str  # "monthly" | "yearly"


class PayOrderRequest(BaseModel):
    order_id: str
    method: str  # "card" | "upi" | "netbanking" | "qr"
    card_number: str | None = None
    card_name: str | None = None
    expiry: str | None = None
    cvv: str | None = None
    upi_id: str | None = None
    bank_name: str | None = None


@router.get("/status")
def billing_status(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_billing_status(db, user)


@router.post("/checkout/create-order")
def create_order(
    payload: CreateOrderRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user),
):
    """Starts a simulated checkout — see billing_service.py for details
    on why this doesn't call any real payment provider."""
    return create_fake_order(db, user, payload.billing_cycle)


@router.post("/checkout/pay")
def pay_order(
    payload: PayOrderRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user),
):
    """Authorizes the simulated payment via the chosen method and, on
    success, upgrades the account to Premium."""
    return pay_fake_order(
        db, user, payload.order_id, payload.method,
        card_number=payload.card_number, card_name=payload.card_name,
        expiry=payload.expiry, cvv=payload.cvv,
        upi_id=payload.upi_id, bank_name=payload.bank_name,
    )
