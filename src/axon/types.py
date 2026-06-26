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
from typing import Mapping, Optional, Sequence, Union

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
class RelationKind(str, Enum):
    """
    The kinds of relation Axon can propose between items.

    ``PROXIMITY`` and ``ABC_BRIDGE`` are implemented. ``ABC_BRIDGE`` recovers curated
    cases in CLOSED discovery (a pre-specified A-C pair) but is experimental and NOT
    validated for OPEN discovery: held-out validation failed (see VERIFICATION_LOG,
    OP1/OP2). ``SAME_MECHANISM_AS``, ``SUPPORTS``, ``CONTRADICTS`` and
    ``MEASUREMENT_BRIDGE`` are declared, unregistered, and fail closed.

    The per-kind status (the single source of truth) is ``RELATION_STATUS`` below —
    docs reference it, they do not restate it.
    """

    PROXIMITY = "proximity"
    SAME_MECHANISM_AS = "same_mechanism_as"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    ABC_BRIDGE = "abc_bridge"
    MEASUREMENT_BRIDGE = "measurement_bridge"


class RelationStatus(str, Enum):
    """Operational status of a relation kind. Two independent axes are encoded
    across ``RelationStatus`` (yield/maturity) and ``general_use`` (open-discovery
    safety): a kind can be safe-but-low-yield, or higher-yield-but-unsafe."""

    SAFE_LOW_YIELD = "safe_low_yield"                    # safe everywhere; surfaces little
    EXPERIMENTAL_CLOSED_ONLY = "experimental_closed_only"  # closed discovery only
    DECLARED_UNREGISTERED = "declared_unregistered"      # no verifier; fails closed


class ValidationState(str, Enum):
    """What validation has actually been done — kept distinct from ``general_use``
    so "safe" is never read as "proven to discover"."""

    SAFE_NO_DISCOVERY_CLAIM = "safe_no_discovery_claim"  # clean/calibrated; makes no discovery claim
    HELD_OUT_FAILED = "held_out_failed"                  # held-out tested and did NOT generalize
    UNTESTED = "untested"                                # never exercised (no verifier)


@dataclass(frozen=True)
class RelationStatusInfo:
    """Status record for one ``RelationKind`` — the single source of truth.

    Fields:
      status          : operational status (yield/maturity axis).
      validation_state: what validation was actually done (NOT a discovery claim).
      general_use     : safe in OPEN discovery? Invariant: True only when
                        validation_state is SAFE_NO_DISCOVERY_CLAIM.
      allowed_use     : what this kind may be used for.
      forbidden_use   : what it must not be used for.
      note            : short pointer to the methodological record (VERIFICATION_LOG).
    """

    status: RelationStatus
    validation_state: ValidationState
    general_use: bool
    allowed_use: str
    forbidden_use: str
    note: str


# ─── SINGLE SOURCE OF TRUTH — every human-readable doc derives from this ───
RELATION_STATUS: Mapping[RelationKind, RelationStatusInfo] = {
    RelationKind.PROXIMITY: RelationStatusInfo(
        status=RelationStatus.SAFE_LOW_YIELD,
        validation_state=ValidationState.SAFE_NO_DISCOVERY_CLAIM,
        general_use=True,
        allowed_use="any discovery, open or closed",
        forbidden_use="none",
        note="methodologically clean, fail-closed, honest null; the SAFER mechanism. "
             "Low yield on small corpora is by design, not a defect. No false positives "
             "demonstrated (FDR-controlled). See VERIFICATION_LOG MVP entry.",
    ),
    RelationKind.ABC_BRIDGE: RelationStatusInfo(
        status=RelationStatus.EXPERIMENTAL_CLOSED_ONLY,
        validation_state=ValidationState.HELD_OUT_FAILED,
        general_use=False,
        allowed_use="closed discovery with a pre-specified A-C pair",
        forbidden_use="open discovery / scanning many candidate C's "
                      "(mass-produces false bridges via the sibling false-positive)",
        note="recovers curated closed cases (Raynaud/fish-oil in-sample); held-out "
             "migraine/magnesium did NOT generalize. See VERIFICATION_LOG OP1 "
             "(thin-mediation power) and OP2 (gate does not separate siblings).",
    ),
    RelationKind.SAME_MECHANISM_AS: RelationStatusInfo(
        status=RelationStatus.DECLARED_UNREGISTERED,
        validation_state=ValidationState.UNTESTED,
        general_use=False,
        allowed_use="none (no verifier registered)",
        forbidden_use="any use — fails closed at verification",
        note="declared placeholder; no explicit null; no verifier.",
    ),
    RelationKind.SUPPORTS: RelationStatusInfo(
        status=RelationStatus.DECLARED_UNREGISTERED,
        validation_state=ValidationState.UNTESTED,
        general_use=False,
        allowed_use="none (no verifier registered)",
        forbidden_use="any use — fails closed at verification",
        note="declared placeholder; no explicit null; no verifier.",
    ),
    RelationKind.CONTRADICTS: RelationStatusInfo(
        status=RelationStatus.DECLARED_UNREGISTERED,
        validation_state=ValidationState.UNTESTED,
        general_use=False,
        allowed_use="none (no verifier registered)",
        forbidden_use="any use — fails closed at verification",
        note="declared placeholder; no explicit null; no verifier.",
    ),
    RelationKind.MEASUREMENT_BRIDGE: RelationStatusInfo(
        status=RelationStatus.DECLARED_UNREGISTERED,
        validation_state=ValidationState.UNTESTED,
        general_use=False,
        allowed_use="none (no verifier registered)",
        forbidden_use="any use — fails closed at verification",
        note="declared placeholder (quantum extra); no explicit null; no verifier.",
    ),
}


def render_relation_status_markdown() -> str:
    """Render RELATION_STATUS.md from the enum. The committed file must equal this
    output (a test asserts it), so the table can never silently drift."""
    lines = [
        "# Relation status",
        "",
        "**Single source of truth:** `RELATION_STATUS` in `src/axon/types.py`.",
        "This file is GENERATED by `scripts/gen_relation_status.py` — do not edit by",
        "hand; `tests/test_relation_status.py` asserts it matches the enum.",
        "",
        "Two independent axes: **status** (how much it finds / maturity) and "
        "**general use** (safe in open discovery). `PROXIMITY` is safe but low-yield; "
        "`ABC_BRIDGE` finds more but has a proven failure mode. One is not simply "
        "\"better\" than the other.",
        "",
        "| Kind | Status | Validation state | General use | Allowed use | Forbidden use | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for kind in RelationKind:
        info = RELATION_STATUS[kind]
        lines.append(
            f"| `{kind.value}` | {info.status.value} | {info.validation_state.value} "
            f"| {'yes' if info.general_use else 'no'} | {info.allowed_use} "
            f"| {info.forbidden_use} | {info.note} |"
        )
    return "\n".join(lines) + "\n"


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
      kind      : the relation type proposed (a ``RelationKind``). Verification
                  dispatches on kind via the registry, and fails closed if no
                  verifier is registered for it.
      score     : the raw proposal strength (e.g. cosine similarity). NOT a
                  truth value and NOT a p-value — just the heuristic that
                  flagged this pair as worth criticising.
      evidence  : free-form supporting detail (shared terms, feature indices...).
      provenance: identifiers/documents the proposal was derived from.
    """

    source_id: str
    target_id: str
    kind: RelationKind
    score: float
    evidence: Mapping[str, object] = field(default_factory=dict)
    provenance: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class BridgeCandidate:
    """
    A GROUP-level relation proposal: two literatures connected through shared
    intermediate terms (an ABC bridge, Swanson's closed discovery).

    This is deliberately NOT the doc-doc ``CandidateRelation``: an ABC bridge holds
    between two *literatures* (concepts) A and C via a set of intermediate B-terms
    present in both, NOT between two documents. A and C typically share little
    surface vocabulary — the connection runs through B.

    Fields:
      kind      : the relation type proposed (``RelationKind.ABC_BRIDGE``).
      a_label   : literature/concept label for the A side.
      c_label   : literature/concept label for the C side.
      b_terms   : the intermediate terms found in both literatures (EVIDENCE,
                  discovered by the method, never hand-labeled).
      score     : raw mediated-connectivity (proposal strength). NOT a truth value
                  and NOT a p-value — the verifier recomputes everything from the
                  literatures and decides against explicit nulls.
      evidence  : free-form detail (direct A-C similarity, per-null p-values...).
      provenance: identifiers/labels the proposal was derived from.
    """

    kind: RelationKind
    a_label: str
    c_label: str
    b_terms: Sequence[str] = field(default_factory=tuple)
    score: float = 0.0
    evidence: Mapping[str, object] = field(default_factory=dict)
    provenance: Sequence[str] = field(default_factory=tuple)


# Anything the verification stage can criticise. Each carries a ``kind`` the
# registry dispatches on. Doc-doc and group-level candidates are distinct types;
# verifiers narrow to the one they handle and reject the other.
RelationCandidate = Union[CandidateRelation, BridgeCandidate]


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
      q_value       : Benjamini-Hochberg adjusted p-value (FDR) across the full
                      set of tested candidates. None until the multiple-testing
                      pass runs. ACCEPTED is assigned only by that pass — a single
                      verifier cannot accept on its own.
      null_model    : human-readable description of the null/control used. An
                      empty string is a red flag: no stated null = not verified.
      n_resolution  : resolution of the null estimate (e.g. number of eligible
                      random pairs). Low resolution → coarse p-value → INCONCLUSIVE.
      reasoning     : short note on why this verdict, for the audit trail.
    """

    candidate: RelationCandidate
    verdict: Verdict
    statistic: float
    p_value: Optional[float] = None
    q_value: Optional[float] = None
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
