"""Stage 1 tests — perception.ingest."""

import pytest

from axon.perception.ingest import normalize_text, ingest_text, ingest_corpus
from axon.types import Document


def test_normalize_collapses_whitespace():
    assert normalize_text("  a\t b\n  c  ") == "a b c"


def test_normalize_is_idempotent():
    once = normalize_text("  x   y ")
    assert normalize_text(once) == once


def test_normalize_rejects_non_str():
    with pytest.raises(TypeError):
        normalize_text(123)  # type: ignore[arg-type]


def test_ingest_text_returns_normalized_document():
    doc = ingest_text("  Hello   World ", doc_id="d1", source="mem")
    assert isinstance(doc, Document)
    assert doc.doc_id == "d1"
    assert doc.text == "Hello World"
    assert doc.source == "mem"
    # Featurization is out of scope: no vector is fabricated.
    assert doc.vector is None


def test_ingest_corpus_is_honestly_unimplemented():
    with pytest.raises(NotImplementedError):
        list(ingest_corpus(["some/path"]))
