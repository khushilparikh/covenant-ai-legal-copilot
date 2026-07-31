"""
Loads the trained risk scoring model and exposes score_clause() /
score_contract() used by Module 7 (AI Risk Assessment).
"""
import os
from functools import lru_cache

import joblib
import pandas as pd

from app.ml.feature_extraction import extract_features

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "risk_model.joblib")

FEATURE_ORDER = [
    "clause_type", "has_cap", "is_uncapped", "has_cure_period", "is_unilateral",
    "is_mutual", "has_survival_clause", "notice_days", "has_negligence_carveout",
    "references_playbook_standard",
]

# Human-readable reasons shown to the reviewer, keyed to the feature that
# triggered them. This is what Module 7 exposes as "reasoning" alongside
# the numeric score.
FLAG_EXPLANATIONS = {
    "is_uncapped": ("high", "No cap found on liability/indemnity exposure."),
    "is_unilateral": ("medium", "Right or obligation appears one-sided (sole discretion language)."),
    "no_cure_period": ("medium", "No cure period found before termination/default rights trigger."),
    "short_notice": ("medium", "Notice period is shorter than the 30-day playbook standard."),
    "no_negligence_carveout": ("low", "No explicit carve-out for gross negligence / willful misconduct."),
}


class RiskScorer:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "Risk model not trained yet. Run: python -m app.ml.train_risk_model"
            )
        self.pipeline = joblib.load(MODEL_PATH)

    def score_clause(self, text: str, clause_type: str) -> dict:
        features = extract_features(text, clause_type)
        row = pd.DataFrame([features])[FEATURE_ORDER]
        score = float(self.pipeline.predict(row)[0])
        score = max(0, min(100, round(score)))

        flags = []
        if features["is_uncapped"]:
            flags.append(FLAG_EXPLANATIONS["is_uncapped"])
        if features["is_unilateral"]:
            flags.append(FLAG_EXPLANATIONS["is_unilateral"])
        if not features["has_cure_period"] and clause_type == "Termination":
            flags.append(FLAG_EXPLANATIONS["no_cure_period"])
        if 0 < features["notice_days"] < 30:
            flags.append(FLAG_EXPLANATIONS["short_notice"])
        if not features["has_negligence_carveout"] and clause_type in ("Liability", "Indemnification"):
            flags.append(FLAG_EXPLANATIONS["no_negligence_carveout"])

        severity = "high" if score >= 61 else "medium" if score >= 31 else "low"
        return {
            "risk_score": score,
            "severity": severity,
            "features": features,
            "flags": [{"severity": s, "reason": r} for s, r in flags],
        }

    def score_contract(self, clause_scores: list[int]) -> int:
        """Aggregate contract-level risk from its clause-level scores.
        Weighted toward the worst clauses rather than a flat mean, since a
        single severe clause should dominate the contract's overall risk."""
        if not clause_scores:
            return 0
        sorted_scores = sorted(clause_scores, reverse=True)
        top_n = sorted_scores[: max(1, len(sorted_scores) // 3)]
        return round(0.6 * (sum(top_n) / len(top_n)) + 0.4 * (sum(sorted_scores) / len(sorted_scores)))


@lru_cache(maxsize=1)
def get_risk_scorer() -> "RiskScorer":
    return RiskScorer()
