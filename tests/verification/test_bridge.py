"""Stage 3 tests — ABC bridge verifier (synthetic, corpus-independent).

Validation is the point: a planted bridge is ACCEPTED; directly-similar and
generic-only pairs are NOT; random focused pairs are accepted at most at rate
alpha; and the nulls RE-SELECT B on every replica (never frozen on the observed
pair)."""

import numpy as np

from axon.types import CandidateRelation, RelationKind, Verdict
from axon.verification.bridge import (
    AbcBridgeVerifier,
    propose_bridge,
    select_b_terms,
    mediated_score,
    _replica_mediated,
)
from axon.verification.multiple_testing import apply_fdr
from axon.relational_representation.literature_store import LiteratureStore
from axon.types import Document

GENERIC = ["humans", "male", "female"]          # in DEFAULT_MESH_STOPLIST
# B-terms model real intermediate vocabulary: COMMON, mid-frequency, present across
# the background (not private to any literature). Modeled from that reality, NOT to
# match the null's mechanics.
B_TERMS = ["blood viscosity", "platelet aggregation", "vasoconstriction", "fibrinogen"]
A_DOM = [f"raynaud_term_{i}" for i in range(8)]   # private, absent from background
C_DOM = [f"fishoil_term_{i}" for i in range(8)]   # private, absent from background
SIM_SHARED = [f"shared_term_{i}" for i in range(8)]

B_BACKGROUND_RATE = 0.25   # B is common in the background (-> common pool, mid-freq)
B_BRIDGE_RATE = 0.9        # A and C use the intermediates heavily (the planted bridge)


def _doc(doc_id, literature, mesh):
    return Document(doc_id=doc_id, text="", metadata={"literature": literature, "mesh": mesh})


def _bridge_corpus(seed=0):
    rng = np.random.default_rng(seed)
    docs = []

    # Background: 6 focused topics. Private dominant vocab PLUS sprinkled B-terms, so
    # B is a common cross-literature pool (background_df > 0) but no two topics
    # specifically co-use the same B-set heavily.
    for k in range(6):
        topic_dom = [f"bg{k}_term_{i}" for i in range(6)]
        for i in range(8):
            b_bg = [b for b in B_TERMS if rng.random() < B_BACKGROUND_RATE]
            docs.append(_doc(f"bg{k}_{i}", f"bg{k}", topic_dom + b_bg + GENERIC))

    # A and C: private dominant vocab + heavy shared use of the B intermediates.
    for i in range(10):
        b_a = [b for b in B_TERMS if rng.random() < B_BRIDGE_RATE]
        docs.append(_doc(f"a{i}", "raynaud", A_DOM + b_a + GENERIC))
        b_c = [b for b in B_TERMS if rng.random() < B_BRIDGE_RATE]
        docs.append(_doc(f"c{i}", "fish_oil", C_DOM + b_c + GENERIC))

    # Directly-similar control pair: heavy shared dominant vocab -> high direct sim.
    for i in range(8):
        docs.append(_doc(f"sa{i}", "sim_a", SIM_SHARED + [f"sa_only_{i%2}"] + GENERIC))
        docs.append(_doc(f"sc{i}", "sim_c", SIM_SHARED + [f"sc_only_{i%2}"] + GENERIC))

    # Generic-only control pair: share ONLY generic terms (distinct dominant vocab).
    for i in range(8):
        docs.append(_doc(f"ga{i}", "gen_a", [f"gen_a_dom_{i%3}"] + GENERIC))
        docs.append(_doc(f"gc{i}", "gen_c", [f"gen_c_dom_{i%3}"] + GENERIC))

    background = [f"bg{k}" for k in range(6)]
    return LiteratureStore(docs, background_labels=background)


def _verifier():
    # Smaller R/n than production for test speed; still 1/(R+1) << alpha for |family|<=few.
    return AbcBridgeVerifier(n_random_pairs=400, n_shuffles=400, seed=0)


def test_planted_bridge_accepted():
    store = _bridge_corpus()
    v = _verifier()
    cand = propose_bridge(store, "raynaud", "fish_oil")
    raw = v.verify(cand, store)
    assert raw.verdict is Verdict.NULL          # provisional; verifier never self-accepts
    assert raw.p_value is not None and raw.p_value < 0.05
    promoted = apply_fdr([raw], alpha=0.05)
    assert promoted[0].verdict is Verdict.ACCEPTED
    # Bridge signature: LOW direct similarity, HIGH mediated connectivity.
    assert "direct_sim=" in raw.reasoning and "mediated=" in raw.reasoning


def test_directly_similar_pair_is_not_a_bridge():
    store = _bridge_corpus()
    raw = _verifier().verify(propose_bridge(store, "sim_a", "sim_c"), store)
    assert raw.verdict is Verdict.REJECTED       # proximity gate fired
    assert "proximity, not a bridge" in raw.reasoning
    assert apply_fdr([raw])[0].verdict is not Verdict.ACCEPTED


def test_generic_only_pair_is_not_accepted():
    store = _bridge_corpus()
    raw = _verifier().verify(propose_bridge(store, "gen_a", "gen_c"), store)
    assert raw.verdict is not Verdict.ACCEPTED   # no shared non-generic support
    assert apply_fdr([raw])[0].verdict is not Verdict.ACCEPTED


def test_calibration_random_focused_pairs_false_accept_within_alpha():
    store = _bridge_corpus()
    v = AbcBridgeVerifier(n_random_pairs=300, n_shuffles=300, seed=1)
    alpha = 0.05
    topics = [f"bg{k}" for k in range(6)]
    rng = np.random.default_rng(123)
    accepted = 0
    trials = 0
    for _ in range(20):
        i, j = rng.choice(len(topics), size=2, replace=False)
        cand = propose_bridge(store, topics[int(i)], topics[int(j)])
        raw = v.verify(cand, store)
        promoted = apply_fdr([raw], alpha=alpha)
        trials += 1
        if promoted[0].verdict is Verdict.ACCEPTED:
            accepted += 1
    assert accepted / trials <= alpha + 1e-9


def test_unsupported_candidate_fails():
    store = _bridge_corpus()
    prox = CandidateRelation(source_id="x", target_id="y",
                             kind=RelationKind.PROXIMITY, score=1.0)
    import pytest
    with pytest.raises(NotImplementedError):
        _verifier().verify(prox, store)


# ── the critical methodological test: B is recomputed per replica ──

def test_select_b_terms_is_support_dependent():
    ng = np.array([True, True, True, True])
    w_a = np.array([1.0, 1.0, 0.0, 1.0])
    w_c = np.array([1.0, 0.0, 1.0, 1.0])
    assert list(np.flatnonzero(select_b_terms(w_a, w_c, ng))) == [0, 3]
    w_c_perm = np.array([0.0, 1.0, 1.0, 1.0])      # support moved
    assert list(np.flatnonzero(select_b_terms(w_a, w_c_perm, ng))) == [1, 3]


def test_replica_mediated_recomputes_B_not_frozen():
    """A null replica must re-select B from the permuted profile, not reuse the
    observed pair's B. Freezing B would be too lenient (selection bias)."""
    ng = np.array([True, True, True, True])
    w_a = np.array([1.0, 1.0, 0.0, 1.0])
    w_c = np.array([1.0, 0.0, 1.0, 1.0])
    obs_b = select_b_terms(w_a, w_c, ng)           # {0, 3}
    w_c_perm = np.array([0.0, 1.0, 1.0, 1.0])

    recomputed = _replica_mediated(w_a, w_c_perm, ng)   # B re-selected -> {1,3} -> 1+1=2
    frozen = mediated_score(w_a, w_c_perm, obs_b)        # frozen B {0,3} -> 0+1=1
    assert recomputed == 2.0
    assert frozen == 1.0
    assert recomputed != frozen                          # recompute differs from frozen
