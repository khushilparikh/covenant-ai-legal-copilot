"""
Loads the trained clause classification model and exposes a simple
classify() API used by the ingestion pipeline (Module 4: Clause
Classification).
"""
import os
from functools import lru_cache

import joblib
import numpy as np

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "clause_classifier.joblib")
ENCODER_PATH = os.path.join(ARTIFACT_DIR, "label_encoder.joblib")


class ClauseClassifier:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Clause classifier not trained yet. Run: "
                "python -m app.ml.train_clause_classifier"
            )
        self.pipeline = joblib.load(MODEL_PATH)
        self.encoder = joblib.load(ENCODER_PATH)

    def classify(self, text: str, top_k: int = 3) -> dict:
        """Returns predicted clause type, confidence, and the top_k ranked classes."""
        proba = self.pipeline.predict_proba([text])[0]
        order = np.argsort(proba)[::-1]
        top = [
            {"label": self.encoder.inverse_transform([i])[0], "confidence": round(float(proba[i]) * 100, 1)}
            for i in order[:top_k]
        ]
        return {
            "label": top[0]["label"],
            "confidence": top[0]["confidence"],
            "top_k": top,
        }

    def classify_batch(self, texts: list[str]) -> list[dict]:
        proba_matrix = self.pipeline.predict_proba(texts)
        results = []
        for proba in proba_matrix:
            order = np.argsort(proba)[::-1]
            best = order[0]
            results.append({
                "label": self.encoder.inverse_transform([best])[0],
                "confidence": round(float(proba[best]) * 100, 1),
            })
        return results


@lru_cache(maxsize=1)
def get_classifier() -> "ClauseClassifier":
    """Cached singleton so the model is loaded from disk once per process."""
    return ClauseClassifier()
