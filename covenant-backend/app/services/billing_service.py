"""
Free-tier upload limit + a fully SIMULATED payment gateway supporting
multiple payment methods (Card, UPI, Netbanking, QR).

This does NOT integrate with any real payment provider (no Razorpay, no
PayPal, no Stripe). It exists so the app can demonstrate a complete
checkout experience across several common payment methods — order
creation, method-specific input, an "authorization" step, and a
success/decline outcome — entirely for educational/demo purposes. No
real money ever moves, and no real card/bank details are ever
transmitted anywhere outside this server.

To wire up a real provider later: replace pay_fake_order() below with
real API calls per method and keep everything else — the upload-limit
enforcement, the Payment/AuditLog bookkeeping, and the API surface — the
same.
"""
import re
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db import models

FREE_UPLOAD_LIMIT = 30
PREMIUM_PRICE_INR_MONTHLY = 999
PREMIUM_PRICE_INR_YEARLY = 9999  # ~2 months free vs. monthly

# Scripted failure cases, so the demo can show a realistic decline path
# for each method, not just the happy path.
DECLINE_TEST_CARD = "4000000000000002"
DECLINE_UPI_ID = "decline@upi"
DECLINE_BANK_NAME = "Test Bank (Always Declines)"

EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])\s*/\s*(\d{2})$")
UPI_RE = re.compile(r"^[\w.\-]{2,64}@[a-zA-Z][\w]{1,64}$")

VALID_METHODS = ("card", "upi", "netbanking", "qr")


def get_upload_count(db: Session, user_id: str) -> int:
    return db.query(models.Contract).filter(models.Contract.uploaded_by_id == user_id).count()


def get_billing_status(db: Session, user: models.User) -> dict:
    used = get_upload_count(db, user.id)
    is_premium = user.plan == "premium"
    limit = None if is_premium else FREE_UPLOAD_LIMIT
    return {
        "plan": user.plan,
        "uploads_used": used,
        "uploads_limit": limit,
        "remaining": None if limit is None else max(0, limit - used),
        "limit_reached": (not is_premium) and used >= FREE_UPLOAD_LIMIT,
        "price_inr_monthly": PREMIUM_PRICE_INR_MONTHLY,
        "price_inr_yearly": PREMIUM_PRICE_INR_YEARLY,
    }


def enforce_upload_limit(db: Session, user: models.User) -> None:
    """Raises 402 Payment Required if a free-plan user has hit the cap."""
    if user.plan == "premium":
        return
    used = get_upload_count(db, user.id)
    if used >= FREE_UPLOAD_LIMIT:
        raise HTTPException(
            status_code=402,
            detail=(
                f"You've reached the free plan limit of {FREE_UPLOAD_LIMIT} contracts. "
                f"Upgrade to Premium to keep uploading."
            ),
        )


def create_fake_order(db: Session, user: models.User, billing_cycle: str) -> dict:
    """Starts a simulated checkout: records a pending Payment row and
    returns an order_id for the frontend's payment page to reference."""
    if billing_cycle not in ("monthly", "yearly"):
        raise HTTPException(status_code=400, detail="billing_cycle must be 'monthly' or 'yearly'.")

    amount_inr = PREMIUM_PRICE_INR_MONTHLY if billing_cycle == "monthly" else PREMIUM_PRICE_INR_YEARLY
    order_id = f"cvt_order_{uuid.uuid4().hex[:20]}"

    payment = models.Payment(
        user_id=user.id, order_id=order_id, amount_inr=amount_inr,
        billing_cycle=billing_cycle, status="pending",
    )
    db.add(payment)
    db.commit()

    return {"order_id": order_id, "amount_inr": amount_inr, "billing_cycle": billing_cycle}


def _authorize_card(card_number: str | None, card_name: str | None, expiry: str | None, cvv: str | None) -> tuple[bool, str]:
    if not card_number or not card_name or not expiry or not cvv:
        raise HTTPException(status_code=400, detail="Card number, name, expiry, and CVV are all required.")
    digits = re.sub(r"\D", "", card_number)
    if len(digits) < 12 or len(digits) > 19:
        raise HTTPException(status_code=400, detail="Enter a valid card number.")
    if not card_name.strip():
        raise HTTPException(status_code=400, detail="Enter the name on the card.")
    if not EXPIRY_RE.match(expiry.strip()):
        raise HTTPException(status_code=400, detail="Enter expiry as MM/YY.")
    if not re.match(r"^\d{3,4}$", cvv.strip()):
        raise HTTPException(status_code=400, detail="Enter a valid CVV.")
    detail = f"Card ending {digits[-4:]}"
    approved = digits != DECLINE_TEST_CARD
    return approved, detail


def _authorize_upi(upi_id: str | None) -> tuple[bool, str]:
    if not upi_id or not UPI_RE.match(upi_id.strip()):
        raise HTTPException(status_code=400, detail="Enter a valid UPI ID (e.g. yourname@bank).")
    upi_id = upi_id.strip()
    approved = upi_id.lower() != DECLINE_UPI_ID
    return approved, f"UPI: {upi_id}"


def _authorize_netbanking(bank_name: str | None) -> tuple[bool, str]:
    if not bank_name or not bank_name.strip():
        raise HTTPException(status_code=400, detail="Select a bank to continue.")
    bank_name = bank_name.strip()
    approved = bank_name != DECLINE_BANK_NAME
    return approved, f"Netbanking: {bank_name}"


def _authorize_qr() -> tuple[bool, str]:
    # No user-entered fields for QR — the "scan" happens on the buyer's
    # phone in a real flow, so this always succeeds in the simulation.
    return True, "QR code payment"


def pay_fake_order(
    db: Session, user: models.User, order_id: str, method: str,
    card_number: str | None = None, card_name: str | None = None,
    expiry: str | None = None, cvv: str | None = None,
    upi_id: str | None = None, bank_name: str | None = None,
) -> dict:
    """Simulates authorizing a payment via the chosen method. Performs
    only basic format validation (this is a fake gateway, not a real
    one) plus one deliberately-scripted decline case per method so the
    failure path can be demonstrated too."""
    if method not in VALID_METHODS:
        raise HTTPException(status_code=400, detail=f"method must be one of {VALID_METHODS}.")

    payment = (
        db.query(models.Payment)
        .filter(models.Payment.order_id == order_id, models.Payment.user_id == user.id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Order not found.")
    if payment.status == "paid":
        raise HTTPException(status_code=400, detail="This order has already been paid.")

    if method == "card":
        approved, detail = _authorize_card(card_number, card_name, expiry, cvv)
    elif method == "upi":
        approved, detail = _authorize_upi(upi_id)
    elif method == "netbanking":
        approved, detail = _authorize_netbanking(bank_name)
    else:
        approved, detail = _authorize_qr()

    payment.method = method
    payment.detail = detail

    if not approved:
        payment.status = "declined"
        db.commit()
        raise HTTPException(
            status_code=402,
            detail="Payment was declined. This is a scripted test case for the decline flow — try different details.",
        )

    payment.status = "paid"
    user.plan = "premium"
    db.add(models.AuditLog(
        user_id=user.id, action="premium_upgrade_paid",
        details={
            "order_id": order_id, "amount_inr": payment.amount_inr,
            "billing_cycle": payment.billing_cycle, "method": method, "detail": detail,
            "gateway": "simulated",
        },
    ))
    db.commit()
    db.refresh(user)

    return get_billing_status(db, user)
