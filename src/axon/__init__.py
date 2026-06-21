"""
Axon — the Science Nervous System (SNS).

Infrastructure for getting a grip on the scientific literature, built on the
thesis that the fundamental unit is the *relation*, not the document — and that
verification comes before discovery, never after.

Axon consumes ``qhda-core`` (the relational layer, pure numpy; the quantum layer
is an optional extra). It does not vendor or reimplement it.

Four stages, in this exact order (the order is the thesis):

    1. perception                 — ingest scientific text into a normalized form
    2. relational_representation  — build the map of relations between items
    3. verification               — criticise every candidate relation; reject
                                    false positives before anything is surfaced
    4. hypothesis                 — discoveries are the OUTPUT of verification,
                                    never an input to it

See ``Manifest.md`` (Polish) for the conceptual contract and
``VERIFICATION_LOG.md`` for the methodological contract.
"""

__version__ = "0.1.0"

# Data contracts that flow between stages.
from .types import (
    Document,
    RelationKind,
    CandidateRelation,
    Verdict,
    VerificationResult,
    Hypothesis,
)

# Stage entry points. Importing these must not require Qiskit — the relational
# layer of qhda-core is pure numpy and the quantum layer is never imported here.
from .perception.ingest import normalize_text, ingest_text, ingest_corpus
from .perception.featurize import Featurizer, TfidfFeaturizer, featurize_documents
from .relational_representation.relation_store import RelationStore
from .verification.verifier import Verifier, RandomPairProximityVerifier, CorpusContext
from .verification.registry import VerifierRegistry, NoVerifierError, verify_all
from .verification.null_models import NullResult, permutation_p_value, bootstrap_ci
from .verification.multiple_testing import benjamini_hochberg, apply_fdr
from .hypothesis.surface import surface_hypotheses, SurfaceReport

__all__ = [
    "__version__",
    # contracts
    "Document",
    "RelationKind",
    "CandidateRelation",
    "Verdict",
    "VerificationResult",
    "Hypothesis",
    # stage 1 — perception
    "normalize_text",
    "ingest_text",
    "ingest_corpus",
    "Featurizer",
    "TfidfFeaturizer",
    "featurize_documents",
    # stage 2 — relational representation
    "RelationStore",
    # stage 3 — verification
    "Verifier",
    "RandomPairProximityVerifier",
    "CorpusContext",
    "VerifierRegistry",
    "NoVerifierError",
    "verify_all",
    "NullResult",
    "permutation_p_value",
    "bootstrap_ci",
    "benjamini_hochberg",
    "apply_fdr",
    # stage 4 — hypothesis
    "surface_hypotheses",
    "SurfaceReport",
]
