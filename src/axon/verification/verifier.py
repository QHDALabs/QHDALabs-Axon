"""
axon.verification.verifier — Stage 3: criticise candidate relations.

This is the core of Axon. Generating candidate relations is cheap; rejecting the
false ones is the real work (Manifest, IV). Every candidate must pass through here
before it can ever reach the hypothesis stage.

Contract for any verifier:
  - It must define an EXPLICIT null/control (what "no effect" looks like,
    quantitatively) before looking at the result.
  - It must be able to return REJECTED or NULL — a verifier that can only accept
    is a noise generator, not a verifier.
  - It must report enough resolution to justify its verdict, and downgrade to
    INCONCLUSIVE rather than overclaim when resolution is too low.
  - It must NOT return ACCEPTED on its own. A single test cannot earn acceptance;
    that is decided across the whole tested family by FDR control
    (``multiple_testing.apply_fdr``). Verifiers return INCONCLUSIVE / REJECTED /
    NULL; apply_fdr promotes the survivors to ACCEPTED.

The MVP implements ONE real verifier: ``RandomPairProximityVerifier`` for
``RelationKind.PROXIMITY``, using an EMPIRICAL RANDOM-PAIR NULL.

Why not permute vector dimensions? An earlier reference permuted the components of
the target vector. For real text vectors that is an INVALID null: it only asks
"is this pair more aligned than a random direction?", a near-trivial bar that
inflates significance. The valid question is "is this pair more similar than
typical pairs FROM THE SAME CORPUS, matched on the obvious confounders (domain and
length)?" — which is what the random-pair null below answers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Protocol, Sequence, Tuple

import numpy as np

from ..types import CandidateRelation, RelationKind, Verdict, VerificationResult


class CorpusContext(Protocol):
    """What a proximity verifier reads from Stage 2 to build its random-pair null.

    Implemented by ``RelationStore``. Exposes the corpus so the null can be drawn
    from real pairs and matched on confounders (domain, length band).
    """

    def vector_for(self, doc_id: str) -> np.ndarray: ...
    def all_doc_ids(self) -> Sequence[str]: ...
    def domain_of(self, doc_id: str) -> str: ...
    def length_band_of(self, doc_id: str) -> int: ...


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class Verifier:
    """
    Abstract base. Subclasses criticise a candidate against an explicit null.

    The base intentionally provides no default — there is no domain-agnostic way
    to criticise a relation, and a silent default would be exactly the "accept
    everything" failure mode the whole stage exists to prevent.
    """

    def verify(self, candidate: CandidateRelation, context: CorpusContext) -> VerificationResult:
        raise NotImplementedError(
            "Verifier is abstract. Implement verify() with an explicit null model "
            "and a verdict that can be REJECTED/NULL, not just ACCEPTED."
        )


# Stratum key: (sorted domain pair, sorted length-band pair).
_StratumKey = Tuple[Tuple[str, str], Tuple[int, int]]


@dataclass
class _CorpusPairs:
    """Precomputed, per-context: similarity matrix + eligible pairs per stratum."""

    pos: Dict[str, int]
    sim: np.ndarray
    pairs_by_stratum: Dict[_StratumKey, List[Tuple[int, int]]] = field(default_factory=dict)


class RandomPairProximityVerifier(Verifier):
    """
    Verifier for ``RelationKind.PROXIMITY`` using an EMPIRICAL RANDOM-PAIR NULL.

    Null model (explicit): the distribution of cosine similarity over real
    document pairs drawn from the SAME corpus, STRATIFIED so each candidate is
    compared only against random pairs matched on its confounders — the unordered
    pair of domains and the unordered pair of length bands. The candidate's own
    pair is excluded from its null.

    p = (#{ stratified random pairs with cos >= observed } + 1) / (n + 1), one-sided.

    Verdict (local; never ACCEPTED here):
      - eligible pairs < ``min_resolution``  -> INCONCLUSIVE (too coarse to decide)
      - observed below the null mean          -> REJECTED   (worse than chance)
      - otherwise                             -> NULL        (provisional; FDR decides)

    Deterministic: with a small corpus the null enumerates ALL eligible pairs, so
    no randomness is involved. Featurizer-agnostic: it reads only vectors, so real
    embeddings can replace TF-IDF without changing this null.
    """

    def __init__(self, *, min_resolution: int = 20) -> None:
        self.min_resolution = int(min_resolution)
        self._cache: Dict[int, _CorpusPairs] = {}

    def _precompute(self, context: CorpusContext) -> _CorpusPairs:
        key = id(context)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        ids = list(context.all_doc_ids())
        pos = {doc_id: i for i, doc_id in enumerate(ids)}
        if not ids:
            pre = _CorpusPairs(pos=pos, sim=np.empty((0, 0)))
            self._cache[key] = pre
            return pre

        mat = np.vstack([np.asarray(context.vector_for(d), dtype=float) for d in ids])
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        unit = mat / norms
        sim = unit @ unit.T

        domains = [context.domain_of(d) for d in ids]
        bands = [context.length_band_of(d) for d in ids]

        pairs: Dict[_StratumKey, List[Tuple[int, int]]] = {}
        n = len(ids)
        for i in range(n):
            for j in range(i + 1, n):
                dpair = tuple(sorted((domains[i], domains[j])))
                bpair = tuple(sorted((bands[i], bands[j])))
                skey: _StratumKey = (dpair, bpair)  # type: ignore[assignment]
                pairs.setdefault(skey, []).append((i, j))

        pre = _CorpusPairs(pos=pos, sim=sim, pairs_by_stratum=pairs)
        self._cache[key] = pre
        return pre

    def verify(self, candidate: CandidateRelation, context: CorpusContext) -> VerificationResult:
        if candidate.kind is not RelationKind.PROXIMITY:
            raise NotImplementedError(
                f"RandomPairProximityVerifier only handles {RelationKind.PROXIMITY!r}, "
                f"got {candidate.kind!r}."
            )
        pre = self._precompute(context)
        ia = pre.pos[candidate.source_id]
        ib = pre.pos[candidate.target_id]
        lo, hi = (ia, ib) if ia < ib else (ib, ia)
        observed = float(pre.sim[lo, hi])

        dpair = tuple(sorted((context.domain_of(candidate.source_id),
                              context.domain_of(candidate.target_id))))
        bpair = tuple(sorted((context.length_band_of(candidate.source_id),
                              context.length_band_of(candidate.target_id))))
        skey: _StratumKey = (dpair, bpair)  # type: ignore[assignment]

        eligible = pre.pairs_by_stratum.get(skey, [])
        null = np.array(
            [pre.sim[i, j] for (i, j) in eligible if (i, j) != (lo, hi)],
            dtype=float,
        )
        n = int(null.size)

        null_desc = (
            f"random within-corpus pairs matched on domain & length band "
            f"(domains={dpair}, bands={bpair}); one-sided cosine upper tail, "
            f"n={n} eligible pairs"
        )

        if n < self.min_resolution:
            return VerificationResult(
                candidate=candidate,
                verdict=Verdict.INCONCLUSIVE,
                statistic=observed,
                p_value=None,
                null_model=null_desc,
                n_resolution=n,
                reasoning=(
                    f"only {n} eligible matched pairs < min {self.min_resolution}; "
                    "too coarse to decide"
                ),
            )

        p = float((np.sum(null >= observed) + 1) / (n + 1))
        null_mean = float(null.mean())
        if observed < null_mean:
            verdict = Verdict.REJECTED
            reason = (
                f"cosine {observed:.3f} below matched-null mean {null_mean:.3f}; "
                "worse than typical comparable pairs"
            )
        else:
            verdict = Verdict.NULL
            reason = (
                f"cosine {observed:.3f} vs matched null mean {null_mean:.3f} "
                f"(raw p={p:.4f}); pending FDR"
            )

        return VerificationResult(
            candidate=candidate,
            verdict=verdict,
            statistic=observed,
            p_value=p,
            null_model=null_desc,
            n_resolution=n,
            reasoning=reason,
        )
