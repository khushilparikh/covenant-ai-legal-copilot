"""
Rule/regex-based feature extraction from clause text.

These engineered features feed the risk scoring model (see risk_scorer.py).
Keeping extraction separate from the model means the model can be retrained
on new feature distributions without touching the NLP parsing logic, and the
same features are reused for the "reasoning" shown to reviewers in the UI.
"""
import re

CAP_PATTERNS = [
    r"shall not exceed", r"aggregate liability.{0,40}(shall|is) (be )?limited",
    r"limited to", r"capped at",
]
UNCAPPED_PATTERNS = [
    r"no limit(ation)? (on|of) liability", r"unlimited liability",
    r"shall not apply", r"in no event.{0,20}(exclude|limit)",
]
CURE_PATTERNS = [r"cure period", r"remains? uncured", r"opportunity to cure", r"fails? to cure"]
UNILATERAL_PATTERNS = [r"\b(sole|absolute) discretion\b", r"\bmay\b.{0,15}\bunilaterally\b",
                        r"at its sole option"]
MUTUAL_PATTERNS = [r"either party", r"each party", r"both parties"]
SURVIVAL_PATTERNS = [r"survive", r"shall continue.{0,20}after termination"]
NEGLIGENCE_CARVEOUT_PATTERNS = [r"gross negligence", r"willful misconduct", r"fraud"]
PLAYBOOK_REF_PATTERNS = [r"standard", r"in accordance with", r"applicable law", r"policy"]

NOTICE_DAYS_RE = re.compile(
    r"(\d{1,3})\s*\)?\s*(?:calendar\s+)?days?\s*(?:prior\s+)?(?:written\s+)?notice", re.IGNORECASE
)
MONTHS_RE = re.compile(r"(\d{1,2})\s*\(?\s*months?\)?", re.IGNORECASE)


def _any_match(patterns, text_lower):
    return any(re.search(p, text_lower) for p in patterns)


def extract_features(text: str, clause_type: str) -> dict:
    t = text.lower()

    notice_days = 0
    m = NOTICE_DAYS_RE.search(text)
    if m:
        notice_days = int(m.group(1))
    else:
        m2 = MONTHS_RE.search(text)
        if m2:
            notice_days = int(m2.group(1)) * 30

    has_cap = _any_match(CAP_PATTERNS, t)
    is_uncapped = (not has_cap) and _any_match(UNCAPPED_PATTERNS, t)
    is_unilateral = _any_match(UNILATERAL_PATTERNS, t)
    is_mutual = (not is_unilateral) and _any_match(MUTUAL_PATTERNS, t)

    return {
        "clause_type": clause_type,
        "has_cap": int(has_cap),
        "is_uncapped": int(is_uncapped),
        "has_cure_period": int(_any_match(CURE_PATTERNS, t)),
        "is_unilateral": int(is_unilateral),
        "is_mutual": int(is_mutual),
        "has_survival_clause": int(_any_match(SURVIVAL_PATTERNS, t)),
        "notice_days": min(notice_days, 365),
        "has_negligence_carveout": int(_any_match(NEGLIGENCE_CARVEOUT_PATTERNS, t)),
        "references_playbook_standard": int(_any_match(PLAYBOOK_REF_PATTERNS, t)),
    }
