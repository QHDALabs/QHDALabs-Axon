"""
axon.types — neutral data contracts that flow between the four stages.

This module defines the currency that moves through the pipeline:

    perception            -> Document
    relational_repr.      -> CandidateRelation          (a *proposal*, unverified)
    verification          -> VerificationResult         (the verdict + the candidate)
    hypothesis            -> Hypothesis                  (built ONLY from accepted results)

Design, mirroring qhda-core's ``MeasurementOutcome`` contract:
  - frozen dataclasses: a stage's output is a fact that happened; downstream
    stages read it, they do not mutate it;
  - no heavy dependencies (only numpy, which is a core dependency);
  - the types encode the thesis. ``Hypothesis`` can only be built from a
    ``VerificationResult`` — there is no constructor path from a raw
    ``CandidateRelation`` to a ``Hypothesis``. Verification is not optional;
    it is the only door.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional, Sequence

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 output — perception
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Document:
    """
    A scientific text item normalized into a form the pipeline can consume.

    Fields:
      doc_id   : stable identifier (DOI, arXiv id, local key...).
      text     : normalized text (see ``perception.ingest.normalize_text``).
      source   : provenance string (file path, URL, corpus name). Optional.
      vector   : optional feature vector for this document. Turning text into a
                 vector (embeddings, term graphs) is NOT done in this scaffold;
                 toy data may supply a precomputed vector so the relational and
                 verification stages can run end to end.
      metadata : free-form metadata (authors, year, section...). Not interpreted
                 by downstream stages; carried for provenance and debugging.
    """

    doc_id: str
    text: str
    source: Optional[str] = None
    vector: Optional[np.ndarray] = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.vector is not None and not isinstance(self.vector, np.ndarray):
            object.__setattr__(self, "vector", np.asarray(self.vector, dtype=float))


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 output — relational representation
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CandidateRelation:
    """
    A *proposed* relation between two items. Cheap to generate, possibly false.

    This is explicitly pre-verification. A ``CandidateRelation`` makes no claim
    to be true; it is a hypothesis-to-be-criticised. The verification stage is
    what decides whether it survives.

    Fields:
      source_id : doc_id of one endpoint.
      target_id : doc_id of the other endpoint.
      kind      : the relation type proposed (e.g. "proximity", "shared-term",
                  "abc-bridge"). The verifier dispatches its criticism on kind.
      score     : the raw proposal strength (e.g. cosine similarity). NOT a
                  truth value and NOT a p-value — just the heuristic that
                  flagged this pair as worth criticising.
      evidence  : free-form supporting detail (shared terms, feature indices...).
      provenance: identifiers/documents the proposal was derived from.
    """

    source_id: str
    target_id: str
    kind: str
    score: float
    evidence: Mapping[str, object] = field(default_factory=dict)
    provenance: Sequence[str] = field(default_factory=tuple)


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3 output — verification
# ─────────────────────────────────────────────────────────────────────────────
class Verdict(str, Enum):
    """
    The outcome of criticising a candidate relation.

    NULL and REJECTED are first-class, valued outcomes — not failures. A system
    that cannot say "this link is spurious" is a noise generator, not science
    (Manifest, IV).
    """

    ACCEPTED = "accepted"          # survived criticism against an explicit null
    REJECTED = "rejected"          # criticism showed it is (likely) spurious
    NULL = "null"                  # honestly indistinguishable from the null
    INCONCLUSIVE = "inconclusive"  # not enough resolution to decide (e.g. too
                                   # few permutations); decide nothing, say so


@dataclass(frozen=True)
class VerificationResult:
    """
    The verdict on a single candidate, plus the evidence that produced it.

    This is the ONLY input the hypothesis stage accepts. It records not just the
    decision but the criticism behind it, so every downstream claim traces back
    to an explicit null model and statistic (Manifest, VIII — transparency).

    Fields:
      candidate     : the relation that was criticised.
      verdict       : see ``Verdict``.
      statistic     : the observed test statistic (domain-defined).
      p_value       : significance against the null, if computed. None when the
                      verifier could not establish one (then verdict is usually
                      INCONCLUSIVE).
      null_model    : human-readable description of the null/control used. An
                      empty string is a red flag: no stated null = not verified.
      n_resolution  : resolution of the null estimate (e.g. permutation count).
                      Low resolution → coarse p-value → prefer INCONCLUSIVE.
      reasoning     : short note on why this verdict, for the audit trail.
    """

    candidate: CandidateRelation
    verdict: Verdict
    statistic: float
    p_value: Optional[float] = None
    null_model: str = ""
    n_resolution: Optional[int] = None
    reasoning: str = ""

    @property
    def is_accepted(self) -> bool:
        return self.verdict is Verdict.ACCEPTED


# ─────────────────────────────────────────────────────────────────────────────
# Stage 4 output — hypothesis
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Hypothesis:
    """
    A surfaced discovery. The OUTPUT of verification, never an input to it.

    A ``Hypothesis`` is built only from an accepted ``VerificationResult`` (see
    ``hypothesis.surface``). There is deliberately no path from a raw
    ``CandidateRelation`` to a ``Hypothesis`` — the type system makes
    "discovery before verification" unrepresentable.

    Fields:
      statement : human-readable claim implied by the relation.
      result    : the accepted verification result this rests on (full audit
                  trail back to candidate, statistic, null model, sources).
      provenance: source identifiers the claim ultimately traces to.
    """

    statement: str
    result: VerificationResult
    provenance: Sequence[str] = field(default_factory=tuple)
