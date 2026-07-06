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

## §2. Claim / construct — `TBD` (frame here, values by governance)

State precisely what the sibling separator **will** and **will not** do. Draft frame:

```text
The separator estimates whether an A–C pair is a SAME-CLASS sibling relation rather than a
distinct-but-bridged one, relative to <a declared structure — TBD: MeSH? co-citation? both>.
A positive result REMOVES bridge confidence (sibling risk); it never asserts a true bridge.
It is one-sided and trust-removing, like V2-A.
```

`TBD (governance):` the exact construct, the declared reference structure, and the
one-sided direction. Do not let the construct claim to "detect true bridges".

## §3. Mechanism — `TBD` (GOVERNANCE DESIGN DECISION — not scaffolded here)

The log says the fix "likely needs more than one cosine cutoff." That is a *direction*, not
a mechanism. This section is intentionally empty of specifics:

```text
TBD (governance): the sibling-vs-bridge separation statistic. Candidate directions to be
chosen and specified by the owner, e.g.:
  - a multi-feature separator (direct_sim + mediated + neighbourhood shape) instead of one cutoff;
  - a structural test on the MeSH neighbourhood (is C inside A's sibling subgraph?);
  - a rank/selectivity test against sibling substitutions (relate to, but distinct from, V2-A).
Whatever is chosen: it is a NEW module around frozen V1; it reads V1 outputs; it does not
edit bridge.py. Once specified, it is frozen before data.
```

I (engineer) will **not** invent this. Once you specify the mechanism, I implement it as a
new, unit-tested module and scaffold its Tier 0 exactly as we did for V2-A.

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
