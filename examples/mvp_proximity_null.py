"""
Axon MVP — end-to-end on a small REAL corpus:

    perception  ->  featurization  ->  relational representation
                ->  verification (random-pair null + FDR)  ->  hypothesis

Claim scope: this surfaces LEXICAL proximity relations (TF-IDF cosine), FDR-
controlled. It makes NO semantic or mechanistic claim. Cross-domain pairs are
expected to be mostly NULL; an honest null is a valid, reported outcome.

Determinism: the TF-IDF featurizer is deterministic and the random-pair null
enumerates ALL eligible matched pairs (no sampling), so this run has no RNG and is
fully reproducible. The only "seeds" are the fixed corpus and these parameters.
"""

from __future__ import annotations

from pathlib import Path

from axon import (
    RandomPairProximityVerifier,
    RelationKind,
    RelationStore,
    TfidfFeaturizer,
    Verdict,
    VerifierRegistry,
    apply_fdr,
    featurize_documents,
    ingest_corpus,
    surface_hypotheses,
    verify_all,
)

CORPUS = Path(__file__).resolve().parent.parent / "data" / "corpus_mvp.json"

ALPHA = 0.05            # target FDR
MIN_RESOLUTION = 20     # min eligible matched pairs, else INCONCLUSIVE
N_LENGTH_BANDS = 2      # coarse length stratification (short/long by median)
MIN_DF, MAX_DF = 2, 0.9


def main() -> None:
    print("Axon MVP — lexical proximity, random-pair null, BH-FDR")
    print(f"(deterministic: exhaustive null, no RNG; alpha={ALPHA}, "
          f"min_resolution={MIN_RESOLUTION}, length_bands={N_LENGTH_BANDS})\n")

    # 1) Perception
    docs = list(ingest_corpus(CORPUS))
    print(f"[perception] ingested {len(docs)} documents from {CORPUS.name}")

    # 1b) Featurization (lexical baseline)
    featurizer = TfidfFeaturizer(min_df=MIN_DF, max_df=MAX_DF)
    docs = featurize_documents(featurizer, docs)
    print(f"[featurize]  TF-IDF lexical baseline, vocabulary dim = {featurizer.dim}")

    # 2) Relational representation
    store = RelationStore(dim=featurizer.dim, n_length_bands=N_LENGTH_BANDS)
    for d in docs:
        store.observe(d)
    candidates = store.candidate_relations(threshold=0.0)  # all pairs; FDR across all
    print(f"[relational] proposed {len(candidates)} candidate proximity relations "
          f"(all pairs; structural_score={store.structural_score:.3f})")

    # 3) Verification — random-pair null, then FDR across the full tested family
    registry = VerifierRegistry()
    registry.register(RelationKind.PROXIMITY,
                      RandomPairProximityVerifier(min_resolution=MIN_RESOLUTION))
    results_raw = verify_all(candidates, registry, store)
    results = apply_fdr(results_raw, alpha=ALPHA)

    def dompair(r) -> str:
        return (f"{store.domain_of(r.candidate.source_id)[:5]}~"
                f"{store.domain_of(r.candidate.target_id)[:5]}")

    # Top candidates by similarity: raw p vs FDR q, with verdict.
    ranked = sorted(results, key=lambda r: r.statistic, reverse=True)
    print("\n[verification] top 8 candidates by cosine (raw p -> FDR q):")
    for r in ranked[:8]:
        p = "  n/a " if r.p_value is None else f"{r.p_value:.4f}"
        q = "  n/a " if r.q_value is None else f"{r.q_value:.4f}"
        print(f"    {r.candidate.source_id:>12} ~ {r.candidate.target_id:<12} "
              f"[{dompair(r):>11}]  cos={r.statistic:+.3f}  p={p}  q={q}  "
              f"-> {r.verdict.value.upper()}")

    # 4) Hypothesis — accepted only; nulls/rejected stay visible as counts.
    report = surface_hypotheses(results)
    print(f"\n[hypothesis] verdict counts (of {len(results)} tested): {report.counts}")
    print(f"[hypothesis] surfaced {len(report.hypotheses)} hypothesis/-es (ACCEPTED only):")
    for h in report.hypotheses:
        print(f"    - {h.statement}")
    if not report.hypotheses:
        print("    (none survived FDR — an honest null is a valid outcome)")

    # Honest cross-domain NULL: a pair across domains that did NOT survive.
    cross_nulls = [
        r for r in results
        if store.domain_of(r.candidate.source_id) != store.domain_of(r.candidate.target_id)
        and r.verdict in (Verdict.NULL, Verdict.REJECTED)
    ]
    if cross_nulls:
        ex = max(cross_nulls, key=lambda r: r.statistic)
        print("\n[honest null] highest-similarity cross-domain pair that did NOT survive:")
        print(f"    {ex.candidate.source_id} ~ {ex.candidate.target_id} "
              f"[{dompair(ex)}]  cos={ex.statistic:+.3f}  "
              f"p={ex.p_value}  q={ex.q_value}  -> {ex.verdict.value.upper()}")
        print(f"    reason: {ex.reasoning}")


if __name__ == "__main__":
    main()
