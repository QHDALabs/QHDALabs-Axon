from pathlib import Path

import pytest

from axon.verification.peer_selection import (
    MeshParseError,
    parent_tree_number,
    parse_descriptor_xml,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "mesh_fragment.xml"


def _tree():
    return parse_descriptor_xml(FIXTURE.read_text(encoding="utf-8"))


def test_parse_keys_descriptors_by_ui():
    tree = _tree()
    assert set(tree.uis()) == {
        "D000200", "D000210", "D000211", "D000220", "D000230", "D000240",
    }
    assert tree.descriptor("D000200").name == "Vascular Diseases"


def test_polyhierarchy_positions_are_all_returned_sorted():
    # A single descriptor occupying two tree positions keeps both, sorted.
    assert _tree().positions_of("D000240") == ("C14.907.355.590", "C20.111")


def test_parent_tree_number_math():
    assert parent_tree_number("C14.907.253") == "C14.907"
    assert parent_tree_number("C14.907") == "C14"
    assert parent_tree_number("C14") is None


def test_children_are_immediate_only():
    # Grandchildren (C14.907.355.590, C14.907.617.500) are NOT immediate children.
    assert _tree().child_tree_numbers("C14.907") == (
        "C14.907.253", "C14.907.355", "C14.907.617",
    )


def test_descendants_include_full_subtree():
    tree = _tree()
    assert tree.descendant_tree_numbers("C14.907.617") == ("C14.907.617.500",)
    assert tree.descendant_tree_numbers("C14.907") == (
        "C14.907.253",
        "C14.907.355",
        "C14.907.355.590",
        "C14.907.617",
        "C14.907.617.500",
    )


def test_ui_at_resolves_occupied_positions_only():
    tree = _tree()
    assert tree.ui_at("C14.907.617") == "D000210"
    assert tree.ui_at("C14") is None          # bare category node — no descriptor
    assert tree.ui_at("C99.999") is None      # absent


def test_parse_rejects_duplicate_descriptor_ui():
    xml = (
        "<DescriptorRecordSet>"
        "<DescriptorRecord><DescriptorUI>D1</DescriptorUI>"
        "<TreeNumberList><TreeNumber>C1.1</TreeNumber></TreeNumberList></DescriptorRecord>"
        "<DescriptorRecord><DescriptorUI>D1</DescriptorUI>"
        "<TreeNumberList><TreeNumber>C1.2</TreeNumber></TreeNumberList></DescriptorRecord>"
        "</DescriptorRecordSet>"
    )
    with pytest.raises(MeshParseError, match="duplicate DescriptorUI"):
        parse_descriptor_xml(xml)


def test_parse_rejects_tree_number_shared_by_two_descriptors():
    xml = (
        "<DescriptorRecordSet>"
        "<DescriptorRecord><DescriptorUI>D1</DescriptorUI>"
        "<TreeNumberList><TreeNumber>C1.1</TreeNumber></TreeNumberList></DescriptorRecord>"
        "<DescriptorRecord><DescriptorUI>D2</DescriptorUI>"
        "<TreeNumberList><TreeNumber>C1.1</TreeNumber></TreeNumberList></DescriptorRecord>"
        "</DescriptorRecordSet>"
    )
    with pytest.raises(MeshParseError, match="claimed by both"):
        parse_descriptor_xml(xml)


def test_parse_rejects_wrong_root():
    with pytest.raises(MeshParseError, match="DescriptorRecordSet"):
        parse_descriptor_xml("<Nope/>")


def test_parse_rejects_empty_descriptor_ui():
    xml = (
        "<DescriptorRecordSet><DescriptorRecord><DescriptorUI></DescriptorUI>"
        "</DescriptorRecord></DescriptorRecordSet>"
    )
    with pytest.raises(MeshParseError, match="non-empty DescriptorUI"):
        parse_descriptor_xml(xml)


def test_parse_rejects_malformed_tree_number():
    xml = (
        "<DescriptorRecordSet><DescriptorRecord><DescriptorUI>D1</DescriptorUI>"
        "<TreeNumberList><TreeNumber>C1..2</TreeNumber></TreeNumberList>"
        "</DescriptorRecord></DescriptorRecordSet>"
    )
    with pytest.raises(MeshParseError, match="malformed TreeNumber"):
        parse_descriptor_xml(xml)
