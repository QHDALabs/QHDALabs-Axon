"""Stage 3 tests — the verifier registry must fail closed.

A candidate whose kind has no registered verifier must RAISE, never silently fall
back to proximity. This makes "no relation kind without its own null" structural."""

import numpy as np
import pytest

from axon.types import CandidateRelation, RelationKind
from axon.verification.registry import VerifierRegistry, NoVerifierError, verify_all
from axon.verification.verifier import RandomPairProximityVerifier


class FakeCorpus:
    def __init__(self, vectors):
        self._v = {k: np.asarray(v, dtype=float) for k, v in vectors.items()}

    def vector_for(self, doc_id):
        return self._v[doc_id]

    def all_doc_ids(self):
        return tuple(self._v)

    def domain_of(self, doc_id):
        return "d"

    def length_band_of(self, doc_id):
        return 0


def _cand(kind):
    return CandidateRelation(source_id="a", target_id="b", kind=kind, score=1.0)


def test_registered_kind_dispatches():
    reg = VerifierRegistry()
    reg.register(RelationKind.PROXIMITY, RandomPairProximityVerifier(min_resolution=1))
    assert reg.registered_kinds() == frozenset({RelationKind.PROXIMITY})
    assert reg.verifier_for(RelationKind.PROXIMITY) is not None


def test_unregistered_kind_fails_closed():
    reg = VerifierRegistry()
    reg.register(RelationKind.PROXIMITY, RandomPairProximityVerifier(min_resolution=1))
    with pytest.raises(NoVerifierError):
        reg.verifier_for(RelationKind.ABC_BRIDGE)


def test_verify_all_fails_closed_on_unregistered_candidate():
    reg = VerifierRegistry()
    reg.register(RelationKind.PROXIMITY, RandomPairProximityVerifier(min_resolution=1))
    ctx = FakeCorpus({"a": [1.0, 0.0], "b": [0.0, 1.0]})
    with pytest.raises(NoVerifierError):
        verify_all([_cand(RelationKind.SAME_MECHANISM_AS)], reg, ctx)
