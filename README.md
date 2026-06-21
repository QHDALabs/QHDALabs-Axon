# Axon — the Science Nervous System (SNS)

Infrastructure for getting a grip on the scientific literature, which grows by
millions of texts per year.

Axon is built on two theses:

1. **The fundamental unit is the relation, not the document.** Value is not in
   unread papers; it is in the unmet connections between papers that already
   exist — often across fields that do not talk to each other.
2. **Verification comes before discovery, never after.** Generating connections
   is cheap and most candidates are false. The hard, central work is rejecting
   the false ones. A system that cannot say "this link is spurious" is a noise
   generator, not science.

The conceptual contract is in [Manifest.md](Manifest.md) (Polish). The
methodological contract — verification before discovery, null results as
first-class data, honest scope claims — is in
[VERIFICATION_LOG.md](VERIFICATION_LOG.md).

> Status: scaffolding. The pipeline composes end to end on toy data; most stages
> are honest stubs (clear docstrings + `NotImplementedError`) with a few
> clearly-labeled minimal reference implementations. There are no benchmark
> claims and no fabricated metrics.

## Architecture — the order is the thesis

Axon is a four-stage pipeline. The order is not incidental; reversing it
(discover first, verify maybe later) produces exactly the inflation of false
findings the project exists to prevent.

```text
1. perception                 ingest scientific text -> normalized Document
2. relational_representation  build the map of relations (a relation store,
                              not a fact store) on qhda-core's relational layer
3. verification               criticise every candidate against an explicit
                              null; reject false positives before anything is
                              surfaced. THIS is the core.
4. hypothesis                 discoveries = the OUTPUT of verification; built
                              only from accepted results, never from raw
                              candidates
```

The thesis is enforced structurally: the hypothesis stage accepts only
`VerificationResult` objects (the output of verification) and raises on anything
else. There is no code path from a raw candidate to a hypothesis.

### Relational and quantum layers

Axon consumes [`qhda-core`](https://github.com/QHDALabs/qhda-core); it does not
vendor or reimplement it. qhda-core has two layers:

- a **relational layer** (pure numpy, always available) — used here for the
  relation store and its coherence-vs-noise signal;
- an optional **quantum layer** (Qiskit, an extra) — wired in only where it
  earns its place.

The relational path of Axon stays fully functional with Qiskit **not** installed,
mirroring qhda-core's dependency boundary.

## Install

Axon depends on qhda-core. Install the dependency first so it resolves to your
local checkout rather than PyPI, then install Axon:

```bash
# relational layer only (pure numpy):
pip install -e ../qhda-core
pip install -e .

# with the optional quantum layer (Qiskit):
pip install -e "../qhda-core[quantum]"
pip install -e ".[quantum]"
```

Development extras (pytest, coverage):

```bash
pip install -e ".[dev]"
```

## Quickstart

```python
import numpy as np
from axon import Document, RelationStore, PermutationVerifier, verify_all, surface_hypotheses

# 1) perception: normalized documents (toy vectors supplied; text->vector is
#    not implemented in the scaffold).
docs = [
    Document("a1", "iron and cognition", vector=np.array([1.0, 1.0, 0.0, 0.0])),
    Document("a2", "dietary iron and memory", vector=np.array([1.0, 0.9, 0.0, 0.0])),
    Document("r1", "coastal mollusks", vector=np.array([0.0, 0.0, 1.0, -1.0])),
]

# 2) relational representation: propose candidate relations (cheap, possibly false)
store = RelationStore(dim=4)
for d in docs:
    store.observe(d)
candidates = store.candidate_relations(threshold=0.5)

# 3) verification: criticise each candidate against an explicit permutation null
results = verify_all(candidates, PermutationVerifier(seed=0), store)

# 4) hypothesis: surface only what survived verification
report = surface_hypotheses(results)
print(report.counts)        # full verdict breakdown — nulls stay visible
print(report.hypotheses)    # accepted only
```

A complete runnable version is in [examples/axon_pipeline.py](examples/axon_pipeline.py):

```bash
python examples/axon_pipeline.py
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The test tree mirrors the package. The verification tests are the core: they
assert the verifier can return `NULL`/`REJECTED` for chance pairs and accepts
only genuine structure.

## What this is not

Axon does not produce truth, replace the scientist, or act as an oracle of
discovery (Manifest, III). It builds the conditions in which an answer can be
found — and trusted.

---

*QHDALabs | Krzysztof Banasiewicz*
