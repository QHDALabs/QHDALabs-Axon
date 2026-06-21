"""Stage 1 tests — perception.featurize (lexical TF-IDF baseline)."""

import numpy as np
import pytest

from axon.perception.featurize import (
    Featurizer,
    TfidfFeaturizer,
    featurize_documents,
    tokenize,
)
from axon.types import Document


def test_tokenize_lowercases_and_drops_stopwords():
    toks = tokenize("The Iron and IRON supplementation")
    assert "the" not in toks and "and" not in toks
    assert toks.count("iron") == 2
    assert "supplementation" in toks


def test_tfidf_is_a_featurizer():
    assert issubclass(TfidfFeaturizer, Featurizer)


def test_tfidf_shape_and_l2_normalized():
    corpus = [
        "iron supplementation cognition memory",
        "iron memory cognition adults",
        "tidal coastal mollusks ocean",
        "compiler optimization sparse graphs",
    ]
    f = TfidfFeaturizer(min_df=1, max_df=1.0)
    X = f.fit_transform(corpus)
    assert X.shape == (4, f.dim)
    norms = np.linalg.norm(X, axis=1)
    assert np.allclose(norms, 1.0)  # every doc has tokens -> unit rows


def test_tfidf_similar_docs_more_similar_than_dissimilar():
    corpus = [
        "iron supplementation cognition memory",
        "iron memory cognition adults",          # shares iron/memory/cognition
        "compiler optimization sparse graphs",   # unrelated
    ]
    X = TfidfFeaturizer(min_df=1, max_df=1.0).fit_transform(corpus)
    sim_related = float(X[0] @ X[1])
    sim_unrelated = float(X[0] @ X[2])
    assert sim_related > sim_unrelated


def test_tfidf_is_deterministic():
    corpus = ["alpha beta gamma", "beta gamma delta", "gamma delta epsilon"]
    a = TfidfFeaturizer(min_df=1).fit_transform(corpus)
    b = TfidfFeaturizer(min_df=1).fit_transform(corpus)
    assert np.array_equal(a, b)


def test_tfidf_transform_before_fit_raises():
    with pytest.raises(RuntimeError):
        TfidfFeaturizer().transform(["x y z"])


def test_tfidf_empty_vocab_raises():
    # All terms appear once; min_df=5 prunes everything.
    with pytest.raises(ValueError):
        TfidfFeaturizer(min_df=5).fit(["a b c", "d e f"])


def test_featurize_documents_attaches_vectors_without_mutating_inputs():
    docs = [
        Document(doc_id="d1", text="iron memory cognition"),
        Document(doc_id="d2", text="iron memory adults"),
    ]
    out = featurize_documents(TfidfFeaturizer(min_df=1), docs)
    assert docs[0].vector is None              # input untouched
    assert out[0].vector is not None
    assert out[0].vector.shape[0] > 0
    assert out[0].doc_id == "d1"
