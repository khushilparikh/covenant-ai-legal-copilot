from sqlalchemy.orm import Session

from app.db import models
from app.ml.embeddings import get_embedding_store
from app.ml.llm_client import answer_contract_question, is_ollama_available
from app.services.ingestion_service import index_contract


def _extractive_fallback_answer(question: str, retrieved: list[dict]) -> dict:
    """Used when Ollama isn't reachable: return the top retrieved clause
    verbatim rather than fabricating a generated answer."""
    if not retrieved:
        return {"answer": "I couldn't find a clause addressing that in this contract.", "sources": []}
    top = retrieved[0]
    return {
        "answer": f"(Ollama not running — showing the most relevant clause directly.) "
                  f"[{top['metadata']['clause_number']}] {top['text']}",
        "sources": [top["metadata"]["clause_number"]],
    }


def ask_contract(db: Session, contract: models.Contract, question: str) -> dict:
    store = get_embedding_store()
    if not store.has_contract(contract.id):
        index_contract(contract)  # index is in-memory in fallback mode; rebuild after restarts
    retrieved = store.search(question, contract_id=contract.id, top_k=5)

    if is_ollama_available():
        try:
            result = answer_contract_question(question, retrieved)
        except Exception:
            result = _extractive_fallback_answer(question, retrieved)
    else:
        result = _extractive_fallback_answer(question, retrieved)

    db.add(models.ChatMessage(contract_id=contract.id, role="user", content=question))
    db.add(models.ChatMessage(contract_id=contract.id, role="ai", content=result["answer"], sources=result["sources"]))
    db.commit()

    return result
