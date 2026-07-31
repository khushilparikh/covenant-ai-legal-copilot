"""
Module 9: Contract Comparison. Matches clauses between two contract
versions by (clause_type + text similarity) rather than clause_number
alone, since renumbering between drafts is common. Uses TF-IDF cosine
similarity for the match (fast, no LLM required); a match above
SIMILARITY_MATCH_THRESHOLD is treated as "the same clause, possibly
modified"; below it, the clause is treated as added/removed.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.db import models

SIMILARITY_MATCH_THRESHOLD = 0.35
IDENTICAL_THRESHOLD = 0.97


def compare_contracts(contract_a: models.Contract, contract_b: models.Contract) -> dict:
    clauses_a = contract_a.clauses
    clauses_b = contract_b.clauses

    if not clauses_a or not clauses_b:
        return {"added": [], "removed": [], "modified": []}

    corpus = [c.text for c in clauses_a] + [c.text for c in clauses_b]
    vectorizer = TfidfVectorizer(stop_words="english").fit(corpus)
    vecs_a = vectorizer.transform([c.text for c in clauses_a])
    vecs_b = vectorizer.transform([c.text for c in clauses_b])
    sim_matrix = cosine_similarity(vecs_a, vecs_b)

    matched_b_indices = set()
    added, removed, modified = [], [], []

    for i, clause_a in enumerate(clauses_a):
        best_j = sim_matrix[i].argmax()
        best_score = sim_matrix[i][best_j]
        if best_score >= SIMILARITY_MATCH_THRESHOLD:
            matched_b_indices.add(best_j)
            if best_score < IDENTICAL_THRESHOLD:
                modified.append({
                    "clause": f"{clause_a.clause_number} {clause_a.clause_type}",
                    "a": clause_a.text[:200],
                    "b": clauses_b[best_j].text[:200],
                    "similarity": round(float(best_score), 3),
                    "risk_change": clauses_b[best_j].risk_score - clause_a.risk_score,
                })
        else:
            removed.append(f"{clause_a.clause_number} {clause_a.clause_type} — {clause_a.text[:80]}")

    for j, clause_b in enumerate(clauses_b):
        if j not in matched_b_indices:
            added.append(f"{clause_b.clause_number} {clause_b.clause_type} — {clause_b.text[:80]}")

    return {"added": added, "removed": removed, "modified": modified}
