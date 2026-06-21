"""
axon.verification.registry — dispatch a candidate to the verifier for its kind.

This makes "no relation kind ships without its own explicit null" a STRUCTURAL
guarantee, mirroring "no hypothesis without verification". A candidate whose kind
has no registered verifier FAILS CLOSED: it raises, never silently falling back to
the proximity verifier (which would criticise it against the wrong null).

The MVP registers exactly one verifier (PROXIMITY). Every other ``RelationKind``
is intentionally left unregistered, so proposing one fails closed.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List

from ..types import CandidateRelation, RelationKind, VerificationResult
from .verifier import CorpusContext, Verifier


class NoVerifierError(LookupError):
    """Raised when a candidate's relation kind has no registered verifier."""


class VerifierRegistry:
    """Maps ``RelationKind`` -> ``Verifier``; fails closed on unknown kinds."""

    def __init__(self) -> None:
        self._verifiers: Dict[RelationKind, Verifier] = {}

    def register(self, kind: RelationKind, verifier: Verifier) -> None:
        self._verifiers[kind] = verifier

    def verifier_for(self, kind: RelationKind) -> Verifier:
        try:
            return self._verifiers[kind]
        except KeyError as exc:
            raise NoVerifierError(
                f"no verifier registered for relation kind {kind.value!r}; failing "
                "closed (no silent fallback to proximity). Register a verifier with "
                "an explicit null for this kind before proposing it."
            ) from exc

    def registered_kinds(self) -> FrozenSet[RelationKind]:
        return frozenset(self._verifiers)


def verify_all(
    candidates: Iterable[CandidateRelation],
    registry: VerifierRegistry,
    context: CorpusContext,
) -> List[VerificationResult]:
    """
    Verify many candidates, dispatching each to its kind's verifier.

    Returns ALL results (including REJECTED / NULL / INCONCLUSIVE) — they are data,
    not noise. Raises ``NoVerifierError`` (fail-closed) on any candidate whose kind
    is unregistered. ACCEPTED is not assigned here: run ``apply_fdr`` over the full
    returned set, then surface.
    """
    return [registry.verifier_for(c.kind).verify(c, context) for c in candidates]
