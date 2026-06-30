"""One-shot DEVELOPMENT grid runner for the V2-A Tier 0 pilot, on real V1.

Runs the frozen 11-cell development grid (mirroring docs/V2A_GENERATOR_PILOT_DEV.md:
the 7 main-table cells plus the 4 boundary probes) in a single invocation and emits
one JSON object to stdout. There are no flags that alter the grid and no per-cell
reruns: one invocation = whole grid = one JSON.

This is DEVELOPMENT calibration (Phase 1). The output is NOT confirmatory Tier 0
evidence and is labelled as such. Scoring is real V1 only — run_width_sweep /
run_latent_parent score via selectivity.frozen_v1_scorer (real propose_bridge through
a real LiteratureStore). If the real V1 import fails, this runner fails loudly; it
never degrades to a substitute scorer.

Usage:  python scripts/pilot_v2a_grid.py
"""

from __future__ import annotations

import json

from axon.verification.tier0_generator import PilotConfig

# Reuse the existing pilot helpers and DEV seeds (0..9 / 0..19). No new seeds.
# Sibling script in scripts/; importable when run as `python scripts/pilot_v2a_grid.py`.
from pilot_v2a_tier0 import (
    DEV_LATENT_PARENT_SEEDS,
    DEV_WIDTH_SEEDS,
    run_latent_parent,
    run_width_sweep,
)

# FROZEN development grid: (id, mechanism_rate, peer_document_ratio, noise_per_document).
# Mirrors docs/V2A_GENERATOR_PILOT_DEV.md — main table (lines 37-43) + boundary probes
# (lines 49-52). Every other PilotConfig field stays at its current default.
GRID_CELLS: tuple[tuple[str, float, float, int], ...] = (
    ("base",          0.30, 1.0, 1),
    ("thin",          0.15, 1.0, 1),
    ("strong",        0.50, 1.0, 1),
    ("thin_halfcorp", 0.15, 0.5, 1),
    ("thin_double",   0.15, 2.0, 1),
    ("thin_noise4",   0.15, 1.0, 4),
    ("thin_half_n4",  0.15, 0.5, 4),
    ("probe_20_h_2",  0.20, 0.5, 2),
    ("probe_20_h_4",  0.20, 0.5, 4),
    ("probe_25_h_4",  0.25, 0.5, 4),
    ("probe_20_1_2",  0.20, 1.0, 2),
)


def run_grid() -> dict[str, object]:
    cells: list[dict[str, object]] = []
    for cell_id, mechanism_rate, peer_document_ratio, noise_per_document in GRID_CELLS:
        config = PilotConfig(
            mechanism_rate=mechanism_rate,
            peer_document_ratio=peer_document_ratio,
            noise_per_document=noise_per_document,
        )
        sweep = run_width_sweep(config)  # all three SpreadModes, real V1
        cells.append(
            {
                "id": cell_id,
                "config": config.__dict__,
                "curves": sweep["curves"],
                # Surfaced verbatim per cell — any within-replicate reversal in ANY
                # cell must be visible (zero reversals is a pilot pass-criterion).
                "monotonicity_violations": sweep["monotonicity_violations"],
            }
        )

    # Latent-parent (mechanism absent) computed exactly ONCE, not per cell.
    latent_config = PilotConfig()
    latent = run_latent_parent(latent_config)

    return {
        "label": "DEVELOPMENT PILOT — NOT CONFIRMATORY",
        "development_width_seeds": list(DEV_WIDTH_SEEDS),
        "development_latent_parent_seeds": list(DEV_LATENT_PARENT_SEEDS),
        "cells": cells,
        "latent_parent": {**latent, "config": latent_config.__dict__},
    }


def main() -> None:
    print(json.dumps(run_grid(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
