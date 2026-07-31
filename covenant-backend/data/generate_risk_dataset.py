"""
Generates a synthetic dataset of engineered clause features -> risk score
(0-100), used to train the risk scoring regression model (Module 7: AI
Risk Assessment).

Risk score is a function of clause type base severity, presence of
protective language (caps, cure periods, mutuality), presence of
aggravating language (uncapped, unilateral, sole discretion), and
extracted numeric terms (notice period length, liability cap duration).
This mirrors how a real risk model would be bootstrapped: rule-derived
labels used to train a model that then generalizes to unseen clause text
via its features, and can later be recalibrated against reviewer-corrected
labels once real audit data is collected.
"""
import csv
import random

random.seed(7)

CLAUSE_TYPES = ["Confidentiality", "Termination", "Liability", "Indemnification",
                "Payment", "Intellectual_Property", "Force_Majeure", "Non_Compete",
                "Arbitration", "Data_Privacy", "General"]

BASE_SEVERITY = {
    "Liability": 55, "Indemnification": 50, "Non_Compete": 48, "Termination": 40,
    "Data_Privacy": 45, "Force_Majeure": 25, "Confidentiality": 30, "Payment": 28,
    "Intellectual_Property": 35, "Arbitration": 32, "General": 20,
}


def make_row():
    clause_type = random.choice(CLAUSE_TYPES)
    base = BASE_SEVERITY[clause_type]

    has_cap = random.random() < 0.5          # liability/indemnity capped
    is_uncapped = (not has_cap) and random.random() < 0.6
    has_cure_period = random.random() < 0.5   # breach has a cure/notice period
    is_unilateral = random.random() < 0.35    # one-sided right (only one party benefits)
    is_mutual = (not is_unilateral) and random.random() < 0.6
    has_survival_clause = random.random() < 0.4
    notice_days = random.choice([0, 15, 30, 45, 60, 90])
    excludes_gross_negligence_carveout = random.random() < 0.5  # good: carve-out present
    references_playbook_standard = random.random() < 0.4

    score = base
    score += 22 if is_uncapped else (-10 if has_cap else 0)
    score += 12 if is_unilateral else (-6 if is_mutual else 0)
    score -= 8 if has_cure_period else 4
    score -= 6 if has_survival_clause else 0
    score -= 10 if excludes_gross_negligence_carveout else 6
    score -= 8 if references_playbook_standard else 0
    if notice_days == 0:
        score += 10
    elif notice_days < 30:
        score += 5
    elif notice_days >= 60:
        score -= 6

    score += random.gauss(0, 5)  # label noise, mirrors reviewer disagreement
    score = max(2, min(98, round(score)))

    return {
        "clause_type": clause_type,
        "has_cap": int(has_cap),
        "is_uncapped": int(is_uncapped),
        "has_cure_period": int(has_cure_period),
        "is_unilateral": int(is_unilateral),
        "is_mutual": int(is_mutual),
        "has_survival_clause": int(has_survival_clause),
        "notice_days": notice_days,
        "has_negligence_carveout": int(excludes_gross_negligence_carveout),
        "references_playbook_standard": int(references_playbook_standard),
        "risk_score": score,
    }


if __name__ == "__main__":
    rows = [make_row() for _ in range(1200)]
    with open("risk_training_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} rows for risk scoring model.")
