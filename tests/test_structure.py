"""Structural tests: the package exposes the four stages, in order, and consumes
qhda-core as a dependency rather than vendoring it."""

import importlib
from pathlib import Path

import axon


def test_version():
    assert axon.__version__


def test_four_stages_importable():
    for stage in (
        "axon.perception",
        "axon.relational_representation",
        "axon.verification",
        "axon.hypothesis",
    ):
        assert importlib.import_module(stage) is not None


def test_public_api_surface():
    expected = {
        "Document", "RelationKind", "RelationStatus", "ValidationState",
        "RelationStatusInfo", "RELATION_STATUS", "render_relation_status_markdown",
        "CandidateRelation", "BridgeCandidate", "Verdict",
        "VerificationResult", "Hypothesis",
        "normalize_text", "ingest_text", "ingest_corpus",
        "Featurizer", "TfidfFeaturizer", "featurize_documents",
        "RelationStore", "LiteratureStore",
        "Verifier", "RandomPairProximityVerifier", "CorpusContext",
        "AbcBridgeVerifier", "propose_bridge",
        "VerifierRegistry", "NoVerifierError", "verify_all",
        "benjamini_hochberg", "apply_fdr",
        "surface_hypotheses",
    }
    assert expected.issubset(set(axon.__all__))


def test_qhda_core_is_consumed_not_vendored():
    """qhda-core must be a dependency, never copied into the Axon package."""
    qhda_core = importlib.import_module("qhda_core")
    assert qhda_core.__version__
    # No vendored copy sitting next to the axon package.
    pkg_parent = Path(axon.__file__).resolve().parent  # .../src/axon
    assert not (pkg_parent / "qhda_core").exists()
    assert not (pkg_parent.parent / "qhda_core").exists()  # .../src/qhda_core
