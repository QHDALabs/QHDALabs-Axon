"""
qhda_core.emergent — warstwa emergentnego czasu.

To jest warstwa KONCEPTUALNA, nie pojedynczy mechanizm. Spina warstwę kwantową
(z której płyną MeasurementOutcome) i relacyjną (h(t)) w jedną narrację:

    "Czas nie jest tłem. Wyłania się z sekwencji zdarzeń relacyjnych."

W różnych projektach miało to różną postać:
  - RQTE:  czas z formalizmu Page-Wootters (zegar kwantowy)
  - XSIG:  tempo ∝ |Δcorr| (jak szybko zmienia się struktura korelacyjna)
  - tu:    uogólnienie — "tempo relacyjne" jako funkcja zmian między zdarzeniami

EmergentClock konsumuje strumień MeasurementOutcome i produkuje:
  - tempo(t)     : jak szybko zmienia się stan między zdarzeniami
  - proper_time  : "czas własny" = skumulowane tempo (nie indeks zdarzenia!)

Kluczowa idea: dwa przebiegi o tej samej liczbie zdarzeń mogą mieć różny
czas własny, jeśli w jednym struktura zmienia się szybko, a w drugim wolno.
To jest emergentny czas — mierzony zmianą, nie liczeniem kroków.

Backend-agnostyczny (numpy). Bez Qiskit.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Callable
import numpy as np

from ..types import MeasurementOutcome


# Funkcja tempa: (poprzedni wektor, bieżący wektor) → skalar tempa
TempoFn = Callable[[Optional[np.ndarray], np.ndarray], float]


def delta_norm_tempo(prev: Optional[np.ndarray], cur: np.ndarray) -> float:
    """
    Domyślne tempo (wzorzec XSIG): |Δ| = ||cur − prev||.
    Pierwsze zdarzenie (prev=None) → tempo = ||cur|| (start od zera).
    """
    if prev is None:
        return float(np.linalg.norm(cur))
    return float(np.linalg.norm(cur - prev))


def cosine_tempo(prev: Optional[np.ndarray], cur: np.ndarray) -> float:
    """
    Alternatywne tempo: 1 − cos_similarity. Mierzy zmianę KIERUNKU struktury,
    nie magnitudy. Użyteczne, gdy interesuje Cię reorientacja, nie wzrost.
    """
    if prev is None:
        return 0.0
    a, b = np.linalg.norm(prev), np.linalg.norm(cur)
    if a < 1e-12 or b < 1e-12:
        return 0.0
    cos_sim = float(np.dot(prev, cur) / (a * b))
    return 1.0 - cos_sim


@dataclass
class EmergentClock:
    """
    Zegar emergentny — mierzy czas własny z sekwencji zdarzeń.

    Użycie:
        clock = EmergentClock()
        for outcome in stream:
            clock.tick(outcome)
        print(clock.proper_time)        # czas własny ≠ liczba zdarzeń
        print(clock.tempo_series)       # tempo w każdym kroku

    proper_time rośnie szybko, gdy struktura zmienia się gwałtownie,
    a wolno, gdy jest stabilna. To jest sedno emergentnego czasu:
    czas mierzony zmianą relacji, nie tykaniem zewnętrznego zegara.
    """
    tempo_fn: TempoFn = delta_norm_tempo

    _prev_vector: Optional[np.ndarray] = field(default=None, init=False)
    tempo_series: List[float] = field(default_factory=list, init=False)
    _n: int = field(default=0, init=False)

    def tick(self, outcome: MeasurementOutcome) -> float:
        """
        Rejestruje jedno zdarzenie, zwraca tempo tego kroku.
        Wymaga outcome.vector (sygnał, którego zmianę mierzymy).
        """
        if outcome.vector is None:
            raise ValueError(
                "EmergentClock.tick wymaga outcome.vector — to wektor, którego "
                "zmianę między zdarzeniami interpretujemy jako upływ czasu."
            )
        cur = np.asarray(outcome.vector, dtype=float)
        tempo = self.tempo_fn(self._prev_vector, cur)
        self.tempo_series.append(tempo)
        self._prev_vector = cur.copy()
        self._n += 1
        return tempo

    @property
    def proper_time(self) -> float:
        """Czas własny = suma temp (skumulowana zmiana strukturalna)."""
        return float(np.sum(self.tempo_series))

    @property
    def mean_tempo(self) -> float:
        return float(np.mean(self.tempo_series)) if self.tempo_series else 0.0

    @property
    def n_events(self) -> int:
        return self._n

    def time_dilation(self) -> float:
        """
        "Dylatacja" względem zegara zdarzeniowego: proper_time / n_events.
        > mean_tempo gdy zmiany przyspieszają, < gdy zwalniają.
        Wartość 1.0-znormalizowana nie ma sensu — to miara względna między
        przebiegami, nie absolutna.
        """
        if self._n == 0:
            return 0.0
        return self.proper_time / self._n

    def reset(self) -> None:
        self._prev_vector = None
        self.tempo_series.clear()
        self._n = 0
