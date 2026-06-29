"""Pair-selectivity audit for ABC bridge candidates.

This module is deliberately trust-removing and shadow-only.  It does not identify
siblings, confounding, mediation, or true bridges.  It asks only whether the
original pair is rank-selective against pre-specified endpoint substitutions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Callable, Mapping, Sequence


ALPHA_RANK_NOMINAL = 0.05
V1_MAX_DF = 0.5
V1_IDF_MIN = 1.0


class SideStatus(str, Enum):
    NOT_DETECTED = "not_detected"
    RISK = "pair_selectivity_not_demonstrated"
    UNASSESSABLE = "unassessable"


class AggregateStatus(str, Enum):
    NO_DEGRADATION = "no_degradation"
    DEGRADE_A = "pair_selectivity_not_demonstrated_a"
    DEGRADE_C = "pair_selectivity_not_demonstrated_c"
    DEGRADE_BOTH = "pair_selectivity_not_demonstrated_both"
    DEGRADE_COVERAGE_A = "coverage_a"
    DEGRADE_COVERAGE_C = "coverage_c"
    DEGRADE_COVERAGE_BOTH = "coverage_both"


@dataclass(frozen=True)
class PeerSet:
    """Deterministic selector output after profile availability is resolved.

    ``profiled_ids`` contribute to the rank denominator. ``missing_ids`` never
    become artificial zero scores. A profiled peer with a genuine mediated score
    of zero remains a valid observation and must stay in ``profiled_ids``.
    """

    endpoint_id: str
    ontology_ids: tuple[str, ...]
    profiled_ids: tuple[str, ...]
    missing_ids: tuple[str, ...] = ()
    provenance: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ontology = set(self.ontology_ids)
        profiled = set(self.profiled_ids)
        missing = set(self.missing_ids)
        if self.endpoint_id in ontology:
            raise ValueError("PeerSet must not include its endpoint")
        if len(ontology) != len(self.ontology_ids):
            raise ValueError("ontology_ids must be deduplicated")
        if not profiled.isdisjoint(missing):
            raise ValueError("profiled_ids and missing_ids must be disjoint")
        if profiled | missing != ontology:
            raise ValueError("profiled_ids and missing_ids must partition ontology_ids")


@dataclass(frozen=True)
class SideAssessment:
    status: SideStatus
    n_ontology: int
    n_profiled: int
    n_missing: int
    k_at_or_above_original: int | None
    p_rank_nominal: float | None
    alpha_rank_nominal: float
    reason: str


@dataclass(frozen=True)
class SelectivityAssessment:
    original_score: float
    side_a: SideAssessment
    side_c: SideAssessment
    aggregate: AggregateStatus
    peer_scores_a: tuple[float, ...]
    peer_scores_c: tuple[float, ...]
    provenance: Mapping[str, object] = field(default_factory=dict)


PairScorer = Callable[[str, str], float]


def minimum_rank_resolution(alpha: float = ALPHA_RANK_NOMINAL) -> int:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    return ceil(1.0 / alpha) - 1


def assess_rank(
    original_score: float,
    peer_scores: Sequence[float],
    *,
    n_ontology: int | None = None,
    alpha: float = ALPHA_RANK_NOMINAL,
) -> SideAssessment:
    """Run the exact conservative rank assessment for one endpoint side."""

    scores = tuple(float(score) for score in peer_scores)
    n_profiled = len(scores)
    n_total = n_profiled if n_ontology is None else int(n_ontology)
    if n_total < n_profiled:
        raise ValueError("n_ontology cannot be smaller than the profiled peer count")
    n_missing = n_total - n_profiled
    n_min = minimum_rank_resolution(alpha)
    if n_profiled < n_min:
        return SideAssessment(
            status=SideStatus.UNASSESSABLE,
            n_ontology=n_total,
            n_profiled=n_profiled,
            n_missing=n_missing,
            k_at_or_above_original=None,
            p_rank_nominal=None,
            alpha_rank_nominal=alpha,
            reason=(
                f"{n_profiled} profiled peers < derived minimum {n_min}; "
                "insufficient rank resolution"
            ),
        )

    k = sum(score >= float(original_score) for score in scores)
    p_rank = (k + 1.0) / (n_profiled + 1.0)
    status = SideStatus.NOT_DETECTED if p_rank <= alpha else SideStatus.RISK
    return SideAssessment(
        status=status,
        n_ontology=n_total,
        n_profiled=n_profiled,
        n_missing=n_missing,
        k_at_or_above_original=k,
        p_rank_nominal=p_rank,
        alpha_rank_nominal=alpha,
        reason=(
            f"k={k}, n_profiled={n_profiled}, "
            f"p_rank_nominal={p_rank:.6f}, alpha_rank_nominal={alpha:.6f}"
        ),
    )


def aggregate_sides(side_a: SideAssessment, side_c: SideAssessment) -> AggregateStatus:
    """IUT for no-degradation; OR for pair-nonselectivity risk."""

    a_risk = side_a.status is SideStatus.RISK
    c_risk = side_c.status is SideStatus.RISK
    if a_risk and c_risk:
        return AggregateStatus.DEGRADE_BOTH
    if a_risk:
        return AggregateStatus.DEGRADE_A
    if c_risk:
        return AggregateStatus.DEGRADE_C

    a_unassessable = side_a.status is SideStatus.UNASSESSABLE
    c_unassessable = side_c.status is SideStatus.UNASSESSABLE
    if a_unassessable and c_unassessable:
        return AggregateStatus.DEGRADE_COVERAGE_BOTH
    if a_unassessable:
        return AggregateStatus.DEGRADE_COVERAGE_A
    if c_unassessable:
        return AggregateStatus.DEGRADE_COVERAGE_C
    return AggregateStatus.NO_DEGRADATION


def assess_pair_selectivity(
    a_label: str,
    c_label: str,
    peers_a: PeerSet,
    peers_c: PeerSet,
    scorer: PairScorer,
    *,
    alpha: float = ALPHA_RANK_NOMINAL,
    provenance: Mapping[str, object] | None = None,
) -> SelectivityAssessment:
    """Score the original and every substitution fresh, then assess both sides."""

    if peers_a.endpoint_id != a_label or peers_c.endpoint_id != c_label:
        raise ValueError("PeerSet endpoint does not match the assessed pair")

    original = float(scorer(a_label, c_label))
    scores_a = tuple(float(scorer(peer, c_label)) for peer in peers_a.profiled_ids)
    scores_c = tuple(float(scorer(a_label, peer)) for peer in peers_c.profiled_ids)
    side_a = assess_rank(original, scores_a, n_ontology=len(peers_a.ontology_ids), alpha=alpha)
    side_c = assess_rank(original, scores_c, n_ontology=len(peers_c.ontology_ids), alpha=alpha)
    return SelectivityAssessment(
        original_score=original,
        side_a=side_a,
        side_c=side_c,
        aggregate=aggregate_sides(side_a, side_c),
        peer_scores_a=scores_a,
        peer_scores_c=scores_c,
        provenance=dict(provenance or {}),
    )


def frozen_v1_scorer(context: object) -> PairScorer:
    """Build the V2-A scorer from the frozen public V1 ``propose_bridge`` API."""

    from .bridge import DEFAULT_MESH_STOPLIST, propose_bridge

    def score(a_label: str, c_label: str) -> float:
        candidate = propose_bridge(
            context,
            a_label,
            c_label,
            stoplist=DEFAULT_MESH_STOPLIST,
            max_df=V1_MAX_DF,
            idf_min=V1_IDF_MIN,
        )
        return float(candidate.score)

    return score
