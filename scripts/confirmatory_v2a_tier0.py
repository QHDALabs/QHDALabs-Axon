"""Confirmatory V2-A Tier 0 run — real V1, seeds derived from the pre-registration SHA.

FROZEN (Phase 3: execute once, log the result as-is). Runs the pre-registered line-A
grid (docs=20), deriving every world seed from the operational pre-registration commit
SHA per §6.4, evaluates the §7 PASS/FAIL criteria (inclusive), and emits one JSON object
with the verdict. Scoring is real V1 only — it reuses the frozen mechanism through
``run_width_sweep`` / ``run_latent_parent`` (which call ``frozen_v1_scorer``); it never
substitutes a scorer.

Per the frozen pre-registration and the development-pilot numbers, this run is EXPECTED
to FAIL at the contract cell ``thin_half_n4`` (θ_full). A FAIL is a first-class result —
logged as-is, no Tier 1, no tuning.

Usage:   python scripts/confirmatory_v2a_tier0.py
Runtime: multi-hour on real V1 at R=200.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence, cast

from axon.verification.tier0_generator import PilotConfig

from pilot_v2a_grid import GRID_CELLS
from pilot_v2a_tier0 import run_latent_parent, run_width_sweep

# --- FROZEN confirmatory parameters (operational pre-registration, line A) ----------
PREREG_SHA = "8ef6057e5a2bcef67a0bcfb5b3d68c4927d6d551"   # seed root (§6.4)
R = 200                                                    # replicates per cell (§6.5)
THETA_WIDTH0 = 0.10        # §7.2  width=0 pass: risk_rate <= θ (per side), base regime
THETA_FULL = 0.80          # §7.3  full-width pass: degradation_rate >= θ
THETA_S2 = 0.90            # §7.4  latent parent pass: risk_rate_a >= θ AND risk_rate_c >= θ
BASE_REGIME = ("base", "strong", "thin")   # cells the width=0 power criterion binds
CONTRACT_CELLS = ("thin_half_n4",)         # a full-width FAIL here == a Tier 0 FAIL (§9.1)

Curve = Mapping[str, object]


def world_seed(sha: str, namespace: str, replicate_index: int) -> int:
    """§6.4 seed derivation: one world per (namespace, replicate) from the prereg SHA.

    ``namespace`` is a grid_cell_id (S1) or the literal ``latent_parent`` (S2).
    """
    payload = f"{sha}|V2A|Tier0|{namespace}|{replicate_index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _f(curve: Curve, key: str) -> float:
    return float(cast(float, curve[key]))


def _full_width_symmetric(curves: Sequence[Curve]) -> Curve:
    points = [c for c in curves if c["mode"] == "symmetric"]
    return max(points, key=lambda c: int(cast(int, c["width"])))


def _width0_symmetric(curves: Sequence[Curve]) -> Curve:
    return next(c for c in curves if c["mode"] == "symmetric" and int(cast(int, c["width"])) == 0)


def evaluate(
    cells: Sequence[Mapping[str, object]], latent: Mapping[str, float]
) -> dict[str, object]:
    """Apply the frozen §7 criteria (inclusive) and return the Tier 0 verdict (§9.1)."""
    checks: list[dict[str, object]] = []

    # §7.1 — S1 monotonicity: exactly zero within-replicate reversals, every cell.
    reversals = {
        str(c["id"]): len(cast(Sequence[object], c["monotonicity_violations"])) for c in cells
    }
    mono_ok = all(v == 0 for v in reversals.values())
    checks.append({"criterion": "S1_monotonicity", "pass": mono_ok, "reversals": reversals})

    # §7.2 — S1 width=0 power: risk_rate <= θ on BOTH sides, base-regime cells.
    w0: dict[str, object] = {}
    w0_ok = True
    for c in cells:
        cid = str(c["id"])
        if cid in BASE_REGIME:
            point = _width0_symmetric(cast(Sequence[Curve], c["curves"]))
            ok = _f(point, "risk_rate_a") <= THETA_WIDTH0 and _f(point, "risk_rate_c") <= THETA_WIDTH0
            w0[cid] = {"risk_rate_a": point["risk_rate_a"], "risk_rate_c": point["risk_rate_c"], "pass": ok}
            w0_ok = w0_ok and ok
    checks.append({"criterion": "S1_width0_power", "theta": THETA_WIDTH0,
                   "scope": list(BASE_REGIME), "pass": w0_ok, "cells": w0})

    # §7.3 — S1 full-width degradation: degradation_rate >= θ; verdict binds on contract cells.
    full: dict[str, object] = {}
    for c in cells:
        cid = str(c["id"])
        point = _full_width_symmetric(cast(Sequence[Curve], c["curves"]))
        ok = _f(point, "degradation_rate") >= THETA_FULL
        full[cid] = {"degradation_rate": point["degradation_rate"], "pass": ok,
                     "contract": cid in CONTRACT_CELLS}
    contract_ok = all(bool(cast(Mapping[str, object], full[cid])["pass"]) for cid in CONTRACT_CELLS)
    checks.append({"criterion": "S1_full_width_degradation", "theta": THETA_FULL,
                   "contract_cells": list(CONTRACT_CELLS), "contract_pass": contract_ok,
                   "all_cells": full})

    # §7.4 — S2 latent parent: both sides >= θ.
    s2_ok = latent["risk_rate_a"] >= THETA_S2 and latent["risk_rate_c"] >= THETA_S2
    checks.append({"criterion": "S2_latent_parent", "theta": THETA_S2,
                   "risk_rate_a": latent["risk_rate_a"], "risk_rate_c": latent["risk_rate_c"],
                   "pass": s2_ok})

    tier0_pass = mono_ok and w0_ok and contract_ok and s2_ok
    return {"tier0_pass": tier0_pass, "verdict": "PASS" if tier0_pass else "FAIL", "checks": checks}


def run_confirmatory(
    sha: str = PREREG_SHA,
    replicates: int = R,
    cells_spec: Sequence[tuple[str, float, float, int]] = GRID_CELLS,
) -> dict[str, object]:
    cells: list[dict[str, object]] = []
    for cell_id, mechanism_rate, peer_document_ratio, noise_per_document in cells_spec:
        config = PilotConfig(
            mechanism_rate=mechanism_rate,
            peer_document_ratio=peer_document_ratio,
            noise_per_document=noise_per_document,
        )
        seeds = [world_seed(sha, cell_id, rep) for rep in range(replicates)]
        sweep = run_width_sweep(config, seeds)
        cells.append({
            "id": cell_id,
            "config": config.__dict__,
            "curves": sweep["curves"],
            "monotonicity_violations": sweep["monotonicity_violations"],
        })

    latent_config = PilotConfig()
    latent_seeds = [world_seed(sha, "latent_parent", rep) for rep in range(replicates)]
    latent = run_latent_parent(latent_config, latent_seeds)

    return {
        "label": "CONFIRMATORY V2-A TIER 0 — line A",
        "pre_registration_sha": sha,
        "replicates": replicates,
        "cells": cells,
        "latent_parent": {**latent, "config": latent_config.__dict__},
        "evaluation": evaluate(cells, latent),
    }


def main() -> None:
    print(json.dumps(run_confirmatory(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
