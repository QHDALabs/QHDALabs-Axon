"""
axon.perception.ingest — Stage 1: raw scientific text -> normalized Document.

Scope of this scaffold:
  - ``normalize_text``  : a minimal, clearly-labeled REFERENCE implementation
                          (whitespace/Unicode normalization). It honestly does
                          what it says — nothing more.
  - ``ingest_text``     : wrap a single normalized string into a ``Document``.
                          Also a minimal reference: it genuinely normalizes and
                          packages, but does NOT featurize (text -> vector) or
                          parse document structure.
  - ``ingest_corpus``   : ingest many sources (files, archives, APIs). NOT
                          implemented — format parsing and segmentation are real
                          work and are out of scope for the scaffold.

What is deliberately NOT here (raise NotImplementedError rather than fake it):
  - PDF/XML/HTML parsing and section segmentation,
  - reference/citation extraction,
  - embedding / feature-vector computation (``Document.vector``).
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Iterator, Mapping, Optional, Union

from ..types import Document


def normalize_text(raw: str) -> str:
    """
    Minimal reference normalization: NFC Unicode + collapsed whitespace.

    Input : raw text of one document.
    Output: normalized text — NFC-normalized, with runs of whitespace collapsed
            to single spaces and surrounding whitespace stripped.

    This is intentionally shallow. It is honest about being a placeholder for a
    real normalization pipeline (de-hyphenation, ligatures, math/figure
    stripping, language handling), which is not implemented here.
    """
    if not isinstance(raw, str):
        raise TypeError(f"normalize_text expects str, got {type(raw).__name__}")
    text = unicodedata.normalize("NFC", raw)
    return " ".join(text.split())


def ingest_text(
    raw: str,
    *,
    doc_id: str,
    source: Optional[str] = None,
    metadata: Optional[Mapping[str, object]] = None,
) -> Document:
    """
    Reference ingestion of a single in-memory string into a ``Document``.

    Input : raw text + a stable ``doc_id`` (+ optional source/metadata).
    Output: a ``Document`` with normalized text and ``vector=None``.

    Honest limits: this attaches NO feature vector — featurization is not
    implemented (see module docstring). Downstream stages that need a vector
    must be given one explicitly (e.g. toy data in examples/tests).
    """
    return Document(
        doc_id=doc_id,
        text=normalize_text(raw),
        source=source,
        vector=None,
        metadata=dict(metadata or {}),
    )


def ingest_corpus(path: Union[str, Path]) -> Iterator[Document]:
    """
    Ingest a committed JSON corpus into a stream of normalized ``Document``.

    Input : path to a JSON file holding a list of records, each with at least
            ``id`` and ``text``; optional ``source``, ``domain``, ``title``,
            ``category``. (This is the schema produced by scripts/fetch_corpus.py;
            see data/corpus_mvp.README.md.)
    Output: an iterator of ``Document`` with normalized text. ``domain``, ``title``
            and ``category`` are carried in ``metadata`` (the relational stage reads
            ``domain`` for null stratification); ``vector`` is left None — call a
            ``Featurizer`` (see ``perception.featurize``) to attach vectors.

    Scope: this reads the project's own JSON corpus. Parsing arbitrary formats
    (PDF/XML/HTML) and section segmentation remain out of scope and are not faked.
    """
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"corpus at {path} must be a JSON list of records")

    for i, rec in enumerate(records):
        if "id" not in rec or "text" not in rec:
            raise ValueError(f"record {i} in {path} is missing required 'id'/'text'")
        meta = {
            "domain": rec.get("domain"),
            "title": rec.get("title"),
            "category": rec.get("category"),
        }
        yield Document(
            doc_id=str(rec["id"]),
            text=normalize_text(str(rec["text"])),
            source=rec.get("source"),
            vector=None,
            metadata=meta,
        )
