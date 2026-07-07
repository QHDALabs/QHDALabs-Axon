import pytest

from axon.verification.peer_selection import parse_descriptor_xml
from axon.verification.sibling_safety import (
    NeighborhoodVerdict,
    endpoint_neighborhood_gate,
)


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


def test_motivating_case_migraine_cluster_headache_vs_magnesium():
    # Headache class: migraine and cluster_headache are one-parent-up neighbours (OP2).
    # Magnesium sits in a different branch (a genuine distant endpoint).
    tree = _tree(
        _rec("HEADACHE", "C10.228.140.546"),
        _rec("MIGRAINE", "C10.228.140.546.399"),
        _rec("CLUSTER_HEADACHE", "C10.228.140.546.221"),
        _rec("MAGNESIUM", "D01.029.500"),
    )
    assert endpoint_neighborhood_gate(tree, "MIGRAINE", "CLUSTER_HEADACHE") is UNSAFE
    assert endpoint_neighborhood_gate(tree, "MIGRAINE", "MAGNESIUM") is CLEAR


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
