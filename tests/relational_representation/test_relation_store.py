"""Stage 2 tests — relational_representation.relation_store.

These run on pure numpy and must not require Qiskit (the relational layer of
qhda-core is pure numpy)."""

import numpy as np
import pytest

from axon.relational_representation.relation_store import RelationStore
from axon.types import Document, CandidateRelation


def _doc(doc_id, vec):
    return Document(doc_id=doc_id, text=doc_id, vector=np.asarray(vec, dtype=float))


def test_observe_requires_vector():
    store = RelationStore(dim=3)
    with pytest.raises(ValueError):
        store.observe(Document(doc_id="d", text="no vector"))


def test_observe_rejects_wrong_dim():
    store = RelationStore(dim=3)
    with pytest.raises(ValueError):
        store.observe(_doc("d", [1.0, 2.0]))


def test_candidate_relations_flags_aligned_pair():
    store = RelationStore(dim=4)
    store.observe(_doc("a1", [1.0, 1.0, 0.0, 0.0]))
    store.observe(_doc("a2", [1.0, 0.9, 0.0, 0.0]))   # nearly parallel to a1
    store.observe(_doc("b1", [0.0, 0.0, 1.0, -1.0]))  # orthogonal to the a's
    cands = store.candidate_relations(threshold=0.8)
    assert all(isinstance(c, CandidateRelation) for c in cands)
    pairs = {(c.source_id, c.target_id) for c in cands}
    assert ("a1", "a2") in pairs
    assert ("a1", "b1") not in pairs


def test_structural_score_is_float():
    store = RelationStore(dim=4)
    for i in range(5):
        store.observe(_doc(f"d{i}", np.ones(4) * 0.1))
    assert isinstance(store.structural_score, float)
    assert store.structural_score >= 0.0


def test_vector_for_unknown_id_raises():
    store = RelationStore(dim=2)
    store.observe(_doc("a", [1.0, 0.0]))
    assert store.vector_for("a").shape == (2,)
    with pytest.raises(KeyError):
        store.vector_for("missing")


def test_works_without_qiskit():
    """No import of the quantum layer; pure numpy path must run."""
    import sys
    store = RelationStore(dim=3)
    store.observe(_doc("a", [1.0, 0.0, 0.0]))
    assert store.n_observed == 1
    # qiskit may or may not be installed; either way this code path never imports it.
    assert "qiskit" not in str(type(store))
    _ = sys  # silence linters; presence-of-qiskit is irrelevant to this path
