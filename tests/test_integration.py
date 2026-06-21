"""
Test integracyjny qhda_core — weryfikuje, że biblioteka odtwarza
kluczowe zachowania z XSIG / qmnet, w czystej, przenośnej formie.
"""

import numpy as np
import pytest

from qhda_core import (
    MeasurementOutcome,
    RelationalState,
    RelationalConfig,
    EmergentClock,
    bridge_probability,
)


# ═══════════════════════════════════════════════════════════════════════════
# WARSTWA RELACYJNA — sedno XSIG: rozróżnić szum od struktury
# ═══════════════════════════════════════════════════════════════════════════

def _stream(mode: str, n_events: int, dim: int, seed: int):
    """Generuje strumień outcome: 'noise' = losowy, 'structure' = koherentny."""
    rng = np.random.default_rng(seed)
    outcomes = []
    for i in range(n_events):
        if mode == "noise":
            vec = rng.normal(0, 1.0, dim)
            zz = rng.normal(0, 0.05)          # losowy znak
            fired = rng.random() > 0.5
        else:  # structure
            phase = np.cos(2 * np.pi * i / n_events)
            vec = phase * np.ones(dim) + rng.normal(0, 0.3, dim)
            zz = 0.06 + abs(rng.normal(0, 0.02))  # systematycznie dodatnie
            fired = True
        outcomes.append(MeasurementOutcome(
            observables={"zz": zz},
            vector=vec,
            bridge_fired=fired,
            index=i,
        ))
    return outcomes


def _run(mode, seed, n_events=40, dim=8):
    state = RelationalState(RelationalConfig(dim=dim, signal_key="zz"))
    for o in _stream(mode, n_events, dim, seed):
        state.update(o)
    return state.structural_score


def test_relational_separates_noise_from_structure():
    """RelationalState daje wyższy structural_score dla struktury niż dla szumu."""
    noise = np.array([_run("noise", s) for s in range(8)])
    struct = np.array([_run("structure", s) for s in range(8)])
    # Struktura powinna mieć systematycznie wyższy wskaźnik
    assert struct.mean() > noise.mean(), (
        f"struktura {struct.mean():.3f} powinna > szum {noise.mean():.3f}"
    )


def test_relational_works_without_qiskit():
    """Warstwa relacyjna działa na czystym numpy — bez Qiskit."""
    state = RelationalState(RelationalConfig(dim=4))
    for i in range(5):
        state.update(MeasurementOutcome(
            observables={}, vector=np.ones(4) * 0.1, index=i
        ))
    assert state.t == 5
    assert state.h_norm >= 0.0


def test_bridge_fired_strengthens_coupling():
    """Most odpalony → silniejsze sprzężenie → większa norma h."""
    cfg = RelationalConfig(dim=4)
    s_fired = RelationalState(cfg)
    s_idle = RelationalState(cfg)
    vec = np.ones(4) * 0.5
    for i in range(10):
        s_fired.update(MeasurementOutcome({}, vec, bridge_fired=True, index=i))
        s_idle.update(MeasurementOutcome({}, vec, bridge_fired=False, index=i))
    assert s_fired.h_norm > s_idle.h_norm


# ═══════════════════════════════════════════════════════════════════════════
# EMERGENTNY CZAS
# ═══════════════════════════════════════════════════════════════════════════

def test_emergent_clock_proper_time_differs_from_event_count():
    """Czas własny ≠ liczba zdarzeń: szybkie zmiany → więcej czasu własnego."""
    fast = EmergentClock()
    slow = EmergentClock()
    rng = np.random.default_rng(0)
    for i in range(20):
        fast.tick(MeasurementOutcome({}, rng.normal(0, 1.0, 8), index=i))   # duże zmiany
        slow.tick(MeasurementOutcome({}, np.ones(8) * 0.01, index=i))        # stabilne
    assert fast.proper_time > slow.proper_time
    assert fast.n_events == slow.n_events == 20  # ta sama liczba zdarzeń


# ═══════════════════════════════════════════════════════════════════════════
# WARSTWA KWANTOWA (tylko jeśli Qiskit dostępny)
# ═══════════════════════════════════════════════════════════════════════════

def test_bridge_probability_formula():
    assert bridge_probability(0.0) == pytest.approx(0.0)
    assert bridge_probability(np.pi) == pytest.approx(1.0)
    assert bridge_probability(np.pi / 2) == pytest.approx(0.5)


def test_quantum_layer_builds_circuit():
    """conditional_cz_bridge i page_wootters_clock budują poprawny obwód."""
    qiskit = pytest.importorskip("qiskit")
    from qiskit import QuantumCircuit
    from qhda_core import conditional_cz_bridge, page_wootters_clock

    qc = QuantumCircuit(6)
    page_wootters_clock(qc, clock_qubits=[0, 1], system_qubits=[2, 3],
                        coupling=0.85, clock_phase=0.3)
    conditional_cz_bridge(qc, ancilla=4, control=2, target=5, drive_angle=np.pi / 2)
    # Obwód powinien mieć operacje (nie jest pusty)
    assert qc.size() > 0
    assert qc.num_qubits == 6
