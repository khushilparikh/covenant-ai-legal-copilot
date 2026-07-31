from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_contract
from app.db import models
from app.db.database import get_db
from app.ml.embeddings import get_embedding_store

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/semantic")
def semantic_search(
    q: str = Query(..., min_length=2),
    contract_id: str | None = None,
    limit: int = 8,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Module 12: semantic + clause-similarity search across the knowledge base,
    scoped to the requesting user's own contracts."""
    store = get_embedding_store()

    if contract_id:
        get_owned_contract(db, contract_id, user)  # 404s if the contract isn't the user's
        return store.search(q, contract_id=contract_id, top_k=limit)

    # No specific contract given — search across all of this user's own
    # contracts. The vector store itself isn't user-aware, so overfetch
    # and filter down to only contracts this user owns.
    owned_ids = {
        c.id for c in db.query(models.Contract.id)
        .filter(models.Contract.uploaded_by_id == user.id).all()
    }
    raw_results = store.search(q, contract_id=None, top_k=max(limit * 4, 20))
    filtered = [r for r in raw_results if r["metadata"].get("contract_id") in owned_ids]
    return filtered[:limit]


@router.get("/keyword")
def keyword_search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Plain keyword search fallback, scoped to the requesting user's own
    contracts."""
    matches = (
        db.query(models.Clause)
        .join(models.Contract, models.Clause.contract_id == models.Contract.id)
        .filter(models.Contract.uploaded_by_id == user.id, models.Clause.text.ilike(f"%{q}%"))
        .limit(25)
        .all()
    )
    return [
        {"contract_id": m.contract_id, "clause_number": m.clause_number,
         "clause_type": m.clause_type, "text": m.text}
        for m in matches
    ]
