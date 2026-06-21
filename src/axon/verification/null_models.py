"""
axon.verification.null_models — explicit null/control models, pure numpy.

These are the methodological backbone of the verification stage. They are real,
working implementations (not stubs): generating an explicit, quantitative null
is the whole point — "no effect" must have a concrete numerical form
(VERIFICATION_LOG, rule 2).

Pure numpy on purpose, matching qhda-core's relational layer ethos: no scipy
dependency until numpy genuinely runs out. Permutation and bootstrap need only
shuffling and resampling.

Resolution matters (VERIFICATION_LOG, rule 4): too few permutations give a coarse
p-value and false conclusions. ``permutation_p_value`` reports ``n_permutations``
so callers can downgrade a verdict to INCONCLUSIVE when resolution is too low.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class NullResult:
    """
    Outcome of comparing an observed statistic against an explicit null.

    Fields:
      observed       : the statistic computed on the real data.
      p_value        : fraction of null draws at least as extreme (one-sided,
                       upper tail), with the standard +1/+1 correction so a
                       p-value is never exactly 0.
      n_resolution   : number of null draws (permutations/resamples). The finest
                       resolvable p-value is ~1/(n+1).
      null_mean      : mean of the null distribution (for reporting/effect size).
      null_std       : std of the null distribution.
    """

    observed: float
    p_value: float
    n_resolution: int
    null_mean: float
    null_std: float


def permutation_p_value(
    statistic: Callable[[np.ndarray], float],
    data: np.ndarray,
    permute: Callable[[np.ndarray, np.random.Generator], np.ndarray],
    *,
    n_permutations: int = 1000,
    rng: np.random.Generator | None = None,
    seed: int | None = None,
) -> NullResult:
    """
    One-sided (upper-tail) permutation test.

    Input:
      statistic : maps a dataset to a scalar test statistic.
      data      : the observed dataset.
      permute   : produces one null dataset from ``data`` under H0 (e.g. shuffle
                  labels / break the association being tested). MUST destroy only
                  the structure under test, preserving marginals.
      n_permutations : number of null draws. More = finer p-value resolution.
      rng       : explicit numpy Generator (takes precedence over ``seed``).
      seed      : convenience reproducibility seed used when ``rng`` is None.
                  Default None => non-deterministic (production default).

    Output: a ``NullResult``.

    Note: this is generic and correct, but it can only be as good as ``permute``.
    Choosing a null that destroys exactly the structure under test (and nothing
    else) is the substantive, domain-specific judgement — see ``verifier``.
    """
    if rng is None:
        rng = np.random.default_rng(seed)
    observed = float(statistic(data))
    null = np.empty(n_permutations, dtype=float)
    for k in range(n_permutations):
        null[k] = float(statistic(permute(data, rng)))
    # +1 correction: count the observed value itself among the draws.
    p = (np.sum(null >= observed) + 1) / (n_permutations + 1)
    return NullResult(
        observed=observed,
        p_value=float(p),
        n_resolution=n_permutations,
        null_mean=float(null.mean()),
        null_std=float(null.std()),
    )


def bootstrap_ci(
    statistic: Callable[[np.ndarray], float],
    data: np.ndarray,
    *,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    rng: np.random.Generator | None = None,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """
    Percentile bootstrap confidence interval for a statistic.

    Input : ``statistic``, observed ``data`` (resampled along axis 0), resample
            count, two-sided ``alpha``. ``rng`` takes precedence over ``seed``;
            ``seed`` is a convenience reproducibility seed (default None =>
            non-deterministic, the production default).
    Output: ``(point_estimate, ci_low, ci_high)``.

    Pure numpy; reported for effect-size honesty alongside the p-value.
    """
    if rng is None:
        rng = np.random.default_rng(seed)
    n = data.shape[0]
    point = float(statistic(data))
    draws = np.empty(n_resamples, dtype=float)
    for k in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        draws[k] = float(statistic(data[idx]))
    lo = float(np.quantile(draws, alpha / 2))
    hi = float(np.quantile(draws, 1 - alpha / 2))
    return point, lo, hi
