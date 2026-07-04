"""MeSH descriptor ontology model and parser — Decision-1, step 1 (pure, offline).

This is the first component of V2-A deterministic peer selection. It parses a MeSH
descriptor XML fragment into an immutable ontology keyed by ``DescriptorUI``, with
parent/child relationships derived from MeSH tree numbers. It performs NO peer
selection (the one-parent-up rule is a separate, later step) and touches NO network
and NO production artifact — it operates on whatever XML fragment it is handed, so
tests run against small committed fixtures rather than the frozen MeSH release.

Schema consumed (only these elements are read; any others in a real record are
ignored). This mirrors the NLM ``DescriptorRecordSet`` schema and MUST be confirmed
against the frozen production ``desc<release>.xml`` before any confirmatory use::

    <DescriptorRecordSet>
      <DescriptorRecord>
        <DescriptorUI>D000200</DescriptorUI>
        <DescriptorName><String>Vascular Diseases</String></DescriptorName>
        <TreeNumberList>
          <TreeNumber>C14.907</TreeNumber>
          ...
        </TreeNumberList>
      </DescriptorRecord>
      ...
    </DescriptorRecordSet>

MeSH tree numbers are dot-separated hierarchy paths (e.g. ``C14.907.253``): the
parent of a tree number is the path with its final segment removed, and a top-level
number (no dot) has no parent within the descriptor set. A single descriptor may
occupy several tree positions (polyhierarchy); identity is always ``DescriptorUI``.

Fail-closed by design: a malformed or ambiguous fragment raises rather than
silently producing a partial tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple
from xml.etree import ElementTree as ET


class MeshParseError(ValueError):
    """Raised when a MeSH descriptor fragment is malformed or ambiguous."""


@dataclass(frozen=True)
class Descriptor:
    """One MeSH descriptor: stable UI, display name, and its tree positions."""

    ui: str
    name: str
    tree_numbers: Tuple[str, ...]


def parent_tree_number(tree_number: str) -> Optional[str]:
    """Immediate parent of a MeSH tree number, or ``None`` for a top-level number.

    The parent is the path with its final dot-segment removed:
    ``C14.907.253`` -> ``C14.907``; ``C14.907`` -> ``C14``; ``C14`` -> ``None``.
    """
    head, dot, _tail = tree_number.rpartition(".")
    return head if dot else None


@dataclass(frozen=True)
class MeshTree:
    """Immutable MeSH ontology fragment, queryable by UI and by tree number.

    Built by :func:`parse_descriptor_xml`. Deterministic: every multi-valued
    accessor returns results in a stable sorted order, so downstream peer
    selection is reproducible regardless of record order in the source fragment.
    """

    _by_ui: Mapping[str, Descriptor]
    _ui_by_tree: Mapping[str, str]

    def uis(self) -> Tuple[str, ...]:
        """All DescriptorUIs in the fragment, sorted."""
        return tuple(sorted(self._by_ui))

    def has(self, ui: str) -> bool:
        return ui in self._by_ui

    def descriptor(self, ui: str) -> Descriptor:
        try:
            return self._by_ui[ui]
        except KeyError:
            raise KeyError(f"descriptor UI not in tree: {ui!r}") from None

    def positions_of(self, ui: str) -> Tuple[str, ...]:
        """Tree numbers this descriptor occupies (sorted, deduplicated)."""
        return self.descriptor(ui).tree_numbers

    def ui_at(self, tree_number: str) -> Optional[str]:
        """DescriptorUI occupying exactly this tree number, or ``None`` if unoccupied.

        An unoccupied number (e.g. a bare category root like ``C14``) returns
        ``None`` rather than raising: it is a valid gap in the tree, not an error.
        """
        return self._ui_by_tree.get(tree_number)

    def child_tree_numbers(self, tree_number: str) -> Tuple[str, ...]:
        """Occupied tree numbers whose *immediate* parent is ``tree_number`` (sorted)."""
        return tuple(
            sorted(t for t in self._ui_by_tree if parent_tree_number(t) == tree_number)
        )

    def descendant_tree_numbers(self, tree_number: str) -> Tuple[str, ...]:
        """Occupied tree numbers strictly *under* ``tree_number`` at any depth (sorted)."""
        prefix = tree_number + "."
        return tuple(sorted(t for t in self._ui_by_tree if t.startswith(prefix)))


def _child_text(record: ET.Element, path: str) -> str:
    element = record.find(path)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_descriptor_xml(xml_text: str) -> MeshTree:
    """Parse a MeSH ``DescriptorRecordSet`` fragment into a :class:`MeshTree`.

    Fail-closed. Raises :class:`MeshParseError` on: invalid XML; a root other than
    ``DescriptorRecordSet``; a missing/empty ``DescriptorUI``; a duplicate
    ``DescriptorUI``; a malformed (empty-segment) tree number; a tree number
    repeated within one descriptor; or the same tree number claimed by two
    descriptors. A descriptor with no tree numbers is allowed — it simply occupies
    no position and can never be selected as a peer.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise MeshParseError(f"invalid MeSH XML: {exc}") from exc
    if root.tag != "DescriptorRecordSet":
        raise MeshParseError(
            f"root element must be DescriptorRecordSet, got {root.tag!r}"
        )

    by_ui: Dict[str, Descriptor] = {}
    ui_by_tree: Dict[str, str] = {}
    for record in root.findall("DescriptorRecord"):
        ui = _child_text(record, "DescriptorUI")
        if not ui:
            raise MeshParseError("DescriptorRecord without a non-empty DescriptorUI")
        if ui in by_ui:
            raise MeshParseError(f"duplicate DescriptorUI: {ui!r}")
        name = _child_text(record, "DescriptorName/String")
        trees: List[str] = []
        for tn_element in record.findall("TreeNumberList/TreeNumber"):
            tree_number = (tn_element.text or "").strip()
            if not tree_number or any(seg == "" for seg in tree_number.split(".")):
                raise MeshParseError(f"malformed TreeNumber {tree_number!r} for {ui!r}")
            if tree_number in trees:
                raise MeshParseError(
                    f"duplicate TreeNumber {tree_number!r} within {ui!r}"
                )
            if tree_number in ui_by_tree:
                raise MeshParseError(
                    f"tree number {tree_number!r} claimed by both "
                    f"{ui_by_tree[tree_number]!r} and {ui!r}"
                )
            trees.append(tree_number)
            ui_by_tree[tree_number] = ui
        by_ui[ui] = Descriptor(ui=ui, name=name, tree_numbers=tuple(sorted(trees)))
    return MeshTree(_by_ui=by_ui, _ui_by_tree=ui_by_tree)
