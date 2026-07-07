# OP2 — Sibling-vs-Bridge Separation — New Card (DRAFT scaffold)

> **STATUS: DRAFT SCAFFOLD — NEW CARD. MECHANISM NOT YET SPECIFIED. NOT FROZEN. NOT A
> PRE-REGISTRATION.** This document frames the problem and the hard boundaries only. The
> separation *mechanism* (§3) and every *numeric criterion* (§6) are design decisions to be
> written by the governance owner; they are left as explicit `TBD` slots here. Nothing in
> this file may seed anything, and this file's commit SHA is **not** a seed root.
> `bridge.py` stays blob `1969f43d8fb172f40bc4c878d519f406ac7499f2` (held-out V1).

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

## §2. Claim / construct — PROPOSED (confirm before freeze)

> **The MeSH Sibling-Substitution Safety Audit estimates SIBLING-CONFOUNDING RISK for a
> candidate A–C bridge, relative to the frozen MeSH release.** It asks one question: is the
> apparent bridge an artifact of A and C being SAME-CLASS (sibling) literatures rather than
> a specific, distinct A–C path? A positive result (`UNSAFE`) **removes** bridge confidence;
> it never asserts a true bridge. One-sided and trust-removing, like V2-A — and, like V2-A,
> every verdict is `modern-ontology-assisted` (relative to the declared MeSH release).**

It does **not** detect true bridges, mediation, or mechanism; it only flags the specific
failure mode OP2 named — a sibling scored as a bridge (cluster_headache ↔ migraine).
`Confirm (governance):` this construct and its one-sided direction.

## §3. Mechanism — MeSH Sibling-Substitution Safety Audit (governance-approved 2026-07-06)

A NEW module around frozen V1; it reuses `select_one_parent_up` (Decision-1) and the frozen
V1 `propose_bridge` scored fresh per pair. It does **not** edit `bridge.py` and uses **no
Qiskit** — this card is a pure, auditable safety gate (§1).

### Component 1 — MeSH endpoint-neighborhood hard gate
**Status: Tier 0 core / binding candidate.**

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
**Status: PROPOSED / statistical layer / §6 TBD — NOT a frozen PASS/FAIL without §6.**

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
YES  Component 1 as the hard OP2 core (binding candidate).
YES  Component 2 as a proposed statistical extension.
NO   Component 2 is NOT a frozen PASS/FAIL without §6.
NO   no changes to bridge.py.
NO   no Qiskit in this card (Qiskit is a later, separate card, e.g. V2-C / QWALK_RELATIONAL_TOPOLOGY).
```

Kept distinct from V2-A on purpose: V2-A tested pair-SELECTIVITY of mediation (power) and
failed Tier 0 on thin mediation; this OP2 audit is a SAFETY gate on ontology adjacency —
distinct construct, distinct verdict, new pre-registration, new seeds.

**Build order:** Component 1 first (module + tests, as a development module frozen later at
the OP2 pre-registration commit). Component 2 only after §6 (coverage, comparable-or-higher
fraction, threshold, `UNASSESSABLE`) is designed.

## §4. Identifiability limits — `TBD` (adapt V2-A's L1–L4)

Restate, for this construct, what is NOT identifiable on the term-profile substrate (e.g.
a sibling and a broad-mechanism bridge may be observationally close). Carry the
`modern-ontology-assisted` caveat if MeSH is the reference structure. `TBD (governance)`.

## §5. Tier 0 design — scenarios that actually test sibling separation

The generator must produce the case the single cutoff fails on: a **same-class sibling**
pair (high direct_sim, NOT a bridge) vs a **distinct-but-bridged** pair (low direct_sim,
real M). The motivating real case is migraine↔cluster_headache (sibling) vs
migraine↔magnesium (bridge). Layers mirror V2-A:

```text
Layer 0  arithmetic fixtures for the separator
Layer 1  determinism on frozen real-MeSH fragments (sibling subgraph membership)
Layer 2  emergent generator: sibling pairs must be flagged; genuine bridges must NOT be
Layer 3  one wiring test (real MeSH fragment -> separator -> verdict over synthetic profiles)
```

Generator scenarios and their frozen expectations: `TBD (governance)`.

## §6. Nulls / PASS / FAIL / STOP — `TBD` (numeric, governance)

Every threshold and the verdict binding are `TBD`, to be derived from a development pilot
and frozen before confirmatory (as with V2-A §7/§9). The STOP rules carry over verbatim:
implementation defect → fix+rerun; method failure → STOP, no Tier 1, no tuning.

## §7. Seed derivation (discipline carried over; SHA is THIS card's, not V2-A's)

```text
world_seed = int.from_bytes(
    SHA256("<THIS_CARD_PREREG_SHA>|OP2|Tier0|<grid_cell_id>|<replicate_index>".encode()),
    "big")[:8]      # namespace "OP2", NOT "V2A"; SHA is this card's pre-reg commit, never 8ef6057
```

`TBD:` R, RNG instantiation, the closed `grid_cell_id` set. Same rules as V2-A §6.4/§6.5.

## §8. What must be filled before this becomes a pre-registration

```text
[ ] §2  construct + declared reference structure (governance)
[ ] §3  the separation mechanism (governance) -> then I implement + unit-test it
[ ] §4  identifiability limits
[ ] §5  generator scenarios + frozen expectations
[ ] §6  numeric PASS/FAIL/STOP, contract-vs-characterization classification
[ ] §7  R, RNG, grid_cell_id set, seed root = this card's future commit SHA
[ ] cold-review sign-off (R1–R4), THEN commit as the operational pre-registration
```

Until §2–§7 are filled and cold-reviewed, this remains a DRAFT scaffold, not a
pre-registration. No mechanism code is written until §3 is specified (code freezes before
data; but here, design precedes code).

---

*QHDALabs — OP2 sibling-separation card, DRAFT scaffold. Mechanism and criteria pending
governance. Not frozen, not a pre-registration, not a seed root. V1/`bridge.py` untouched.*
