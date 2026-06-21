"""
Przykład: qhda_core w projekcie wildfire (klasyczny, BEZ Qiskit).

Pokazuje, że warstwa relacyjna działa identycznie, czy sygnał pochodzi
z obwodu kwantowego (XSIG), czy z danych satelitarnych (wildfire).

Tutaj: 33 węzły lasu (Dolny Śląsk), każdy ma stan stresu (NDWI, suchość).
RelationalState akumuluje "pamięć" propagacji stresu między węzłami w czasie,
dokładnie jak h(t) w XSIG akumulował korelacje — ten sam mechanizm, inne dane.
"""

import numpy as np
from qhda_core import MeasurementOutcome, RelationalState, RelationalConfig, EmergentClock


def simulate_wildfire_season(n_nodes=33, n_weeks=20, seed=0):
    """
    Symuluje sezon: co tydzień odczyt stresu węzłów (proxy NDWI).
    Buduje MeasurementOutcome RĘCZNIE z danych — bez żadnego obwodu kwantowego.
    """
    rng = np.random.default_rng(seed)

    # Stan relacyjny: akumuluje wzorzec stresu przez sezon
    state = RelationalState(RelationalConfig(
        dim=n_nodes,
        coupling_fired=0.7,   # silna pamięć, gdy próg suszy przekroczony
        coupling_base=0.3,
        gain=0.4,
    ))
    clock = EmergentClock()  # tempo = jak szybko zmienia się rozkład stresu

    # Trend sezonowy: rosnąca susza (NDWI spada)
    for week in range(n_weeks):
        seasonal_dryness = -0.3 - 0.4 * (week / n_weeks)
        node_stress = seasonal_dryness + rng.normal(0, 0.15, n_nodes)

        # "Most odpala", gdy średni stres przekracza próg krytyczny
        bridge = bool(node_stress.mean() < -0.5)

        outcome = MeasurementOutcome(
            observables={"mean_ndwi": float(node_stress.mean())},
            vector=node_stress,        # wektor stanu 33 węzłów
            bridge_fired=bridge,
            index=week,
            meta={"week": week, "region": "Dolny Slask"},
        )

        state.update(outcome)
        clock.tick(outcome)

    return state, clock


if __name__ == "__main__":
    print("qhda_core w wildfire — warstwa relacyjna bez Qiskit\n")

    state, clock = simulate_wildfire_season()

    print(f"Tygodni w sezonie:        {state.t}")
    print(f"Norma stanu |h(T)|:       {state.h_norm:.4f}")
    print(f"Wskaznik strukturalnosci: {state.structural_score:.4f}")
    print(f"  (wysoki = stres narasta koherentnie, nie losowo)")
    print()
    print(f"Czas wlasny (proper time): {clock.proper_time:.4f}")
    print(f"Liczba zdarzen:            {clock.n_events}")
    print(f"Dylatacja:                 {clock.time_dilation():.4f}")
    print(f"  (czas wlasny != liczba tygodni — mierzy tempo zmian suszy)")
    print()
    print("Ten sam RelationalState i EmergentClock, ktorych uzywasz w XSIG.")
    print("Zero Qiskit. Zero przepisywania. Import i dziala.")
