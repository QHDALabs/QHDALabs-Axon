"""End-to-end MVP test on the committed real corpus.

Pins the HONEST result: under a valid random-pair null with BH-FDR across all
pairs, no lexical-proximity relation survives in this 40-document corpus. This is
deterministic (exhaustive null, no RNG). The test guards the methodology, not a
"nice" outcome — zero accepted is the correct, reported result."""

from pathlib import Path

import pytest

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


@pytest.fixture(scope="module")
def results():
    docs = featurize_documents(
        TfidfFeaturizer(min_df=2, max_df=0.9), list(ingest_corpus(CORPUS))
    )
    store = RelationStore(dim=docs[0].vector.shape[0], n_length_bands=2)
    for d in docs:
        store.observe(d)
    candidates = store.candidate_relations(threshold=0.0)
    reg = VerifierRegistry()
    reg.register(RelationKind.PROXIMITY, RandomPairProximityVerifier(min_resolution=20))
    raw = verify_all(candidates, reg, store)
    return store, raw, apply_fdr(raw, alpha=0.05)


def test_corpus_has_two_domains_40_docs():
    docs = list(ingest_corpus(CORPUS))
    assert len(docs) == 40
    domains = {d.metadata["domain"] for d in docs}
    assert domains == {"astrophysics", "neuroscience"}


def test_all_pairs_tested(results):
    _, raw, _ = results
    assert len(raw) == 40 * 39 // 2  # 780


def test_fdr_rejects_everything_honestly(results):
    """Nominal significance exists, but nothing survives FDR — the whole point."""
    _, raw, fdr = results
    nominal = [r for r in raw if r.p_value is not None and r.p_value < 0.05]
    assert len(nominal) > 0                       # the naive view would "find" links
    report = surface_hypotheses(fdr)
    assert report.counts["accepted"] == 0         # the valid null + FDR rejects them
    assert report.counts["inconclusive"] == 0
    assert report.counts["accepted"] + report.counts["rejected"] + report.counts["null"] == 780


def test_has_an_honest_cross_domain_null(results):
    store, _, fdr = results
    cross_nulls = [
        r for r in fdr
        if store.domain_of(r.candidate.source_id) != store.domain_of(r.candidate.target_id)
        and r.verdict in (Verdict.NULL, Verdict.REJECTED)
    ]
    assert cross_nulls  # at least one cross-domain pair that does not survive


def test_deterministic(results):
    """Re-running the pipeline yields identical p-values (no RNG)."""
    docs = featurize_documents(
        TfidfFeaturizer(min_df=2, max_df=0.9), list(ingest_corpus(CORPUS))
    )
    store = RelationStore(dim=docs[0].vector.shape[0], n_length_bands=2)
    for d in docs:
        store.observe(d)
    reg = VerifierRegistry()
    reg.register(RelationKind.PROXIMITY, RandomPairProximityVerifier(min_resolution=20))
    raw2 = verify_all(store.candidate_relations(threshold=0.0), reg, store)
    _, raw, _ = results
    p1 = [r.p_value for r in raw]
    p2 = [r.p_value for r in raw2]
    assert p1 == p2
