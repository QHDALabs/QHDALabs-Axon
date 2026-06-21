"""
qhda_core.quantum — warstwa kwantowa: mosty i zegar Page-Wootters.

Czysty Qiskit. To są mechanizmy, które LECĄ NA QC. Buduje QuantumCircuit.

Import qiskit jest LENIWY (wewnątrz funkcji), nie na poziomie modułu. Dzięki temu:
    import qhda_core            # działa zawsze, też bez Qiskit
    from qhda_core.quantum ... # rzuca czytelny błąd dopiero gdy Qiskit brakuje

To pozwala projektowi klasycznemu (wildfire) zaimportować qhda_core i używać
warstwy relacyjnej, nie mając w ogóle zainstalowanego Qiskit.

Mechanizmy:
  conditional_cz_bridge — most z qmnet: ancilla steruje CZ między dwoma
                          niezwiązanymi qubitami. "Odpala", gdy ancilla→|1⟩.
  page_wootters_clock   — rejestr zegara PW w superpozycji + sprzężenie
                          clock↔system (czas relacyjny wyłania się z korelacji).
"""

from __future__ import annotations
from typing import Optional, Sequence
import numpy as np


def _require_qiskit():
    """Leniwy import Qiskit z czytelnym komunikatem, jeśli brakuje."""
    try:
        from qiskit import QuantumCircuit  # noqa: F401
        return
    except ImportError as e:
        raise ImportError(
            "qhda_core.quantum wymaga Qiskit. Zainstaluj:\n"
            "    pip install 'qhda-core[quantum]'\n"
            "Warstwa relacyjna (qhda_core.relational) działa bez Qiskit."
        ) from e


# ═══════════════════════════════════════════════════════════════════════════
# CONDITIONAL CZ BRIDGE  (z qmnet)
# ═══════════════════════════════════════════════════════════════════════════

def conditional_cz_bridge(
    qc,
    ancilla: int,
    control: int,
    target: int,
    drive_angle: float,
    uncompute: bool = True,
):
    """
    Dodaje warunkowy most CZ do istniejącego obwodu (in-place).

    Mechanizm z qmnet: ancilla obracana o drive_angle decyduje, czy most
    "odpala". Gdy ancilla bliska |1⟩, między control a target powstaje
    korelacja ZZ — most łączy qubity, które nie są bezpośrednio związane.

    Schemat (CX–CZ–CX zachowuje koherencję):
        ry(drive_angle) na ancilla
        CX(ancilla → target)
        CZ(control, target)
        CX(ancilla → target)   [jeśli uncompute]

    Parametry:
      qc          : QuantumCircuit do modyfikacji (in-place)
      ancilla     : indeks qubita-wyzwalacza
      control     : indeks qubita kontrolnego mostu
      target      : indeks qubita docelowego mostu
      drive_angle : kąt RY na ancilli ∈ [0, π]. 0 → most martwy,
                    π → most maksymalnie aktywny. P(|1⟩) = sin²(angle/2).
      uncompute   : czy odwrócić CX po CZ (zalecane dla zachowania koherencji
                    ancilli do dalszych operacji).

    Zwraca: qc (ten sam obiekt, dla łańcuchowania).

    Konwencja drive_angle (z XSIG): mapuj siłę sygnału na kąt, np.
        drive_angle = π · clip(signal_strength, 0.2, 0.95)
    żeby most nigdy nie był ani całkiem martwy, ani nasycony.
    """
    _require_qiskit()
    qc.ry(drive_angle, ancilla)
    qc.cx(ancilla, target)
    qc.cz(control, target)
    if uncompute:
        qc.cx(ancilla, target)
    return qc


def bridge_probability(drive_angle: float) -> float:
    """P(ancilla=|1⟩) = sin²(angle/2) — prawdopodobieństwo odpalenia mostu."""
    return float(np.sin(drive_angle / 2.0) ** 2)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE-WOOTTERS CLOCK
# ═══════════════════════════════════════════════════════════════════════════

def page_wootters_clock(
    qc,
    clock_qubits: Sequence[int],
    system_qubits: Sequence[int],
    coupling: float = 0.85,
    clock_phase: float = 0.0,
):
    """
    Inicjalizuje rejestr zegara Page-Wootters i sprzęga go z systemem (in-place).

    Mechanizm z qmnet/XSIG: czas nie jest parametrem zewnętrznym — wyłania się
    z korelacji między rejestrem "zegara" a rejestrem "systemu". Zegar w
    równomiernej superpozycji reprezentuje wszystkie "momenty" naraz; sprzężenie
    clock↔system sprawia, że stan systemu zależy od "odczytu zegara".

    Kroki:
      1. Hadamard na każdym qubicie zegara → superpozycja momentów.
      2. Opcjonalna faza RZ(clock_phase) na pierwszym qubicie zegara —
         moduluje "tempo" zegara (w XSIG: faza ∝ |Δcorr|, tempo zmian struktury).
      3. Sprzężenie controlled-RY: każdy qubit zegara warunkuje odpowiadający
         qubit systemu (moment historii ↔ amplituda obserwabli).

    Parametry:
      qc            : QuantumCircuit (in-place)
      clock_qubits  : indeksy rejestru zegara
      system_qubits : indeksy rejestru systemu
      coupling      : siła sprzężenia clock↔system ∈ [0,1] (×π/2 jako kąt CRY)
      clock_phase   : faza modulująca tempo zegara [rad]

    Zwraca: qc.
    """
    _require_qiskit()

    # 1. Superpozycja momentów
    for cq in clock_qubits:
        qc.h(cq)

    # 2. Modulacja tempa zegara
    if abs(clock_phase) > 1e-12 and len(clock_qubits) > 0:
        qc.rz(clock_phase, clock_qubits[0])

    # 3. Sprzężenie clock↔system
    n_sys = len(system_qubits)
    for k, cq in enumerate(clock_qubits):
        if n_sys == 0:
            break
        target = system_qubits[k % n_sys]
        qc.cry(coupling * np.pi / 2, cq, target)
        # propagacja korelacji do sąsiedniego qubita systemu
        if k + 1 < n_sys:
            qc.cx(target, system_qubits[(k + 1) % n_sys])

    return qc
