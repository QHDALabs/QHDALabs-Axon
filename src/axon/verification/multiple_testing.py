"""
axon.verification.multiple_testing — Benjamini-Hochberg FDR control, pure numpy.

Proposing many candidate relations and testing each one is a false-positive
generator unless the multiple comparisons are accounted for. FDR control is part
of "reject false connections", not an optional add-on.

``benjamini_hochberg`` is the numeric primitive. ``apply_fdr`` is the policy that
turns it into verdicts: ACCEPTED is assigned HERE and only here — a single
verifier reports a p-value and a provisional NULL/REJECTED, and acceptance is
decided across the whole tested family. No verifier can accept on its own.
"""

from __future__ import annotations

import dataclasses
from typing import List, Sequence, Tuple

import numpy as np

from ..types import Verdict, VerificationResult


def benjamini_hochberg(
    pvalues: Sequence[float], alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Benjamini-Hochberg step-up FDR.

    Input : a sequence of p-values and the target FDR ``alpha``.
    Output: ``(rejected, qvalues)`` aligned to the input order, where ``rejected``
            is a boolean mask of hypotheses significant at FDR ``alpha`` and
            ``qvalues`` are the BH-adjusted p-values (clipped to [0, 1]).

    Pure numpy. ``rejected == (qvalues <= alpha)`` by construction, which is the
    standard step-up rule.
    """
    p = np.asarray(pvalues, dtype=float)
    n = p.size
    if n == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=float)

    order = np.argsort(p, kind="mergesort")
    ranked = p[order]
    ranks = np.arange(1, n + 1, dtype=float)

    # BH-adjusted p-values, made monotone non-decreasing from the largest p down.
    q_sorted = ranked * n / ranks
    q_sorted = np.minimum.accumulate(q_sorted[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0.0, 1.0)

    qvalues = np.empty(n, dtype=float)
    qvalues[order] = q_sorted
    rejected = qvalues <= alpha
    return rejected, qvalues


def apply_fdr(
    results: Sequence[VerificationResult], alpha: float = 0.05
) -> List[VerificationResult]:
    """
    Apply BH-FDR across the full tested family and assign final ACCEPTED verdicts.

    Family : every result that received a usable p-value (verdict NULL or
             REJECTED). INCONCLUSIVE results carry no p-value and are excluded from
             the family and left unchanged.
    Effect : each family member gets its ``q_value``; a NULL result that BH rejects
             becomes ACCEPTED. REJECTED stays REJECTED (it is worse than chance; its
             p-value is high and BH would not reject it anyway).

    Returns NEW result objects (inputs are frozen and untouched).
    """
    out = list(results)
    family = [
        i
        for i, r in enumerate(out)
        if r.p_value is not None and r.verdict in (Verdict.NULL, Verdict.REJECTED)
    ]
    if not family:
        return out

    pvals = [out[i].p_value for i in family]
    rejected, qvalues = benjamini_hochberg([p for p in pvals if p is not None], alpha)

    for k, i in enumerate(family):
        r = out[i]
        q = float(qvalues[k])
        if bool(rejected[k]) and r.verdict is Verdict.NULL:
            verdict = Verdict.ACCEPTED
            reason = f"{r.reasoning}; BH-FDR significant (q={q:.4f} <= {alpha})"
        elif r.verdict is Verdict.NULL:
            verdict = Verdict.NULL
            reason = f"{r.reasoning}; not significant after BH-FDR (q={q:.4f})"
        else:  # REJECTED stays REJECTED
            verdict = r.verdict
            reason = r.reasoning
        out[i] = dataclasses.replace(r, verdict=verdict, q_value=q, reasoning=reason)

    return out
