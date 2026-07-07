from pathlib import Path

import pytest

from axon.verification.peer_selection import parse_descriptor_xml, select_one_parent_up
from axon.verification.sibling_safety import (
    NeighborhoodVerdict,
    endpoint_neighborhood_gate,
)

_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "op2_headache_fixture.xml"
MIGRAINE, CLUSTER_HEADACHE, MAGNESIUM = "D008881", "D003027", "D008274"


def _real_mesh_tree():
    return parse_descriptor_xml(_FIXTURE.read_text(encoding="utf-8"))


def _rec(ui, *tree_numbers):
    tns = "".join(f"<TreeNumber>{t}</TreeNumber>" for t in tree_numbers)
    return (
        f"<DescriptorRecord><DescriptorUI>{ui}</DescriptorUI>"
        f"<TreeNumberList>{tns}</TreeNumberList></DescriptorRecord>"
    )


def _tree(*records):
    return parse_descriptor_xml(
        "<DescriptorRecordSet>" + "".join(records) + "</DescriptorRecordSet>"
    )


UNSAFE = NeighborhoodVerdict.UNSAFE_NEIGHBORHOOD_ADJACENCY
CLEAR = NeighborhoodVerdict.NO_ADJACENCY


def test_adjacent_siblings_are_unsafe():
    tree = _tree(
        _rec("P", "C01.100"),
        _rec("A", "C01.100.200"),
        _rec("C", "C01.100.300"),   # sibling of A under the same parent
    )
    assert endpoint_neighborhood_gate(tree, "A", "C") is UNSAFE


def test_or_rule_fires_from_either_side():
    tree = _tree(
        _rec("P", "C01.100"),
        _rec("A", "C01.100.200"),
        _rec("C", "C01.100.300"),
    )
    assert endpoint_neighborhood_gate(tree, "A", "C") is UNSAFE
    assert endpoint_neighborhood_gate(tree, "C", "A") is UNSAFE


def test_unrelated_endpoints_are_not_adjacent():
    tree = _tree(
        _rec("PA", "C01.100"),
        _rec("A", "C01.100.200"),
        _rec("PB", "C14.900"),
        _rec("C", "C14.900.300"),   # different branch entirely
    )
    assert endpoint_neighborhood_gate(tree, "A", "C") is CLEAR


def test_real_mesh_migraine_cluster_headache_is_unsafe_both_orders():
    # The frozen OP2 motivating case on REAL MeSH 2026 UIs/tree-numbers: cluster headache is
    # in migraine's one-parent-up neighbourhood, so the pair is UNSAFE — ontology structure
    # catches what direct_max=0.30 missed. UNSAFE in either argument order.
    tree = _real_mesh_tree()
    assert endpoint_neighborhood_gate(tree, MIGRAINE, CLUSTER_HEADACHE) is UNSAFE
    assert endpoint_neighborhood_gate(tree, CLUSTER_HEADACHE, MIGRAINE) is UNSAFE


def test_real_mesh_migraine_magnesium_is_not_adjacent():
    # The genuine distant endpoint (a chemical in D01, not a disease in C10) is not adjacent.
    assert endpoint_neighborhood_gate(_real_mesh_tree(), MIGRAINE, MAGNESIUM) is CLEAR


def test_real_mesh_adjacency_is_one_sided_and_the_or_rule_catches_it():
    # On real MeSH the adjacency is ONE-SIDED: cluster headache sits deeper under the shared
    # primary-headache parent, so it is in migraine's neighbourhood but not vice versa. The
    # gate's OR rule is exactly what makes the pair UNSAFE regardless of order.
    tree = _real_mesh_tree()
    assert CLUSTER_HEADACHE in select_one_parent_up(tree, MIGRAINE)
    assert MIGRAINE not in select_one_parent_up(tree, CLUSTER_HEADACHE)


def test_parent_child_is_not_flagged_as_sibling():
    # The gate targets siblings, not the hierarchy: a child in the endpoint's subtree is
    # excluded from its one-parent-up neighbourhood, so parent~child is NO_ADJACENCY.
    tree = _tree(
        _rec("P", "C01.100"),
        _rec("A", "C01.100.200"),
        _rec("CHILD", "C01.100.200.500"),   # descendant of A
    )
    assert endpoint_neighborhood_gate(tree, "A", "CHILD") is CLEAR


def test_unknown_endpoint_raises():
    tree = _tree(_rec("A", "C01.100.200"))
    with pytest.raises(KeyError):
        endpoint_neighborhood_gate(tree, "A", "NOPE")
