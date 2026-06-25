"""
ABC-bridge recovery on the frozen pre-1986 PubMed corpus (closed discovery).

Methodological validation: does the bridge verifier RECOVER the known Raynaud /
fish-oil connection (Swanson, 1986) from pre-1986 literature, where A and C share
no surface vocabulary and the link must run through intermediate B-terms? This is
NOT a scientific discovery claim — the statistic was shaped in-sample for this case.
Held-out generalization (migraine / magnesium) is a later step.

Deterministic: frozen corpus + fixed seed; B re-selected on every null replica.
"""

from __future__ import annotations

import json
from pathlib import Path

from axon.types import Document, Verdict
from axon.relational_representation.literature_store import LiteratureStore
from axon.verification.bridge import AbcBridgeVerifier, propose_bridge
from axon.verification.multiple_testing import apply_fdr

CORPUS = Path(__file__).resolve().parent.parent / "data" / "bridge_corpus.json"
BACKGROUND = ["asthma", "epilepsy", "glaucoma", "psoriasis",
              "tuberculosis", "hepatitis", "appendicitis", "cataract"]
SEED = 0


def main() -> None:
    recs = json.loads(CORPUS.read_text(encoding="utf-8"))
    docs = [
        Document(doc_id=r["id"], text=r.get("text", ""),
                 metadata={"literature": r["literature"], "mesh": r["mesh"]})
        for r in recs
    ]
    store = LiteratureStore(docs, background_labels=BACKGROUND)
    v = AbcBridgeVerifier(n_random_pairs=2000, n_shuffles=2000, seed=SEED)

    print("Axon ABC-bridge recovery — Raynaud / fish-oil, pre-1986 (closed discovery)")
    print(f"(deterministic, seed={SEED}; MeSH substrate; B discovered by the method)\n")

    cand = propose_bridge(store, "raynaud", "fish_oil")
    raw = v.verify(cand, store)
    promoted = apply_fdr([raw], alpha=0.05)[0]          # closed-discovery family = 1

    print(f"[discovery] raynaud ~ fish_oil")
    print(f"  bridge signature: direct_sim={cand.evidence['direct_sim']:.3f} (low), "
          f"|B|={len(cand.b_terms)}, mediated={cand.evidence['mediated']:.3f}")
    print(f"  {raw.reasoning}")
    print(f"  FDR (family=1, controls validated separately): "
          f"q={promoted.q_value:.4f} -> {promoted.verdict.value.upper()}")
    print(f"  discovered B-terms (method, top 12): {list(cand.b_terms)[:12]}")

    print("\n[controls] (validated separately — must NOT be accepted)")
    for c_label in ("scleroderma", "dental_caries"):
        r = v.verify(propose_bridge(store, "raynaud", c_label), store)
        print(f"  raynaud ~ {c_label:13s}: {r.verdict.value.upper():12s} | {r.reasoning[:70]}")

    print("\nNote: the binding null is the weaker random-pair null; the margin is "
          "modest (real recovery, not overwhelming). Methodological validation, not "
          "a scientific discovery claim.")


if __name__ == "__main__":
    main()
