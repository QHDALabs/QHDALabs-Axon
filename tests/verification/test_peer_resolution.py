from pathlib import Path

import pytest

from axon.verification.peer_selection import (
    parse_descriptor_xml,
    resolve_peerset,
    select_one_parent_up,
)
from axon.verification.selectivity import PeerSet

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "mesh" / "mesh_fragment.xml"


def test_all_profiled_partition():
    peerset = resolve_peerset("E", ("p1", "p2", "p3"), lambda ui: True)
    assert isinstance(peerset, PeerSet)
    assert peerset.ontology_ids == ("p1", "p2", "p3")
    assert peerset.profiled_ids == ("p1", "p2", "p3")
    assert peerset.missing_ids == ()


def test_partition_by_availability_preserves_input_order():
    available = {"p1": True, "p2": False, "p3": True, "p4": False}
    peerset = resolve_peerset("E", ("p1", "p2", "p3", "p4"), lambda ui: available[ui])
    assert peerset.profiled_ids == ("p1", "p3")
    assert peerset.missing_ids == ("p2", "p4")


def test_all_missing_gives_empty_profiled():
    peerset = resolve_peerset("E", ("p1", "p2"), lambda ui: False)
    assert peerset.profiled_ids == ()
    assert peerset.missing_ids == ("p1", "p2")


def test_predicate_is_called_exactly_once_per_peer_in_order():
    calls = []

    def available(ui):
        calls.append(ui)
        return True

    resolve_peerset("E", ("p1", "p2", "p3"), available)
    assert calls == ["p1", "p2", "p3"]


def test_endpoint_in_ontology_fails_closed():
    with pytest.raises(ValueError, match="must not include its endpoint"):
        resolve_peerset("E", ("E", "p1"), lambda ui: True)


def test_duplicate_ontology_fails_closed():
    with pytest.raises(ValueError, match="ontology_ids must be deduplicated"):
        resolve_peerset("E", ("p1", "p1"), lambda ui: True)


def test_selection_to_resolution_chain_on_fixture():
    tree = parse_descriptor_xml(FIXTURE.read_text(encoding="utf-8"))
    peers = select_one_parent_up(tree, "D000210")   # ("D000220", "D000230", "D000240")
    # D000230 has no usable profile -> missing; the other two are profiled.
    peerset = resolve_peerset("D000210", peers, lambda ui: ui != "D000230")
    assert peerset.ontology_ids == ("D000220", "D000230", "D000240")
    assert peerset.profiled_ids == ("D000220", "D000240")
    assert peerset.missing_ids == ("D000230",)
