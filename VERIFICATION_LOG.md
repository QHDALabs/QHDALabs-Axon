# Verification Log — Axon

> Not a changelog. A log of concept verification — the process "before a concept
> becomes a theory". Pattern established in XSIG.

## Methodological contract

Axon's reason to exist is rejecting false connections, not generating them
(Manifest, IV). This log is where that discipline lives. Three commitments:

- **Verification before discovery.** A connection is criticised against an
  explicit null *before* it is surfaced as a hypothesis. Structurally, the
  hypothesis stage accepts only verified results — there is no path from a raw
  candidate to a discovery.
- **Null results are first-class data.** A rigorously established "no effect" is
  a publishable, valuable outcome, not a failure. `NULL` and `REJECTED` verdicts
  are reported and counted, never silently dropped.
- **Honest scope claims.** No overclaiming, no hype, no fabricated metrics.
  Stubs are honestly stubs. Reference implementations are labeled as minimal.
  "We ran it through a quantum processor" is not proof of anything — the method
  (control, null, statistics) verifies, not the substrate.

## How to use

For each hypothesis/observable, ONE entry, in this order (do not reorder —
writing the hypothesis BEFORE the test guards against fitting the test to the
result):

```text
### [date] Hypothesis: <name>

**Question:** what exactly is being tested (one sentence)
**Hypothesis:** what I expect and why
**Null / control:** what "no effect" looks like (bootstrap? permutation? constant?)
**Metric:** what is measured, what significance threshold
**Artifact risk:** what could produce a false signal (smooth model? too few points?)

--- boundary: everything below is written AFTER running ---

**Result:** numbers
**Interpretation:** physical signal / artifact / null — and why
**Decision:** next step
```

## Hard rules (from XSIG)

1. **Hypothesis before test.** Writing the hypothesis after seeing the result is
   not verification.
2. **Explicit null.** "No effect" must have a concrete, numerical form.
3. **Raw over smooth.** A parametric model can manufacture a false signal from
   its own smoothness (lesson: King raw vs dipole α — z=1.29 → z=−0.66 after
   switching to raw data).
4. **Resolution.** Too few permutations = coarse p-value = false conclusions
   (lesson: 30 permutations gave z=+1.17, 500 gave z=−0.66 — the sign flipped).
5. **Null is a result.** A negative result obtained by a rigorous method is
   publishable.
6. **The substrate encodes, it does not certify.** "I ran it through a quantum
   processor" is not proof. The method verifies (control, null, statistics), not
   the quantum-ness of the computation.

---

## Entries

### [2026-06-21] Session: initial scaffolding (engineering, no scientific claim)

This is an engineering entry, not a hypothesis test — recorded here for the audit
trail. No scientific hypothesis was tested and no metrics are claimed.

**Scope:** stand up the four-stage package (`perception`,
`relational_representation`, `verification`, `hypothesis`) as a consumer of
qhda-core; wire the verification-before-discovery thesis into the type system.

**What is real vs stub:**
- Real, working: the methodological backbone — `verification/null_models.py`
  (pure-numpy permutation test and bootstrap CI) and `PermutationVerifier`, which
  genuinely criticises proximity candidates against an explicit permutation null
  and can return `NULL`/`REJECTED`. The structural guarantee in `hypothesis`
  (accepts only `VerificationResult`).
- Minimal labeled reference: `perception.normalize_text` / `ingest_text`,
  `RelationStore.observe` / `candidate_relations` (cosine proximity heuristic).
- Honest stub (`NotImplementedError`): `ingest_corpus` (format parsing),
  text→vector featurization, ABC/Swanson bridge construction, the abstract
  `Verifier.verify`.

**Verification (engineering):** end-to-end toy pipeline runs on pure numpy
without Qiskit; an aligned document pair is `ACCEPTED` (p≈0.001 against the
permutation null) while a chance pair returns `NULL` (p≈0.37). 28 tests pass,
including the core verification tests asserting the verifier does not accept
chance pairs. These are illustrative pipeline outputs on synthetic data, **not**
a scientific claim about any literature.

**Decision:** next, replace the proximity reference with real relation extraction
and define explicit null models per relation kind. No relation kind ships without
a stated null and the ability to reject.

---

### [YYYY-MM-DD] Hypothesis: <first scientific hypothesis>

**Question:**
**Hypothesis:**
**Null / control:**
**Metric:**
**Artifact risk:**

<!-- write the result after running -->
