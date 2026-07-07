"""OP2 sibling-vs-bridge safety gate — Component 1: MeSH endpoint-neighborhood hard gate.

Structural safety check for an ABC-bridge candidate. If one endpoint sits in the other's
one-parent-up MeSH neighbourhood, the pair is same-class by ontology structure — a sibling
confound, not a distinct bridge. **Ontology structure overrides the weak cosine gate**
(`direct_max`) that missed this (OP2: cluster_headache adjacent to migraine slipped under
0.30). Deterministic, offline, **no Qiskit**; a NEW module around frozen V1 — it does not
edit `bridge.py`.

Trust-removing and one-sided: `UNSAFE_NEIGHBORHOOD_ADJACENCY` removes bridge confidence;
`NO_ADJACENCY` adds none — it only means this gate found no adjacency. Component 2
(sibling-substitution specificity) is a separate, proposed statistical layer pending §6 of
the OP2 card and is deliberately NOT in this module.
"""

from __future__ import annotations

from enum import Enum

from .peer_selection import MeshTree, select_one_parent_up


class NeighborhoodVerdict(str, Enum):
    """Component-1 verdict. One-sided: only ``UNSAFE_...`` carries information."""

    UNSAFE_NEIGHBORHOOD_ADJACENCY = "unsafe_neighborhood_adjacency"
    NO_ADJACENCY = "no_adjacency"


def endpoint_neighborhood_gate(tree: MeshTree, a_ui: str, c_ui: str) -> NeighborhoodVerdict:
    """OP2 Component 1: flag `UNSAFE` when the endpoints are ontology-adjacent.

    ``UNSAFE_NEIGHBORHOOD_ADJACENCY`` iff ``C`` is in ``A``'s one-parent-up neighbourhood
    **or** ``A`` is in ``C``'s. The rule is an ``OR``, so it can fire one-sidedly when a
    descriptor's multiple MeSH tree positions make the neighbourhood asymmetric — hence
    *neighborhood adjacency*, not "mutual sibling".

    Raises ``KeyError`` (fail-loud) if either endpoint is absent from ``tree``; assessing
    adjacency for an endpoint outside the ontology is not meaningful here. (Coverage /
    ``UNASSESSABLE`` handling is deferred to §6 of the OP2 card.)
    """
    if c_ui in select_one_parent_up(tree, a_ui) or a_ui in select_one_parent_up(tree, c_ui):
        return NeighborhoodVerdict.UNSAFE_NEIGHBORHOOD_ADJACENCY
    return NeighborhoodVerdict.NO_ADJACENCY
