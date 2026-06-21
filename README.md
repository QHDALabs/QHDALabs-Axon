# qhda-core

**Autorskie mechanizmy QHDALabs jako biblioteka wielokrotnego użytku.**

*Krzysztof Banasiewicz | QHDALabs*

Cztery mechanizmy wypracowane w qmnet, RTANA i XSIG — wydzielone tak, żeby
importować je w kolejnych projektach zamiast przepisywać od zera.

---

## Architektura: dwie warstwy

```text

WARSTWA KWANTOWA  (leci na QC, wymaga Qiskit)
  conditional_cz_bridge   — most z qmnet
  page_wootters_clock     — zegar Page-Wootters
        │
        │  produkuje
        ▼
  MeasurementOutcome      — neutralny kontrakt (zwykłe liczby, zero zależności)
        │
        │  konsumuje
        ▼
WARSTWA RELACYJNA  (CPU, czysty numpy, zawsze dostępna)
  RelationalState         — akumulator h(t) (z RTANA)
  EmergentClock           — emergentny czas (tempo zmian relacyjnych)
```

**Dlaczego dwie warstwy:** bridges i Page-Wootters to obwody kwantowe — lecą
na QC. Ale `h(t)` to klasyczna pętla czytająca wyniki pomiarów — w RTANA był
PyTorch, w XSIG numpy, nigdy obwodem. Wciśnięcie go do Qiskit zmusiłoby do
przepisywania przy każdym projekcie klasycznym. Rozdzielenie warstw sprawia,
że `RelationalState` działa w wildfire **bez instalowania Qiskit**.

---

## Instalacja

```bash
# Tylko warstwa relacyjna (lekka, projekty klasyczne jak wildfire):
pip install git+ssh://git@github.com/QHDALabs/qhda-core.git

# Z warstwą kwantową (Qiskit, projekty na QC jak XSIG):
pip install "qhda-core[quantum] @ git+ssh://git@github.com/QHDALabs/qhda-core.git"

# Wszystko (Qiskit + PyTorch + testy):
pip install "qhda-core[all] @ git+ssh://git@github.com/QHDALabs/qhda-core.git"
```

Lokalnie (editable, do rozwoju biblioteki):

```bash
git clone git@github.com:QHDALabs/qhda-core.git
cd qhda-core
pip install -e ".[all]"
```

---

## Użycie

### Warstwa relacyjna (bez Qiskit) — np. wildfire

```python
from qhda_core import MeasurementOutcome, RelationalState, RelationalConfig

state = RelationalState(RelationalConfig(dim=33, signal_key="stress"))

for week, node_stress in enumerate(weekly_readings):
    outcome = MeasurementOutcome(
        observables={"stress": node_stress.mean()},
        vector=node_stress,                       # stan 33 węzłów
        bridge_fired=(node_stress.mean() < -0.5), # próg suszy
        index=week,
    )
    state.update(outcome)

print(state.structural_score)   # czy stres narasta koherentnie?
```

### Warstwa kwantowa (Qiskit) — np. XSIG

```python
from qiskit import QuantumCircuit
from qhda_core import page_wootters_clock, conditional_cz_bridge

qc = QuantumCircuit(8)
page_wootters_clock(qc, clock_qubits=[0,1,2], system_qubits=[3,4,5],
                    coupling=0.85, clock_phase=delta_corr)
conditional_cz_bridge(qc, ancilla=6, control=3, target=7,
                      drive_angle=bridge_angle)
```

### Emergentny czas

```python
from qhda_core import EmergentClock

clock = EmergentClock()
for outcome in stream:
    clock.tick(outcome)

clock.proper_time      # czas własny ≠ liczba zdarzeń
clock.time_dilation()  # tempo zmian relacyjnych
```

---

## Mechanizmy — pochodzenie

| Mechanizm | Pochodzenie | Warstwa |
|---|---|---|
| `conditional_cz_bridge` | qmnet (measurement-fueled bridges) | kwantowa |
| `page_wootters_clock` | qmnet / RQTE (Page-Wootters formalism) | kwantowa |
| `RelationalState` (h(t)) | RTANA (relational temporal awareness) | relacyjna |
| `EmergentClock` | RQTE / XSIG (emergent relational time) | relacyjna |
| `MeasurementOutcome` | kontrakt — nowy, spina warstwy | neutralna |

---

## Filozofia kontraktu

`MeasurementOutcome` jest celowo neutralny — nie zna Qiskit, nie zna PyTorch.
To zwykłe liczby (obserwable z pomiarów). Dzięki temu warstwę kwantową można
wymienić (Qiskit → Cirq → sprzęt) bez ruszania relacyjnej, a warstwa relacyjna
działa nawet bez żadnego obwodu — sygnał budujesz ręcznie z danych.

To jest ta sama struktura, co w każdym hybrydowym algorytmie kwantowym
(VQE, QAOA): kwantowy rdzeń + klasyczna pętla nad nim. Fizyczny QC tego nie
zmienia — obwód leci na sprzęt, wyniki wracają do Pythona, `h(t)` mieli je
klasycznie.

---

## Testy

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Licencja

krzyshtof.com RCSAL v2.0
