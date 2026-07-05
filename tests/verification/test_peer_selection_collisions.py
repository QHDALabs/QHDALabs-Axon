from pathlib import Path

import pytest

from axon.verification.peer_selection import (
    MeshParseError,
    parse_descriptor_file,
    parse_descriptor_xml,
    select_one_parent_up,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "mesh_fragment.xml"


def _rec(ui, *tree_numbers):
    tns = "".join(f"<TreeNumber>{t}</TreeNumber>" for t in tree_numbers)
    return (
        f"<DescriptorRecord><DescriptorUI>{ui}</DescriptorUI>"
        f"<TreeNumberList>{tns}</TreeNumberList></DescriptorRecord>"
    )


def _xml(*records):
    return "<DescriptorRecordSet>" + "".join(records) + "</DescriptorRecordSet>"


def test_streaming_parser_equals_in_memory_parser_on_fixture():
    from_string = parse_descriptor_xml(FIXTURE.read_text(encoding="utf-8"))
    streamed = parse_descriptor_file(str(FIXTURE))
    assert streamed.uis() == from_string.uis()
    for ui in from_string.uis():
        assert streamed.positions_of(ui) == from_string.positions_of(ui)
    assert select_one_parent_up(streamed, "D000210") == select_one_parent_up(
        from_string, "D000210"
    )


def test_streaming_parser_tolerates_shared_positions(tmp_path):
    path = tmp_path / "shared.xml"
    path.write_text(_xml(_rec("D1", "C1.1"), _rec("D2", "C1.1")), encoding="utf-8")
    tree = parse_descriptor_file(str(path))
    assert tree.owners_at("C1.1") == ("D1", "D2")
    assert tree.tree_number_collisions() == {"C1.1": ("D1", "D2")}


def test_streaming_parser_rejects_wrong_root(tmp_path):
    path = tmp_path / "bad.xml"
    path.write_text("<Nope/>", encoding="utf-8")
    with pytest.raises(MeshParseError, match="DescriptorRecordSet"):
        parse_descriptor_file(str(path))


def test_select_unions_all_owners_of_a_shared_sibling_position():
    # A sibling position owned by two descriptors -> both are peers (union by owner).
    tree = parse_descriptor_xml(
        _xml(
            _rec("P", "C01.100"),
            _rec("E", "C01.100.200"),
            _rec("S1", "C01.100.300"),
            _rec("S2", "C01.100.300"),   # shares the sibling position with S1
        )
    )
    assert select_one_parent_up(tree, "E") == ("S1", "S2")


def test_select_excludes_a_descriptor_sharing_the_endpoint_position():
    # Conservative exclusion: a descriptor co-owning the endpoint's own position is
    # NOT a peer — the same place in the ontology is never counted as a peer.
    tree = parse_descriptor_xml(
        _xml(
            _rec("P", "C01.100"),
            _rec("E", "C01.100.200"),
            _rec("X", "C01.100.200"),   # co-owns the endpoint position
            _rec("S", "C01.100.300"),
        )
    )
    peers = select_one_parent_up(tree, "E")
    assert peers == ("S",)
    assert "X" not in peers


def test_select_excludes_a_descriptor_sharing_an_endpoint_subtree_position():
    # Conservative exclusion extends to the endpoint's descendant subtree.
    tree = parse_descriptor_xml(
        _xml(
            _rec("P", "C01.100"),
            _rec("E", "C01.100.200"),
            _rec("C", "C01.100.200.500"),   # endpoint child (subtree)
            _rec("Y", "C01.100.200.500"),   # co-owns the endpoint subtree position
            _rec("S", "C01.100.300"),
        )
    )
    peers = select_one_parent_up(tree, "E")
    assert peers == ("S",)
    assert "C" not in peers and "Y" not in peers
