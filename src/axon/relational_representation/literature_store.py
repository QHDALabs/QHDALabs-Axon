"""
axon.relational_representation.literature_store — group-level substrate for ABC bridges.

Groups documents into literatures (by ``metadata['literature']``) and exposes the
materials an ABC-bridge verifier needs:

  - a term profile per literature (mean term-frequency * IDF over its documents);
  - IDF and background document-frequency computed over a BACKGROUND pool that is
    DISJOINT from the literatures under test (no circularity: A and C do not
    inflate their own IDF);
  - sampling of two focused background literatures for the random-literature-pair
    null (comparable, focused literatures — not a topically-scattered bag).

Term substrate is swappable via ``term_extractor`` (a Document -> list[str]). The
default reads MeSH descriptors from ``metadata['mesh']`` (controlled vocabulary,
the cleaner B substrate for biomedical text), falling back to lexical tokens.
Either way the verifier's null contract is unchanged — it reads only profiles.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from ..perception.featurize import tokenize
from ..types import Document

TermExtractor = Callable[[Document], List[str]]


def default_term_extractor(doc: Document) -> List[str]:
    """MeSH descriptors (as atomic, lowercased tokens) if present, else lexical tokens."""
    mesh = doc.metadata.get("mesh")
    if isinstance(mesh, (list, tuple)) and mesh:
        return [str(m).strip().lower() for m in mesh if str(m).strip()]
    return tokenize(doc.text)


class LiteratureStore:
    """Groups documents by literature label and serves the ABC-bridge context."""

    def __init__(
        self,
        documents: Sequence[Document],
        *,
        background_labels: Sequence[str],
        term_extractor: Optional[TermExtractor] = None,
    ) -> None:
        extract = term_extractor or default_term_extractor
        self._background_labels = list(background_labels)

        tokens_by_doc: List[List[str]] = []
        labels: List[str] = []
        for doc in documents:
            label = str(doc.metadata.get("literature") or "")
            if not label:
                raise ValueError(f"document {doc.doc_id!r} has no metadata['literature']")
            tokens_by_doc.append(extract(doc))
            labels.append(label)

        vocab = sorted({t for toks in tokens_by_doc for t in toks})
        if not vocab:
            raise ValueError("no terms extracted from the corpus")
        self._vocab: List[str] = vocab
        index = {t: i for i, t in enumerate(vocab)}
        V = len(vocab)

        # Per-document count vectors, grouped by literature label.
        by_label: Dict[str, List[np.ndarray]] = {}
        for toks, label in zip(tokens_by_doc, labels):
            vec = np.zeros(V, dtype=float)
            for t in toks:
                vec[index[t]] += 1.0
            by_label.setdefault(label, []).append(vec)
        self._counts: Dict[str, np.ndarray] = {
            label: np.vstack(vecs) for label, vecs in by_label.items()
        }

        # IDF / background df over the BACKGROUND pool only (disjoint from A/C).
        bg = [self._counts[l] for l in self._background_labels if l in self._counts]
        if not bg:
            raise ValueError("no background documents found for the given background_labels")
        bg_matrix = np.vstack(bg)
        n_bg = bg_matrix.shape[0]
        bg_df = np.count_nonzero(bg_matrix > 0, axis=0).astype(float)
        self._n_bg = n_bg
        self._bg_df_ratio: np.ndarray = bg_df / n_bg
        self._idf: np.ndarray = np.log((1.0 + n_bg) / (1.0 + bg_df)) + 1.0

        # Precompute per-literature profiles: mean TF over its docs, times IDF.
        self._profile_cache: Dict[str, np.ndarray] = {
            label: mat.mean(axis=0) * self._idf for label, mat in self._counts.items()
        }

    # ── LiteratureContext interface ──
    def vocab(self) -> Sequence[str]:
        return self._vocab

    def idf(self) -> np.ndarray:
        return self._idf

    def background_df_ratio(self) -> np.ndarray:
        return self._bg_df_ratio

    def profile(self, label: str) -> np.ndarray:
        try:
            return self._profile_cache[label]
        except KeyError as exc:
            raise KeyError(f"unknown literature {label!r}") from exc

    def literature_size(self, label: str) -> int:
        return int(self._counts[label].shape[0])

    def background_topics(self) -> Sequence[str]:
        return tuple(l for l in self._background_labels if l in self._counts)

    def _profile_from_counts(self, mat: np.ndarray) -> np.ndarray:
        prof: np.ndarray = mat.mean(axis=0) * self._idf
        return prof

    def sample_two_background_profiles(
        self,
        size_a: int,
        size_c: int,
        rng: np.random.Generator,
        exclude: frozenset[str] = frozenset(),
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Draw two DISTINCT focused background literatures and sample doc subsets of
        the requested sizes from each (with replacement). Returns their profiles.

        Focused (each pseudo-literature is drawn from a single background topic) and
        comparable — this is the honest null, not a scattered bag of random docs.
        """
        topics = [t for t in self.background_topics() if t not in exclude]
        if len(topics) < 2:
            raise ValueError("need at least 2 background topics not in `exclude`")
        i, j = rng.choice(len(topics), size=2, replace=False)
        mat_a = self._counts[topics[int(i)]]
        mat_c = self._counts[topics[int(j)]]
        idx_a = rng.integers(0, mat_a.shape[0], size=size_a)
        idx_c = rng.integers(0, mat_c.shape[0], size=size_c)
        return self._profile_from_counts(mat_a[idx_a]), self._profile_from_counts(mat_c[idx_c])
