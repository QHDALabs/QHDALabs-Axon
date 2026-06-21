"""
qhda_core — autorskie mechanizmy QHDALabs jako biblioteka wielokrotnego użytku.

Krzysztof Banasiewicz | QHDALabs

Cztery mechanizmy, dwie warstwy:

  WARSTWA KWANTOWA (leci na QC, wymaga [quantum]):
    conditional_cz_bridge  — most z qmnet
    page_wootters_clock    — zegar Page-Wootters

  WARSTWA RELACYJNA (CPU, czysty numpy, zawsze dostępna):
    RelationalState        — akumulator h(t) (z RTANA)
    EmergentClock          — emergentny czas (tempo zmian relacyjnych)

  KONTRAKT (spina warstwy):
    MeasurementOutcome     — neutralny typ przepływający z kwantowej do relacyjnej

Import warstwy relacyjnej działa zawsze:
    from qhda_core import RelationalState, EmergentClock, MeasurementOutcome

Import warstwy kwantowej wymaga Qiskit (pip install 'qhda-core[quantum]'):
    from qhda_core import conditional_cz_bridge, page_wootters_clock
"""

__version__ = "0.1.0"

# ── Kontrakt + warstwa relacyjna: zawsze dostępne (tylko numpy) ──
from .types import MeasurementOutcome
from .relational.state import RelationalState, RelationalConfig, tanh_activation
from .emergent.clock import EmergentClock, delta_norm_tempo, cosine_tempo

# ── Warstwa kwantowa: import "miękki" ──
# Importujemy nazwy, ale faktyczne wywołanie funkcji sprawdzi Qiskit wewnątrz
# (przez _require_qiskit). Samo `from qhda_core import conditional_cz_bridge`
# działa bez Qiskit; dopiero WYWOŁANIE rzuci czytelny błąd, jeśli brakuje.
from .quantum.circuits import (
    conditional_cz_bridge,
    bridge_probability,
    page_wootters_clock,
)

__all__ = [
    "__version__",
    # kontrakt
    "MeasurementOutcome",
    # relacyjna
    "RelationalState",
    "RelationalConfig",
    "tanh_activation",
    # emergentny czas
    "EmergentClock",
    "delta_norm_tempo",
    "cosine_tempo",
    # kwantowa
    "conditional_cz_bridge",
    "bridge_probability",
    "page_wootters_clock",
]
