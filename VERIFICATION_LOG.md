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

<!-- result entry appended below AFTER the run -->

---

### [YYYY-MM-DD] Hypothesis: <first scientific hypothesis>

**Question:**
**Hypothesis:**
**Null / control:**
**Metric:**
**Artifact risk:**

<!-- write the result after running -->
