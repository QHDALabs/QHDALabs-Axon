"""
axon.hypothesis.surface — Stage 4: turn verified results into hypotheses.

Discoveries are the OUTPUT of verification, never an input to it. This module
makes that structural, not merely conventional:

  - its only input type is ``VerificationResult`` (the Stage-3 output);
  - it actively refuses anything else (e.g. a raw ``CandidateRelation``) with a
    ``TypeError`` — there is no code path that surfaces an unverified relation;
  - only ACCEPTED results become hypotheses; REJECTED / NULL / INCONCLUSIVE are
    reported as counts (they are first-class data), never silently dropped.

A hypothesis module that could run before verification would be a bug. Here it
cannot: feed it candidates and it raises.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..types import Hypothesis, Verdict, VerificationResult


@dataclass(frozen=True)
class SurfaceReport:
    """
    Result of a surfacing pass.

    ``hypotheses`` holds only what survived verification. ``counts`` records the
    full verdict breakdown so the null/rejected results stay visible — an honest
    "we rejected N of M" is part of the output, not an embarrassment to hide.
    """

    hypotheses: List[Hypothesis]
    counts: dict


def _require_verified(item: object) -> VerificationResult:
    """Guard: the only thing that may enter Stage 4 is a VerificationResult."""
    if not isinstance(item, VerificationResult):
        raise TypeError(
            "hypothesis stage accepts only VerificationResult (the output of "
            f"verification), got {type(item).__name__}. Verification precedes "
            "discovery — there is no path from a raw candidate to a hypothesis."
        )
    return item


def _statement_for(result: VerificationResult) -> str:
    """Render a plain-language claim for an accepted relation."""
    c = result.candidate
    return (
        f"{c.source_id} and {c.target_id} are related ({c.kind}): "
        f"statistic={result.statistic:.3f}, p={result.p_value!r} "
        f"vs null [{result.null_model}]."
    )


def surface_hypotheses(results: Iterable[object]) -> SurfaceReport:
    """
    Surface hypotheses from verification results.

    Input : an iterable of ``VerificationResult`` (anything else raises).
    Output: a ``SurfaceReport`` with accepted-only hypotheses plus the full
            verdict counts.

    This is a real, minimal implementation: it filters to ACCEPTED, wraps each
    into a ``Hypothesis`` carrying its full audit trail, and tallies every
    verdict. The "intelligence" of ranking/clustering hypotheses is future work
    and is intentionally not faked here.
    """
    counts = {v: 0 for v in Verdict}
    hypotheses: List[Hypothesis] = []

    for item in results:
        result = _require_verified(item)
        counts[result.verdict] += 1
        if result.is_accepted:
            hypotheses.append(
                Hypothesis(
                    statement=_statement_for(result),
                    result=result,
                    provenance=tuple(result.candidate.provenance),
                )
            )

    return SurfaceReport(
        hypotheses=hypotheses,
        counts={v.value: n for v, n in counts.items()},
    )
