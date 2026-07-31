"""
Extracts contract-level metadata for Module 2 (Document Intelligence):
title, effective/expiry dates, parties, jurisdiction, monetary values,
notice periods, payment terms, governing law.

Uses spaCy's NER (PERSON/ORG/DATE/MONEY/GPE) when available for parties,
dates, and monetary values, layered with legal-contract-specific regex
for fields spaCy has no concept of (governing law, notice periods, defined
"Party" aliases). Falls back to pure regex if spaCy / the en_core_web_sm
model isn't installed, so the pipeline still runs without the extra
~500MB model download.
"""
import re
from datetime import datetime

try:
    import spacy
    _NLP = None
    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        _NLP = None
except ImportError:
    spacy = None
    _NLP = None

DATE_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    re.IGNORECASE,
)
MONEY_RE = re.compile(r"\$\s?[\d,]+(?:\.\d{2})?(?:\s?(?:USD|million|thousand))?", re.IGNORECASE)
GOVERNING_LAW_RE = re.compile(
    r"govern(?:ed|ing)\s+(?:by|in accordance with)\s+(?:the\s+)?laws?\s+of\s+([A-Z][\w\s]{2,40}?)(?:,|\.|\band\b|$)",
    re.IGNORECASE,
)
NOTICE_PERIOD_RE = re.compile(
    r"(\d{1,3})\s*\)?\s*(?:calendar\s+)?days?\s*(?:prior\s+)?(?:written\s+)?notice", re.IGNORECASE
)
PARTY_DEFINITION_RE = re.compile(
    r'([A-Z][\w&,\.\s]{2,60}?)\s*\(\s*["\']?(?:the\s+)?["\']?([A-Z][\w]+)["\']?\s*\)',
)
PAYMENT_TERMS_RE = re.compile(r"\bnet\s*(15|30|45|60|90)\b", re.IGNORECASE)
TITLE_HINT_RE = re.compile(
    r"^(.{0,120}?(?:Agreement|Contract|MSA|NDA|Lease|Order))\s*$", re.MULTILINE
)


def _spacy_dates_money_orgs(text: str):
    dates, money, orgs = [], [], []
    if _NLP is None:
        return dates, money, orgs
    doc = _NLP(text[:100000])  # cap for performance on very long contracts
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dates.append(ent.text)
        elif ent.label_ == "MONEY":
            money.append(ent.text)
        elif ent.label_ == "ORG":
            orgs.append(ent.text)
    return dates, money, orgs


def extract_metadata(text: str) -> dict:
    dates_regex = DATE_RE.findall(text)
    money_regex = MONEY_RE.findall(text)
    parties_defined = PARTY_DEFINITION_RE.findall(text)

    sp_dates, sp_money, sp_orgs = _spacy_dates_money_orgs(text)

    all_dates = list(dict.fromkeys(dates_regex + sp_dates))
    all_money = list(dict.fromkeys(money_regex + sp_money))

    gov_law_match = GOVERNING_LAW_RE.search(text)
    payment_match = PAYMENT_TERMS_RE.search(text)
    notice_matches = [int(m) for m in NOTICE_PERIOD_RE.findall(text)]
    title_match = TITLE_HINT_RE.search(text)

    _NON_PARTY_ALIASES = {"Agreement", "Contract", "Company", "Order", "Exhibit", "Section", "Schedule"}
    parties = list(dict.fromkeys(
        [alias for _, alias in parties_defined if alias not in _NON_PARTY_ALIASES] or sp_orgs[:4]
    ))

    return {
        "title": title_match.group(1).strip() if title_match else None,
        "parties": parties[:6],
        "effective_date": all_dates[0] if all_dates else None,
        "expiry_date": all_dates[1] if len(all_dates) > 1 else None,
        "all_dates_found": all_dates[:10],
        "governing_law": gov_law_match.group(1).strip() if gov_law_match else None,
        "monetary_values": all_money[:10],
        "payment_terms": f"Net {payment_match.group(1)}" if payment_match else None,
        "notice_periods_days": sorted(set(notice_matches)),
        "extraction_method": "spacy+regex" if _NLP else "regex_only",
    }
