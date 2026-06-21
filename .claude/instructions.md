# Project context — Axon (Science Nervous System)

> Claude (Code/Cowork) reads this as context. Conventions live in
> [CLAUDE.md](CLAUDE.md); this file is the short project identity.

## What the project is

Axon is the codename for the Science Nervous System (SNS): infrastructure for
getting a grip on the scientific literature. Core thesis: the fundamental unit is
the *relation*, not the document — and verification comes before discovery, never
after. Four stages, in order: `perception` → `relational_representation` →
`verification` → `hypothesis`.

## Origin / authorship

QHDALabs | Krzysztof Banasiewicz. Shared mechanisms come from `qhda-core`
(relational layer in pure numpy; optional quantum layer via Qiskit). Axon
**consumes** qhda-core — it does not vendor or reimplement it.

## Working style

- Technical, precise communication. No marketing, no overclaiming.
- A null result is a result, not a failure — report it honestly.
- Distinguish a genuine signal from a method artifact.
- Python, clean modules, tests. English in code/docs; `Manifest.md` stays Polish.
- Environment: Windows, VSCode; project venv at `.venv/` (Python 3.12).

## Verification rules (lesson from XSIG)

See [../VERIFICATION_LOG.md](../VERIFICATION_LOG.md). Hypothesis written BEFORE
the test; explicit null/control; raw data over smooth models; enough resolution
for the p-value.

## Current state

Scaffolding complete: four-stage package under `src/axon/`, consuming qhda-core;
verification-before-discovery enforced by the type system; pure-numpy permutation
null implemented; toy end-to-end example and a mirrored test suite (28 tests).
Most domain logic is honest stubs. Update this section as work proceeds.

## What NOT to do

- Do not write "ran it through QC" as a stamp of truth — the substrate encodes,
  the method verifies.
- Do not fit the test to a desired result.
- Do not vendor or reimplement qhda-core; do not import its quantum layer on the
  relational path.
