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
