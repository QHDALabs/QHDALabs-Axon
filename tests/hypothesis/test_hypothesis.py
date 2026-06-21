"""Stage 4 tests — hypothesis.surface.

The structural guarantee under test: verification precedes discovery. The stage
accepts only VerificationResult, and only ACCEPTED results become hypotheses."""

import pytest

from axon.types import (
    CandidateRelation,
    Hypothesis,
    RelationKind,
    Verdict,
    VerificationResult,
)
from axon.hypothesis.surface import surface_hypotheses


def _result(verdict, a="x", b="y", p=0.01):
    cand = CandidateRelation(source_id=a, target_id=b, kind=RelationKind.PROXIMITY,
                             score=0.9, provenance=(a, b))
    return VerificationResult(
        candidate=cand, verdict=verdict, statistic=0.9, p_value=p,
        null_model="random-pair", n_resolution=1000,
    )


def test_rejects_unverified_input():
    """Feeding a raw candidate (skipping verification) must fail loudly."""
    raw = CandidateRelation(source_id="a", target_id="b",
                            kind=RelationKind.PROXIMITY, score=1.0)
    with pytest.raises(TypeError):
        surface_hypotheses([raw])


def test_only_accepted_results_surface():
    results = [
        _result(Verdict.ACCEPTED, "a", "b"),
        _result(Verdict.NULL, "c", "d"),
        _result(Verdict.REJECTED, "e", "f"),
        _result(Verdict.INCONCLUSIVE, "g", "h"),
    ]
    report = surface_hypotheses(results)
    assert len(report.hypotheses) == 1
    assert all(isinstance(h, Hypothesis) for h in report.hypotheses)
    assert report.hypotheses[0].result.candidate.source_id == "a"


def test_counts_keep_null_and_rejected_visible():
    results = [
        _result(Verdict.ACCEPTED),
        _result(Verdict.NULL),
        _result(Verdict.NULL),
        _result(Verdict.REJECTED),
    ]
    report = surface_hypotheses(results)
    assert report.counts["accepted"] == 1
    assert report.counts["null"] == 2
    assert report.counts["rejected"] == 1
    assert report.counts["inconclusive"] == 0


def test_provenance_is_carried_through():
    report = surface_hypotheses([_result(Verdict.ACCEPTED, "src", "tgt")])
    assert report.hypotheses[0].provenance == ("src", "tgt")
