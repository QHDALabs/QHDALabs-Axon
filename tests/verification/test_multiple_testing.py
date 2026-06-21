"""Stage 3 tests — Benjamini-Hochberg FDR control and its verdict policy."""

import numpy as np

from axon.types import CandidateRelation, RelationKind, Verdict, VerificationResult
from axon.verification.multiple_testing import benjamini_hochberg, apply_fdr


def test_bh_empty():
    rejected, q = benjamini_hochberg([], 0.05)
    assert rejected.size == 0 and q.size == 0


def test_bh_all_tiny_pvalues_all_rejected():
    rejected, q = benjamini_hochberg([1e-6, 1e-6, 1e-6], 0.05)
    assert rejected.all()
    assert np.all(q <= 0.05)


def test_bh_all_large_pvalues_none_rejected():
    rejected, _ = benjamini_hochberg([0.4, 0.6, 0.9], 0.05)
    assert not rejected.any()


def test_bh_matches_manual_step_up():
    # p sorted: 0.001, 0.008, 0.2, 0.3, 0.5 ; n=5, alpha=0.05.
    # Largest k with p_(k) <= k/n*alpha: k=1 (0.001<=0.01), k=2 (0.008<=0.02),
    # k=3 (0.2<=0.03? no)... only k<=2 qualify -> step-up rejects ranks 1 and 2.
    p = [0.2, 0.3, 0.001, 0.5, 0.008]   # indices 2 and 4 are the two smallest
    rejected, _ = benjamini_hochberg(p, 0.05)
    assert rejected[2]  # p=0.001
    assert rejected[4]  # p=0.008
    assert not rejected[0] and not rejected[1] and not rejected[3]


def test_bh_qvalues_are_monotone_in_p():
    p = np.array([0.001, 0.01, 0.02, 0.2, 0.5])
    _, q = benjamini_hochberg(p, 0.05)
    assert np.all(np.diff(q) >= -1e-12)  # non-decreasing with increasing p


def _result(verdict, p, a="a", b="b"):
    cand = CandidateRelation(source_id=a, target_id=b, kind=RelationKind.PROXIMITY,
                             score=1.0)
    return VerificationResult(candidate=cand, verdict=verdict, statistic=0.5,
                              p_value=p, null_model="random-pair", n_resolution=100)


def test_apply_fdr_promotes_null_to_accepted():
    results = [_result(Verdict.NULL, 1e-4, "a", "b")] + [
        _result(Verdict.NULL, 0.9, f"x{i}", f"y{i}") for i in range(3)
    ]
    out = apply_fdr(results, 0.05)
    assert out[0].verdict is Verdict.ACCEPTED
    assert out[0].q_value is not None and out[0].q_value <= 0.05
    assert all(r.verdict is Verdict.NULL for r in out[1:])


def test_apply_fdr_keeps_rejected_rejected():
    results = [_result(Verdict.REJECTED, 0.8), _result(Verdict.NULL, 0.9, "c", "d")]
    out = apply_fdr(results, 0.05)
    assert out[0].verdict is Verdict.REJECTED
    assert out[0].q_value is not None  # still annotated


def test_apply_fdr_ignores_inconclusive():
    inc = _result(Verdict.INCONCLUSIVE, None)
    out = apply_fdr([inc], 0.05)
    assert out[0].verdict is Verdict.INCONCLUSIVE
    assert out[0].q_value is None
