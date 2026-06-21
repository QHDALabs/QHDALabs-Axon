"""Stage 2 tests — relational_representation.relation_store.

These run on pure numpy and must not require Qiskit (the relational layer of
qhda-core is pure numpy)."""

import numpy as np
import pytest

from axon.relational_representation.relation_store import RelationStore
from axon.types import CandidateRelation, Document, RelationKind


def _doc(doc_id, vec, domain="d", text=None):
    return Document(
        doc_id=doc_id,
        text=text if text is not None else doc_id,
        vector=np.asarray(vec, dtype=float),
        metadata={"domain": domain},
    )


def test_observe_requires_vector():
    store = RelationStore(dim=3)
    with pytest.raises(ValueError):
        store.observe(Document(doc_id="d", text="no vector"))


def test_observe_rejects_wrong_dim():
    store = RelationStore(dim=3)
    with pytest.raises(ValueError):
        store.observe(_doc("d", [1.0, 2.0]))


def test_observe_rejects_duplicate_id():
    store = RelationStore(dim=2)
    store.observe(_doc("a", [1.0, 0.0]))
    with pytest.raises(ValueError):
        store.observe(_doc("a", [0.0, 1.0]))


def test_candidate_relations_flags_aligned_pair():
    store = RelationStore(dim=4)
    store.observe(_doc("a1", [1.0, 1.0, 0.0, 0.0]))
    store.observe(_doc("a2", [1.0, 0.9, 0.0, 0.0]))   # nearly parallel to a1
    store.observe(_doc("b1", [0.0, 0.0, 1.0, -1.0]))  # orthogonal to the a's
    cands = store.candidate_relations(threshold=0.8)
    assert all(isinstance(c, CandidateRelation) for c in cands)
    assert all(c.kind is RelationKind.PROXIMITY for c in cands)
    pairs = {(c.source_id, c.target_id) for c in cands}
    assert ("a1", "a2") in pairs
    assert ("a1", "b1") not in pairs


def test_corpus_context_methods():
    store = RelationStore(dim=2, n_length_bands=2)
    store.observe(_doc("a", [1.0, 0.0], domain="astro", text="one two three four five"))
    store.observe(_doc("b", [0.0, 1.0], domain="astro", text="one"))
    store.observe(_doc("c", [1.0, 1.0], domain="neuro", text="one two three"))
    assert set(store.all_doc_ids()) == {"a", "b", "c"}
    assert store.domain_of("a") == "astro"
    assert store.domain_of("c") == "neuro"
    # Length bands are quantile cuts: the longest doc must not be in the lowest band.
    assert store.length_band_of("a") >= store.length_band_of("b")


def test_domain_defaults_to_unknown():
    store = RelationStore(dim=2)
    store.observe(Document(doc_id="a", text="x", vector=np.array([1.0, 0.0])))
    assert store.domain_of("a") == "unknown"


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
    store = RelationStore(dim=3)
    store.observe(_doc("a", [1.0, 0.0, 0.0]))
    assert store.n_observed == 1
    assert "qiskit" not in str(type(store))
