"""Smoke test for the pilot run() split into run_width_sweep / run_latent_parent.

Guards that the split stays behavior-preserving: run() must reuse the two helpers'
outputs verbatim (no recomputation, no drift) and keep its original JSON shape. Uses
a tiny config and the real V1 scorer (pure numpy, no network)."""

import importlib.util
from pathlib import Path

import pytest

from axon.verification.tier0_generator import PilotConfig

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "pilot_v2a_tier0.py"


@pytest.fixture(scope="module")
def pilot():
    spec = importlib.util.spec_from_file_location("pilot_v2a_tier0", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tiny() -> PilotConfig:
    return PilotConfig(n_peers=1, documents_per_literature=5, background_documents_per_topic=5)


def test_split_composes_without_drift(pilot):
    cfg = _tiny()
    sweep = pilot.run_width_sweep(cfg)
    assert set(sweep) == {"curves", "monotonicity_violations"}

    latent = pilot.run_latent_parent(cfg)
    assert set(latent) == {"risk_rate_a", "risk_rate_c"}

    full = pilot.run(cfg)
    assert set(full) == {
        "label", "development_width_seeds", "development_latent_parent_seeds",
        "config", "monotonicity_violations", "curves", "latent_parent",
    }
    assert full["label"] == "DEVELOPMENT PILOT — NOT CONFIRMATORY"
    # run() reuses the helpers' outputs verbatim.
    assert full["latent_parent"] == latent
    assert full["curves"] == sweep["curves"]
    assert full["monotonicity_violations"] == sweep["monotonicity_violations"]
