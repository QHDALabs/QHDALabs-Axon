"""Development-only synthetic generator for the V2-A Tier 0 pilot.

The generator emits documents, not profiles. Mechanism terms are injected into
existing documents, the background is fixed for a whole replicate, and widening
uses nested prefixes of one frozen peer permutation.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable

import numpy as np


class SpreadMode(str, Enum):
    A_ONLY = "a_only"
    C_ONLY = "c_only"
    SYMMETRIC = "symmetric"


@dataclass(frozen=True)
class SyntheticDocument:
    doc_id: str
    literature: str
    mesh: tuple[str, ...]


@dataclass(frozen=True)
class PilotConfig:
    """Development values only; none are confirmatory until separately frozen."""

    n_peers: int = 24
    documents_per_literature: int = 60
    peer_document_ratio: float = 1.0
    background_topics: int = 8
    background_documents_per_topic: int = 60
    parent_terms: int = 16
    mechanism_terms: int = 8
    private_terms: int = 24
    generic_terms: int = 4
    noise_terms: int = 64
    parent_rate: float = 0.45
    mechanism_rate: float = 0.30
    private_rate: float = 0.55
    background_mechanism_rate: float = 0.25
    noise_per_document: int = 1


@dataclass(frozen=True)
class SyntheticWorld:
    config: PilotConfig
    base_documents: tuple[SyntheticDocument, ...]
    background_labels: tuple[str, ...]
    peers_a: tuple[str, ...]
    peers_c: tuple[str, ...]
    permutation_a: tuple[str, ...]
    permutation_c: tuple[str, ...]
    mechanism_masks: dict[str, tuple[tuple[str, ...], ...]]

    def documents_for_width(
        self,
        width: int,
        mode: SpreadMode,
    ) -> tuple[SyntheticDocument, ...]:
        """Add M to existing documents; never add documents or modify background."""

        if not 0 <= width <= self.config.n_peers:
            raise ValueError("width must be between zero and n_peers")
        enabled: set[str] = set()
        if mode in (SpreadMode.A_ONLY, SpreadMode.SYMMETRIC):
            enabled.update(self.permutation_a[:width])
        if mode in (SpreadMode.C_ONLY, SpreadMode.SYMMETRIC):
            enabled.update(self.permutation_c[:width])

        indices: dict[str, int] = {}
        output: list[SyntheticDocument] = []
        for doc in self.base_documents:
            index = indices.get(doc.literature, 0)
            indices[doc.literature] = index + 1
            if doc.literature not in enabled:
                output.append(doc)
                continue
            extra = self.mechanism_masks[doc.literature][index]
            output.append(replace(doc, mesh=doc.mesh + extra))
        return tuple(output)


def build_world(
    seed: int,
    config: PilotConfig = PilotConfig(),
    *,
    latent_parent: bool = False,
) -> SyntheticWorld:
    """Create one paired world shared by every mechanism-width cell."""

    _validate_config(config)
    rng = np.random.default_rng(seed)
    m_terms = tuple(f"mechanism_{i}" for i in range(config.mechanism_terms))
    generic = tuple(f"generic_{i}" for i in range(config.generic_terms))
    noise = tuple(f"noise_{i}" for i in range(config.noise_terms))
    parent_a = tuple(f"parent_a_{i}" for i in range(config.parent_terms))
    parent_c = parent_a if latent_parent else tuple(
        f"parent_c_{i}" for i in range(config.parent_terms)
    )
    peers_a = tuple(f"peer_a_{i:02d}" for i in range(config.n_peers))
    peers_c = tuple(f"peer_c_{i:02d}" for i in range(config.n_peers))
    endpoint_labels = ("endpoint_a", "endpoint_c")
    all_target_labels = endpoint_labels + peers_a + peers_c

    documents: list[SyntheticDocument] = []
    masks: dict[str, tuple[tuple[str, ...], ...]] = {}
    for label in all_target_labels:
        side_a = label == "endpoint_a" or label.startswith("peer_a_")
        parent = parent_a if side_a else parent_c
        private = tuple(f"private_{label}_{i}" for i in range(config.private_terms))
        label_masks: list[tuple[str, ...]] = []
        n_documents = config.documents_per_literature
        if label.startswith("peer_"):
            n_documents = max(1, round(n_documents * config.peer_document_ratio))
        for doc_index in range(n_documents):
            base_terms = (
                _sample_terms(rng, parent, config.parent_rate)
                + _sample_terms(rng, private, config.private_rate)
                + generic
                + _sample_noise(rng, noise, config.noise_per_document)
            )
            endpoint_m = (
                _sample_terms(rng, m_terms, config.mechanism_rate)
                if label in endpoint_labels
                else ()
            )
            documents.append(
                SyntheticDocument(
                    doc_id=f"{label}_{doc_index:03d}",
                    literature=label,
                    mesh=base_terms + endpoint_m,
                )
            )
            label_masks.append(_sample_terms(rng, m_terms, config.mechanism_rate))
        masks[label] = tuple(label_masks)

    background_labels = tuple(f"background_{i:02d}" for i in range(config.background_topics))
    for label in background_labels:
        private = tuple(f"private_{label}_{i}" for i in range(config.private_terms))
        background_m = _balanced_term_assignments(
            rng,
            m_terms,
            config.background_documents_per_topic,
            config.background_mechanism_rate,
        )
        for doc_index in range(config.background_documents_per_topic):
            mesh = (
                _sample_terms(rng, private, config.private_rate)
                + background_m[doc_index]
                + generic
                + _sample_noise(rng, noise, config.noise_per_document)
            )
            documents.append(
                SyntheticDocument(
                    doc_id=f"{label}_{doc_index:03d}",
                    literature=label,
                    mesh=mesh,
                )
            )

    return SyntheticWorld(
        config=config,
        base_documents=tuple(documents),
        background_labels=background_labels,
        peers_a=peers_a,
        peers_c=peers_c,
        permutation_a=tuple(rng.permutation(peers_a).tolist()),
        permutation_c=tuple(rng.permutation(peers_c).tolist()),
        mechanism_masks=masks,
    )


def _sample_terms(
    rng: np.random.Generator,
    terms: tuple[str, ...],
    rate: float,
) -> tuple[str, ...]:
    if not terms:
        return ()
    mask = rng.random(len(terms)) < rate
    return tuple(term for term, include in zip(terms, mask) if include)


def _sample_noise(
    rng: np.random.Generator,
    terms: tuple[str, ...],
    count: int,
) -> tuple[str, ...]:
    if count == 0:
        return ()
    selected = rng.choice(len(terms), size=count, replace=False)
    return tuple(terms[int(index)] for index in selected)


def _balanced_term_assignments(
    rng: np.random.Generator,
    terms: tuple[str, ...],
    n_documents: int,
    rate: float,
) -> tuple[tuple[str, ...], ...]:
    """Place every term at a fixed document frequency in the background.

    This makes M common-pool eligible by construction instead of merely likely:
    every M term has background_df > 0 and, for rates <= 0.5, df_ratio <= 0.5.
    """

    per_document: list[list[str]] = [[] for _ in range(n_documents)]
    occurrences = min(n_documents, max(1, round(rate * n_documents)))
    for term in terms:
        indices = rng.choice(n_documents, size=occurrences, replace=False)
        for index in indices:
            per_document[int(index)].append(term)
    return tuple(tuple(items) for items in per_document)


def _validate_config(config: PilotConfig) -> None:
    if config.n_peers < 1 or config.documents_per_literature < 1:
        raise ValueError("n_peers and documents_per_literature must be positive")
    if config.peer_document_ratio <= 0.0:
        raise ValueError("peer_document_ratio must be positive")
    if config.noise_per_document > config.noise_terms:
        raise ValueError("noise_per_document cannot exceed noise_terms")
    rates: Iterable[float] = (
        config.parent_rate,
        config.mechanism_rate,
        config.private_rate,
        config.background_mechanism_rate,
    )
    if any(not 0.0 <= rate <= 1.0 for rate in rates):
        raise ValueError("all inclusion rates must be in [0, 1]")
