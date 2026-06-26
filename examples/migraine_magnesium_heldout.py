"""
Held-out ABC-bridge test — migraine / magnesium, pre-1988 (Swanson 1988).

Runs the PRE-REGISTERED, FROZEN AbcBridgeVerifier (no statistic changes) on a corpus
fetched AFTER the rule was committed. Outcome is reported as-is.

Recorded result: NON-RECOVERY. The true migraine/magnesium bridge does not beat its
nulls (q=0.12), while a directly-similar control (cluster headache) slips under the
proximity gate and would be falsely accepted. Held-out reveals the in-sample
(Raynaud/fish-oil) success did not generalize. See VERIFICATION_LOG.md.
"""

from __future__ import annotations

import json
from pathlib import Path

from axon.types import Document
from axon.relational_representation.literature_store import LiteratureStore
from axon.verification.bridge import AbcBridgeVerifier, propose_bridge
from axon.verification.multiple_testing import apply_fdr

CORPUS = Path(__file__).resolve().parent.parent / "data" / "heldout_corpus.json"
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

    print("Axon held-out ABC-bridge — migraine / magnesium, pre-1988 (frozen verifier)\n")

    cand = propose_bridge(store, "migraine", "magnesium")
    raw = v.verify(cand, store)
    prom = apply_fdr([raw], alpha=0.05)[0]
    print("[discovery] migraine ~ magnesium")
    print(f"  signature: direct_sim={cand.evidence['direct_sim']:.3f}, |B|={len(cand.b_terms)}, "
          f"mediated={cand.evidence['mediated']:.3f}")
    print(f"  {raw.reasoning}")
    print(f"  FDR family-1: q={prom.q_value:.4f} -> {prom.verdict.value.upper()}")
    print(f"  B-terms (top 12): {list(cand.b_terms)[:12]}")

    print("\n[controls] (validated separately)")
    for c_label in ("cluster_headache", "dental_caries"):
        r = v.verify(propose_bridge(store, "migraine", c_label), store)
        q = apply_fdr([r])[0]
        print(f"  migraine ~ {c_label:16s}: raw {r.verdict.value.upper():12s} "
              f"family-1 {q.verdict.value.upper():9s} | {r.reasoning[:64]}")

    print("\nOutcome: NON-RECOVERY. The true bridge does not pass; the directly-similar")
    print("control (cluster headache, direct_sim=0.283) slips under the 0.30 gate and")
    print("would be falsely accepted. Held-out did not generalize. Logged as-is, no tuning.")


if __name__ == "__main__":
    main()
