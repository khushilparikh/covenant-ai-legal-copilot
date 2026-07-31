"""
Module 10 (Contract Knowledge Base) + Module 12 (Clause Search Engine):
generates embeddings for clauses and performs semantic similarity search.
Also backs the retrieval step of Module 11 (Chat With Contract) — the
Ollama LLM only ever answers using clauses retrieved here, so responses
stay grounded in the actual contract instead of hallucinating terms.

Primary path: sentence-transformers (all-MiniLM-L6-v2) + ChromaDB, persisted
to disk. If those packages aren't installed, falls back to a TF-IDF +
cosine-similarity in-memory index so semantic search still works (with
lower recall on paraphrased queries) without requiring the ~90MB model
download — useful for a first run before `pip install -r requirements.txt`
finishes.
"""
import os
from functools import lru_cache

CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "chroma_store")


class EmbeddingStore:
    """Backend-agnostic wrapper: prefers sentence-transformers + ChromaDB,
    falls back to scikit-learn TF-IDF if those aren't installed."""

    def __init__(self):
        self.backend = None
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.client = chromadb.PersistentClient(path=CHROMA_DIR)
            self.collection = self.client.get_or_create_collection("clauses")
            self.backend = "sentence-transformers+chroma"
        except ImportError:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self.vectorizer = TfidfVectorizer(stop_words="english")
            self._docs = {}  # id -> {"text":..., "metadata":...}
            self._matrix = None
            self.backend = "tfidf_fallback"

    # -- write path --------------------------------------------------
    def upsert_clauses(self, contract_id: str, clauses: list[dict]):
        """clauses: [{id, text, clause_type, risk_score, clause_number}, ...]"""
        ids = [f"{contract_id}:{c['id']}" for c in clauses]
        texts = [c["text"] for c in clauses]
        metadatas = [
            {"contract_id": contract_id, "clause_type": c.get("clause_type", ""),
             "risk_score": c.get("risk_score", 0), "clause_number": c.get("clause_number", "")}
            for c in clauses
        ]

        if self.backend == "sentence-transformers+chroma":
            embeddings = self.model.encode(texts).tolist()
            self.collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        else:
            for _id, text, meta in zip(ids, texts, metadatas):
                self._docs[_id] = {"text": text, "metadata": meta}
            self._rebuild_tfidf_index()

    def _rebuild_tfidf_index(self):
        if not self._docs:
            return
        corpus = [d["text"] for d in self._docs.values()]
        self._matrix = self.vectorizer.fit_transform(corpus)
        self._doc_ids = list(self._docs.keys())

    # -- read path ----------------------------------------------------
    def search(self, query: str, contract_id: str | None = None, top_k: int = 5) -> list[dict]:
        if self.backend == "sentence-transformers+chroma":
            where = {"contract_id": contract_id} if contract_id else None
            q_emb = self.model.encode([query]).tolist()
            res = self.collection.query(query_embeddings=q_emb, n_results=top_k, where=where)
            out = []
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                out.append({"text": doc, "metadata": meta, "score": round(1 - dist, 3)})
            return out
        else:
            from sklearn.metrics.pairwise import cosine_similarity

            if self._matrix is None:
                return []
            q_vec = self.vectorizer.transform([query])
            sims = cosine_similarity(q_vec, self._matrix)[0]
            ranked = sorted(zip(self._doc_ids, sims), key=lambda x: x[1], reverse=True)
            out = []
            for doc_id, score in ranked:
                meta = self._docs[doc_id]["metadata"]
                if contract_id and meta["contract_id"] != contract_id:
                    continue
                out.append({"text": self._docs[doc_id]["text"], "metadata": meta, "score": round(float(score), 3)})
                if len(out) >= top_k:
                    break
            return out


@lru_cache(maxsize=1)
def get_embedding_store() -> "EmbeddingStore":
    return EmbeddingStore()
