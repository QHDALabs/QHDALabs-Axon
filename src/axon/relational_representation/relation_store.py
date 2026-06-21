"""
axon.relational_representation.relation_store — Stage 2.

Build the map of relations between perceived items. This is a *relation store*,
not a fact store: it holds candidate dependencies to be criticised, never
asserted truths.

It is built on qhda-core's relational layer (``RelationalState`` /
``MeasurementOutcome``), which is pure numpy. This stage MUST work with Qiskit
not installed — we import only the relational layer of qhda-core, never the
quantum layer, mirroring qhda-core's own dependency boundary.

What it does:
  - ``observe``            : fold a featurized document into a qhda-core
                             ``RelationalState`` and record its vector, domain and
                             length (the latter two are confounders the verification
                             null stratifies on).
  - ``candidate_relations``: propose ``CandidateRelation`` pairs by cosine
                             proximity. A cheap proposal generator — high score
                             means "worth criticising", NOT "related". The claim is
                             the verification stage's job.
  - ``structural_score``   : expose qhda-core's structural score (coherence signal).

The store also serves as the ``CorpusContext`` the proximity verifier reads from:
it can enumerate all doc ids and report each document's domain and length band, so
the random-pair null can be matched on those confounders.

NOT implemented (raise rather than fake): ABC (Swanson) bridge construction,
cross-domain term alignment, mechanistic relation kinds.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# Relational layer of qhda-core ONLY. Importing this must not require Qiskit.
from qhda_core import MeasurementOutcome, RelationalState, RelationalConfig

from ..types import CandidateRelation, Document, RelationKind


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
        n_length_bands: int = 2,
    ) -> None:
        """
        Input : feature dimensionality ``dim`` (must match document vectors),
                qhda-core relational coupling parameters, and ``n_length_bands``
                (how coarsely to bucket document length for null stratification;
                2 = short/long by median, keeps strata viable in a small corpus).
        """
        self._dim = int(dim)
        self._n_length_bands = max(1, int(n_length_bands))
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
        self._domains: List[str] = []
        self._lengths: List[int] = []
        self._pos: Dict[str, int] = {}

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
        if document.doc_id in self._pos:
            raise ValueError(f"duplicate doc_id {document.doc_id!r}")
        outcome = MeasurementOutcome(
            observables={"norm": float(np.linalg.norm(vec))},
            vector=vec,
            bridge_fired=bridge_fired,
            index=len(self._ids),
            meta={"doc_id": document.doc_id},
        )
        self._state.update(outcome)
        self._pos[document.doc_id] = len(self._ids)
        self._ids.append(document.doc_id)
        self._vectors.append(vec)
        self._domains.append(str(document.metadata.get("domain") or "unknown"))
        self._lengths.append(len(document.text.split()))

    def candidate_relations(
        self, *, threshold: float = 0.5, kind: RelationKind = RelationKind.PROXIMITY
    ) -> List[CandidateRelation]:
        """
        Propose candidate relations by cosine proximity over observed vectors.

        Input : a similarity ``threshold`` in [-1, 1].
        Output: a list of ``CandidateRelation`` for every unordered pair whose
                cosine similarity >= ``threshold``.

        This is a cheap proposal generator. A high score means "worth criticising",
        NOT "related". Whether a candidate survives is decided by the verification
        stage against an explicit null — many proposals are spurious by construction.
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

    # ── CorpusContext: what the proximity verifier reads for its random-pair null ──
    def vector_for(self, doc_id: str) -> np.ndarray:
        """Return the stored feature vector for ``doc_id``."""
        try:
            return self._vectors[self._pos[doc_id]]
        except KeyError as exc:
            raise KeyError(f"unknown doc_id {doc_id!r}") from exc

    def all_doc_ids(self) -> Sequence[str]:
        """All observed doc ids, in observation order."""
        return tuple(self._ids)

    def domain_of(self, doc_id: str) -> str:
        """Domain label of ``doc_id`` ('unknown' if none was provided)."""
        return self._domains[self._pos[doc_id]]

    def length_band_of(self, doc_id: str) -> int:
        """
        Coarse length band of ``doc_id`` in ``[0, n_length_bands)``.

        Bands are quantile cuts over the observed length distribution, so they are
        relative to this corpus. Used to match random pairs on document length.
        """
        length = self._lengths[self._pos[doc_id]]
        thresholds = self._length_thresholds()
        return int(np.searchsorted(thresholds, length, side="right"))

    def _length_thresholds(self) -> np.ndarray:
        if self._n_length_bands <= 1 or not self._lengths:
            return np.empty(0, dtype=float)
        qs = [k / self._n_length_bands for k in range(1, self._n_length_bands)]
        thresholds: np.ndarray = np.quantile(np.asarray(self._lengths, dtype=float), qs)
        return thresholds

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
