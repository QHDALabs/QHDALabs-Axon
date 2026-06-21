"""Stage 3 tests — verification. This is the core: false-positive rejection.

A verifier that can only accept is a noise generator. These tests assert it can
return NULL/REJECTED for spurious pairs and ACCEPTED only for real structure."""

import numpy as np
import pytest

from axon.types import CandidateRelation, Verdict
from axon.verification.verifier import Verifier, PermutationVerifier
from axon.verification.null_models import permutation_p_value


class DictContext:
    """Minimal VectorContext backed by a dict, for testing."""

    def __init__(self, vectors):
        self._v = {k: np.asarray(v, dtype=float) for k, v in vectors.items()}

    def vector_for(self, doc_id):
        return self._v[doc_id]


def _candidate(a, b, score=1.0, kind="proximity"):
    return CandidateRelation(source_id=a, target_id=b, kind=kind, score=score,
                             provenance=(a, b))


def test_base_verifier_is_abstract():
    with pytest.raises(NotImplementedError):
        Verifier().verify(_candidate("a", "b"), DictContext({}))


def test_unsupported_kind_raises():
    v = PermutationVerifier(seed=0)
    ctx = DictContext({"a": [1, 0], "b": [0, 1]})
    with pytest.raises(NotImplementedError):
        v.verify(_candidate("a", "b", kind="abc-bridge"), ctx)


def test_accepts_genuinely_aligned_pair():
    rng = np.random.default_rng(0)
    pattern = rng.normal(0, 1.0, 32)
    ctx = DictContext({
        "a": pattern + rng.normal(0, 0.1, 32),
        "b": pattern + rng.normal(0, 0.1, 32),
    })
    v = PermutationVerifier(alpha=0.05, n_permutations=2000, seed=1)
    result = v.verify(_candidate("a", "b"), ctx)
    assert result.verdict is Verdict.ACCEPTED
    assert result.p_value < 0.05
    assert result.null_model  # an explicit null was stated


def test_rejects_or_nulls_spurious_pair():
    """The point of the whole stage: a chance pair must NOT be accepted."""
    rng = np.random.default_rng(7)
    ctx = DictContext({
        "a": rng.normal(0, 1.0, 64),
        "b": rng.normal(0, 1.0, 64),  # independent of a
    })
    v = PermutationVerifier(alpha=0.05, n_permutations=2000, seed=2)
    result = v.verify(_candidate("a", "b"), ctx)
    assert result.verdict is not Verdict.ACCEPTED
    assert result.verdict in (Verdict.NULL, Verdict.REJECTED)


def test_low_resolution_is_inconclusive_not_overclaimed():
    ctx = DictContext({"a": [1.0, 1.0, 1.0, 1.0], "b": [1.0, 1.0, 1.0, 1.0]})
    v = PermutationVerifier(n_permutations=10, min_resolution=200, seed=0)
    result = v.verify(_candidate("a", "b"), ctx)
    assert result.verdict is Verdict.INCONCLUSIVE


def test_permutation_p_value_resolution_floor():
    """p-value cannot be finer than ~1/(n+1) — the +1 correction guarantees >0."""
    data = np.array([3.0, 1.0, 2.0])
    res = permutation_p_value(
        statistic=lambda x: float(x[0]),
        data=data,
        permute=lambda x, r: r.permutation(x),
        n_permutations=100,
        rng=np.random.default_rng(0),
    )
    assert res.p_value >= 1.0 / (100 + 1)
    assert res.n_resolution == 100
