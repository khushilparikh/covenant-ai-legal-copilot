import io
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.core.config import get_settings
from app.db import models
from app.db.database import get_db
from app.schemas.contract import ContractDetail, ContractStatusUpdate, ContractSummary
from app.services.billing_service import enforce_upload_limit
from app.services.ingestion_service import ingest_contract
from app.services.report_service import generate_contract_report_pdf

router = APIRouter(prefix="/api/contracts", tags=["Contracts"])
settings = get_settings()

VALID_STATUSES = {s.value for s in models.ReviewStatus}


@router.post("/upload", response_model=ContractDetail)
async def upload_contract(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    enforce_upload_limit(db, user)

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.MAX_UPLOAD_MB}MB upload limit.")

    contract = ingest_contract(
        db=db, filename=file.filename, file_bytes=file_bytes,
        uploaded_by_id=user.id, upload_dir=settings.UPLOAD_DIR,
    )
    return contract


@router.get("", response_model=list[ContractSummary])
def list_contracts(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    query = db.query(models.Contract).filter(models.Contract.uploaded_by_id == user.id)
    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(VALID_STATUSES)}.")
        query = query.filter(models.Contract.status == status_filter)
    return query.order_by(models.Contract.created_at.desc()).all()


@router.get("/{contract_id}", response_model=ContractDetail)
def get_contract(contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_contract(db, contract_id, user)


@router.patch("/{contract_id}/status", response_model=ContractDetail)
def update_status(
    contract_id: str, payload: ContractStatusUpdate,
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(VALID_STATUSES)}.")

    contract = get_owned_contract(db, contract_id, user)

    previous = contract.status.value
    contract.status = models.ReviewStatus(payload.status)
    db.add(models.AuditLog(
        contract_id=contract.id, user_id=user.id, action="status_changed",
        details={"from": previous, "to": payload.status},
    ))
    db.commit()
    db.refresh(contract)
    return contract


@router.get("/{contract_id}/export/pdf")
def export_contract_pdf(
    contract_id: str, db: Session = Depends(get_db), user: models.User = Depends(get_current_user),
):
    """Downloads a PDF report covering everything extracted/inferred about
    the contract: metadata, executive summary, risk flags, the full
    clause-by-clause breakdown, and compliance audit results if one has
    been run."""
    contract = get_owned_contract(db, contract_id, user)

    compliance_rows = (
        db.query(models.ComplianceResult)
        .filter(models.ComplianceResult.contract_id == contract.id)
        .all()
    )
    rule_map = {r.id: r.name for r in db.query(models.PlaybookRule).all()}
    compliance_results = [
        SimpleNamespace(
            rule_name=rule_map.get(r.rule_id, "Unknown rule"),
            status=r.status.value,
            reasoning=r.reasoning,
        )
        for r in compliance_rows
    ]

    pdf_bytes = generate_contract_report_pdf(contract, compliance_results)
    filename = f"{contract.display_code}_report.pdf"

    db.add(models.AuditLog(
        contract_id=contract.id, user_id=user.id, action="report_exported",
        details={"format": "pdf"},
    ))
    db.commit()

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
