"""Layer 3 — one wiring test for V2-A peer selection (pre-registration §5).

Checks that the pieces connect: a (real-shaped) MeSH fragment flows through
``select_one_parent_up`` -> ``resolve_peerset`` -> ``PeerSet`` -> the selectivity
gate over SYNTHETIC profiles. It exercises INTERFACES only; its verdict is NOT
Tier 0 behavioural evidence and proves nothing about the gate's contract (that is
Layer 2). The scorer here is a synthetic stand-in, never ``frozen_v1_scorer``.
"""

from pathlib import Path

from axon.verification.peer_selection import (
    parse_descriptor_xml,
    resolve_peerset,
    select_one_parent_up,
)
from axon.verification.selectivity import (
    AggregateStatus,
    SideStatus,
    assess_pair_selectivity,
    minimum_rank_resolution,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "mesh_fragment.xml"

_M0 = 100.0  # original-pair synthetic score; peers score strictly below it


def _rec(ui, *tree_numbers):
    tns = "".join(f"<TreeNumber>{t}</TreeNumber>" for t in tree_numbers)
    return (
        f"<DescriptorRecord><DescriptorUI>{ui}</DescriptorUI>"
        f"<TreeNumberList>{tns}</TreeNumberList></DescriptorRecord>"
    )


def _set(*records):
    return parse_descriptor_xml(
        "<DescriptorRecordSet>" + "".join(records) + "</DescriptorRecordSet>"
    )


def test_wiring_real_fixture_missing_peer_never_reaches_the_scorer():
    # Real-shaped committed MeSH fragment -> select -> resolve -> gate.
    tree = parse_descriptor_xml(FIXTURE.read_text(encoding="utf-8"))
    peers = select_one_parent_up(tree, "D000210")          # D000220, D000230, D000240
    peers_a = resolve_peerset("D000210", peers, lambda ui: ui != "D000230")  # D000230 missing
    peers_c = resolve_peerset("CZ", (), lambda ui: True)   # empty C side (coverage)

    scored = []

    def scorer(a_label, c_label):
        scored.append((a_label, c_label))
        return _M0 if (a_label, c_label) == ("D000210", "CZ") else 1.0

    result = assess_pair_selectivity("D000210", "CZ", peers_a, peers_c, scorer)

    scored_a = {a for a, _ in scored}
    assert "D000230" not in scored_a          # missing peer never scored (no zero-fill)
    assert {"D000220", "D000240"} <= scored_a  # profiled peers were scored
    assert result.side_a.n_profiled == 2
    assert result.side_a.n_missing == 1
    assert result.side_a.status is SideStatus.UNASSESSABLE   # 2 < n_min, tiny fixture
    assert result.aggregate is AggregateStatus.DEGRADE_COVERAGE_BOTH


def test_wiring_reaches_an_assessable_not_detected_end_to_end():
    # A larger synthetic MeSH fragment (>= n_min siblings per side) so the chain
    # reaches an assessable verdict. Endpoint is top-ranked -> NOT_DETECTED.
    n_min = minimum_rank_resolution(0.05)

    def branch(parent, endpoint_ui, prefix):
        records = [_rec(f"{prefix}_P", parent), _rec(endpoint_ui, f"{parent}.900")]
        for i in range(n_min):
            records.append(_rec(f"{prefix}{i:02d}", f"{parent}.{i:03d}"))
        return records

    tree = _set(*(branch("C01.100", "EA", "a") + branch("C02.200", "EC", "c")))
    peers_a = resolve_peerset("EA", select_one_parent_up(tree, "EA"), lambda ui: True)
    peers_c = resolve_peerset("EC", select_one_parent_up(tree, "EC"), lambda ui: True)
    assert len(peers_a.profiled_ids) == n_min
    assert len(peers_c.profiled_ids) == n_min

    def scorer(a_label, c_label):
        return _M0 if (a_label, c_label) == ("EA", "EC") else 1.0

    result = assess_pair_selectivity("EA", "EC", peers_a, peers_c, scorer)
    assert result.side_a.status is SideStatus.NOT_DETECTED
    assert result.side_c.status is SideStatus.NOT_DETECTED
    assert result.side_a.p_rank_nominal == 1.0 / (n_min + 1)
    assert result.aggregate is AggregateStatus.NO_DEGRADATION
