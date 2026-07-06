"""Unit tests for the confirmatory runner's pure logic: SHA-derived seeds and the
frozen §7 verdict. These need no real V1 — they pin `world_seed` and `evaluate` so the
Tier 0 verdict cannot silently drift. The multi-hour real-V1 run is separate."""

import hashlib
import importlib.util
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load():
    sys.path.insert(0, str(_SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "confirmatory_v2a_tier0", _SCRIPTS / "confirmatory_v2a_tier0.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONF = _load()


def _cell(cid, w0_a, w0_c, full_deg, reversals=0):
    return {
        "id": cid,
        "monotonicity_violations": [{} for _ in range(reversals)],
        "curves": [
            {"mode": "symmetric", "width": 0, "risk_rate_a": w0_a, "risk_rate_c": w0_c,
             "degradation_rate": max(w0_a, w0_c)},
            {"mode": "symmetric", "width": 1, "risk_rate_a": 0.0, "risk_rate_c": 0.0,
             "degradation_rate": full_deg},
            # non-symmetric points must be ignored by the verdict:
            {"mode": "a_only", "width": 1, "risk_rate_a": 0.0, "risk_rate_c": 0.0,
             "degradation_rate": 0.0},
        ],
    }


def test_world_seed_is_deterministic_and_64_bit():
    a = CONF.world_seed("abc", "base", 0)
    assert a == CONF.world_seed("abc", "base", 0)          # deterministic
    assert a != CONF.world_seed("abc", "base", 1)          # per replicate
    assert a != CONF.world_seed("abc", "thin", 0)          # per cell namespace
    assert 0 <= a < 2 ** 64                                # 64-bit big-endian
    expected = int.from_bytes(
        hashlib.sha256(b"abc|V2A|Tier0|base|0").digest()[:8], "big"
    )
    assert a == expected


def _base_cells(thin_half_n4_full_deg):
    # base regime clears width=0 (<=0.10); contract cell carries the tested full deg.
    return [
        _cell("base", 0.0, 0.0, 1.0),
        _cell("strong", 0.0, 0.0, 1.0),
        _cell("thin", 0.1, 0.1, 1.0),
        _cell("thin_half_n4", 0.0, 0.0, thin_half_n4_full_deg),
        _cell("probe_20_h_2", 0.0, 0.0, 0.6),   # characterization: fails but does not bind
    ]


def test_verdict_fails_when_contract_cell_misses_full_width():
    cells = _base_cells(thin_half_n4_full_deg=0.6)   # < 0.80
    result = CONF.evaluate(cells, {"risk_rate_a": 0.95, "risk_rate_c": 0.95})
    assert result["verdict"] == "FAIL"
    assert result["tier0_pass"] is False


def test_verdict_passes_when_all_frozen_criteria_hold():
    cells = _base_cells(thin_half_n4_full_deg=0.9)   # >= 0.80
    result = CONF.evaluate(cells, {"risk_rate_a": 0.95, "risk_rate_c": 0.95})
    assert result["verdict"] == "PASS"
    assert result["tier0_pass"] is True


def test_verdict_fails_on_any_monotonicity_reversal():
    cells = _base_cells(thin_half_n4_full_deg=0.9)
    cells[0]["monotonicity_violations"].append({"seed": 1})  # one reversal in `base`
    result = CONF.evaluate(cells, {"risk_rate_a": 0.95, "risk_rate_c": 0.95})
    assert result["verdict"] == "FAIL"


def test_verdict_fails_when_latent_parent_below_theta():
    cells = _base_cells(thin_half_n4_full_deg=0.9)
    result = CONF.evaluate(cells, {"risk_rate_a": 0.80, "risk_rate_c": 0.95})  # A < 0.90
    assert result["verdict"] == "FAIL"


def test_characterization_cell_failure_does_not_bind_verdict():
    # probe_* fails full-width (0.6) but is not a contract cell -> verdict stays PASS.
    cells = _base_cells(thin_half_n4_full_deg=0.9)
    assert CONF.evaluate(cells, {"risk_rate_a": 0.95, "risk_rate_c": 0.95})["verdict"] == "PASS"
