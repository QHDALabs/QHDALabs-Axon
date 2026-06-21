"""
qhda_core.relational — warstwa relacyjna: akumulacja stanu h(t).

To jest uogólnienie mechanizmu z RTANA / RTANAv4 (XSIG), oczyszczone z konkretów
konkretnego projektu. Działa na czystym numpy — ZERO zależności od Qiskit.

Mechanizm (ten sam, co w rtana_v1.py i RTANAv4):
    h(t+1) = activation( J · h(t) + gain · signal(t) )

gdzie:
  - h(t)        : wewnętrzny "zegar relacyjny" / stan akumulujący historię
  - J           : siła sprzężenia (większa, gdy most odpalił → silniejsza pamięć)
  - signal(t)   : sygnał z bieżącego zdarzenia (z MeasurementOutcome)
  - activation  : funkcja nieliniowa (domyślnie tanh, ograniczająca stan)

Kluczowa właściwość (z XSIG):
  - dla szumu białego: h(t) błądzi losowo → |h(T)| ~ √T
  - dla struktury koherentnej: h(t) rośnie szybciej → |h(T)| > √T · σ
  → wskaźnik strukturalności S = |h(T)| · √T / std jest miarą "ile pamięci".

Backend: domyślnie numpy. Jeśli ktoś poda tensory torch, mechanizm zadziała
identycznie (operacje są elementarne: mnożenie, dodawanie, tanh), o ile backend
udostępnia te operacje. Świadomie NIE importujemy torch tutaj — to zachowuje
rdzeń lekki. Wsparcie torch jest opt-in przez podanie własnego `activation`/ops.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional, List
import numpy as np

from ..types import MeasurementOutcome


# Typ funkcji aktywacji: wektor → wektor
Activation = Callable[[np.ndarray], np.ndarray]


def tanh_activation(x: np.ndarray) -> np.ndarray:
    """Domyślna aktywacja — tanh ogranicza stan do [-1, 1]^dim."""
    return np.tanh(x)


@dataclass
class RelationalConfig:
    """
    Konfiguracja dynamiki relacyjnej. Wartości domyślne odpowiadają
    kalibracji sprawdzonej w XSIG (RTANAv4).
    """
    dim: int = 8                      # wymiar stanu h
    coupling_base: float = 0.20       # J gdy most NIE odpalił
    coupling_fired: float = 0.60      # J gdy most odpalił (silniejsza pamięć)
    gain: float = 0.40                # waga sygnału wejściowego
    noise_sigma: float = 0.30         # oczekiwany rozrzut h dla szumu białego
                                      # (do normalizacji wskaźnika strukturalności)
    signal_key: Optional[str] = None  # która obserwabla steruje sygnałem;
                                      # None → użyj outcome.vector bezpośrednio


@dataclass
class RelationalState:
    """
    Stan relacyjny h(t) — akumulator historii zdarzeń.

    Użycie (identyczny wzorzec niezależnie od projektu):
        state = RelationalState(RelationalConfig(dim=8))
        for outcome in stream_of_outcomes:
            state.update(outcome)
        print(state.structural_score)

    Projekt kwantowy (XSIG): outcome pochodzi z obwodu Qiskit.
    Projekt klasyczny (wildfire): outcome budowany ręcznie z danych.
    RelationalState nie widzi różnicy — to jest sens hybrydy.
    """
    config: RelationalConfig = field(default_factory=RelationalConfig)
    activation: Activation = tanh_activation

    # Stan wewnętrzny
    h: np.ndarray = field(init=False)
    t: int = field(default=0, init=False)
    history: List[dict] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.h = np.zeros(self.config.dim, dtype=float)

    # ────────────────────────────────────────────────────────────────────
    def _extract_signal(self, outcome: MeasurementOutcome) -> np.ndarray:
        """
        Buduje wektor sygnału z outcome.

        Dwie ścieżki:
          1. config.signal_key ustawiony → sygnał = obserwabla × vector
             (wzorzec XSIG: zz_02 × corr_features — magnituda korelacji)
          2. signal_key = None → sygnał = sam vector
             (wzorzec klasyczny: bezpośredni wektor cech)
        """
        cfg = self.config
        if outcome.vector is not None:
            vec = np.zeros(cfg.dim)
            n = min(len(outcome.vector), cfg.dim)
            vec[:n] = outcome.vector[:n]
        else:
            vec = np.zeros(cfg.dim)

        if cfg.signal_key is not None:
            scalar = outcome.get(cfg.signal_key, 0.0)
            return scalar * vec
        return vec

    # ────────────────────────────────────────────────────────────────────
    def update(self, outcome: MeasurementOutcome) -> None:
        """
        Jeden krok akumulacji: h(t) → h(t+1).

        Siła sprzężenia J zależy od tego, czy most odpalił:
          - bridge_fired=True  → J = coupling_fired (silna pamięć)
          - bridge_fired=False → J = coupling_base
          - bridge_fired=None  → J = coupling_base (brak info = ostrożnie)
        """
        cfg = self.config
        self.t += 1

        fired = bool(outcome.bridge_fired) if outcome.bridge_fired is not None else False
        J = cfg.coupling_fired if fired else cfg.coupling_base

        signal = self._extract_signal(outcome)
        self.h = self.activation(J * self.h + cfg.gain * signal)

        self.history.append({
            "t": self.t,
            "h_norm": float(np.linalg.norm(self.h)),
            "bridge_fired": fired,
        })

    # ────────────────────────────────────────────────────────────────────
    @property
    def h_norm(self) -> float:
        return float(np.linalg.norm(self.h))

    @property
    def structural_score(self) -> float:
        """
        Wskaźnik strukturalności (uogólniony S_struct z XSIG).

        S = |h(T)| · √T / (std historii |h|)

        Interpretacja:
          - dla szumu: |h| błądzi wokół noise_sigma·√T → S umiarkowane
          - dla struktury: |h| rośnie ponad √T → S wysokie

        Gdy historia jest za krótka (<3 kroki), zwraca 0.0 (za mało danych).
        """
        if self.t < 3 or len(self.history) < 3:
            return 0.0
        norms = np.array([e["h_norm"] for e in self.history])
        std = float(norms.std()) + 1e-8
        return float(self.h_norm * np.sqrt(self.t) / std)

    def reset(self) -> None:
        """Zeruje stan — przydatne między niezależnymi przebiegami."""
        self.h = np.zeros(self.config.dim, dtype=float)
        self.t = 0
        self.history.clear()
