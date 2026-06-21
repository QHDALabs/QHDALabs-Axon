"""Stage 3 tests — verification. This is the core: false-positive rejection.

The verifier must be able to return INCONCLUSIVE / REJECTED / NULL and must NEVER
return ACCEPTED on its own (acceptance is decided by FDR across the family). Tests
use a controlled FakeCorpus so the null is exactly known."""

import numpy as np
import pytest

from axon.types import CandidateRelation, RelationKind, Verdict
from axon.verification.verifier import Verifier, RandomPairProximityVerifier
from axon.verification.multiple_testing import apply_fdr


class FakeCorpus:
    """Deterministic CorpusContext with explicit vectors / domains / length bands."""

    def __init__(self, vectors, domains=None, bands=None):
        self._v = {k: np.asarray(v, dtype=float) for k, v in vectors.items()}
        self._dom = domains or {k: "d" for k in self._v}
        self._band = bands or {k: 0 for k in self._v}

    def vector_for(self, doc_id):
        return self._v[doc_id]

    def all_doc_ids(self):
        return tuple(self._v)

    def domain_of(self, doc_id):
        return self._dom[doc_id]

    def length_band_of(self, doc_id):
        return self._band[doc_id]


def _cand(a, b, kind=RelationKind.PROXIMITY):
    return CandidateRelation(source_id=a, target_id=b, kind=kind, score=1.0,
                             provenance=(a, b))


def _single_domain_corpus(n=12, seed=0):
    """One domain, one band: stratum = all C(n,2) pairs. Plant an aligned a~b."""
    rng = np.random.default_rng(seed)
    dim = 16
    pattern = rng.normal(0, 1.0, dim)
    vectors = {f"r{i}": rng.normal(0, 1.0, dim) for i in range(n - 2)}
    vectors["a"] = pattern + rng.normal(0, 0.05, dim)
    vectors["b"] = pattern + rng.normal(0, 0.05, dim)
    return FakeCorpus(vectors)


def test_base_verifier_is_abstract():
    with pytest.raises(NotImplementedError):
        Verifier().verify(_cand("a", "b"), FakeCorpus({"a": [1, 0], "b": [0, 1]}))


def test_unsupported_kind_raises():
    v = RandomPairProximityVerifier(min_resolution=1)
    ctx = FakeCorpus({"a": [1, 0], "b": [0, 1]})
    with pytest.raises(NotImplementedError):
        v.verify(_cand("a", "b", kind=RelationKind.ABC_BRIDGE), ctx)


def test_verifier_never_returns_accepted_on_its_own():
    """Acceptance requires FDR; a single verify() must not accept."""
    ctx = _single_domain_corpus()
    v = RandomPairProximityVerifier(min_resolution=5)
    result = v.verify(_cand("a", "b"), ctx)
    assert result.verdict is not Verdict.ACCEPTED
    assert result.verdict is Verdict.NULL          # high cos, above null mean, pending
    assert result.p_value is not None and result.p_value < 0.05
    assert result.null_model                        # an explicit null was stated


def test_aligned_pair_accepted_only_after_fdr():
    ctx = _single_domain_corpus()
    v = RandomPairProximityVerifier(min_resolution=5)
    raw = v.verify(_cand("a", "b"), ctx)
    # Family of one with low p -> BH threshold alpha -> ACCEPTED.
    promoted = apply_fdr([raw], alpha=0.05)
    assert promoted[0].verdict is Verdict.ACCEPTED
    assert promoted[0].q_value is not None and promoted[0].q_value <= 0.05


def test_chance_pair_is_not_accepted():
    """The point of the whole stage: a chance pair must NOT be accepted."""
    rng = np.random.default_rng(7)
    vectors = {f"r{i}": rng.normal(0, 1.0, 32) for i in range(10)}
    ctx = FakeCorpus(vectors)
    v = RandomPairProximityVerifier(min_resolution=5)
    raw = v.verify(_cand("r0", "r1"), ctx)
    assert raw.verdict in (Verdict.NULL, Verdict.REJECTED)
    promoted = apply_fdr([raw], alpha=0.05)
    assert promoted[0].verdict is not Verdict.ACCEPTED


def test_low_resolution_is_inconclusive_not_overclaimed():
    ctx = FakeCorpus({"a": [1.0, 1.0], "b": [1.0, 1.0], "c": [0.0, 1.0]})
    v = RandomPairProximityVerifier(min_resolution=20)  # only 3 pairs available
    result = v.verify(_cand("a", "b"), ctx)
    assert result.verdict is Verdict.INCONCLUSIVE
    assert result.p_value is None


def test_null_excludes_the_candidate_pair_itself():
    """The candidate's own similarity must not be part of its own null."""
    ctx = _single_domain_corpus()
    v = RandomPairProximityVerifier(min_resolution=5)
    result = v.verify(_cand("a", "b"), ctx)
    # n eligible = C(12,2) - 1 (the a~b pair removed) = 65.
    assert result.n_resolution == 12 * 11 // 2 - 1
