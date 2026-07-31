"""
Trains the risk scoring model used by Module 7 (AI Risk Assessment).

Pipeline: one-hot encode clause_type + numeric/binary features ->
GradientBoostingRegressor -> risk_score (0-100).

A gradient-boosted tree model is used (rather than a fixed formula) so the
score can capture interaction effects between features (e.g. "uncapped
liability" matters far more when notice_days is also 0) and can be
recalibrated later against real reviewer-corrected risk labels without
rewriting scoring logic by hand.

Run:
    python -m app.ml.train_risk_model
"""
import json
import os

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "risk_training_data.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")

NUMERIC_FEATURES = [
    "has_cap", "is_uncapped", "has_cure_period", "is_unilateral", "is_mutual",
    "has_survival_clause", "notice_days", "has_negligence_carveout",
    "references_playbook_standard",
]
CATEGORICAL_FEATURES = ["clause_type"]


def build_pipeline():
    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ], remainder="passthrough")

    model = GradientBoostingRegressor(
        n_estimators=250, max_depth=3, learning_rate=0.06, random_state=42,
    )
    return Pipeline([("prep", preprocess), ("model", model)])


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df["risk_score"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    pred = pipeline.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    r2 = r2_score(y_test, pred)
    print(f"Risk model — MAE: {mae:.2f} points, R^2: {r2:.3f}")

    final_pipeline = build_pipeline()
    final_pipeline.fit(X, y)

    joblib.dump(final_pipeline, os.path.join(ARTIFACT_DIR, "risk_model.joblib"))
    with open(os.path.join(ARTIFACT_DIR, "risk_metrics.json"), "w") as f:
        json.dump({"mae": mae, "r2": r2, "n_train": len(X_train), "n_test": len(X_test)}, f, indent=2)
    print(f"Saved model artifacts to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
