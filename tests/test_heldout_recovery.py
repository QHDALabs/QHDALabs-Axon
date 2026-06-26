"""Held-out ABC-bridge test on the frozen pre-1988 corpus — migraine / magnesium.

These tests PIN THE ACTUAL, HONEST OUTCOME (a non-recovery plus a control-separation
failure), not a desired one. The verifier was pre-registered and frozen before the
corpus was fetched (see VERIFICATION_LOG.md); the result is recorded as-is, no tuning.

Deterministic: frozen corpus + seed."""

import json
from pathlib import Path

import pytest

from axon.types import Document, Verdict
from axon.relational_representation.literature_store import LiteratureStore
from axon.verification.bridge import AbcBridgeVerifier, propose_bridge
from axon.verification.multiple_testing import apply_fdr

CORPUS = Path(__file__).resolve().parent.parent / "data" / "heldout_corpus.json"
BACKGROUND = ["asthma", "epilepsy", "glaucoma", "psoriasis",
              "tuberculosis", "hepatitis", "appendicitis", "cataract"]


@pytest.fixture(scope="module")
def store():
    recs = json.loads(CORPUS.read_text(encoding="utf-8"))
    docs = [
        Document(doc_id=r["id"], text=r.get("text", ""),
                 metadata={"literature": r["literature"], "mesh": r["mesh"]})
        for r in recs
    ]
    return LiteratureStore(docs, background_labels=BACKGROUND)


@pytest.fixture(scope="module")
def verifier():
    return AbcBridgeVerifier(n_random_pairs=2000, n_shuffles=2000, seed=0)


def test_true_bridge_not_recovered(store, verifier):
    """Honest negative: the migraine/magnesium bridge has the right signature
    (very low direct similarity) but does NOT beat its nulls -> not accepted."""
    cand = propose_bridge(store, "migraine", "magnesium")
    raw = verifier.verify(cand, store)
    assert cand.evidence["direct_sim"] < 0.10          # correct signature (distant A/C)
    assert len(cand.b_terms) >= 10                     # B forms (no sparsity STOP)
    promoted = apply_fdr([raw], alpha=0.05)[0]
    assert promoted.verdict is not Verdict.ACCEPTED    # NON-RECOVERY
    assert raw.p_value is not None and raw.p_value > 0.05


def test_directly_similar_control_does_not_separate(store, verifier):
    """STOP finding: cluster headache (same headache class) slips UNDER the frozen
    0.30 proximity gate and would be falsely accepted as a bridge — a control that
    does not separate. Pinned to document the method's failure, not endorse it."""
    raw = verifier.verify(propose_bridge(store, "migraine", "cluster_headache"), store)
    assert raw.candidate.evidence  # has evidence
    cand = propose_bridge(store, "migraine", "cluster_headache")
    assert cand.evidence["direct_sim"] < 0.30          # gate did NOT fire (just under)
    assert apply_fdr([raw], alpha=0.05)[0].verdict is Verdict.ACCEPTED  # false accept


def test_unrelated_control_rejected(store, verifier):
    """The unrelated control DOES separate: worse than chance."""
    raw = verifier.verify(propose_bridge(store, "migraine", "dental_caries"), store)
    assert raw.verdict is Verdict.REJECTED
    assert apply_fdr([raw], alpha=0.05)[0].verdict is not Verdict.ACCEPTED


def test_calibration_holds_on_background(store):
    """The frozen shuffled-B still calibrates: random focused background pairs are
    not falsely accepted."""
    v = AbcBridgeVerifier(n_random_pairs=600, n_shuffles=600, seed=1)
    import numpy as np
    rng = np.random.default_rng(123)
    accepted = 0
    trials = 12
    for _ in range(trials):
        i, j = rng.choice(len(BACKGROUND), size=2, replace=False)
        raw = v.verify(propose_bridge(store, BACKGROUND[int(i)], BACKGROUND[int(j)]), store)
        if apply_fdr([raw], alpha=0.05)[0].verdict is Verdict.ACCEPTED:
            accepted += 1
    assert accepted / trials <= 0.05 + 1e-9
