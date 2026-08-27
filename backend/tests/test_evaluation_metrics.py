"""Tests for the deterministic half of the offline evaluation.

The judged metrics are an LLM's opinion and are not asserted here; `score_retrieval` is
what decides whether a retrieval change looks like an improvement, so it has to keep
meaning what it claims.
"""
import json
from pathlib import Path

from evaluation.offline_eval import GOLDEN, score_retrieval

EXPECTED = ["Protein PTC 2022.pdf", "Energy PTC 2022.pdf"]


def test_reaching_an_expected_document_counts_as_a_hit():
    hit, mrr = score_retrieval(EXPECTED, ["Cardio PTC 2022.pdf", "Protein PTC 2022.pdf"])

    assert hit == 1.0
    assert mrr == 0.5


def test_the_rank_of_the_first_expected_document_is_what_counts():
    """Two runs that both find the document are not equally good: MRR is the part of the
    score that notices which one put it first."""
    top_hit, top_mrr = score_retrieval(EXPECTED, ["Protein PTC 2022.pdf", "Cardio PTC 2022.pdf"])
    late_hit, late_mrr = score_retrieval(
        EXPECTED, ["Cardio PTC 2022.pdf", "Stretching PTC 2022.pdf", "Energy PTC 2022.pdf"]
    )

    assert top_hit == late_hit == 1.0  # both found it, only the rank differs
    assert top_mrr > late_mrr


def test_retrieving_only_unrelated_documents_scores_zero():
    assert score_retrieval(EXPECTED, ["Cardio PTC 2022.pdf", "Stretching PTC 2022.pdf"]) == (0.0, 0.0)


def test_an_unlabelled_question_never_counts_as_a_hit():
    """Silently scoring 1.0 for a question with no expected_sources would hide a gap in
    the dataset behind a perfect result."""
    assert score_retrieval([], ["Protein PTC 2022.pdf"]) == (0.0, 0.0)


def test_every_golden_question_carries_expected_sources():
    questions = json.loads(Path(GOLDEN).read_text(encoding="utf-8"))["questions"]

    unlabelled = [q["id"] for q in questions if not q.get("expected_sources")]

    assert not unlabelled, f"questions without expected_sources: {unlabelled}"
