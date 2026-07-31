"""
Module 6: Compliance Audit Engine.

Evaluates a contract's clauses against the organization's active playbook
rules (see PlaybookRule) and records a ComplianceResult per rule. Rule
evaluation reuses the same engineered features the risk model consumes
(app.ml.feature_extraction), so a rule like "requires liability cap" checks
the same `has_cap` signal the risk model was trained on rather than
duplicating logic.
"""
from sqlalchemy.orm import Session

from app.db import models
from app.ml.feature_extraction import extract_features

DEFAULT_PLAYBOOK = [
    dict(name="Liability cap required", applies_to_clause_type="Liability",
         rule_kind="requires_cap", description="Liability clauses must specify a cap on damages."),
    dict(name="Minimum termination notice: 30 days", applies_to_clause_type="Termination",
         rule_kind="min_notice_days", threshold_value="30",
         description="Termination clauses must provide at least 30 days' notice."),
    dict(name="Data breach notification within 48 hours", applies_to_clause_type="Data_Privacy",
         rule_kind="max_notice_days", threshold_value="48",
         description="Data privacy clauses must commit to breach notification within 48 hours."),
    dict(name="Confidentiality must survive termination", applies_to_clause_type="Confidentiality",
         rule_kind="requires_survival", description="Confidentiality obligations must explicitly survive termination."),
    dict(name="Indemnification carve-out for gross negligence", applies_to_clause_type="Indemnification",
         rule_kind="requires_negligence_carveout", description="Indemnification clauses should carve out gross negligence / willful misconduct."),
]


def seed_default_playbook(db: Session):
    if db.query(models.PlaybookRule).count() > 0:
        return
    for rule in DEFAULT_PLAYBOOK:
        db.add(models.PlaybookRule(**rule))
    db.commit()


def _evaluate_rule(rule: models.PlaybookRule, clauses: list[models.Clause]) -> tuple[str, str, str | None]:
    matching = [c for c in clauses if c.clause_type == rule.applies_to_clause_type]
    if not matching:
        return "needs_review", f"No {rule.applies_to_clause_type} clause was found in this contract.", None

    clause = matching[0]
    features = extract_features(clause.text, clause.clause_type)

    if rule.rule_kind == "requires_cap":
        ok = bool(features["has_cap"]) and not features["is_uncapped"]
        reasoning = ("Liability is explicitly capped." if ok else
                     "No liability cap found — exposure may be unlimited.")
    elif rule.rule_kind == "min_notice_days":
        threshold = int(rule.threshold_value)
        ok = features["notice_days"] >= threshold
        reasoning = (f"Notice period is {features['notice_days']} days (>= {threshold} required)." if ok else
                     f"Notice period is {features['notice_days']} days, below the required {threshold}.")
    elif rule.rule_kind == "max_notice_days":
        threshold = int(rule.threshold_value)
        ok = 0 < features["notice_days"] <= threshold
        reasoning = (f"Breach notification window is {features['notice_days']}h (<= {threshold} required)." if ok else
                     f"Breach notification window is {features['notice_days']}h, exceeding the {threshold}h policy.")
    elif rule.rule_kind == "requires_survival":
        ok = bool(features["has_survival_clause"])
        reasoning = ("Survival language found." if ok else "No survival language found post-termination.")
    elif rule.rule_kind == "requires_negligence_carveout":
        ok = bool(features["has_negligence_carveout"])
        reasoning = ("Gross negligence / willful misconduct carve-out present." if ok else
                     "No carve-out for gross negligence or willful misconduct.")
    else:
        return "needs_review", "Unrecognized rule type.", clause.id

    return ("compliant" if ok else "non_compliant"), reasoning, clause.id


def run_compliance_audit(db: Session, contract: models.Contract) -> list[models.ComplianceResult]:
    seed_default_playbook(db)
    rules = db.query(models.PlaybookRule).filter(models.PlaybookRule.active == True).all()  # noqa: E712

    db.query(models.ComplianceResult).filter(models.ComplianceResult.contract_id == contract.id).delete()

    results = []
    for rule in rules:
        status, reasoning, clause_id = _evaluate_rule(rule, contract.clauses)
        result = models.ComplianceResult(
            contract_id=contract.id, rule_id=rule.id,
            status=models.ComplianceStatus(status), reasoning=reasoning,
            related_clause_id=clause_id,
        )
        db.add(result)
        results.append(result)

    overall = ("non_compliant" if any(r.status == models.ComplianceStatus.NON_COMPLIANT for r in results)
               else "needs_review" if any(r.status == models.ComplianceStatus.NEEDS_REVIEW for r in results)
               else "compliant")

    db.add(models.AuditLog(
        contract_id=contract.id, action="compliance_audit_run",
        details={"overall_status": overall, "rules_checked": len(results)},
    ))
    db.commit()
    return results
