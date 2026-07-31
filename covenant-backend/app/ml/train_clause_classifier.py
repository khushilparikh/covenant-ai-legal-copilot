"""
Trains the clause classification model used by Module 4 (Clause Classification).

Pipeline: TF-IDF (word + char n-grams) -> Logistic Regression (multinomial).
Logistic Regression is used (rather than a black-box model) because it
outputs calibrated class probabilities directly, which the API surfaces as
the "confidence score" required by the SRS (Module 4 output).

Run:
    python -m app.ml.train_clause_classifier

Outputs (saved to app/ml/artifacts/):
    clause_classifier.joblib   -> sklearn Pipeline (vectorizer + model)
    label_encoder.joblib       -> LabelEncoder for class <-> id mapping
    metrics.json                -> accuracy / per-class precision-recall for the report
"""
import json
import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "clause_training_data.csv")
ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def build_pipeline():
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.9,
        sublinear_tf=True,
        stop_words="english",
    )
    clf = LogisticRegression(
        max_iter=2000,
        C=4.0,
        class_weight="balanced",
    )
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} labeled examples, {df['label'].nunique()} classes.")

    encoder = LabelEncoder()
    y = encoder.fit_transform(df["label"])
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(
        y_test, y_pred, target_names=encoder.classes_, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_test, y_pred).tolist()

    print(f"\nTest accuracy: {acc:.3f}\n")
    print(classification_report(y_test, y_pred, target_names=encoder.classes_, zero_division=0))

    # Refit on full dataset for the deployed model (common practice once
    # held-out metrics have been recorded).
    final_pipeline = build_pipeline()
    final_pipeline.fit(df["text"], y)

    joblib.dump(final_pipeline, os.path.join(ARTIFACT_DIR, "clause_classifier.joblib"))
    joblib.dump(encoder, os.path.join(ARTIFACT_DIR, "label_encoder.joblib"))
    with open(os.path.join(ARTIFACT_DIR, "metrics.json"), "w") as f:
        json.dump(
            {"test_accuracy": acc, "classes": list(encoder.classes_),
             "classification_report": report, "confusion_matrix": cm},
            f, indent=2,
        )
    print(f"\nSaved model artifacts to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
