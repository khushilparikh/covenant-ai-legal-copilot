# Covenant Backend — AI Legal Copilot Platform

FastAPI + PostgreSQL backend implementing Modules 1–15 of the SRS. Real,
trained ML models handle clause classification and risk scoring; NLP
handles entity extraction and semantic search; Ollama (local LLM) handles
the open-ended generation (summaries, chat answers, redline suggestions).

## What's ML/NLP here (for your project report)

| Module | Technique | File |
|---|---|---|
| Clause Classification (4) | TF-IDF + Logistic Regression, 11 classes, trained on `data/clause_training_data.csv` | `app/ml/clause_classifier.py`, `train_clause_classifier.py` |
| Risk Assessment (7) | Engineered features (regex/rule-based) → Gradient Boosted Regression Trees | `app/ml/risk_scorer.py`, `train_risk_model.py`, `feature_extraction.py` |
| Document Intelligence (2) | spaCy NER (dates/orgs/money) + regex for contract-specific fields (governing law, notice periods) | `app/ml/entity_extractor.py` |
| Clause Search / Knowledge Base (10, 12) | Sentence embeddings (`all-MiniLM-L6-v2`) + ChromaDB vector search; TF-IDF cosine-similarity fallback if those packages aren't installed | `app/ml/embeddings.py` |
| Contract Comparison (9) | TF-IDF + cosine similarity clause matching across versions | `app/services/comparison_service.py` |
| Summary / Chat / Redlining (5, 8, 11) | Retrieval-Augmented Generation: embeddings retrieve relevant clauses → Ollama (Llama 3 8B) generates grounded text | `app/ml/llm_client.py` |

The classifier and risk model were trained and evaluated in this
repository (see `app/ml/artifacts/metrics.json` and `risk_metrics.json`
after training) — 95.1% test accuracy on clause classification, R²=0.906
on risk scoring.

## 1. Prerequisites

- Python 3.11+
- PostgreSQL (already installed locally, per your setup)
- [Ollama](https://ollama.com) running locally, with a model pulled:
  ```
  ollama pull llama3:8b
  ollama serve
  ```
  The app still works without Ollama running — it falls back to
  extractive summaries and shows the top retrieved clause directly for
  chat — but summaries/chat/redlining are far better with it.

## 2. Set up PostgreSQL

```sql
CREATE DATABASE covenant;
```

## 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional but recommended
```

## 4. Configure environment

```bash
cp .env.example .env
# edit .env — set DATABASE_URL to match your Postgres user/password
```

## 5. Train the ML models

The trained model artifacts aren't committed (they're regenerated from the
training scripts, which is also better practice for a project report —
you can show accuracy/loss and regenerate on demand):

```bash
python -m app.ml.train_clause_classifier
python -m app.ml.train_risk_model
```

This prints accuracy/precision/recall (classifier) and MAE/R² (risk model)
and saves artifacts to `app/ml/artifacts/`.

## 6. Create the schema + demo login

```bash
python -m app.db.seed
```

This creates all tables and a demo admin account:
`admin@covenant.dev` / `ChangeMe123!`

(Alembic is also configured under `alembic/` if you want versioned
migrations going forward — `alembic revision --autogenerate -m "..."` then
`alembic upgrade head` — but `seed.py`'s `create_all()` is enough to get
started.)

## 7. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

## Typical flow to test end-to-end

1. `POST /api/auth/login` with the demo credentials → copy `access_token`
2. `POST /api/contracts/upload` with a PDF/DOCX contract (Bearer auth) →
   runs the full pipeline: text extraction → clause segmentation →
   ML classification → ML risk scoring → NLP entity extraction →
   embedding indexing → (LLM or extractive) summary
3. `GET /api/contracts/{id}` → full analysis
4. `POST /api/compliance/{id}/run` → compliance audit vs. the seeded
   playbook rules
5. `POST /api/chat/ask` with `{"contract_id": ..., "question": "..."}` →
   RAG-grounded answer
6. `GET /api/dashboard/summary` → the numbers behind Module 15

## Project structure

```
app/
  main.py                 FastAPI app + router wiring
  core/                   settings, JWT/password auth
  db/                      SQLAlchemy models, session, seed script
  ml/                      all ML/NLP: classifiers, risk model, NER,
                           embeddings, LLM client, training scripts
  schemas/                 Pydantic request/response models
  services/                business logic orchestrating ML + DB
  api/routes/               one router per SRS module group
data/                       synthetic training data generators + CSVs
alembic/                    optional versioned migrations
```

## Note on scope

This is Phase 2 of the build (backend core). The Phase 1 UI/UX preview
(`covenant_ui.jsx`) is a design reference with mock data — wiring the real
React app to these endpoints (auth, file upload, live dashboard numbers,
etc.) is the next phase.
