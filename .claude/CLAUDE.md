# Axon — conventions for Claude

Axon is the Science Nervous System (SNS): a relation-first, verification-before-
discovery layer over the scientific literature. Read [Manifest.md](../Manifest.md)
(Polish, the conceptual contract — never edit or translate it) and
[VERIFICATION_LOG.md](../VERIFICATION_LOG.md) (the methodological contract).

## Architecture — the order is the thesis

Four stages under `src/axon/`, in this exact order. Reversing the order is a bug.

1. `perception` — ingest scientific text into a normalized `Document`.
2. `relational_representation` — build the relation map on qhda-core's relational
   layer. A relation store, not a fact store.
3. `verification` — criticise every candidate against an explicit null before it
   is surfaced. False-positive rejection is the core function.
4. `hypothesis` — discoveries are the OUTPUT of verification. The stage accepts
   only `VerificationResult`; there is no path from a raw candidate to a
   hypothesis. A hypothesis module that runs before verification is a bug.

Data contracts live in `axon/types.py` (`Document`, `CandidateRelation`,
`Verdict`, `VerificationResult`, `Hypothesis`) — frozen, numpy-only.

## Dependency boundary

- Axon **consumes** `qhda-core`; it does not vendor or reimplement it. Never copy
  qhda-core source into this repo. Import the relational layer from `qhda_core`.
- The relational path must work with **Qiskit not installed**. Do not import the
  quantum layer (`qhda_core.quantum`) outside code that is explicitly the optional
  quantum extra.
- Dependency name: distribution `qhda-core`, import `qhda_core`. This package:
  distribution `qhdalabs-axon`, import `axon`.

## Environment

- Project venv: `.venv/` in this repo (Python 3.12). Use `./.venv/Scripts/python.exe`
  — not the global Python.
- qhda-core is installed editable from the sibling checkout `../qhda-core`.
  Install qhda-core **before** Axon so it resolves locally, not from PyPI:
  `pip install -e ../qhda-core` then `pip install -e .`.

## Non-negotiable conventions

- **Verification precedes discovery**, structurally and in code flow.
- **Honest null results are first-class.** `NULL`/`REJECTED` are reported and
  counted, never silently dropped. No overclaiming, no hype language anywhere.
- **No fabricated metrics or invented numbers.** Synthetic-data outputs are
  labeled as illustrative, not as scientific claims.
- **Stubs are honestly stubs:** clear docstring (intent + inputs/outputs) and
  `raise NotImplementedError`. A minimal reference implementation is allowed only
  if it genuinely does what it says and is labeled "minimal reference". Never
  write placeholder logic that pretends to work.
- **No relation kind ships without an explicit null** and the ability to reject.
- Every Markdown code fence carries a language tag (```python, ```text, ...) —
  never a bare fence.
- English everywhere in code, docstrings, README, this file, VERIFICATION_LOG.
  `Manifest.md` stays Polish and untouched.
- Small, reviewable changes. When unsure, ask rather than guess.

## Verify-first workflow

Before fleshing out code, confirm the environment composes:

```bash
./.venv/Scripts/python.exe -c "import axon, qhda_core"
./.venv/Scripts/python.exe -m pytest -q
```

Do not write stubs against an environment that does not compose.
