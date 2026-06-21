"""
axon.relational_representation.relation_store — Stage 2.

Build the map of relations between perceived items. This is a *relation store*,
not a fact store: it holds candidate dependencies to be criticised, never
asserted truths.

It is built on qhda-core's relational layer (``RelationalState`` /
``MeasurementOutcome``), which is pure numpy. This stage MUST work with Qiskit
not installed — we import only the relational layer of qhda-core, never the
quantum layer, mirroring qhda-core's own dependency boundary.

Scope of this scaffold:
  - ``RelationStore.observe``           : fold a document's feature vector into a
                                          qhda-core ``RelationalState``. Minimal
                                          REFERENCE: it requires a precomputed
                                          ``Document.vector`` (text -> vector is
                                          not implemented here).
  - ``RelationStore.candidate_relations``: propose ``CandidateRelation`` pairs by
                                          cosine proximity over observed vectors.
                                          Minimal REFERENCE heuristic — a cheap
                                          proposal generator, explicitly NOT a
                                          claim of real relatedness. That claim
                                          is the verification stage's job.
  - ``RelationStore.structural_score``  : expose qhda-core's structural score for
                                          the observed stream (coherence vs noise).

NOT implemented (raise rather than fake): turning text into vectors/term graphs,
ABC (Swanson) bridge construction, cross-domain term alignment.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

# Relational layer of qhda-core ONLY. Importing this must not require Qiskit.
from qhda_core import MeasurementOutcome, RelationalState, RelationalConfig

from ..types import CandidateRelation, Document


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity with a zero-norm guard. Pure numpy."""
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class RelationStore:
    """
    Accumulates perceived items and proposes candidate relations between them.

    The store keeps two things:
      - a qhda-core ``RelationalState`` that folds each observation into an
        accumulating h(t) (used as a coherence-vs-noise signal over the stream);
      - the observed (doc_id, vector) pairs, used to propose candidate relations.
    """

    def __init__(
        self,
        *,
        dim: int,
        coupling_fired: float = 0.7,
        coupling_base: float = 0.3,
        gain: float = 0.4,
    ) -> None:
        """
        Input : feature dimensionality ``dim`` (must match document vectors) and
                qhda-core relational coupling parameters.
        """
        self._dim = int(dim)
        self._state = RelationalState(
            RelationalConfig(
                dim=self._dim,
                coupling_fired=coupling_fired,
                coupling_base=coupling_base,
                gain=gain,
            )
        )
        self._ids: List[str] = []
        self._vectors: List[np.ndarray] = []

    def observe(self, document: Document, *, bridge_fired: Optional[bool] = None) -> None:
        """
        Fold one document into the relational state.

        Input : a ``Document`` carrying a feature ``vector`` of length ``dim``.
        Effect: updates the qhda-core ``RelationalState`` and stores the vector
                for later candidate proposal.

        Honest limit: this requires ``document.vector`` to be present. Computing
        a vector from text is NOT implemented in this scaffold; callers must
        supply it (toy data in examples/tests does).
        """
        if document.vector is None:
            raise ValueError(
                f"document {document.doc_id!r} has no feature vector; text->vector "
                "featurization is not implemented in this scaffold (see module docstring)."
            )
        vec = np.asarray(document.vector, dtype=float)
        if vec.shape != (self._dim,):
            raise ValueError(
                f"document {document.doc_id!r} vector has shape {vec.shape}, "
                f"expected ({self._dim},)"
            )
        outcome = MeasurementOutcome(
            observables={"norm": float(np.linalg.norm(vec))},
            vector=vec,
            bridge_fired=bridge_fired,
            index=len(self._ids),
            meta={"doc_id": document.doc_id},
        )
        self._state.update(outcome)
        self._ids.append(document.doc_id)
        self._vectors.append(vec)

    def candidate_relations(
        self, *, threshold: float = 0.5, kind: str = "proximity"
    ) -> List[CandidateRelation]:
        """
        Propose candidate relations by cosine proximity over observed vectors.

        Input : a similarity ``threshold`` in [-1, 1].
        Output: a list of ``CandidateRelation`` for every unordered pair whose
                cosine similarity >= ``threshold``.

        This is a minimal REFERENCE heuristic. A high score here means "worth
        criticising", NOT "related". Whether a candidate survives is decided by
        the verification stage against an explicit null — generating these
        proposals is cheap and many will be spurious by construction.
        """
        candidates: List[CandidateRelation] = []
        n = len(self._vectors)
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine(self._vectors[i], self._vectors[j])
                if sim >= threshold:
                    candidates.append(
                        CandidateRelation(
                            source_id=self._ids[i],
                            target_id=self._ids[j],
                            kind=kind,
                            score=sim,
                            evidence={"cosine": sim},
                            provenance=(self._ids[i], self._ids[j]),
                        )
                    )
        return candidates

    def vector_for(self, doc_id: str) -> np.ndarray:
        """Return the stored feature vector for ``doc_id`` (used by verifiers)."""
        try:
            return self._vectors[self._ids.index(doc_id)]
        except ValueError as exc:
            raise KeyError(f"unknown doc_id {doc_id!r}") from exc

    def vector_matrix(self) -> Tuple[List[str], np.ndarray]:
        """Return ``(ids, matrix)`` of all observed vectors, for null models."""
        if not self._vectors:
            return [], np.empty((0, self._dim))
        return list(self._ids), np.vstack(self._vectors)

    @property
    def structural_score(self) -> float:
        """qhda-core structural score of the observed stream (coherence signal)."""
        return float(self._state.structural_score)

    @property
    def n_observed(self) -> int:
        return len(self._ids)
