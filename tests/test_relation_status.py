"""RELATION_STATUS is the single source of truth for relation-kind status.

These tests read ONLY from the enum and assert the quarantine holds, the two axes
stay separate, and the generated markdown table cannot drift from the enum."""

from pathlib import Path

from axon.types import (
    RELATION_STATUS,
    RelationKind,
    RelationStatus,
    ValidationState,
    render_relation_status_markdown,
)

STATUS_MD = Path(__file__).resolve().parent.parent / "RELATION_STATUS.md"


def test_every_kind_has_a_status():
    assert set(RELATION_STATUS) == set(RelationKind)


def test_proximity_is_safe_low_yield():
    s = RELATION_STATUS[RelationKind.PROXIMITY]
    assert s.status is RelationStatus.SAFE_LOW_YIELD
    assert s.validation_state is ValidationState.SAFE_NO_DISCOVERY_CLAIM
    assert s.general_use is True


def test_abc_bridge_is_experimental_closed_only_and_quarantined():
    s = RELATION_STATUS[RelationKind.ABC_BRIDGE]
    assert s.status is RelationStatus.EXPERIMENTAL_CLOSED_ONLY
    assert s.validation_state is ValidationState.HELD_OUT_FAILED
    assert s.general_use is False  # forbidden in open discovery


def test_declared_kinds_are_unregistered_and_untested():
    for kind in (RelationKind.SAME_MECHANISM_AS, RelationKind.SUPPORTS,
                 RelationKind.CONTRADICTS, RelationKind.MEASUREMENT_BRIDGE):
        s = RELATION_STATUS[kind]
        assert s.status is RelationStatus.DECLARED_UNREGISTERED
        assert s.validation_state is ValidationState.UNTESTED
        assert s.general_use is False


def test_invariant_general_use_implies_safe_no_discovery_claim():
    for s in RELATION_STATUS.values():
        if s.general_use:
            assert s.validation_state is ValidationState.SAFE_NO_DISCOVERY_CLAIM


def test_invariant_declared_unregistered_is_quarantined():
    for s in RELATION_STATUS.values():
        if s.status is RelationStatus.DECLARED_UNREGISTERED:
            assert s.validation_state is ValidationState.UNTESTED
            assert s.general_use is False


def test_status_markdown_matches_enum():
    """The committed table must equal the freshly rendered enum (no drift). If this
    fails, run `python scripts/gen_relation_status.py`."""
    assert STATUS_MD.read_text(encoding="utf-8") == render_relation_status_markdown()
