"""
Minimal end-to-end Axon pipeline on toy data:

    perception  ->  relational representation  ->  verification  ->  hypothesis

The order is the thesis. Candidate relations are cheap and many are spurious by
construction; verification against an explicit permutation null is what decides
which survive. Rejected / null results are printed too — they are data, not
failures.

Runs on pure numpy. Qiskit is NOT required (the relational layer of qhda-core is
pure numpy, and Axon never imports the quantum layer here).

Note on the toy vectors: turning text into feature vectors is NOT implemented in
this scaffold, so this example supplies precomputed vectors directly. Two
documents share a latent pattern (should survive verification); the others are
random (should be indistinguishable from the null).
"""

import numpy as np

from axon import (
    Document,
    RelationStore,
    PermutationVerifier,
    verify_all,
    surface_hypotheses,
    normalize_text,
)

DIM = 16

# Fixed seeds make this example deterministic: the toy vectors and the
# permutation null are both reproducible, so the printed p-values are stable.
DOC_SEED = 0          # toy feature vectors
PERM_SEED = 1         # permutation null in the verifier


def build_toy_documents(seed: int = DOC_SEED):
    """Perception (toy): normalized text + a precomputed feature vector."""
    rng = np.random.default_rng(seed)

    # A shared latent pattern for the two "aligned" documents.
    pattern = rng.normal(0, 1.0, DIM)

    raw = {
        "doc_A1": ("  Iron supplementation   and cognitive   performance.  ",
                   pattern + rng.normal(0, 0.25, DIM)),     # aligned with A2
        "doc_A2": ("Dietary iron\tand memory in adults.",
                   pattern + rng.normal(0, 0.25, DIM)),     # aligned with A1
        "doc_R1": ("Tidal patterns of coastal mollusks.",
                   rng.normal(0, 1.0, DIM)),                # unrelated / random
        "doc_R2": ("Compiler optimization for sparse graphs.",
                   rng.normal(0, 1.0, DIM)),                # unrelated / random
    }

    docs = []
    for doc_id, (text, vector) in raw.items():
        # normalize_text is the real (minimal) perception step; the vector is
        # supplied because featurization is out of scope for the scaffold.
        docs.append(Document(doc_id=doc_id, text=normalize_text(text), vector=vector))
    return docs


def main() -> None:
    print("Axon toy pipeline — perception -> relational -> verification -> hypothesis")
    print(f"(deterministic: doc_seed={DOC_SEED}, perm_seed={PERM_SEED})\n")

    # 1) Perception
    docs = build_toy_documents(seed=DOC_SEED)
    print(f"[perception] ingested {len(docs)} documents (normalized text + toy vectors)")

    # 2) Relational representation
    store = RelationStore(dim=DIM)
    for d in docs:
        store.observe(d)
    candidates = store.candidate_relations(threshold=0.0)  # propose all pairs
    print(f"[relational] structural_score={store.structural_score:.3f}, "
          f"proposed {len(candidates)} candidate relations (cheap, possibly false)")

    # 3) Verification — explicit permutation null; can REJECT / return NULL
    verifier = PermutationVerifier(alpha=0.05, n_permutations=1000, seed=PERM_SEED)
    results = verify_all(candidates, verifier, store)
    print("[verification] verdicts:")
    for r in results:
        c = r.candidate
        print(f"    {c.source_id:>6} ~ {c.target_id:<6}  "
              f"cos={r.statistic:+.3f}  p={r.p_value:.4f}  -> {r.verdict.value.upper()}")

    # 4) Hypothesis — built ONLY from accepted results
    report = surface_hypotheses(results)
    print(f"\n[hypothesis] verdict counts: {report.counts}")
    print(f"[hypothesis] surfaced {len(report.hypotheses)} hypothesis/-es "
          f"(accepted only):")
    for h in report.hypotheses:
        print(f"    - {h.statement}")

    if not report.hypotheses:
        print("    (none survived verification — an honest null is a valid outcome)")


if __name__ == "__main__":
    main()
