"""
Orchestrates Modules 1-5 + 7 + 10: ingest a file end-to-end into a fully
analyzed Contract row with its Clause children.

Upload -> extract text -> segment clauses -> classify each clause (ML) ->
score risk per clause (ML) -> extract contract-level entities (NLP) ->
persist -> index clauses in the embedding store -> (optionally) generate
an LLM executive summary if Ollama is reachable.
"""
import os
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.ml.clause_classifier import get_classifier
from app.ml.embeddings import get_embedding_store
from app.ml.entity_extractor import extract_metadata
from app.ml.llm_client import OllamaUnavailableError, is_ollama_available, summarize_contract
from app.ml.risk_scorer import get_risk_scorer
from app.ml.text_extraction import extract_text, segment_into_clauses


def _next_display_code(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(models.Contract).count() + 1
    return f"CV-{year}-{count:04d}"


def _extractive_summary(clause_texts: list[str], max_sentences: int = 5) -> str:
    """Fallback used when Ollama isn't running: picks the highest-signal
    sentences (longest + earliest, cheap proxy for salience) rather than
    leaving the summary blank."""
    if not clause_texts:
        return "No clauses were extracted from this document."
    ranked = sorted(clause_texts, key=len, reverse=True)[:max_sentences]
    return " ".join(ranked)


def index_contract(contract: models.Contract) -> None:
    """(Re)index a contract's clauses in the embedding store."""
    if not contract.clauses:
        return
    get_embedding_store().upsert_clauses(contract.id, [
        {"id": c.id, "text": c.text, "clause_type": c.clause_type,
         "risk_score": c.risk_score, "clause_number": c.clause_number}
        for c in contract.clauses
    ])


def ingest_contract(db: Session, filename: str, file_bytes: bytes, uploaded_by_id: str | None,
                     upload_dir: str) -> models.Contract:
    classifier = get_classifier()
    scorer = get_risk_scorer()
    store = get_embedding_store()

    # 1. Persist the raw file
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 2. Extract text (Module 1)
    extraction = extract_text(filename, file_bytes)
    full_text = extraction["full_text"]
    if not full_text.strip():
        os.remove(file_path)
        raise HTTPException(
            status_code=422,
            detail="No readable text found. This looks like a scanned PDF and OCR is unavailable - "
                   "install Tesseract (https://github.com/UB-Mannheim/tesseract/wiki) or upload a text-based PDF/DOCX.",
        )

    # 3. Segment + classify + score each clause (Modules 3, 4, 7)
    raw_segments = segment_into_clauses(full_text)
    clause_rows: list[models.Clause] = []
    clause_texts_for_summary = []

    if raw_segments:
        classifications = classifier.classify_batch([s["text"] for s in raw_segments])
        for seg, cls in zip(raw_segments, classifications):
            risk = scorer.score_clause(seg["text"], cls["label"])
            clause = models.Clause(
                clause_number=seg["clause_number"],
                text=seg["text"],
                clause_type=cls["label"],
                classification_confidence=cls["confidence"],
                risk_score=risk["risk_score"],
                risk_severity=models.RiskSeverity(risk["severity"]),
            )
            clause.risk_flags = [
                models.RiskFlag(severity=models.RiskSeverity(f["severity"]), reason=f["reason"])
                for f in risk["flags"]
            ]
            clause_rows.append(clause)
            clause_texts_for_summary.append(seg["text"])

    # 4. Contract-level entity extraction (Module 2)
    metadata = extract_metadata(full_text)

    # 5. Contract-level risk aggregation
    contract_risk = scorer.score_contract([c.risk_score for c in clause_rows])

    # 6. Executive summary — LLM if available, extractive fallback otherwise
    if is_ollama_available():
        try:
            summary = summarize_contract(clause_texts_for_summary)
        except Exception:  # never let the LLM break an upload
            summary = _extractive_summary(clause_texts_for_summary)
    else:
        summary = _extractive_summary(clause_texts_for_summary)

    # 7. Persist Contract + Clauses
    contract = models.Contract(
        display_code=_next_display_code(db),
        title=metadata.get("title") or filename.rsplit(".", 1)[0],
        contract_type="General",
        counterparty=(metadata.get("parties") or [None])[0],
        filename=filename,
        file_path=file_path,
        page_count=extraction["page_count"],
        status=models.ReviewStatus.PENDING_REVIEW,
        risk_score=contract_risk,
        effective_date=metadata.get("effective_date"),
        expiry_date=metadata.get("expiry_date"),
        governing_law=metadata.get("governing_law"),
        payment_terms=metadata.get("payment_terms"),
        parties=metadata.get("parties"),
        monetary_values=metadata.get("monetary_values"),
        executive_summary=summary,
        uploaded_by_id=uploaded_by_id,
        clauses=clause_rows,
    )
    db.add(contract)
    db.flush()  # assigns contract.id without committing yet

    db.add(models.AuditLog(
        contract_id=contract.id, user_id=uploaded_by_id, action="uploaded",
        details={"filename": filename, "page_count": extraction["page_count"]},
    ))
    db.add(models.AuditLog(
        contract_id=contract.id, user_id=uploaded_by_id, action="ai_analyzed",
        details={"clauses_extracted": len(clause_rows), "contract_risk_score": contract_risk},
    ))
    db.commit()
    db.refresh(contract)

    # 8. Index clauses for semantic search / chat retrieval (Modules 10-12)
    try:
        index_contract(contract)
    except Exception as e:
        print(f"[ingest] indexing failed (contract still saved): {type(e).__name__}: {e}")

    return contract
