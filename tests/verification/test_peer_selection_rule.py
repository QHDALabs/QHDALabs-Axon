from pathlib import Path

import pytest

from axon.verification.peer_selection import (
    ONE_PARENT_UP,
    parse_descriptor_xml,
    select_one_parent_up,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "mesh_fragment.xml"


def _fixture_tree():
    return parse_descriptor_xml(FIXTURE.read_text(encoding="utf-8"))


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


def test_radius_constant_is_one_parent_up():
    assert ONE_PARENT_UP == "ONE_PARENT_UP"


def test_single_parent_returns_sibling_subgraphs_excluding_endpoint_and_subtree():
    # Endpoint D000210 (C14.907.617). Parent C14.907. Peers = the sibling subgraph:
    # D000220, D000230, and D000240 (a node under sibling D000230 — subgraph, not
    # only immediate siblings). Endpoint (D000210) and its subtree child (D000211)
    # are excluded; the parent (D000200) is never a peer.
    peers = select_one_parent_up(_fixture_tree(), "D000210")
    assert peers == ("D000220", "D000230", "D000240")
    assert "D000210" not in peers      # endpoint excluded
    assert "D000211" not in peers      # endpoint subtree excluded
    assert "D000200" not in peers      # parent is not a peer


def test_polyhierarchy_unions_peers_across_positions_and_dedups_by_ui():
    tree = _set(
        _rec("PA", "C01.100"),
        _rec("E", "C01.100.200", "C02.050.200"),   # endpoint at two positions
        _rec("PB", "C02.050"),
        _rec("S1", "C01.100.300"),                  # sibling under PA only
        _rec("S2", "C01.100.400", "C02.050.400"),   # shared sibling (polyhierarchic)
        _rec("S3", "C02.050.300"),                  # sibling under PB only
    )
    # Union across both branches; S2 appears in both but is deduplicated by UI.
    assert select_one_parent_up(tree, "E") == ("S1", "S2", "S3")


def test_never_ascends_to_grandparent():
    tree = _set(
        _rec("P", "C01.100"),
        _rec("E", "C01.100.200"),
        _rec("SIB", "C01.100.300"),   # under the parent -> peer
        _rec("UNCLE", "C01.500"),     # under the grandparent C01, NOT under C01.100
    )
    peers = select_one_parent_up(tree, "E")
    assert peers == ("SIB",)
    assert "UNCLE" not in peers


def test_traversal_order_independence():
    records = [
        _rec("P", "C01.100"),
        _rec("E", "C01.100.200"),
        _rec("S1", "C01.100.300"),
        _rec("S2", "C01.100.400"),
    ]
    forward = select_one_parent_up(_set(*records), "E")
    reverse = select_one_parent_up(_set(*reversed(records)), "E")
    assert forward == reverse == ("S1", "S2")


def test_fail_closed_empty_when_no_siblings():
    tree = _set(_rec("P", "C01.100"), _rec("E", "C01.100.200"))
    assert select_one_parent_up(tree, "E") == ()


def test_fail_closed_empty_when_endpoint_is_top_level():
    tree = _set(_rec("E", "C01"), _rec("OTHER", "C02"))
    assert select_one_parent_up(tree, "E") == ()


def test_unknown_endpoint_raises():
    tree = _set(_rec("E", "C01.100.200"))
    with pytest.raises(KeyError):
        select_one_parent_up(tree, "NOPE")
