"""
axon.perception.featurize — turn document text into feature vectors.

This is the MVP featurization: a LEXICAL baseline (TF-IDF, pure numpy). It
captures lexical / distributional proximity — overlap in the words documents use.
It does NOT capture semantic or mechanistic equivalence; two papers describing the
same mechanism in different vocabularies will look distant here. That is a known
limitation of the baseline, stated honestly, not a bug.

The featurizer sits behind a small swappable interface (``Featurizer``). Real
embeddings can be dropped in later as another ``Featurizer`` WITHOUT touching the
verification null: the random-pair null in the verification stage operates on
whatever vectors come out of here, so it is featurizer-agnostic.
"""

from __future__ import annotations

import math
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Sequence

import numpy as np

from ..types import Document

# Minimal English stopword set. Deliberately small and explicit — not a curated
# linguistic resource, just enough to stop the most common function words from
# dominating the lexical signal.
_STOPWORDS = frozenset(
    """
    a an the and or but if then else of to in on for with without within from by
    at as is are was were be been being this that these those it its we our they
    their he she his her you your i me my not no nor do does did done can could
    will would shall should may might must have has had having which who whom whose
    what when where why how all any both each few more most other some such than too
    very s t can than into over under between out up down off about against during
    above below here there also using used use based via given show shown results
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]+")


def tokenize(text: str) -> List[str]:
    """Lowercase, extract alphabetic-leading tokens (len>=2), drop stopwords.

    Minimal and explicit: this is a lexical baseline, not an NLP pipeline.
    """
    return [
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) >= 2 and tok not in _STOPWORDS
    ]


class Featurizer(ABC):
    """Swappable text -> vector interface.

    Implementations must be deterministic: same texts in, same vectors out. The
    verification null relies only on the vectors, so any Featurizer (lexical now,
    embeddings later) plugs in without changing the null contract.
    """

    @abstractmethod
    def fit(self, texts: Sequence[str]) -> "Featurizer":
        """Learn any corpus-level parameters (e.g. vocabulary, IDF)."""

    @abstractmethod
    def transform(self, texts: Sequence[str]) -> np.ndarray:
        """Map texts to a 2-D array of shape (len(texts), dim)."""

    def fit_transform(self, texts: Sequence[str]) -> np.ndarray:
        return self.fit(texts).transform(texts)

    @property
    @abstractmethod
    def dim(self) -> int:
        """Output dimensionality (defined after ``fit``)."""


class TfidfFeaturizer(Featurizer):
    """
    Pure-numpy TF-IDF (lexical baseline).

    fit  : build the vocabulary (terms kept if document frequency is within
           [min_df, max_df]) and smoothed inverse document frequencies.
    transform: term frequency * idf, L2-normalized per row (so cosine similarity
               is just a dot product).

    min_df / max_df prune terms that are too rare (noise) or too ubiquitous
    (uninformative). All deterministic — no randomness.
    """

    def __init__(self, *, min_df: int = 2, max_df: float = 0.9) -> None:
        self.min_df = int(min_df)
        self.max_df = float(max_df)
        self._vocab: Dict[str, int] = {}
        self._idf: np.ndarray = np.empty(0, dtype=float)

    def fit(self, texts: Sequence[str]) -> "TfidfFeaturizer":
        n_docs = len(texts)
        if n_docs == 0:
            raise ValueError("cannot fit TfidfFeaturizer on an empty corpus")
        token_lists = [tokenize(t) for t in texts]

        df: Dict[str, int] = {}
        for toks in token_lists:
            for term in set(toks):
                df[term] = df.get(term, 0) + 1

        max_count = self.max_df * n_docs
        kept = sorted(
            term
            for term, d in df.items()
            if d >= self.min_df and d <= max_count
        )
        if not kept:
            raise ValueError(
                "empty vocabulary after min_df/max_df pruning; relax the thresholds "
                f"(min_df={self.min_df}, max_df={self.max_df}, n_docs={n_docs})"
            )
        self._vocab = {term: i for i, term in enumerate(kept)}

        # Smoothed idf: log((1 + n) / (1 + df)) + 1  (sklearn-style smoothing).
        idf = np.empty(len(kept), dtype=float)
        for term, i in self._vocab.items():
            idf[i] = math.log((1.0 + n_docs) / (1.0 + df[term])) + 1.0
        self._idf = idf
        return self

    def transform(self, texts: Sequence[str]) -> np.ndarray:
        if not self._vocab:
            raise RuntimeError("TfidfFeaturizer.transform called before fit")
        mat = np.zeros((len(texts), len(self._vocab)), dtype=float)
        for row, text in enumerate(texts):
            for term in tokenize(text):
                j = self._vocab.get(term)
                if j is not None:
                    mat[row, j] += 1.0
        mat *= self._idf  # broadcast idf across columns
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0  # leave all-zero rows as zeros
        normalized: np.ndarray = mat / norms
        return normalized

    @property
    def dim(self) -> int:
        return len(self._vocab)


def featurize_documents(
    featurizer: Featurizer, documents: Sequence[Document]
) -> List[Document]:
    """
    Attach feature vectors to documents (returns NEW Documents; inputs unchanged).

    Fits the featurizer on the corpus, then returns copies of each Document with
    ``vector`` set. Keeping this separate from ingestion makes the featurizer
    swappable without touching perception or the null contract.
    """
    vectors = featurizer.fit_transform([d.text for d in documents])
    out: List[Document] = []
    for d, vec in zip(documents, vectors):
        out.append(
            Document(
                doc_id=d.doc_id,
                text=d.text,
                source=d.source,
                vector=vec,
                metadata=d.metadata,
            )
        )
    return out
