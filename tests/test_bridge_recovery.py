"""ABC-bridge recovery on the frozen pre-1986 corpus (methodological validation).

Closed discovery: the FDR family is the single pre-specified discovery hypothesis
(raynaud ~ fish_oil). Negative controls are validated SEPARATELY (they must not be
accepted) — they are specificity checks, not competing discovery candidates, so
pooling them into the discovery FDR would penalize due diligence. See
VERIFICATION_LOG.md for the full justification and its boundary (this leniency does
NOT carry to open discovery).

Deterministic: frozen corpus + seed; exhaustive-ish nulls with fixed seed."""

import json
from pathlib import Path

import pytest

from axon.types import Document, Verdict
from axon.relational_representation.literature_store import LiteratureStore
from axon.verification.bridge import AbcBridgeVerifier, propose_bridge
from axon.verification.multiple_testing import apply_fdr

CORPUS = Path(__file__).resolve().parent.parent / "data" / "bridge_corpus.json"
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


def test_known_bridge_recovered(store, verifier):
    """raynaud ~ fish_oil: bridge signature + passes both nulls + FDR (family=1)."""
    cand = propose_bridge(store, "raynaud", "fish_oil")
    raw = verifier.verify(cand, store)

    # Bridge signature: LOW direct similarity, MANY mediating B-terms.
    assert cand.evidence["direct_sim"] < 0.10
    assert len(cand.b_terms) >= 25
    # Passes both nulls at raw alpha; the binding (weaker) null is random-pair.
    assert raw.verdict is Verdict.NULL          # verifier never self-accepts
    assert raw.p_value is not None and raw.p_value < 0.05

    # Closed-discovery FDR family = the single discovery hypothesis.
    promoted = apply_fdr([raw], alpha=0.05)
    assert promoted[0].verdict is Verdict.ACCEPTED
    assert promoted[0].q_value is not None and promoted[0].q_value < 0.05


def test_discovered_b_terms_are_mechanistic(store):
    """The B-terms are discovered by the method, not assigned. They should include
    the platelet/prostaglandin/vascular intermediates Swanson identified."""
    cand = propose_bridge(store, "raynaud", "fish_oil")
    b = {t.lower() for t in cand.b_terms}
    mechanistic = {"blood platelets", "arachidonic acid", "blood vessels",
                   "blood pressure", "aspirin"}
    assert mechanistic & b, f"expected some of {mechanistic} in {sorted(b)[:20]}"


def test_negative_controls_not_accepted(store, verifier):
    """Specificity: directly-similar and unrelated controls must NOT be accepted."""
    sim = verifier.verify(propose_bridge(store, "raynaud", "scleroderma"), store)
    assert sim.verdict is Verdict.REJECTED      # proximity gate (high direct sim)
    assert "proximity, not a bridge" in sim.reasoning

    rand = verifier.verify(propose_bridge(store, "raynaud", "dental_caries"), store)
    assert rand.verdict is not Verdict.ACCEPTED
    assert apply_fdr([rand])[0].verdict is not Verdict.ACCEPTED
