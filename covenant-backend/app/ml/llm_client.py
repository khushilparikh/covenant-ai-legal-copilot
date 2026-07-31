"""
Thin client for the locally-running Ollama server, used for the
generative pieces of the pipeline that are genuinely open-ended
(Module 5 Contract Summary, Module 8 AI Redlining, Module 11 Chat With
Contract). Everything upstream of this file — clause classification, risk
scoring, entity extraction, semantic search — is deterministic, inspectable
ML/NLP; the LLM is only used for well-grounded natural-language generation
where the classifiers above have already narrowed the problem.

Requires Ollama running locally: https://ollama.com
    ollama pull llama3:8b
    ollama serve   (defaults to http://localhost:11434)
"""
import json
import os

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")
REQUEST_TIMEOUT = 60.0


class OllamaUnavailableError(Exception):
    pass


def _generate(prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            resp = client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()["response"].strip()
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise OllamaUnavailableError(
            f"Could not reach Ollama at {OLLAMA_BASE_URL}. "
            f"Make sure `ollama serve` is running and `{OLLAMA_MODEL}` is pulled."
        ) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise OllamaUnavailableError(
                f"Model `{OLLAMA_MODEL}` isn't available on your Ollama server. "
                f"Run `ollama pull {OLLAMA_MODEL}` first."
            ) from e
        raise OllamaUnavailableError(
            f"Ollama returned an unexpected error ({e.response.status_code})."
        ) from e


SUMMARY_SYSTEM_PROMPT = (
    "You are a contract analysis assistant. Summarize using ONLY the clause "
    "text provided. Never invent dates, amounts, or parties not present in "
    "the text. Keep the summary factual and concise."
)

CHAT_SYSTEM_PROMPT = (
    "You are Covenant, a contract Q&A assistant. Answer the user's question "
    "using ONLY the retrieved clauses provided below. If the answer isn't "
    "in the retrieved clauses, say the contract doesn't appear to address "
    "it — never guess. Always cite the clause number(s) you used, e.g. "
    "(see \u00a74.2)."
)

REDLINE_SYSTEM_PROMPT = (
    "You are a contract redlining assistant. Given a clause and the reason "
    "it was flagged as risky, propose a revised version that mitigates the "
    "risk while staying commercially reasonable and consistent with the "
    "clause's original intent. Return strictly valid JSON with keys "
    "'suggested_text' and 'reason', nothing else."
)


def summarize_contract(clause_texts: list[str]) -> str:
    joined = "\n\n".join(f"- {c}" for c in clause_texts[:40])
    prompt = f"Contract clauses:\n{joined}\n\nWrite a 4-6 sentence executive summary covering key obligations, dates, and risks."
    return _generate(prompt, system=SUMMARY_SYSTEM_PROMPT, temperature=0.1)


def answer_contract_question(question: str, retrieved_clauses: list[dict]) -> dict:
    context = "\n\n".join(
        f"[{c['metadata']['clause_number']}] {c['text']}" for c in retrieved_clauses
    )
    prompt = f"Retrieved clauses:\n{context}\n\nQuestion: {question}\n\nAnswer:"
    answer = _generate(prompt, system=CHAT_SYSTEM_PROMPT, temperature=0.1)
    return {
        "answer": answer,
        "sources": [c["metadata"]["clause_number"] for c in retrieved_clauses],
    }


def generate_redline(clause_text: str, flag_reasons: list[str]) -> dict:
    prompt = (
        f"Original clause:\n{clause_text}\n\n"
        f"Flagged issues: {'; '.join(flag_reasons)}\n\n"
        f"Propose a revised clause as JSON: {{\"suggested_text\": ..., \"reason\": ...}}"
    )
    raw = _generate(prompt, system=REDLINE_SYSTEM_PROMPT, temperature=0.2)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"suggested_text": raw, "reason": "Model did not return structured JSON; showing raw output."}


def is_ollama_available() -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
