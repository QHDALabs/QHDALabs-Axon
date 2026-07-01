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

### [2026-06-21] Session: MVP proximity — null-model fix + FDR (engineering + methodology, no scientific claim)

Engineering + methodology entry. No scientific hypothesis about the literature is
tested; the corpus is illustrative. Numbers below are pipeline outputs on a fixed,
real corpus, **not** a claim about any paper or any relation between papers.

**The flaw we fixed (this is the point).** The scaffold's proximity verifier built
its null by permuting the *components* of one vector. For real text vectors that is
an INVALID null: it tests "is this pair more aligned than a random direction in
feature space?" — a near-trivial bar that any two same-domain TF-IDF vectors clear,
inflating significance. It answers the wrong question.

**The valid null.** For `PROXIMITY` the null is now EMPIRICAL: the distribution of
cosine similarity over real document pairs FROM THE SAME CORPUS, stratified so each
candidate is compared only against random pairs matched on its confounders — the
unordered pair of domains and a coarse (median-split) length band. The candidate's
own pair is excluded. p = (#{matched pairs with cos >= observed} + 1) / (n + 1),
one-sided. This asks the right question: "more similar than typical comparable
pairs?" It is featurizer-agnostic (reads only vectors), so real embeddings can
replace TF-IDF later without changing the null.

**Multiple testing.** Proposing many relations and testing each is a false-positive
generator. We added Benjamini-Hochberg FDR (pure numpy) across the full tested
family. ACCEPTED is assigned ONLY by the FDR pass — a single verifier reports a
p-value and a provisional NULL/REJECTED; it cannot accept on its own.

**Structure.** `RelationKind` enum + a fail-closed verifier registry: a candidate
whose kind has no registered verifier RAISES (no silent fallback to proximity),
making "no relation kind without its own null" structural, mirroring "no hypothesis
without verification". MVP registers exactly `PROXIMITY`.

**Result (deterministic; exhaustive null, no RNG).** Corpus: 40 real arXiv
abstracts, two domains (astro-ph.CO, q-bio.NC). TF-IDF dim 676. 780 candidate
pairs (all). Verdicts: 0 ACCEPTED, 311 NULL, 469 REJECTED, 0 INCONCLUSIVE. 34
pairs are nominally significant (raw p<0.05); **0 survive BH-FDR** (all q=1.0).
Highest-similarity cross-domain pair (`arXiv:2606.19452` ~ `arXiv:2606.16693`,
cos=0.203, raw p=0.0093) is an honest NULL after FDR.

**Interpretation.** This is the correct, honest outcome, not a failure. The old
invalid null would have manufactured ~34 "significant" links; the valid null + FDR
rejects them. There is also a structural fact worth recording: an empirical
same-corpus pair null has a p-value floor of ~1/(stratum size) ≥ 1/(#pairs), while
BH's rank-1 threshold is α/(#pairs); since the floor exceeds that threshold,
**testing all pairs with an empirical null can essentially never accept** — the
null's resolution cannot outpace the multiple-testing burden. Per the project's
no-tuning rule, thresholds were NOT adjusted to manufacture a survivor.

**Decision:** keep this as the honest MVP. A *usable* discovery setting needs a
pre-registered, hypothesis-driven candidate set (so #tests ≪ stratum size) or a
null whose resolution is independent of corpus size — the latter reintroduces the
"smooth model" risk (rule 3) and is deferred. Mechanistic relation kinds remain
unregistered (fail closed) until each has its own explicit null.

---

### [2026-06-25] Session: ABC bridge — recovery of a known closed discovery (methodological validation, no scientific claim)

Engineering + methodology entry. **METHODOLOGICAL VALIDATION, not a scientific
discovery**: the question is whether the method RECOVERS a documented bridge
(Swanson's Raynaud / fish-oil, 1986) from pre-1986 literature. The statistic was
shaped IN-SAMPLE for this case, so recovery validates the machinery, not a claim
about biology. Held-out generalization (migraine / magnesium) is the next step and
will run WITHOUT touching the statistic.

**Bridge model.** A and C are literatures; the relation is group-level
(`BridgeCandidate`), not doc-doc. Substrate: MeSH descriptors (controlled
vocabulary; pre-1986 records often lack abstracts but carry MeSH). Profile
`w_L[t] = mean_TF * idf[t]` (idf from a background pool DISJOINT from A/C).
`mediated = sum_{t in B} min(w_A[t], w_C[t])`; `direct_sim = cos(w_A, w_C)` over
non-generic vocab. A bridge has LOW direct_sim and HIGH mediated; a high-direct_sim
pair is proximity and is gated out (`direct_max=0.30`). B-selection (shared support
among non-generic terms) is part of the statistic and is **re-selected on every null
replica**, never frozen on the observed pair. Generic-B control: drop MeSH
check-tags/ubiquitous descriptors (stoplist), `background_df_ratio > max_df`, and
low-idf terms.

**Two nulls (both reported; `p = max(p1, p2)`).**
1. random-literature-pair: mediated for two focused, unrelated background
   literatures of the same sizes;
2. shuffled-B: permute w_C to break the specific A-B-C alignment.

**Artifact found and fixed (verify-first, on synthetic data, BEFORE the real corpus).**
The first shuffled-B permuted the WHOLE w_C vector. That manufactured overlaps
between each literature's PRIVATE dominant terms (A-dom × C-dom) — impossible in the
observed data, where those vocabularies are disjoint — inflating the null and
killing its power: a cleanly planted bridge could not beat it without raising
direct_sim past the proximity gate (parameter sweep confirmed the bind). Fix:
restrict the shuffle to the COMMON POOL (`background_df > 0`); literature-private
terms (`df == 0`) stay fixed. This removes impossible events and keeps legal ones.

**Anchor — calibration of the corrected null (this is what makes the p-values mean
anything).** Full pipeline (B-selection per replica + both nulls + gate + FDR) on
focused, unrelated background pairs: **false-ACCEPTED = 0 / 30 (rate 0.000)**, well
under α=0.05. The corrected shuffled-B bought power without buying a leak. Planted
synthetic bridge (modeled from reality — B common/mid-frequency in background,
independently of the null's mechanics): direct_sim=0.090, p_random_pair=0.0005,
p_shuffled_B=0.0005 → ACCEPTED. Hard negatives: directly-similar → REJECTED (gate);
generic-only → INCONCLUSIVE.

**Recovery (frozen pre-1986 corpus, 717 records, all with MeSH; seed=0, R=n=2000).**
`raynaud ~ fish_oil`: direct_sim=**0.046** (very low), |B|=**34**, mediated=**5.10**;
**p_random_pair=0.0345, p_shuffled_B=0.0005**, p=max=0.0345.
- FDR family = **{raynaud~fish_oil}** (closed discovery, one pre-specified pair) →
  **q=0.0345 → ACCEPTED**.
- For transparency: pooling the negative controls into the family would give
  **q=0.069** (not accepted). That pooling is what OPEN discovery requires; here it
  does not apply (see boundary).

**Why family = 1 (decision, not cosmetics).** FDR controls false discoveries among
the RODZINA of discovery CANDIDATES. A negative control is not a candidate — it
validates the method, it does not compete as a discovery. FDR-ing the real
hypothesis against its own controls penalizes due diligence (the more specificity
checks you run, the harder it becomes to accept a true bridge), which is wrong.
Closed discovery with one pre-specified A–C pair = a family of size 1.

**BOUNDARY (carried loudly).** Family-1 is legitimate ONLY because `raynaud~fish_oil`
was **pre-specified** (a documented Swanson case fixed BEFORE the fetch; corpus
restricted to pre-1986 so there is no post-discovery A–C leak) and was NOT chosen
from a scan over candidate C's by p-value. In OPEN discovery the family is ALL
scanned C's and FDR over them is mandatory — this leniency DOES NOT transfer.

**Honest reading of the margin.** The binding null is the WEAKER random-pair null
(p=0.0345), not shuffled-B (0.0005); the margin is modest. Recovery is real but not
overwhelming. The bridge SIGNATURE is unambiguous, and the B-terms surfaced by the
method — `blood platelets`, `arachidonic acid`, `aspirin`, `blood vessels`,
`blood pressure`, `angiography` — are the platelet / prostaglandin / vascular
pathway Swanson identified: qualitative confirmation that the method found the right
mechanism, not a coincidental lexical overlap.

**Controls (specificity holds).** `raynaud ~ scleroderma` → REJECTED (proximity gate,
direct_sim=0.346 — clinically near Raynaud, so directly similar, not a bridge).
`raynaud ~ dental_caries` → REJECTED (mediated below the random-pair null mean,
p_random=0.746).

**Decision:** keep as validated recovery under the closed-discovery design.
`ABC_BRIDGE` is now a registered relation kind with its own explicit nulls; the
other mechanistic kinds remain unregistered (fail closed). Next: held-out
migraine / magnesium recovery, run without changing the statistic — held-out
evidence outweighs in-sample.

---

### [2026-06-26] PRE-REGISTRATION: held-out ABC-bridge test — migraine / magnesium

Written and committed BEFORE any fetch or run (this is commit #1 on
`feature/migraine-magnesium-heldout`; a draft PR is opened immediately after it, so
GitHub timestamps the rule ahead of the result). The value of a held-out test is
that the statistic is frozen and recorded before the result is seen. This entry
fixes, ahead of data:

A = migraine, C = magnesium (Swanson's second documented bridge, 1988). Fixed before
seeing any corpus; NOT selected from a scan over candidate C's.

FROZEN CODE — verifiable fact, not a promise. The bridge logic is frozen at:
- base commit `5101c8e4d231b1d420b91c016ddf1e16260a32d0` (main after the ABC work),
- `src/axon/verification/bridge.py` blob `1969f43d8fb172f40bc4c878d519f406ac7499f2`.
Anyone can `git diff` bridge.py from that blob against this PR and see ZERO changes.
Not one line of bridge.py changes for this test: the bridge statistic
(mediated = sum_{t in B} min(w_A[t], w_C[t])), direct_max=0.30, the B-selection rule
(shared support among non-generic terms, re-selected on EVERY null replica), both
nulls (random-literature-pair + shuffled-B over the common pool background_df>0),
R = n_random_pairs = n_shuffles = 2000, seed = 0, alpha = 0.05, and the family-1 FDR
rule. Family-1 is legitimate ONLY because A-C is pre-specified here; in open
discovery the family is all scanned C's. Migraine/magnesium runs through the
UNCHANGED AbcBridgeVerifier.

FROZEN CORPUS RECIPE — no post-hoc engineering to make a result appear:
- A = migraine ("migraine"), C = magnesium ("magnesium"); MeSH substrate.
- Date filter 1900:1987[dp] (strictly pre-1988, before Swanson's publication).
- Directly-similar control: cluster headache (same primary-headache class; expected
  high direct_sim -> gated as proximity).
- Unrelated control: dental caries (expected worse-than-chance).
- Background (IDF + random-pair null): asthma, epilepsy, glaucoma, psoriasis,
  tuberculosis, hepatitis, appendicitis, cataract — focused, comparable, disjoint
  from A/C/controls.

COMMITMENT: whatever the verifier returns goes into the log as-is — ACCEPTED, NULL,
or honest near-miss. Zero tuning of statistic, thresholds, B-rule, nulls, or corpus
after seeing the outcome. A non-recovery is a RESULT ("the method generalizes to one
case, not the class"), logged as such, not a failure.

STOP conditions (report, never quiet workaround): if pre-1988 MeSH is too sparse/flat
to form B -> STOP and report (do NOT swap to abstracts or loosen filters). If the
controls do not separate (directly-similar high direct_sim; unrelated worse-than-
chance) -> STOP and report (adjust nothing).

**RESULT [2026-06-26] — logged as-is per the commitment above. Outcome: NON-RECOVERY
+ control-separation failure. Zero tuning; bridge.py blob 1969f43d… unchanged.**

Corpus: 710 pre-1988 PubMed records, all with MeSH (B forms fine — no sparsity STOP).
Verifier: the frozen `AbcBridgeVerifier` (R=n=2000, seed=0), family-1 FDR.

**migraine ~ magnesium — NOT recovered.**
- Bridge signature is correct: direct_sim=**0.013** (very low), |B|=**22**, mediated=2.41.
- Nulls: **p_random_pair=0.1214, p_shuffled_B=0.1074**, p=max=0.1214 → family-1
  **q=0.1214 → NULL**. Not a near-miss; ~2.4x the 0.05 threshold.
- Mechanism: `platelet aggregation` IS among the discovered B-terms, but
  `vasoconstriction`, `cortical spreading depression`, `serotonin` are NOT; the B
  set is noisy (`blood glucose`, `reference values`, `radiography`, `risk factors`
  alongside `norepinephrine`, `calcium`, `hemodynamics`, `adenosine diphosphate`).
  The mechanism is only weakly and partially surfaced.

**Control separation — FAILED (STOP condition).**
- `migraine ~ cluster_headache` (directly-similar control, expected gated as
  proximity): direct_sim=**0.283** — just UNDER the frozen `direct_max=0.30`, so the
  gate did NOT fire. It then scored mediated=**8.60**, p_random=**0.0135**,
  p_shuffled=**0.0005** → family-1 **q=0.0135 → would be ACCEPTED**. A same-class
  non-bridge looks like a STRONGER bridge to migraine than the true target magnesium
  does. The directly-similar control did not separate.
- `migraine ~ dental_caries` (unrelated control): REJECTED, worse than chance
  (p_random=0.891). This control separated correctly.
- Calibration on focused unrelated background pairs (full pipeline): false-accept
  **0/30 (0.000)** — the frozen shuffled-B still holds against random pairs.

**Interpretation — TWO distinct findings about the method (not one vague "it didn't
work"). Held-out generalization FAILED; statistic frozen; this card is spent once.**

**Finding 1 — LIMITED POWER (range-of-validity limit).** The true, genuinely-distant
bridge migraine↔magnesium (mediated=2.41) does NOT beat its nulls (p≈0.12). The
statistic detected the in-sample Raynaud/fish-oil bridge (mediated=5.10, medium
mediation) but is effectively BLIND to a very distant bridge carried by thin
mediation. The mediated-connectivity statistic has a sensitivity floor: it finds
medium-mediation bridges and misses very thin ones. That is a boundary of its reach,
established on held-out data.

**Finding 2 — THE GATE DOES NOT SEPARATE SIBLINGS (the stronger result).** Cluster
headache is NOT a bridge — it is a sibling literature of migraine (same primary-
headache class). Yet it has direct_sim=0.283, slips UNDER the frozen direct_max=0.30
gate, and with q=0.0135 WOULD BE FALSELY ACCEPTED as a bridge — and a *stronger* one
to migraine (mediated=8.60) than the true target magnesium (2.41). This is a
SYSTEMATIC false-positive on closely-related literatures: in open discovery, scanning
migraine against many candidate C's, every clinical sibling would generate a spurious
"bridge". The held-out test caught this BEFORE it could be shipped. The hard
direct_max threshold is the wrong instrument for separating siblings from bridges —
proximity and bridging are not cleanly split by a single cosine cutoff.

The unrelated control `dental_caries` separated correctly (worse than chance), and
the frozen shuffled-B null still calibrates (false-accept 0/30 on background pairs) —
so neither finding is an artifact of a broken null; they are properties of the
mediated statistic and the gate.

**Commitment honored.** Nothing was tuned. The bridge statistic, thresholds, B-rule,
nulls, and corpus recipe are exactly as pre-registered; bridge.py is byte-identical
to blob `1969f43d8fb172f40bc4c878d519f406ac7499f2` (verify with `git hash-object`).

**Open problems (for a SEPARATE, future, re-validated effort — do NOT touch bridge.py
here; this is no longer held-out for migraine/magnesium):**
- OP1 — sensitivity to thin mediation: the mediated statistic misses very distant
  bridges. A power-aware statistic (e.g. normalizing for each literature's own mass,
  or weighting rare shared intermediates) would need its own held-out validation.
- OP2 — sibling separation: a single direct_sim gate at 0.30 does not distinguish a
  sibling literature from a true bridge (cluster headache at 0.283). Separating
  "same class" from "distinct-but-bridged" likely needs more than one cosine cutoff.
Both are recorded as open; any fix is a new card with a new pre-registration.

---

### [2026-06-26] Post-hoc note on migraine/magnesium ground-truth strength (does NOT revise the verdict)

Added after the held-out result was registered and merged. This is an interpretive
observation, not a re-scoring. The verdict stands: migraine/magnesium = NON-RECOVERY,
statistic frozen, no tuning.

Observation (evidence checked 2026-06-27). The ground-truth for migraine/magnesium is
clinically WEAKER and less definitive than assumed when the test was designed. A 2026
systematic review (NOT a meta-analysis — no quantitative synthesis) covered 6 RCTs
(~502 participants); results were formulation-dependent and inconsistent, with 3 of 6
trials reporting favorable efficacy signals, and the certainty of evidence for migraine
frequency and severity rated LOW due to risk of bias and inconsistency (Jagunmolu et al.,
2026). An earlier NCCIH summary (updated 2021) cited a 2018 review of 5 studies / 253
participants, 3 of 5 favorable, "possibly effective". (A 2025 quantitative meta-analysis
exists but pools many supplements together — its counts cannot be attributed to magnesium,
so it is not used here.) Swanson's 1988 case documents a coherent, disconnected MECHANISTIC
path in the pre-1988 literature; it does not establish that magnesium treats migraine.

Consequence — scoped strictly to OP1. Because the target itself is a thin, partially
supported bridge, this single non-recovery is LESS DIAGNOSTIC for OP1 (sensitivity to
thin mediation) than originally assumed: we cannot distinguish "the method is under-
sensitive" from "the target is a genuinely weak/ambiguous bridge" on this case alone.
This rescopes how much OP1 weight this one case carries; it does NOT mean the method
recovered anything.

OP2 is UNAFFECTED. The sibling false-positive (cluster headache, direct_sim=0.283,
slips under direct_max=0.30, would be accepted with q=0.0135) is a STRUCTURAL defect of
the statistic + gate. It holds regardless of whether magnesium clinically helps migraine
and regardless of the benchmark's evidential strength. OP2 remains the stronger result
and is not weakened by this note.

Terminology: "true bridge" is avoided; use "historically documented LBD bridge". A
historically documented discovery case is a recovery-mechanics validation target, NOT an
automatic biomedical truth label.

---

### [2026-06-29] Session: V2-A Tier 0 development pilot (PRs #7, #8) — DEVELOPMENT, NOT CONFIRMATORY

Engineering entry. **DEVELOPMENT calibration only — NOT confirmatory Tier 0 evidence,
NOT a Tier 0 pass, NOT a validation of the method.** No V2-A Tier 0 pre-registration is
committed or frozen. Every number below is a development-pilot output and is labelled.

**Merged work.**
- PR #7 (merged): consolidated the V2-A docs under `docs/`; added the pair-selectivity
  module (`verification/selectivity.py`), the Tier 0 generator
  (`verification/tier0_generator.py`), the pilot script, and tests. PilotConfig
  development document-count defaults changed 60 → 20 (development values only).
  `frozen_v1_scorer` context annotation narrowed to `LiteratureContext` via a
  TYPE_CHECKING import (the runtime `propose_bridge` import stays lazy).
- PR #8 (merged): one-shot DEVELOPMENT grid runner (`scripts/pilot_v2a_grid.py`) run on
  REAL V1 (`frozen_v1_scorer → propose_bridge → LiteratureStore`; fail-loud, no fallback
  scorer). Split `run()` into `run_width_sweep` / `run_latent_parent`; brought `scripts/`
  under the strict mypy gate (`mypy src scripts`).

**Development pilot outcome (real V1; the full grid JSON is a local artifact, not committed).**
Framing note: the only claim here is "real V1 produced these numbers." Rank-decision
agreement is NOT value-fidelity, and nothing here confirms the earlier reconstruction or
constitutes a Tier 0 pass.
- *DEVELOPMENT — NOT CONFIRMATORY:* **0 within-replicate monotonicity reversals** across
  all 11 grid cells and all three spread modes. This meets the S1 zero-reversal PILOT
  criterion — a development result, **not** a Tier 0 pass.
- *DEVELOPMENT — NOT CONFIRMATORY:* latent_parent (M absent): risk_rate_a = **1.00**,
  risk_rate_c = **0.95**.
- *DEVELOPMENT — NOT CONFIRMATORY:* contract cell `thin_half_n4` (M=0.15 / ratio=0.5 /
  noise=4): real-V1 degradation **0.40 / 0.40** — confirms the low-power boundary is
  genuine, not a reconstruction artifact. Recorded plainly, not softened. The probes
  `probe_20_h_2`, `probe_20_h_4`, `probe_25_h_4` sit in the same
  half-corpus × noise × thin-M corner.

**Still open — nothing frozen.** Numeric PASS criteria, the MeSH 2026 artifact URL + SHA,
the confirmatory seed derivation, the cold review, and the pre-registration provenance
question all remain unresolved. No V2-A Tier 0 pre-registration is committed or frozen;
`ABC_BRIDGE_V2A_TIER0_PRE_REGISTRATION.md` is still an uncommitted draft. `bridge.py`
unchanged (blob `1969f43d8fb172f40bc4c878d519f406ac7499f2`).

---

### [YYYY-MM-DD] Hypothesis: <first scientific hypothesis>

**Question:**
**Hypothesis:**
**Null / control:**
**Metric:**
**Artifact risk:**

<!-- write the result after running -->
