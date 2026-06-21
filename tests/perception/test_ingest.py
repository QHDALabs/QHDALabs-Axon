"""Stage 1 tests — perception.ingest."""

import json

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


def test_ingest_corpus_reads_json(tmp_path):
    records = [
        {"id": "x1", "source": "arXiv:x1", "domain": "astro",
         "title": "T1", "text": "  alpha   beta  "},
        {"id": "x2", "source": "arXiv:x2", "domain": "neuro",
         "title": "T2", "text": "gamma delta"},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(records), encoding="utf-8")

    docs = list(ingest_corpus(path))
    assert [d.doc_id for d in docs] == ["x1", "x2"]
    assert docs[0].text == "alpha beta"          # normalized
    assert docs[0].metadata["domain"] == "astro"
    assert docs[0].source == "arXiv:x1"
    assert docs[0].vector is None                # featurization is a separate step


def test_ingest_corpus_requires_id_and_text(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"id": "x1"}]), encoding="utf-8")
    with pytest.raises(ValueError):
        list(ingest_corpus(path))
