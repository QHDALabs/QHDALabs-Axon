"""
axon.verification.bridge — Stage 3 for ABC bridges (Swanson closed discovery).

An ABC bridge connects two literatures A and C that share little surface
vocabulary, through intermediate B-terms present in both. Direct A-C similarity is
LOW; B-mediated connectivity is HIGH. The verifier must separate these: a
high-direct-similarity pair is proximity, not a bridge.

Bridge statistic (over a term substrate, MeSH descriptors by default):
  profile w_L[t] = mean term-frequency over L's docs * idf[t]      (idf from background)
  B-selection (recomputed wherever profiles change — see below):
      t is a B-term iff  w_A[t] > 0 AND w_C[t] > 0  AND  t is non-generic
      non-generic := background_df_ratio[t] <= max_df  AND  t not in stoplist
                     AND  idf[t] >= idf_min
  direct_sim  = cosine(w_A, w_C) over the non-generic vocabulary  (must be LOW)
  mediated    = sum_{t in B} min(w_A[t], w_C[t])                  (the test statistic)

Two explicit nulls (both reported; max(p1, p2) must pass):
  1. random-literature-pair: mediated for two focused, unrelated background
     literatures (disjoint from A/C) of the same sizes.
  2. shuffled-B: permute w_C (preserving its marginal), breaking the specific
     A-B-C alignment.

CRITICAL — B is part of the statistic, not a pre-filter. B-selection is recomputed
on EVERY null replica (from the permuted / resampled profiles). Freezing B on the
observed pair would condition the null on the observed shared support and make it
far too lenient — the same selection-bias failure mode as in proximity. The
per-replica recomputation is done by ``_replica_mediated``.

Acceptance is via FDR only (``multiple_testing.apply_fdr``); this verifier returns
INCONCLUSIVE / REJECTED / NULL, never ACCEPTED.
"""

from __future__ import annotations

from typing import Any, List, Protocol, Sequence, Tuple

import numpy as np

from ..types import BridgeCandidate, RelationCandidate, RelationKind, Verdict, VerificationResult
from .verifier import Verifier

# Generic MeSH descriptors / check-tags that "bridge" everything; excluded from B.
DEFAULT_MESH_STOPLIST = frozenset(
    {
        "humans", "animals", "male", "female", "adult", "middle aged", "aged",
        "child", "child, preschool", "infant", "adolescent", "young adult",
        "rats", "mice", "rabbits", "dogs", "cattle", "in vitro techniques",
        "time factors", "retrospective studies", "prospective studies",
        "reproducibility of results", "sensitivity and specificity",
    }
)


class LiteratureContext(Protocol):
    """Materials the ABC-bridge verifier reads (implemented by LiteratureStore)."""

    def vocab(self) -> Sequence[str]: ...
    def idf(self) -> np.ndarray: ...
    def background_df_ratio(self) -> np.ndarray: ...
    def profile(self, label: str) -> np.ndarray: ...
    def literature_size(self, label: str) -> int: ...
    def background_topics(self) -> Sequence[str]: ...
    def sample_two_background_profiles(
        self, size_a: int, size_c: int, rng: np.random.Generator, exclude: frozenset[str]
    ) -> Tuple[np.ndarray, np.ndarray]: ...


def select_b_terms(w_a: np.ndarray, w_c: np.ndarray, non_generic: np.ndarray) -> np.ndarray:
    """B-term mask: shared support among non-generic terms. A FUNCTION of the
    profiles, so it is recomputed whenever the profiles change (per null replica)."""
    mask: np.ndarray = (w_a > 0.0) & (w_c > 0.0) & non_generic
    return mask


def mediated_score(w_a: np.ndarray, w_c: np.ndarray, b_mask: np.ndarray) -> float:
    """Mediated connectivity: sum of min(w_a, w_c) over the B-terms."""
    if not b_mask.any():
        return 0.0
    return float(np.minimum(w_a, w_c)[b_mask].sum())


def _replica_mediated(w_a: np.ndarray, w_c: np.ndarray, non_generic: np.ndarray) -> float:
    """Mediated score with B RE-SELECTED from these (possibly permuted/resampled)
    profiles. Used by both nulls so B is never frozen on the observed pair."""
    return mediated_score(w_a, w_c, select_b_terms(w_a, w_c, non_generic))


def direct_similarity(w_a: np.ndarray, w_c: np.ndarray, non_generic: np.ndarray) -> float:
    """Cosine of the two profiles over the non-generic vocabulary."""
    a = w_a * non_generic
    c = w_c * non_generic
    na = float(np.linalg.norm(a))
    nc = float(np.linalg.norm(c))
    if na == 0.0 or nc == 0.0:
        return 0.0
    return float(np.dot(a, c) / (na * nc))


def _shuffled_b_null(
    w_a: np.ndarray,
    w_c: np.ndarray,
    non_generic: np.ndarray,
    common_pool: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Shuffled-B null, restricted to the COMMON POOL (terms with background_df>0).

    Only w_c weights on shareable, cross-literature terms are permuted; literature-
    PRIVATE terms (background_df==0, e.g. each literature's own dominant vocabulary)
    stay fixed. This breaks the specific A-B-C alignment within the pool where
    bridges actually live, WITHOUT manufacturing private-term overlaps (A-dom x
    C-dom) that are impossible in the observed data. B is still re-selected per
    replica."""
    pool_idx = np.flatnonzero(common_pool)
    null = np.empty(n, dtype=float)
    for r in range(n):
        w_c_perm = w_c.copy()
        w_c_perm[pool_idx] = w_c[pool_idx][rng.permutation(pool_idx.size)]
        null[r] = _replica_mediated(w_a, w_c_perm, non_generic)  # B recomputed
    return null


def _random_pair_null(
    context: LiteratureContext,
    a_label: str,
    c_label: str,
    non_generic: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    size_a = context.literature_size(a_label)
    size_c = context.literature_size(c_label)
    exclude = frozenset({a_label, c_label})
    null = np.empty(n, dtype=float)
    for r in range(n):
        w_a2, w_c2 = context.sample_two_background_profiles(size_a, size_c, rng, exclude)
        null[r] = _replica_mediated(w_a2, w_c2, non_generic)     # B recomputed
    return null


def propose_bridge(
    context: LiteratureContext,
    a_label: str,
    c_label: str,
    *,
    stoplist: frozenset[str] = DEFAULT_MESH_STOPLIST,
    max_df: float = 0.5,
    idf_min: float = 1.0,
) -> BridgeCandidate:
    """Build a closed-discovery bridge candidate for literatures A and C.

    Computes the observed B-terms and mediated score for the proposal's evidence;
    the verifier recomputes everything against the nulls."""
    non_generic = _non_generic_mask(context, stoplist, max_df, idf_min)
    w_a = context.profile(a_label)
    w_c = context.profile(c_label)
    b_mask = select_b_terms(w_a, w_c, non_generic)
    vocab = context.vocab()
    b_terms = tuple(vocab[int(i)] for i in np.flatnonzero(b_mask))
    med = mediated_score(w_a, w_c, b_mask)
    dsim = direct_similarity(w_a, w_c, non_generic)
    return BridgeCandidate(
        kind=RelationKind.ABC_BRIDGE,
        a_label=a_label,
        c_label=c_label,
        b_terms=b_terms,
        score=med,
        evidence={"mediated": med, "direct_sim": dsim, "n_b_terms": len(b_terms)},
        provenance=(a_label, c_label),
    )


def _non_generic_mask(
    context: LiteratureContext, stoplist: frozenset[str], max_df: float, idf_min: float
) -> np.ndarray:
    vocab = context.vocab()
    stop_mask = np.array([v in stoplist for v in vocab], dtype=bool)
    mask: np.ndarray = (
        (context.background_df_ratio() <= max_df)
        & (~stop_mask)
        & (context.idf() >= idf_min)
    )
    return mask


class AbcBridgeVerifier(Verifier):
    """ABC-bridge verifier for ``RelationKind.ABC_BRIDGE`` (closed discovery)."""

    def __init__(
        self,
        *,
        stoplist: frozenset[str] = DEFAULT_MESH_STOPLIST,
        max_df: float = 0.5,
        idf_min: float = 1.0,
        min_b_terms: int = 2,
        direct_max: float = 0.30,
        n_random_pairs: int = 2000,
        n_shuffles: int = 2000,
        seed: int = 0,
    ) -> None:
        self.stoplist = stoplist
        self.max_df = float(max_df)
        self.idf_min = float(idf_min)
        self.min_b_terms = int(min_b_terms)
        self.direct_max = float(direct_max)
        self.n_random_pairs = int(n_random_pairs)
        self.n_shuffles = int(n_shuffles)
        self.seed = int(seed)

    def verify(self, candidate: RelationCandidate, context: Any) -> VerificationResult:
        if not isinstance(candidate, BridgeCandidate) or candidate.kind is not RelationKind.ABC_BRIDGE:
            raise NotImplementedError(
                f"AbcBridgeVerifier only handles {RelationKind.ABC_BRIDGE!r} "
                f"BridgeCandidate, got {candidate!r}."
            )
        ctx: LiteratureContext = context
        non_generic = _non_generic_mask(ctx, self.stoplist, self.max_df, self.idf_min)
        w_a = ctx.profile(candidate.a_label)
        w_c = ctx.profile(candidate.c_label)

        obs_b = select_b_terms(w_a, w_c, non_generic)
        n_b = int(obs_b.sum())
        dsim = direct_similarity(w_a, w_c, non_generic)
        obs_med = mediated_score(w_a, w_c, obs_b)

        null_desc = (
            f"max(random-literature-pair, shuffled-B restricted to common pool "
            f"[background_df>0]); B re-selected per replica; generic-B filter "
            f"(max_df={self.max_df}, idf_min={self.idf_min}, |stoplist|={len(self.stoplist)}); "
            f"direct_max={self.direct_max}; R={self.n_random_pairs}, "
            f"n_shuffles={self.n_shuffles}, seed={self.seed}"
        )

        if n_b < self.min_b_terms:
            return _result(candidate, Verdict.INCONCLUSIVE, obs_med, None, null_desc, n_b,
                           f"direct_sim={dsim:.3f}; only {n_b} B-terms < min "
                           f"{self.min_b_terms}; cannot resolve")

        if len([t for t in ctx.background_topics()
                if t not in (candidate.a_label, candidate.c_label)]) < 2:
            return _result(candidate, Verdict.INCONCLUSIVE, obs_med, None, null_desc, n_b,
                           "fewer than 2 background topics for the random-pair null")

        if dsim > self.direct_max:
            return _result(candidate, Verdict.REJECTED, obs_med, None, null_desc, n_b,
                           f"direct similarity {dsim:.3f} > {self.direct_max}; "
                           "this is proximity, not a bridge")

        common_pool = ctx.background_df_ratio() > 0.0
        rng = np.random.default_rng(self.seed)
        null_shuf = _shuffled_b_null(w_a, w_c, non_generic, common_pool, self.n_shuffles, rng)
        null_rand = _random_pair_null(ctx, candidate.a_label, candidate.c_label,
                                      non_generic, self.n_random_pairs, rng)

        p_shuf = float((np.sum(null_shuf >= obs_med) + 1) / (self.n_shuffles + 1))
        p_rand = float((np.sum(null_rand >= obs_med) + 1) / (self.n_random_pairs + 1))
        p = max(p_shuf, p_rand)
        resolution = min(self.n_random_pairs, self.n_shuffles)

        reason = (
            f"mediated={obs_med:.4f}, direct_sim={dsim:.3f}, |B|={n_b}; "
            f"p_random_pair={p_rand:.4f}, p_shuffled_B={p_shuf:.4f}, p=max={p:.4f}"
        )
        if obs_med < float(null_rand.mean()):
            verdict = Verdict.REJECTED
            reason = f"{reason}; below random-pair null mean (worse than chance)"
        else:
            verdict = Verdict.NULL
            reason = f"{reason}; pending FDR"

        return _result(candidate, verdict, obs_med, p, null_desc, resolution, reason)


def _result(
    candidate: BridgeCandidate,
    verdict: Verdict,
    statistic: float,
    p_value: Any,
    null_model: str,
    n_resolution: int,
    reasoning: str,
) -> VerificationResult:
    return VerificationResult(
        candidate=candidate,
        verdict=verdict,
        statistic=float(statistic),
        p_value=p_value,
        null_model=null_model,
        n_resolution=n_resolution,
        reasoning=reasoning,
    )
