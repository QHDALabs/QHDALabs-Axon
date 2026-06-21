"""
axon.verification.verifier — Stage 3: criticise candidate relations.

This is the core of Axon. Generating candidate relations is cheap; rejecting the
false ones is the real work (Manifest, IV). Every candidate must pass through
here before it can ever reach the hypothesis stage.

Contract for any verifier:
  - It must define an EXPLICIT null/control (what "no effect" looks like,
    quantitatively) before looking at the result.
  - It must be able to return REJECTED or NULL — a verifier that can only accept
    is a noise generator, not a verifier.
  - It must report enough resolution to justify its verdict, and downgrade to
    INCONCLUSIVE rather than overclaim when resolution is too low.

The abstract ``Verifier`` states this contract and refuses to guess
(NotImplementedError). ``PermutationVerifier`` is a minimal, clearly-labeled
REFERENCE implementation for proximity candidates that genuinely runs a
permutation null and can reject.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from ..types import CandidateRelation, Verdict, VerificationResult
from .null_models import permutation_p_value


class VectorContext(Protocol):
    """Minimal context a verifier reads from Stage 2: a vector per doc_id."""

    def vector_for(self, doc_id: str) -> np.ndarray: ...


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class Verifier:
    """
    Abstract base. Subclasses criticise a candidate against an explicit null.

    Subclasses must implement ``verify``. The base intentionally does not provide
    a default — there is no domain-agnostic way to criticise a relation, and a
    silent default would be exactly the "accept everything" failure mode the
    whole stage exists to prevent.
    """

    def verify(self, candidate: CandidateRelation, context: VectorContext) -> VerificationResult:
        """
        Input : a ``CandidateRelation`` and the Stage-2 context it came from.
        Output: a ``VerificationResult`` with an explicit verdict, statistic,
                p-value and a stated null model.

        NOT IMPLEMENTED in the base class — choosing the null and statistic for a
        relation ``kind`` is the substantive work and must be done explicitly.
        """
        raise NotImplementedError(
            "Verifier is abstract. Implement verify() with an explicit null model "
            "and a verdict that can be REJECTED/NULL, not just ACCEPTED."
        )


class PermutationVerifier(Verifier):
    """
    Reference verifier for "proximity" candidates (cosine similarity of vectors).

    Null model (explicit): hold the source vector fixed and permute the
    components of the target vector. This breaks any positional alignment between
    the two vectors while preserving each vector's magnitude profile. Under H0
    (the two items are not aligned beyond chance), the observed cosine should sit
    inside the permutation distribution.

    Verdict logic:
      - resolution below ``min_resolution``        -> INCONCLUSIVE
      - p < alpha                                  -> ACCEPTED  (beats the null)
      - observed below the null mean               -> REJECTED  (worse than chance)
      - otherwise                                  -> NULL      (indistinguishable)

    This really can reject: two vectors that are similar only by chance land at
    high p and are NOT surfaced. That rejection is a first-class result.
    """

    def __init__(
        self,
        *,
        alpha: float = 0.05,
        n_permutations: int = 1000,
        min_resolution: int = 200,
        seed: int | None = None,
    ) -> None:
        self.alpha = float(alpha)
        self.n_permutations = int(n_permutations)
        self.min_resolution = int(min_resolution)
        self._seed = seed

    def verify(self, candidate: CandidateRelation, context: VectorContext) -> VerificationResult:
        if candidate.kind != "proximity":
            raise NotImplementedError(
                f"PermutationVerifier only handles kind='proximity', "
                f"got {candidate.kind!r}. Implement a verifier for that kind."
            )
        v_src = np.asarray(context.vector_for(candidate.source_id), dtype=float)
        v_tgt = np.asarray(context.vector_for(candidate.target_id), dtype=float)

        rng = np.random.default_rng(self._seed)
        null = permutation_p_value(
            statistic=lambda x: _cosine(v_src, x),
            data=v_tgt,
            permute=lambda x, r: r.permutation(x),
            n_permutations=self.n_permutations,
            rng=rng,
        )

        null_desc = (
            f"permute target-vector components, fixed source; "
            f"one-sided cosine upper tail, n={null.n_resolution}"
        )

        if null.n_resolution < self.min_resolution:
            verdict = Verdict.INCONCLUSIVE
            reason = (
                f"resolution {null.n_resolution} < min {self.min_resolution}; "
                "p-value too coarse to decide"
            )
        elif null.p_value < self.alpha:
            verdict = Verdict.ACCEPTED
            reason = f"cosine {null.observed:.3f} beats null (p={null.p_value:.4f} < {self.alpha})"
        elif null.observed < null.null_mean:
            verdict = Verdict.REJECTED
            reason = (
                f"cosine {null.observed:.3f} below null mean {null.null_mean:.3f}; "
                "worse than chance"
            )
        else:
            verdict = Verdict.NULL
            reason = (
                f"cosine {null.observed:.3f} indistinguishable from null "
                f"(p={null.p_value:.4f} >= {self.alpha})"
            )

        return VerificationResult(
            candidate=candidate,
            verdict=verdict,
            statistic=null.observed,
            p_value=null.p_value,
            null_model=null_desc,
            n_resolution=null.n_resolution,
            reasoning=reason,
        )


def verify_all(
    candidates, verifier: Verifier, context: VectorContext
) -> list[VerificationResult]:
    """
    Run a verifier over many candidates. Convenience for the pipeline.

    Returns ALL results, including REJECTED/NULL/INCONCLUSIVE — they are data,
    not noise to be silently dropped. Filtering to accepted results happens only
    at the hypothesis stage.
    """
    return [verifier.verify(c, context) for c in candidates]
