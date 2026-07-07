# OP2 — Sibling-vs-Bridge Separation — New Card (DRAFT scaffold)

> **STATUS: DRAFT — C1-ONLY Tier 0. NOT FROZEN. NOT YET A PRE-REGISTRATION.** Mechanism
> approved (§3, 2026-07-06): **Component 1** (MeSH endpoint-neighborhood hard gate) is the
> Tier 0 core — a **deterministic safety invariant**, not a statistical experiment.
> **Component 2** stays `PROPOSED_NOT_FROZEN` (no numbers, no commitment, out of this
> freeze). Because C1 is deterministic there is **no generator, no seeds, no R, no
> statistical thresholds** — see §5–§7. `bridge.py` stays blob
> `1969f43d8fb172f40bc4c878d519f406ac7499f2` (held-out V1); no Qiskit in this card.

Scaffolded after the V2-A Tier 0 confirmatory FAIL (2026-07-06, method failure at
`thin_half_n4`). V2-A addressed **pair selectivity / power**; it did not pass Tier 0 and
does not close OP2. OP2 is the separate, stronger structural finding.

---

## §0. Problem (OP2, grounded in VERIFICATION_LOG)

Verbatim from the log (migraine/magnesium held-out, 2026-06-26 and post-hoc note):

> OP2 — sibling separation: a single `direct_sim` gate at 0.30 does not distinguish a
> sibling literature from a true bridge (cluster headache at 0.283). Separating "same
> class" from "distinct-but-bridged" likely needs more than one cosine cutoff.
>
> The sibling false-positive (cluster headache, direct_sim=0.283, slips under
> `direct_max=0.30`, would be accepted with q=0.0135) is a STRUCTURAL defect of the
> statistic + gate … OP2 remains the stronger result.

In one sentence: **a single cosine cutoff (`direct_max`) cannot separate a same-class
sibling literature from a genuinely distant-but-bridged one.** Cluster headache — a
non-bridge sibling of migraine — is scored as a *stronger* bridge than the true target.
In open discovery, every clinical sibling would generate a spurious "bridge".

## §1. Hard boundaries (loud — read before anything)

- **V1 is frozen and held-out.** The `direct_max = 0.30` gate lives in `bridge.py`
  (lines ~198/207/246), blob `1969f43d8fb172f40bc4c878d519f406ac7499f2`. **This card MUST
  NOT change `bridge.py`.** OP2's remedy is a NEW mechanism *around* V1 (as V2-A was), not
  an edit to V1's gate. Any temptation to "just move the threshold" is out of scope — the
  finding is that a single cutoff is the wrong instrument, not that 0.30 is the wrong number.
- **No reuse of spent seeds/SHA.** The V2-A Tier 0 pre-registration SHA
  `8ef6057e5a2bcef67a0bcfb5b3d68c4927d6d551` and its confirmatory seeds are **spent**. The
  V2-A dev seeds (`0..9` / `0..19`) are **burned**. This card gets its OWN pre-registration
  and its OWN seed root; it may reuse none of the above.
- **Code freezes before data.** The separation mechanism (once §3 is chosen) is committed
  and frozen before any confirmatory seed is derived; confirmatory seeds derive ONLY from
  THIS card's pre-registration commit SHA.
- **Shadow/audit-only, Tier 0 only.** Even a Tier 0 PASS grants at most
  `EXPERIMENTAL_TIER0_ONLY`; a real gate needs a separate Tier 1. This card does not
  authorize production gating.
- **Honest scope.** No overclaiming; a Tier 0 FAIL is a first-class result logged as-is.
- **No Qiskit in this card.** OP2 is a pure, auditable safety gate on the relational /
  ontology layer; it imports no quantum layer. Any quantum approach is a separate, later
  card (e.g. `V2-C / QWALK_RELATIONAL_TOPOLOGY`), after OP2.

## §2. Claim / construct — CONFIRMED (governance 2026-07-06)

> **The MeSH Sibling-Substitution Safety Audit estimates SIBLING-CONFOUNDING RISK for a
> candidate A–C bridge, relative to the frozen MeSH release.** It asks one question: is the
> apparent bridge an artifact of A and C being SAME-CLASS (sibling) literatures rather than
> a specific, distinct A–C path? A positive result (`UNSAFE`) **removes** bridge confidence;
> it never asserts a true bridge. One-sided and trust-removing, like V2-A — and, like V2-A,
> every verdict is `modern-ontology-assisted` (relative to the declared MeSH release).**

It does **not** detect true bridges, mediation, or mechanism; it only flags the specific
failure mode OP2 named — a sibling scored as a bridge (cluster_headache ↔ migraine).
`Confirmed (governance, 2026-07-06):` this construct and its one-sided direction.

## §3. Mechanism — MeSH Sibling-Substitution Safety Audit (governance-approved 2026-07-06)

A NEW module around frozen V1; it reuses `select_one_parent_up` (Decision-1) and the frozen
V1 `propose_bridge` scored fresh per pair. It does **not** edit `bridge.py` and uses **no
Qiskit** — this card is a pure, auditable safety gate (§1).

### Component 1 — MeSH endpoint-neighborhood hard gate
**Status: `TIER0_CORE_CANDIDATE` — the OP2 Tier 0 core, deterministic (see §5–§7).**

```text
If C ∈ select_one_parent_up(A)  OR  A ∈ select_one_parent_up(C):
    return UNSAFE_NEIGHBORHOOD_ADJACENCY
```

The direct OP2 fix: **ontology structure overrides the weak cosine gate.** The rule is an
`OR`, so it may fire one-sidedly (a descriptor's multi-tree MeSH positions can make the
neighbourhood asymmetric) — hence `NEIGHBORHOOD_ADJACENCY`, not "mutual sibling". This
catches the motivating case (`cluster_headache` adjacent to `migraine`) that
`direct_max=0.30` missed. Deterministic; testable on frozen MeSH fragments.

### Component 2 — sibling-substitution specificity audit
**Status: `PROPOSED_NOT_FROZEN` — future statistical layer; NOT in this Tier 0, no numbers,
no commitment.**

```text
Run frozen V1 on sibling substitutions:
    propose_bridge(A_sibling, C)
    propose_bridge(A, C_sibling)
If the substituted pairs reproduce comparable-or-higher bridge evidence:
    return UNSAFE_NON_SPECIFIC_SIGNAL
```

`§6 TBD (governance):` the "comparable-or-higher" statistic, its threshold, the coverage /
`UNASSESSABLE` rule, and whether Component 2 binds Tier 0 at all. Component 2 is a proposed
statistical extension only; it is **not** frozen as PASS/FAIL until §6 is designed.

### Decision record (governance, 2026-07-06)
```text
SCOPE  OP2 Tier 0 = C1 ONLY (a deterministic MeSH-adjacency safety invariant).
YES    Component 1 is sufficient for this narrow Tier 0.
NO     Component 2 does NOT enter this freeze — PROPOSED_NOT_FROZEN, no numbers.
NO     do not mix the deterministic gate with an unsettled statistic.
NO     no changes to bridge.py.
NO     no Qiskit in this card (Qiskit is a later, separate card, e.g. V2-C / QWALK_RELATIONAL_TOPOLOGY).
```

Kept distinct from V2-A on purpose: V2-A tested pair-SELECTIVITY of mediation (power) and
failed Tier 0 on thin mediation; this OP2 audit is a SAFETY gate on ontology adjacency —
distinct construct, distinct verdict, new pre-registration, new seeds.

**Build order:** Component 1 first (module + tests, as a development module frozen later at
the OP2 pre-registration commit). Component 2 only after §6 (coverage, comparable-or-higher
fraction, threshold, `UNASSESSABLE`) is designed.

## §4. Limits (structural gate — not statistical)

- **L1 — modern-ontology-assisted.** Every verdict is relative to the frozen MeSH release;
  adjacency is whatever that release encodes. This is a scope limitation of the claim.
- **L2 — adjacency, not all confounding.** C1 flags one specific, structural failure mode:
  an endpoint inside the other's one-parent-up MeSH neighbourhood. It does not claim to
  catch every sibling/confounder — only ontology adjacency. One-sided:
  `UNSAFE_NEIGHBORHOOD_ADJACENCY` removes trust; `NO_ADJACENCY` adds none.
- **L3 — hierarchy is out of scope.** Parent–child (an endpoint in the other's descendant
  subtree) is deliberately NOT flagged: `select_one_parent_up` excludes the endpoint's
  subtree, so C1 targets siblings/neighbours, not ancestors/descendants. A known, intended
  boundary, not a defect.
- **L4 — coverage.** An endpoint absent from the frozen MeSH fails loud (`KeyError`); an
  endpoint with no branch peers simply yields `NO_ADJACENCY`. A dedicated `UNASSESSABLE`
  coverage state belongs to the future statistical layer (C2/§6), not to C1.

## §5. Tier 0 design — C1-only: a deterministic safety invariant (not an experiment)

C1 is deterministic, so OP2 Tier 0 is **not** a statistical experiment: no generator, no
replicates, no distribution. Tier 0 = a frozen, auditable invariant checked by the unit
tests already merged (`tests/verification/test_sibling_safety.py`) on frozen MeSH
fragments. The invariant, in words:

```text
The MeSH endpoint-neighborhood hard gate must:
  (a) return UNSAFE_NEIGHBORHOOD_ADJACENCY when either endpoint is in the other's
      one-parent-up neighbourhood — including the frozen motivating fixture
      migraine ~ cluster_headache;
  (b) return NO_ADJACENCY for a genuinely distant pair — migraine ~ magnesium;
  (c) fire the OR from either argument order;
  (d) NOT flag parent ~ child (hierarchy is out of scope, L3);
  (e) touch no V1 (bridge.py blob stays 1969f43d…) and import no Qiskit.
```

No Layer-2 generator and no Layer-3 stochastic wiring — those were V2-A's statistical
apparatus and do not apply to a deterministic gate.

## §6. PASS / FAIL / STOP — deterministic (almost empty by design)

**No R, no RNG, no distribution, no statistical thresholds.** PASS is a conjunction of
deterministic conditions, all already exercised by the merged tests:

```text
PASS iff ALL of:
  - test_sibling_safety.py passes (adjacency caught; OR both orders; unrelated clear;
    parent~child not flagged; unknown endpoint raises);
  - the frozen fixture migraine ~ cluster_headache returns UNSAFE_NEIGHBORHOOD_ADJACENCY;
  - migraine ~ magnesium returns NO_ADJACENCY;
  - bridge.py blob == 1969f43d8fb172f40bc4c878d519f406ac7499f2 (V1 untouched);
  - the module imports no Qiskit.
FAIL = any of the above breaks.
STOP = implementation defect -> fix + rerun the deterministic checks. There is no "method
       failure" mode here: there is no statistic to fail.
```

Being deterministic, this Tier 0 is reproducible on any machine — no seed, no multi-hour run.

## §7. Seed derivation — N/A for C1

C1 is deterministic: **no seeds, no confirmatory RNG run, no seed root.** The §6.4-style
seed machinery does not apply. It would return only if Component 2 (the statistical layer)
is ever pursued — and only under its OWN new pre-registration, whose commit SHA (never
`8ef6057…`) would seed it. Nothing in THIS card is a seed root.

## §8. What remains before this C1-only card becomes a pre-registration

```text
[x] §0–§2  problem, boundaries, construct (confirmed 2026-07-06)
[x] §3     mechanism — Component 1 approved; C2 = PROPOSED_NOT_FROZEN, out of this freeze
[x] C1     implemented + unit-tested (merged: sibling_safety.py, test_sibling_safety.py)
[ ] §4–§7  fold this deterministic-Tier-0 revision into final form
[ ] freeze the motivating fixture (migraine ~ cluster_headache) as a committed test asset,
    ideally with REAL MeSH UIs/tree-numbers (current test uses synthetic ids)
[ ] cold-review sign-off — lighter than V2-A (no numbers to review): check the invariant,
    the frozen fixture, V1-untouched, no-Qiskit — THEN commit as the OP2 pre-registration
```

C1-only makes the remaining path short: no numeric grid, no seed derivation, no multi-hour
run to design or execute. Design still precedes the freeze commit.

---

*QHDALabs — OP2 sibling-separation card. C1-only Tier 0: a deterministic MeSH-adjacency
safety invariant. Component 2 is a future statistical layer (`PROPOSED_NOT_FROZEN`). Not
frozen, not yet a pre-registration, not a seed root. V1/`bridge.py` untouched; no Qiskit.*
