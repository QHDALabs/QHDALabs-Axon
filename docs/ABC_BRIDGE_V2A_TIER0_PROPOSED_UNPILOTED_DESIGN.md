# ABC_BRIDGE V2-A — Tier 0 Proposed / Unpiloted Grid Design

**Status:** PROPOSED / UNPILOTED / NOT FROZEN
**Date:** 2026-06-27

Reference design for a larger confirmatory grid (docs=60, families 40/12/60/20,
PeerSet {19,24,30}+{5,12,18}, R=200). NO pilot run (reconstruction NOR real V1)
has exercised this grid. This file is NOT the operational pre-registration.
The commit SHA of this file MUST NOT be used to derive confirmatory seeds.
Canonical design doc: docs/ABC_BRIDGE_V2A_TIER0_DRAFT.md

---

## 0. Purpose and scope of this document

This document covers **Tier 0 only**: whether the V2-A selectivity mechanism
satisfies its own contract on emergent synthetic data where ground truth is known
because we generated it. Tier 0 tests **contract compliance**, not biomedical validity.

This document does **not** cover:
- **Tier 1** (external validity: real, time-separated, blind-labelled cases). That is a
  separate card with its own pre-registration, written only if Tier 0 passes.
- **Production use.** On Tier 0 pass, V2-A is `EXPERIMENTAL_TIER0_ONLY`: it runs in
  shadow/audit mode, annotates, and never changes a real verdict or degrades a
  production candidate.

**Commitment.** Whatever Tier 0 returns is logged as-is. The STOP rule (§7) is binding.
No tuning of the mechanism, thresholds, generator grid, or expectations after seeing the
result. A Tier 0 failure is a RESULT ("the mechanism does not meet its contract"), logged
as such, not a problem to be engineered away in place.

**Relationship to V1.** V2-A is a NEW module. It does not modify `bridge.py`; its blob
must remain `1969f43d8fb172f40bc4c878d519f406ac7499f2` (the held-out integrity depends on
it). V2-A obtains each substitution's mediated score by calling the frozen V1 bridge
computation **fresh per pair** (which re-selects B per pair); it never reuses the original
pair's B and never edits V1.

---

## 1. Construct contract (load-bearing)

> **V2-A does not identify mediation or true bridges.** It estimates **sibling-confounding
> risk relative to a prespecified MeSH structure** by testing whether an A–C candidate is
> insufficiently distinguishable from candidates produced through endpoint substitution.
> A positive result only **removes** confidence and can **never** support acceptance.

> **Every V2-A verdict is relative to the declared MeSH release.** When MeSH 2026 is
> applied to a historical corpus, the result is **modern-ontology-assisted** and does not
> represent sibling structure knowable at the corpus cutoff, nor does it reproduce a
> historically available discovery procedure.

`modern-ontology-assisted` is a **scope limitation of the claim**, not a tag. Metadata
fields (§5) enable its audit but do not replace it.

### The four identifiability limits (frozen as scope constraints)

- **L1 — Co-occurrence non-identifiability.** On the term-profile substrate, a domain
  marker and a mechanism are observationally indistinguishable. V2-A therefore reports
  *risk of non-selectivity*, never *mediation*. A `RISK` result means
  `PAIR_SELECTIVITY_NOT_DEMONSTRATED`, not "sibling/confounder detected".
- **L2 — Ontology-relative construct drift.** Verdicts are relative to the declared MeSH
  release. Applying a later ontology to an earlier corpus injects post-cutoff ontological
  knowledge (`temporal ontology leakage`). MeSH version is part of the construct
  definition, not a technical dependency.
- **L3 — Broad-mechanism non-identifiability.** A domain marker and a genuine mechanism
  shared across branch peers are indistinguishable here. V2-A degrades **both** as
  non-selective. It validates only **pair-selective** bridge candidates. Degrading a
  genuine broad-mechanism bridge is an **intended** false negative under the cost
  asymmetry: Axon prefers withholding a broad bridge to falsely naming a sibling a
  discovery.
- **L4 — Exchangeability assumption.** The 0.05 error interpretation of the rank test
  holds only if branch-peer mediated values are exchangeable with the original under the
  null. MeSH sibling-hood is an *ontological*, not a *statistical*, guarantee of
  exchangeability; peers may differ in literature size, MeSH density, or era in ways that
  shift mediated independently of bridging. V2-A does not test or correct for peer
  non-exchangeability; it reports an audit (§2.6) and declares the bound nominal.

---

## 2. Method specification (FROZEN)

### 2.1 Gate direction

V2-A is a **one-sided, trust-removing gate**. It can only withhold confidence; it never
adds confidence and never marks anything a bridge. It is symmetric in A and C (no
semantic assumption that one endpoint is a disease and the other a substance).

### 2.2 Peer selection (Decision 1) — deterministic

For each endpoint, peers are **one-parent-up branch peers** from a frozen MeSH snapshot:

```text
for each tree position of the endpoint descriptor:
    1. go exactly one parent up
    2. take all descriptors under that parent
    3. exclude the endpoint itself and its entire descendant subtree
    4. union across all tree positions of the endpoint (full polyhierarchy)
    5. deduplicate by stable DescriptorUI (not by name, not by tree number)
```

- **Radius = exactly one parent up.** This is an **arbitrary, prespecified protocol
  parameter**, selected as the narrowest radius covering the known OP2 case. It is frozen
  for this card; changing the radius is a new card.
- **Polyhierarchy: union of all positions.** Never pick a single convenient path.
- **Identity key: DescriptorUI** (tree numbers are unstable across releases).
- **No eligible branch peers → `UNASSESSABLE: COVERAGE_*`.** Absence of peers does not
  mean "no sibling risk"; it means risk is not assessable against this ontology and
  corpus. Fail closed; never substitute a different endpoint, never relax the rule.

Frozen ontology provenance:

```text
ontology:           MeSH
release:            2026
source artifact:    descriptor XML
artifact SHA-256:   <computed at fetch; recorded here on commit>
identity key:       DescriptorUI
neighborhood radius: ONE_PARENT_UP
paths:              union of all tree positions
```

### 2.3 Substitution contrast (Decision 2) — both sides, independent

```text
Side A:  D_A = { mediated(a_peer, C)  for a_peer in PeerSet_A }
Side C:  D_C = { mediated(A, c_peer)  for c_peer in PeerSet_C }
```

- Each substitution is a **full new pair**: new profile, **B re-selected from scratch for
  that pair**, new mediated, new provenance. It **never** inherits B from (A, C).
- `D_A` and `D_C` are **never merged** (different ontology branches, possibly different
  cardinality and natural scale).

### 2.4 Selectivity statistic (Decision 3) — exact rank test

```text
m0   = mediated(A, C)
D    = the substitution distribution for the side (D_A or D_C)
n    = |D|
k    = count of d in D with d >= m0     # ties count AGAINST selectivity
p_rank_nominal = (k + 1) / (n + 1)       # exact, one-sided, no tie randomisation
```

Per-side verdict:

```text
p_rank_nominal <= alpha_rank_nominal   -> NOT_DETECTED   (selectivity demonstrated, this side)
p_rank_nominal >  alpha_rank_nominal   -> RISK           (PAIR_SELECTIVITY_NOT_DEMONSTRATED, this side)
```

- **The single free parameter is `alpha_rank_nominal = 0.05`.** Everything else is derived.
- **Minimum cardinality is derived, not a separate threshold:**

```text
p_min = 1 / (n + 1)
n_min = ceil(1 / alpha) - 1 = 19    (for alpha = 0.05)
n < n_min  ->  UNASSESSABLE: INSUFFICIENT_RANK_RESOLUTION
```

  Below `n_min`, even an original strictly greater than all peers cannot reach
  `p <= alpha`; the side is unassessable, not "selective".
- **Required rank is derived** from `(k+1)/(n+1) <= alpha`; we do not configure a required
  rank `r`.
- **No normalization of mediated.** No marginal-mass denominator. There is no neutral
  denominator: each candidate (`/mass(X)`, `/min`, `/sqrt`, `/union`) changes the estimand
  and the peer ranking — it would be a different method requiring its own pre-registration.
  Non-exchangeability stays declared (L4), not papered over.

### 2.5 Aggregation (Decision 2A) — IUT for pass, OR for risk, fail-closed

`NO_DEGRADATION` requires selectivity demonstrated on **both** sides
(intersection–union test); anything else withholds confidence:

```text
side A          side C          aggregate
NOT_DETECTED    NOT_DETECTED    NO_DEGRADATION
RISK            any             DEGRADE: SIBLING_RISK_A
any             RISK            DEGRADE: SIBLING_RISK_C
UNASSESSABLE    NOT_DETECTED    DEGRADE: COVERAGE_A          (incl. RESOLUTION_A)
NOT_DETECTED    UNASSESSABLE    DEGRADE: COVERAGE_C          (incl. RESOLUTION_C)
UNASSESSABLE    UNASSESSABLE    DEGRADE: COVERAGE_BOTH
```

- `alpha` is **not** split between sides: each side is tested at full `alpha`; the IUT
  controls the size of the composite `NO_DEGRADATION` claim because it requires both.
- `NO_DEGRADATION` does **not** add trust or confirm a bridge. It states only that this
  test, under L4, did not compel degradation. All other nulls, FDR, and method limits
  still apply.
- A pair that looks selective on one side and non-selective on the other is **not** a
  contradiction; it is "specific on side X, indistinguishable from neighbourhood on side
  Y", and the contract requires degradation (OR).

### 2.6 Exchangeability audit (reported, never gating)

For the endpoint and each peer, record but do **not** feed into the verdict:

```text
- document count
- total profile mass
- mean MeSH descriptors per document
- publication year range / median
```

If the audit shows imbalance, the result is recorded together with L4. We do **not**
normalize after seeing the data.

### 2.7 Result provenance (emitted with every verdict)

```text
ontology: MeSH         release: 2026         artifact_sha256: ...
corpus_cutoff: <e.g. 1987-12-31>             temporal_alignment: POSTDATED_ONTOLOGY
radius: ONE_PARENT_UP
side_A: { n, p_rank_nominal, verdict }
side_C: { n, p_rank_nominal, verdict }
aggregate: { verdict, reason }
exchangeability_audit: { ... §2.6 ... }
```

Statistic names carry the conditionality: `p_rank_nominal`, `alpha_rank_nominal`. We do
**not** write "error rate is controlled at 0.05"; we write "under the branch-peer
exchangeability assumption (L4), the nominal false-release probability is bounded by 0.05".

---

## 3. Tier 0 generator (FROZEN)

### 3.1 What Tier 0 tests, and what it cannot

Tier 0 tests whether the FROZEN mechanism (§2) behaves per contract when profiles arise
**emergently** from a latent generative process — not when we hand-write profile vectors.
It is **not** evidence of biomedical realism. External validity is Tier 1 only.

### 3.2 Latent generative model

The vocabulary is partitioned into latent term families:

```text
P    : latent-parent / domain terms (shared within a domain)
M    : mechanism terms (the genuine cross-literature path, when present)
U_X  : private terms of literature X
G    : generic terms (should be removed by max_df / stoplist)
N    : noise terms
```

A literature is a latent mixture over these families. The generator emits **documents**,
**per-document MeSH-descriptor counts**, and **assignments** — it does NOT write mediated
or profile values directly. Axon's **real** profile builder then computes `mean_TF * idf`,
real B-selection runs, real mediated is computed, the real rank gate runs. The generator
controls structure; it never controls the statistic's output.

### 3.3 The single primary axis: mechanism_width

The **selective** and **broad** bridge are ONE generator differing only by:

```text
mechanism_width = number of branch-peers (in the given PeerSet) that inherit the M component
```

Held identical across the sweep: the same A and C, the same M strength, the same private
masses, the same latent parent, the same document model, the same noise level.

```text
width = 0            -> mechanism present only for the original pair  -> expect NOT_DETECTED
width increasing     -> M spreads onto more peers                     -> RISK frequency rises
width ~ full PeerSet -> broad mechanism                               -> expect RISK
```

The contract does **not** fix a width at which the verdict must flip. With emergent
sampling, a peer inheriting M may by chance score just below or above the original. We
therefore freeze the **shape of the expectation**, not a break point (§4).

### 3.4 PeerSet boundary

The generator receives an **explicit synthetic `PeerSet`** (stable synthetic IDs, frozen
cardinality, explicit latent membership). The generator does **NOT** build a synthetic
MeSH tree. Peer *selection* (the deterministic one-parent-up rule, §2.2) is tested
separately on frozen fragments of the **real** MeSH (§5, Layer 1). Reason: deterministic
rules get deterministic fixtures; emergent behaviour gets a stochastic generator. A
synthetic tree would only test our assumptions about synthetic trees, and would
contaminate `mechanism_width` (is a transition due to M-width or to a conveniently shaped
topology?).

### 3.5 Generator scenarios

```text
S1 SELECTIVE→BROAD sweep  : A,C in disjoint domains, connected via M; sweep mechanism_width.
                            Primary Tier 0 curve.
S2 LATENT_PARENT          : A,C share domain P; apparent connection is domain-driven; A's
                            peers share P with C too. M absent. Expect RISK (degrade).
S3 COVERAGE/RESOLUTION    : PeerSet cardinality below n_min. Expect UNASSESSABLE regardless
                            of structure.
```

---

## 4. Frozen expectations (shape, not point)

For each scenario we freeze the **expected qualitative behaviour of the verdict
distribution over replicates**, never a single deterministic outcome on emergent data:

- **S1:** `P(RISK)` is **monotone non-decreasing** in `mechanism_width`; near **0** at
  `width = 0`; near **1** at `width = full PeerSet`; the full transition curve is reported
  without selecting a favourable point post hoc.
- **S2:** `P(RISK)` is **high** (degradation dominates) across replicates; latent-parent
  structure is not released as selective.
- **S3:** verdict is `UNASSESSABLE: INSUFFICIENT_RANK_RESOLUTION` in **all** replicates
  with `n < 19`; this is independent of S1/S2 structure.
- **Ties** behave conservatively (count against selectivity) wherever they occur.

We do **not** pre-register "at width = k the verdict flips here".

---

## 5. Three test layers (roles are distinct)

```text
Layer 0  Direct profile fixtures (UNIT, arithmetic only — NOT Tier 0 proof)
         mediated correctness, exact rank, ties, n_min boundary, side aggregation.

Layer 1  PeerSelector fixtures on frozen REAL MeSH fragments (deterministic — proves
         Decision 1 is implemented, NOT that peers are scientifically exchangeable):
           - single parent
           - polyhierarchy (e.g. a descriptor with multiple tree positions)
           - union of peers across all direct parents
           - dedup by DescriptorUI
           - endpoint and its subtree excluded
           - no ascent to grandparents
           - branch-order independence (same result regardless of traversal order)
           - explicit snapshot / version provenance

Layer 2  Tier 0 generative grid (§3, §6) — the contract-compliance curve. THIS is the
         Tier 0 evidence.

Layer 3  One integration test (wiring): real frozen MeSH fragment -> PeerSelector ->
         PeerSet -> synthetic profiles -> SelectivityGate. Checks interfaces only; its
         verdict is NOT part of the Tier 0 curve and is NOT proof of mechanism behaviour.
```

**Boundary that must not blur:** Layer 1 proves "the code selects exactly the peers the
frozen one-parent-up rule defines". It does **not** prove "those peers form a correct
exchangeability set" — that remains under L4 and is assessable only at Tier 1.

---

## 6. Grid (PROPOSED / UNPILOTED — not frozen, not exercised)

> PROPOSED / UNPILOTED historical proposal. No pilot run (reconstruction nor real V1)
> has exercised this grid. All values below — including `master_seed = 0` — are a
> proposal, NOT frozen and NOT operational. Confirmatory seeds derive ONLY from the
> operational pre-registration commit SHA, never from this file (karta §1). Retained
> verbatim as historical record.
>
> Combinatorial explosion is avoided by a **base configuration plus one-axis-at-a-time
> (OFAT) robustness sweeps**, not a full Cartesian product.

```text
Vocabulary family sizes:
    |P| = 40    |M| = 12    |U_X| = 60 per literature    |G| = 20    |N| drawn per doc

Base configuration (S1, width-swept):
    domains: A and C in disjoint domains (no shared P)
    M strength (relative family weight in an M-carrying literature): MODERATE = 0.30
    private mass (U_X relative weight):                              0.50
    profile imbalance (|docs_A| : |docs_peer|):                     1.0 (balanced)
    generic mass (G):                                               0.10 (must be filtered)
    noise level (N per doc):                                        LOW
    documents per literature:                                       60

PeerSet cardinalities (n in the rank test):
    assessable:    {19, 24, 30}
    unassessable:  {5, 12, 18}    (S3 -> UNASSESSABLE)

mechanism_width sweep (applied to each assessable PeerSet, as counts):
    {0, 1, 2, 4, 6, 9, 12, 18, 24, 30}  clipped to <= cardinality

OFAT robustness sweeps (around base, S1, at PeerSet=24):
    M strength:        {0.15 (thin), 0.30 (base), 0.50 (strong)}
    profile imbalance: {0.5, 1.0, 2.0}   (peers smaller / equal / larger than endpoint)
    noise level:       {LOW, MEDIUM}

S2 LATENT_PARENT:
    A and C share P (shared-domain weight 0.30); M absent; peers share P with C;
    PeerSet cardinality in {19, 24, 30}.

Replicates and seeds:
    replicates per cell: R = 200
    master_seed = 0 (frozen)
    per-replicate seed = deterministic function of
        (master_seed, scenario_id, peerset_cardinality, mechanism_width, ofat_cell, replicate_index)
    seed scheme frozen; no reseeding after seeing results.
```

---

## 7. Pass criteria and STOP rule

**Tier 0 PASSES iff all hold** (assessed on the frozen grid, as curve-shape per §4, never
a hand-picked point):

```text
1. S1: P(RISK) monotone non-decreasing in mechanism_width; ~0 at width 0; ~1 at full width,
       for every assessable PeerSet cardinality.
2. S2: P(RISK) high (degradation dominates) across replicates.
3. S3: UNASSESSABLE: INSUFFICIENT_RANK_RESOLUTION in all n<19 replicates.
4. Ties behave conservatively wherever observed.
5. OFAT sweeps: the S1 qualitative shape survives each single-axis variation (thin M may
   shift the curve; it must not invert monotonicity).
```

**On FAIL:**

```text
- STOP. No Tier 1.
- The failure is logged as-is (which criterion, observed behaviour).
- Any change to the mechanism (§2) requires a NEW card with a NEW pre-registration.
- Do NOT tune alpha, the statistic, peer rule, or the generator to force a pass.
```

**On PASS:**

```text
- Status: EXPERIMENTAL_TIER0_ONLY (separate status entry / method card; the single source
  of truth in RELATION_STATUS governs).
- Shadow / audit mode ONLY: V2-A annotates; it does NOT change real verdicts and does NOT
  degrade production candidates.
- This grants the right to call V2-A an executable prototype. It does NOT grant use as a
  real gate. Only an independent Tier 1 can grant that.
- Tier 1 is a separate, later pre-registration.
```

---

## 8. Explicitly out of scope

```text
- Tier 1: external validity, real time-separated cases, blind panel, validation firewall,
  causal/interventional bridge labels. Separate card.
- Normalization of mediated: a different method; own pre-registration and own
  imbalance-control validation (L4).
- bridge.py / V1: untouched, blob 1969f43d... frozen; V1 stays the held-out artifact.
- Production gating of any kind.
- Any claim of detecting mediation, true bridges, or sibling structure as fact. V2-A
  detects pair-selectivity-not-demonstrated, relative to a declared ontology, under L1–L4.
```

---

*QHDALabs — ABC_BRIDGE V2-A, Tier 0 PROPOSED / UNPILOTED grid design. NOT frozen, NOT the
operational pre-registration. Its commit SHA MUST NOT seed confirmatory runs; changes
require a new card. Canonical design doc: docs/ABC_BRIDGE_V2A_TIER0_DRAFT.md*
