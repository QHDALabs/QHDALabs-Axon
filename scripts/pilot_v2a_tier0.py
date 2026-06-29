"""Run the V2-A generator pilot on development seeds only.

This script is calibration infrastructure, not a confirmatory Tier 0 run. Its
output must not be used as confirmatory evidence and its seeds must not be reused
after the pre-registration is frozen.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import replace

from axon.relational_representation.literature_store import LiteratureStore
from axon.types import Document
from axon.verification.selectivity import PeerSet, assess_pair_selectivity, frozen_v1_scorer
from axon.verification.tier0_generator import (
    PilotConfig,
    SpreadMode,
    SyntheticWorld,
    build_world,
)


DEV_WIDTH_SEEDS = tuple(range(10))
DEV_LATENT_PARENT_SEEDS = tuple(range(20))


def _store(world: SyntheticWorld, width: int, mode: SpreadMode) -> LiteratureStore:
    documents = [
        Document(
            doc_id=doc.doc_id,
            text="",
            metadata={"literature": doc.literature, "mesh": list(doc.mesh)},
        )
        for doc in world.documents_for_width(width, mode)
    ]
    return LiteratureStore(documents, background_labels=world.background_labels)


def run(config: PilotConfig) -> dict[str, object]:
    widths = tuple(range(config.n_peers + 1))
    modes = (SpreadMode.A_ONLY, SpreadMode.C_ONLY, SpreadMode.SYMMETRIC)
    risk_counts: defaultdict[tuple[str, int, str], int] = defaultdict(int)
    aggregate_counts: defaultdict[tuple[str, int], int] = defaultdict(int)
    monotonicity_violations: list[dict[str, object]] = []

    for seed in DEV_WIDTH_SEEDS:
        world = build_world(seed, config)
        for mode in modes:
            previous = (False, False)
            for width in widths:
                store = _store(world, width, mode)
                peers_a = PeerSet("endpoint_a", world.peers_a, world.peers_a)
                peers_c = PeerSet("endpoint_c", world.peers_c, world.peers_c)
                assessment = assess_pair_selectivity(
                    "endpoint_a",
                    "endpoint_c",
                    peers_a,
                    peers_c,
                    frozen_v1_scorer(store),
                    provenance={"development_seed": seed, "mode": mode.value, "width": width},
                )
                current = (
                    assessment.side_a.status.value == "pair_selectivity_not_demonstrated",
                    assessment.side_c.status.value == "pair_selectivity_not_demonstrated",
                )
                if previous[0] and not current[0] or previous[1] and not current[1]:
                    monotonicity_violations.append(
                        {"seed": seed, "mode": mode.value, "width": width,
                         "previous": previous, "current": current}
                    )
                previous = current
                risk_counts[(mode.value, width, "a")] += int(current[0])
                risk_counts[(mode.value, width, "c")] += int(current[1])
                aggregate_counts[(mode.value, width)] += int(current[0] or current[1])

    curves = []
    for mode in modes:
        for width in widths:
            curves.append(
                {
                    "mode": mode.value,
                    "width": width,
                    "risk_rate_a": risk_counts[(mode.value, width, "a")] / len(DEV_WIDTH_SEEDS),
                    "risk_rate_c": risk_counts[(mode.value, width, "c")] / len(DEV_WIDTH_SEEDS),
                    "degradation_rate": aggregate_counts[(mode.value, width)] / len(DEV_WIDTH_SEEDS),
                }
            )
    latent_risk_a = 0
    latent_risk_c = 0
    latent_config = replace(config, mechanism_rate=0.0)
    for seed in DEV_LATENT_PARENT_SEEDS:
        world = build_world(seed, latent_config, latent_parent=True)
        store = _store(world, 0, SpreadMode.SYMMETRIC)
        assessment = assess_pair_selectivity(
            "endpoint_a",
            "endpoint_c",
            PeerSet("endpoint_a", world.peers_a, world.peers_a),
            PeerSet("endpoint_c", world.peers_c, world.peers_c),
            frozen_v1_scorer(store),
            provenance={"development_seed": seed, "scenario": "latent_parent"},
        )
        latent_risk_a += int(
            assessment.side_a.status.value == "pair_selectivity_not_demonstrated"
        )
        latent_risk_c += int(
            assessment.side_c.status.value == "pair_selectivity_not_demonstrated"
        )
    return {
        "label": "DEVELOPMENT PILOT — NOT CONFIRMATORY",
        "development_width_seeds": list(DEV_WIDTH_SEEDS),
        "development_latent_parent_seeds": list(DEV_LATENT_PARENT_SEEDS),
        "config": config.__dict__,
        "monotonicity_violations": monotonicity_violations,
        "curves": curves,
        "latent_parent": {
            "risk_rate_a": latent_risk_a / len(DEV_LATENT_PARENT_SEEDS),
            "risk_rate_c": latent_risk_c / len(DEV_LATENT_PARENT_SEEDS),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", type=int, default=24)
    parser.add_argument("--documents", type=int, default=20)
    parser.add_argument("--background-documents", type=int, default=20)
    parser.add_argument("--mechanism-rate", type=float, default=0.30)
    parser.add_argument("--peer-document-ratio", type=float, default=1.0)
    parser.add_argument("--noise-per-document", type=int, default=1)
    args = parser.parse_args()
    config = PilotConfig(
        n_peers=args.peers,
        documents_per_literature=args.documents,
        background_documents_per_topic=args.background_documents,
        mechanism_rate=args.mechanism_rate,
        peer_document_ratio=args.peer_document_ratio,
        noise_per_document=args.noise_per_document,
    )
    print(json.dumps(run(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
