import pytest

from axon.verification.selectivity import (
    AggregateStatus,
    PeerSet,
    SideStatus,
    aggregate_sides,
    assess_pair_selectivity,
    assess_rank,
    minimum_rank_resolution,
)


def test_minimum_resolution_is_derived_from_alpha():
    assert minimum_rank_resolution(0.05) == 19


def test_top_rank_passes_at_nineteen():
    result = assess_rank(1.0, [0.5] * 19)
    assert result.status is SideStatus.NOT_DETECTED
    assert result.p_rank_nominal == pytest.approx(0.05)


def test_tie_counts_against_selectivity():
    result = assess_rank(1.0, [1.0] + [0.5] * 18)
    assert result.status is SideStatus.RISK
    assert result.k_at_or_above_original == 1


def test_missing_profiles_do_not_become_zero_scores():
    result = assess_rank(1.0, [0.5] * 18, n_ontology=30)
    assert result.status is SideStatus.UNASSESSABLE
    assert result.n_missing == 12
    assert result.n_profiled == 18


def test_real_zero_from_profiled_peer_remains_in_rank_denominator():
    result = assess_rank(1.0, [0.0] * 19, n_ontology=19)
    assert result.status is SideStatus.NOT_DETECTED
    assert result.n_profiled == 19


def test_pair_assessment_scores_every_substitution_fresh():
    calls = []

    def scorer(a, c):
        calls.append((a, c))
        return 10.0 if (a, c) == ("a", "c") else 1.0

    peers_a = PeerSet("a", tuple(f"a{i}" for i in range(19)),
                      tuple(f"a{i}" for i in range(19)))
    peers_c = PeerSet("c", tuple(f"c{i}" for i in range(19)),
                      tuple(f"c{i}" for i in range(19)))
    result = assess_pair_selectivity("a", "c", peers_a, peers_c, scorer)
    assert len(calls) == 39
    assert result.aggregate is AggregateStatus.NO_DEGRADATION


def test_one_sided_risk_degrades_the_aggregate():
    risk = assess_rank(1.0, [1.0] + [0.0] * 18)
    clean = assess_rank(1.0, [0.0] * 19)
    assert aggregate_sides(risk, clean) is AggregateStatus.DEGRADE_A
    assert aggregate_sides(clean, risk) is AggregateStatus.DEGRADE_C


def test_valid_peerset_constructs():
    peers = PeerSet("a", ("p1", "p2", "p3", "m1", "m2"), ("p1", "p2", "p3"), ("m1", "m2"))
    assert peers.profiled_ids == ("p1", "p2", "p3")
    assert peers.missing_ids == ("m1", "m2")


def test_duplicate_profiled_id_raises():
    with pytest.raises(ValueError, match="profiled_ids must be deduplicated"):
        PeerSet("a", ("p1", "p2"), ("p1", "p1", "p2"), ())


def test_duplicate_missing_id_raises():
    with pytest.raises(ValueError, match="missing_ids must be deduplicated"):
        PeerSet("a", ("p1", "m1"), ("p1",), ("m1", "m1"))


# --- S3: rank-resolution gate as a deterministic boundary invariant -----------------
# These exercise assess_pair_selectivity (the full two-sided entry point, with real
# PeerSet construction and aggregation) at the n_min boundary, NOT the assess_rank
# helper in isolation. S3 is gate ARITHMETIC: it must hold for any synthetic scorer.
# No real V1, no generator, no gate-logic change. n_min is taken from the exposed
# minimum_rank_resolution derivation, never hardcoded.

_M0 = 10.0  # original-pair score; synthetic scorers place peers relative to this


def _peer_ids(prefix, n):
    return tuple(f"{prefix}{i}" for i in range(n))


def test_s3_below_nmin_is_unassessable_for_any_scorer():
    # n_profiled = n_min - 1 on side A -> UNASSESSABLE by count alone, independent
    # of the mediated values. Side C is held selective so the aggregate is
    # specifically coverage degradation on A.
    n_min = minimum_rank_resolution(0.05)

    def make(side_a_score):
        def scorer(a, c):
            if (a, c) == ("A", "C"):
                return _M0
            if c == "C":                 # side-A substitution: scorer(peer_a, "C")
                return side_a_score(a)
            return 1.0                   # side-C substitution: strictly below m0
        return scorer

    for side_a_score in (lambda a: 1.0, lambda a: 999.0, lambda a: (hash(a) % 7) * 1.0):
        peers_a = PeerSet("A", _peer_ids("a", n_min - 1), _peer_ids("a", n_min - 1))
        peers_c = PeerSet("C", _peer_ids("c", n_min), _peer_ids("c", n_min))
        result = assess_pair_selectivity("A", "C", peers_a, peers_c, make(side_a_score))
        assert result.side_a.status is SideStatus.UNASSESSABLE
        assert result.side_a.n_profiled == n_min - 1
        assert result.aggregate is AggregateStatus.DEGRADE_COVERAGE_A


def test_s3_nmin_is_tight_top_rank_reaches_alpha():
    # At exactly n_min profiled peers, a strictly top-ranked original reaches
    # p = 1/(n_min+1) = alpha -> NOT_DETECTED. Proves n_min is tight, not slack.
    n_min = minimum_rank_resolution(0.05)
    peers_a = PeerSet("A", _peer_ids("a", n_min), _peer_ids("a", n_min))
    peers_c = PeerSet("C", _peer_ids("c", n_min), _peer_ids("c", n_min))
    result = assess_pair_selectivity(
        "A", "C", peers_a, peers_c,
        lambda a, c: _M0 if (a, c) == ("A", "C") else 1.0,
    )
    assert result.side_a.p_rank_nominal == pytest.approx(1.0 / (n_min + 1))
    assert result.side_a.p_rank_nominal == pytest.approx(0.05)
    assert result.side_a.status is SideStatus.NOT_DETECTED
    assert result.side_c.status is SideStatus.NOT_DETECTED
    assert result.aggregate is AggregateStatus.NO_DEGRADATION


def test_s3_tie_counts_against_selectivity_through_pair():
    # A single peer scoring == m0 raises k by one, pushing p above alpha -> RISK.
    # A tie must never be counted in the original's favour.
    n_min = minimum_rank_resolution(0.05)
    peers_a = PeerSet("A", _peer_ids("a", n_min), _peer_ids("a", n_min))
    peers_c = PeerSet("C", _peer_ids("c", n_min), _peer_ids("c", n_min))

    def scorer(a, c):
        if (a, c) == ("A", "C"):
            return _M0
        if c == "C" and a == "a0":        # exactly one side-A peer ties m0
            return _M0
        return 1.0

    result = assess_pair_selectivity("A", "C", peers_a, peers_c, scorer)
    assert result.side_a.k_at_or_above_original == 1
    assert result.side_a.p_rank_nominal == pytest.approx(2.0 / (n_min + 1))
    assert result.side_a.status is SideStatus.RISK
    assert result.aggregate is AggregateStatus.DEGRADE_A


def test_s3_missing_profiles_never_enter_rank_denominator():
    # missing_ids are never scored (no artificial zeros) and never enter the rank
    # denominator; only profiled peers count. n_profiled drives the rank test.
    n_min = minimum_rank_resolution(0.05)
    missing = tuple(f"am{i}" for i in range(5))
    calls = []

    def scorer(a, c):
        calls.append((a, c))
        return _M0 if (a, c) == ("A", "C") else 1.0

    peers_a = PeerSet("A", _peer_ids("a", n_min) + missing, _peer_ids("a", n_min), missing)
    peers_c = PeerSet("C", _peer_ids("c", n_min), _peer_ids("c", n_min))
    result = assess_pair_selectivity("A", "C", peers_a, peers_c, scorer)

    assert not any(a in set(missing) for a, _ in calls)   # missing peers never scored
    assert len(result.peer_scores_a) == n_min
    assert result.side_a.n_profiled == n_min
    assert result.side_a.n_missing == len(missing)
    assert result.side_a.p_rank_nominal == pytest.approx(1.0 / (n_min + 1))
    assert result.side_a.status is SideStatus.NOT_DETECTED


# --- aggregate_sides truth table: deterministic IUT-for-pass / OR-for-risk closure ---
# Completes the AggregateStatus outcomes not already pinned (existing tests cover
# NO_DEGRADATION, DEGRADE_A, DEGRADE_C, DEGRADE_COVERAGE_A). Pure arithmetic over
# aggregate_sides — no generator, no real V1, no gate-logic change. Side states are
# built with assess_rank at / below the exposed n_min, so this stays scorer-agnostic.


def _side_risk():
    # one peer ties m0 -> k=1, p = 2/(n_min+1) > alpha -> RISK (assessable)
    n_min = minimum_rank_resolution(0.05)
    return assess_rank(1.0, [1.0] + [0.0] * (n_min - 1))


def _side_clean():
    # original strictly top-ranked at exactly n_min -> p = alpha -> NOT_DETECTED
    n_min = minimum_rank_resolution(0.05)
    return assess_rank(1.0, [0.0] * n_min)


def _side_unassessable():
    # n_profiled = n_min - 1 -> below resolution -> UNASSESSABLE
    n_min = minimum_rank_resolution(0.05)
    return assess_rank(1.0, [0.0] * (n_min - 1))


def test_aggregate_both_sides_risk_degrades_both():
    assert _side_risk().status is SideStatus.RISK
    assert aggregate_sides(_side_risk(), _side_risk()) is AggregateStatus.DEGRADE_BOTH


def test_aggregate_coverage_degradation_c_and_both():
    assert _side_unassessable().status is SideStatus.UNASSESSABLE
    assert aggregate_sides(_side_clean(), _side_unassessable()) is AggregateStatus.DEGRADE_COVERAGE_C
    assert (
        aggregate_sides(_side_unassessable(), _side_unassessable())
        is AggregateStatus.DEGRADE_COVERAGE_BOTH
    )


def test_aggregate_risk_takes_precedence_over_unassessable():
    # OR-for-risk beats coverage: a RISK side degrades by risk even when the other
    # side is merely UNASSESSABLE. Risk is never masked by a coverage gap.
    assert aggregate_sides(_side_risk(), _side_unassessable()) is AggregateStatus.DEGRADE_A
    assert aggregate_sides(_side_unassessable(), _side_risk()) is AggregateStatus.DEGRADE_C
