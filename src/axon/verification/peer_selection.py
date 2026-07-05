"""MeSH ontology, one-parent-up peer selection, and profile resolution — V2-A
Decision-1 (pure, offline).

This module carries the deterministic half of V2-A peer selection, built in steps:
(1) parse a MeSH descriptor XML source into an immutable ontology keyed by
``DescriptorUI`` with parent/child derived from tree numbers — from a small in-memory
fragment (:func:`parse_descriptor_xml`) or, memory-bounded, streamed from the full
production file (:func:`parse_descriptor_file`); (2) select one-parent-up branch peers
for an endpoint (:func:`select_one_parent_up`); (3) resolve those peers into a
gate-ready :class:`PeerSet` by profile availability (:func:`resolve_peerset`).
It touches NO network and mutates NO verification result.

Schema consumed (only these elements are read; any others in a real record are
ignored). This mirrors the NLM ``DescriptorRecordSet`` schema, confirmed against the
frozen production ``desc<release>.xml``::

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

MeSH tree numbers are dot-separated hierarchy paths (e.g. ``C14.907.253``): the parent
of a tree number is the path with its final segment removed, and a top-level number
(no dot) has no parent within the descriptor set. A single descriptor may occupy
several tree positions (polyhierarchy); identity is always ``DescriptorUI``.

**Shared tree positions are real.** In production MeSH a single tree number can be
owned by more than one descriptor (e.g. `B03.300.390.400.001` is owned by both
`D047991` and `D048013` in MeSH 2026). The model reflects this faithfully rather than
forcing artificial uniqueness: a tree number maps to a *tuple* of owner UIs
(:meth:`MeshTree.owners_at`), collisions are surfaced
(:meth:`MeshTree.tree_number_collisions`), and endpoint exclusion is **conservative**
(any descriptor sharing an endpoint position or subtree position is excluded from
peers). A tree number repeated *within one descriptor*, an empty/malformed tree
number, an empty or duplicate ``DescriptorUI``, or a wrong root element still fail
closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

from .selectivity import PeerSet


class MeshParseError(ValueError):
    """Raised when a MeSH descriptor source is malformed or internally inconsistent."""


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
    """Immutable MeSH ontology, queryable by UI and by tree number.

    Built by :func:`parse_descriptor_xml` / :func:`parse_descriptor_file`. Deterministic:
    every multi-valued accessor returns results in a stable sorted order, so downstream
    peer selection is reproducible regardless of record order in the source.

    ``_owners_by_tree`` maps a tree number to the tuple of DescriptorUIs that occupy it
    — usually one, but genuinely more than one where production MeSH shares a position.
    """

    _by_ui: Mapping[str, Descriptor]
    _owners_by_tree: Mapping[str, Tuple[str, ...]]

    def uis(self) -> Tuple[str, ...]:
        """All DescriptorUIs in the source, sorted."""
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

    def owners_at(self, tree_number: str) -> Tuple[str, ...]:
        """DescriptorUIs occupying exactly this tree number (sorted).

        Empty tuple for an unoccupied number (e.g. a bare category root like ``C14``) —
        a valid gap, not an error. Usually one UI; more than one where the position is
        genuinely shared in MeSH.
        """
        return self._owners_by_tree.get(tree_number, ())

    def tree_number_collisions(self) -> Dict[str, Tuple[str, ...]]:
        """Tree numbers owned by more than one descriptor (sorted keys). Empty if none."""
        return {
            t: owners
            for t, owners in sorted(self._owners_by_tree.items())
            if len(owners) > 1
        }

    def child_tree_numbers(self, tree_number: str) -> Tuple[str, ...]:
        """Occupied tree numbers whose *immediate* parent is ``tree_number`` (sorted)."""
        return tuple(
            sorted(t for t in self._owners_by_tree if parent_tree_number(t) == tree_number)
        )

    def descendant_tree_numbers(self, tree_number: str) -> Tuple[str, ...]:
        """Occupied tree numbers strictly *under* ``tree_number`` at any depth (sorted)."""
        prefix = tree_number + "."
        return tuple(sorted(t for t in self._owners_by_tree if t.startswith(prefix)))


def _child_text(record: ET.Element, path: str) -> str:
    element = record.find(path)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _ingest_record(
    record: ET.Element,
    by_ui: Dict[str, Descriptor],
    owners: Dict[str, List[str]],
) -> None:
    """Validate one ``DescriptorRecord`` and fold it into the accumulating maps.

    Fail-closed on an empty/duplicate ``DescriptorUI``, a malformed (empty-segment)
    tree number, or a tree number repeated *within this record*. A tree number already
    owned by a *different* descriptor is appended (shared positions are real MeSH).
    """
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
            raise MeshParseError(f"duplicate TreeNumber {tree_number!r} within {ui!r}")
        trees.append(tree_number)
        owners.setdefault(tree_number, []).append(ui)
    by_ui[ui] = Descriptor(ui=ui, name=name, tree_numbers=tuple(sorted(trees)))


def _finalize_owners(owners: Dict[str, List[str]]) -> Dict[str, Tuple[str, ...]]:
    return {tree_number: tuple(sorted(uis)) for tree_number, uis in owners.items()}


def parse_descriptor_xml(xml_text: str) -> MeshTree:
    """Parse an in-memory MeSH ``DescriptorRecordSet`` fragment into a :class:`MeshTree`.

    For the multi-hundred-MB production release use :func:`parse_descriptor_file`, which
    streams; this one holds the whole document in memory and suits committed fixtures.
    Raises :class:`MeshParseError` on invalid XML or a wrong root element; per-record
    validation is shared with the streaming parser (see :func:`_ingest_record`).
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
    owners: Dict[str, List[str]] = {}
    for record in root.findall("DescriptorRecord"):
        _ingest_record(record, by_ui, owners)
    return MeshTree(_by_ui=by_ui, _owners_by_tree=_finalize_owners(owners))


def parse_descriptor_file(path: str) -> MeshTree:
    """Stream-parse a MeSH ``DescriptorRecordSet`` file into a :class:`MeshTree`.

    Uses ``ET.iterparse`` and clears each record after ingesting it, so memory stays
    bounded (tens of MB) even for the full production release. Same per-record
    validation and same resulting :class:`MeshTree` as :func:`parse_descriptor_xml`.
    Raises :class:`MeshParseError` on invalid XML, a wrong/absent root element, or any
    per-record inconsistency.
    """
    by_ui: Dict[str, Descriptor] = {}
    owners: Dict[str, List[str]] = {}
    root_seen = False
    try:
        for event, elem in ET.iterparse(path, events=("start", "end")):
            if event == "start":
                if not root_seen:
                    if elem.tag != "DescriptorRecordSet":
                        raise MeshParseError(
                            f"root element must be DescriptorRecordSet, got {elem.tag!r}"
                        )
                    root_seen = True
                continue
            if elem.tag == "DescriptorRecord":
                _ingest_record(elem, by_ui, owners)
                elem.clear()
    except ET.ParseError as exc:
        raise MeshParseError(f"invalid MeSH XML: {exc}") from exc
    if not root_seen:
        raise MeshParseError("no DescriptorRecordSet root element found")
    return MeshTree(_by_ui=by_ui, _owners_by_tree=_finalize_owners(owners))


#: The single, frozen neighbourhood radius for V2-A peer selection (§2.2). It is a
#: prespecified protocol parameter; changing it is a new card, not an edit here.
ONE_PARENT_UP = "ONE_PARENT_UP"


def select_one_parent_up(tree: MeshTree, endpoint_ui: str) -> Tuple[str, ...]:
    """Deterministic one-parent-up branch peers for an endpoint (Decision-1, §2.2).

    For every tree position of the endpoint: go exactly one parent up and take every
    descriptor owning any tree number under that parent (sibling *subgraphs*, not only
    immediate siblings), unioned across all of the endpoint's positions (full
    polyhierarchy) and deduplicated by stable ``DescriptorUI``. The rule never ascends
    to a grandparent, and the parent descriptor itself is never a peer.

    **Conservative exclusion for shared positions.** Excluded from peers is *every*
    descriptor that owns any tree number equal to, or descending from, any of the
    endpoint's tree positions — not just the endpoint itself. So if the endpoint ever
    shares a tree position with another descriptor, that other descriptor is also
    excluded: the same place in the ontology is never counted as a peer.

    Fail-closed: returns an empty tuple when no eligible branch peers exist (no
    siblings, or a top-level position with no parent). An empty result means "not
    assessable against this ontology", surfaced by the caller as coverage — never
    silently "no risk". Raises ``KeyError`` if ``endpoint_ui`` is not in ``tree``.
    Output is sorted, hence independent of source record order.
    """
    endpoint = tree.descriptor(endpoint_ui)

    excluded_uis: set[str] = {endpoint_ui}
    for position in endpoint.tree_numbers:
        excluded_uis.update(tree.owners_at(position))
        for tree_number in tree.descendant_tree_numbers(position):
            excluded_uis.update(tree.owners_at(tree_number))

    peer_uis: set[str] = set()
    for position in endpoint.tree_numbers:
        parent = parent_tree_number(position)
        if parent is None:
            continue  # top-level position: no parent to branch from
        for tree_number in tree.descendant_tree_numbers(parent):
            for owner in tree.owners_at(tree_number):
                if owner not in excluded_uis:
                    peer_uis.add(owner)
    return tuple(sorted(peer_uis))


#: Reports whether a selected peer descriptor has a usable V1 literature profile.
ProfileAvailability = Callable[[str], bool]


def resolve_peerset(
    endpoint_id: str,
    ontology_ids: Sequence[str],
    has_profile: ProfileAvailability,
    *,
    provenance: Optional[Mapping[str, object]] = None,
) -> PeerSet:
    """Partition selected ontology peers into profiled vs missing, as a :class:`PeerSet`.

    ``ontology_ids`` are the DescriptorUIs returned by :func:`select_one_parent_up`.
    ``has_profile(peer_ui)`` reports whether that peer has a usable V1 literature
    profile. Peers WITH a profile go to ``profiled_ids`` and enter the rank denominator;
    peers WITHOUT one go to ``missing_ids`` and are NEVER scored as artificial zeros
    (see the :class:`PeerSet` contract and the S3 rank gate). Input order is preserved,
    so the partition is deterministic. The predicate is called exactly once per peer.

    Pure glue: it calls no scorer and mutates no verdict. It builds a :class:`PeerSet`,
    whose invariants (endpoint excluded, deduplicated, disjoint, partitioning) are
    enforced on construction — so a malformed selection fails closed here rather than
    reaching the gate.
    """
    profiled: List[str] = []
    missing: List[str] = []
    for peer in ontology_ids:
        (profiled if has_profile(peer) else missing).append(peer)
    return PeerSet(
        endpoint_id=endpoint_id,
        ontology_ids=tuple(ontology_ids),
        profiled_ids=tuple(profiled),
        missing_ids=tuple(missing),
        provenance=dict(provenance or {}),
    )
