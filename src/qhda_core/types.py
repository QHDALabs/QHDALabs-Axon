"""
qhda_core.types — kontrakt między warstwą kwantową a relacyjną.

To jest serce architektury hybrydowej. Definiuje JEDEN, neutralny typ danych,
który przepływa z warstwy kwantowej (obwody na QC) do warstwy relacyjnej
(akumulacja h(t) na CPU).

Filozofia:
  warstwa kwantowa  →  produkuje  →  MeasurementOutcome  →  konsumuje  →  warstwa relacyjna

MeasurementOutcome jest CELOWO neutralny — nie zna Qiskit, nie zna PyTorch.
To zwykłe liczby (obserwable wyciągnięte z pomiarów). Dzięki temu:
  - warstwę kwantową można wymienić (Qiskit → Cirq → sprzęt) bez ruszania relacyjnej
  - warstwę relacyjną można użyć BEZ żadnego obwodu (np. wildfire: stres węzłów
    klasyczny, MeasurementOutcome budowany ręcznie z danych satelitarnych)

Ten plik NIE importuje ani qiskit, ani torch. To gwarancja izolacji warstw.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Optional
import numpy as np


@dataclass(frozen=True)
class MeasurementOutcome:
    """
    Neutralny wynik jednego "zdarzenia" (jednego okna / kroku / pomiaru).

    To jest waluta przepływająca między warstwami. Warstwa kwantowa wypełnia
    go obserwablami wyciągniętymi z countów obwodu; warstwa relacyjna czyta
    tylko te pola — nie wie i nie musi wiedzieć, skąd pochodzą.

    Pola:
      observables : słownik nazwanych skalarów — główny ładunek informacyjny.
                    Przykłady z XSIG: {"zz_02": -0.05, "parity": 0.1, "ancilla": 0.6}
                    Przykłady z wildfire: {"ndwi": -0.7, "stress": 0.3}
      vector      : opcjonalny wektor cech tego zdarzenia (np. corr_features
                    w XSIG, albo wektor stanu węzła w wildfire). Używany przez
                    warstwę relacyjną jako sygnał wejściowy do h(t).
      bridge_fired: czy "most" odpalił w tym zdarzeniu (sygnał z warstwy
                    kwantowej, że wykryto strukturę). Steruje siłą sprzężenia
                    w update relacyjnym. None = brak informacji o moście.
      index       : numer zdarzenia w sekwencji (okno w, krok czasowy t...).
      meta        : dowolne metadane (np. zakres ℓ, pozycja na niebie) —
                    relacyjna warstwa ich nie używa, ale bywają przydatne
                    do logowania i debugowania.

    Niezmienność (frozen): outcome reprezentuje fakt, który się wydarzył.
    Nie modyfikujemy go po utworzeniu — jeśli chcesz inny, twórz nowy.
    """
    observables: Mapping[str, float]
    vector: Optional[np.ndarray] = None
    bridge_fired: Optional[bool] = None
    index: int = 0
    meta: Mapping[str, object] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        """Wygodny dostęp do pojedynczej obserwabli z wartością domyślną."""
        return float(self.observables.get(key, default))

    def __post_init__(self):
        # Walidacja lekka — nie chcemy nadmiarowej ceremonii, ale łapiemy
        # typowe błędy wcześnie (np. wektor jako lista zamiast ndarray).
        if self.vector is not None and not isinstance(self.vector, np.ndarray):
            object.__setattr__(self, "vector", np.asarray(self.vector, dtype=float))
