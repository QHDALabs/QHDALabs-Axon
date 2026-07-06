# V2-A Tier 0 — Cold-Review Package (PROPOSED, line A / docs=20)

> **STATUS: COLD-REVIEW SIGNED OFF (2026-07-06) — ready to commit as the operational
> pre-registration (line A). NOT YET FROZEN / NOT YET COMMITTED.** The §6/§7 numbers are
> cold-review-approved (see §9); they freeze on the commit. No confirmatory seed may be
> derived until this document is committed as the operational pre-registration and that
> commit's SHA exists (§6.4). `bridge.py` stays blob
> `1969f43d8fb172f40bc4c878d519f406ac7499f2`.

Built on the canon [docs/ABC_BRIDGE_V2A_TIER0_DRAFT.md] (`DRAFT — NOT FROZEN`) plus the
validated development-pilot artifact. This is **line A (docs=20)** only. The docs=60
grid in `ABC_BRIDGE_V2A_TIER0_PROPOSED_UNPILOTED_DESIGN.md` is a separate, unpiloted
line B; its values and its commit SHA do **not** apply here and must never seed line A.

---

## 0. Provenance validation (why these numbers are trustworthy)

Source: `v2a_dev_grid.json` — one-shot **real-V1** development grid
(`scripts/pilot_v2a_grid.py`), frozen `bridge.py` blob `1969f43d…`, development seeds
`0..9` (width) / `0..19` (latent parent). It is DEVELOPMENT calibration, **not**
confirmatory, and is a local artifact (not committed).

Cross-checked against the three VERIFICATION_LOG #8 anchors — all match exactly:

| Anchor (logged #8) | Logged | Artifact | Match |
|---|---|---|---|
| within-replicate monotonicity reversals (11 cells × 3 modes) | 0 | 0 | ✓ |
| latent_parent risk_rate_a / risk_rate_c | 1.00 / 0.95 | 1.0 / 0.95 | ✓ |
| contract cell `thin_half_n4` full-width symmetric degradation | 0.40 / 0.40 | 0.4 / 0.4 | ✓ |

The artifact is a faithful reproduction of #8. Development-pilot numbers carry a label;
they set the confirmatory criteria (per DRAFT §12) but are not themselves a Tier 0 pass.

---

## §6. Confirmatory grid — line A (PROPOSED)

### 6.1 Fixed generator parameters (from the dev config, line A)

```text
documents_per_literature        = 20        n_peers                    = 24
background_topics               = 8         background_documents/topic = 20
background_mechanism_rate       = 0.25
parent_terms   = 16   parent_rate   = 0.45
mechanism_terms= 8    mechanism_rate= <per cell>
private_terms  = 24   private_rate  = 0.55
generic_terms  = 4
noise_terms    = 64   noise_per_document = <per cell>
peer_document_ratio = <per cell>
```

### 6.2 The 11 frozen cells (canonical `grid_cell_id`)

`grid_cell_id` is the cell `id` string below — this is the token that enters the seed
derivation (§6.4). The set is closed; classification is **a cold-review decision**, the
only pre-classified one being the frozen contract cell.

| grid_cell_id | mechanism_rate | peer_ratio | noise | proposed role |
|---|---|---|---|---|
| `base` | 0.30 | 1.0 | 1 | base regime |
| `thin` | 0.15 | 1.0 | 1 | OFAT: thin M |
| `strong` | 0.50 | 1.0 | 1 | OFAT: strong M |
| `thin_halfcorp` | 0.15 | 0.5 | 1 | OFAT: half corpus |
| `thin_double` | 0.15 | 2.0 | 1 | OFAT: double corpus |
| `thin_noise4` | 0.15 | 1.0 | 4 | OFAT: high noise |
| **`thin_half_n4`** | **0.15** | **0.5** | **4** | **FROZEN CONTRACT cell** |
| `probe_20_h_2` | 0.20 | 0.5 | 2 | boundary probe |
| `probe_20_h_4` | 0.20 | 0.5 | 4 | boundary probe |
| `probe_25_h_4` | 0.25 | 0.5 | 4 | boundary probe |
| `probe_20_1_2` | 0.20 | 1.0 | 2 | boundary probe |

`thin_half_n4` is a **contract cell**: per DRAFT §12 / VERIFICATION_LOG it cannot be
downgraded to characterization after seeing its number. Its failure of a frozen
criterion **is** a Tier 0 failure.

### 6.3 Scenarios

```text
S1  width sweep, 3 spread modes {a_only, c_only, symmetric}, width 0..24 (= n_peers),
    per cell. One frozen peer permutation per side per replicate; widths = nested
    prefixes (DRAFT §9.7). Width and mode are READ INDICES into one world, not seeds.
S2  latent_parent (M absent, shared parent) — separate seed namespace.
S3  coverage/resolution: n_profiled < 19 -> UNASSESSABLE (deterministic; already
    proven by unit tests test_s3_* and the assess_pair_selectivity gate).
```

### 6.4 Seed derivation (agreed; width/mode are read indices, NOT seeds)

```text
world_seed = int.from_bytes(
    SHA256("<sha>|V2A|Tier0|<grid_cell_id>|<replicate_index>".encode("utf-8")).digest()[:8],
    "big")                                    # S1 cells

world_seed = int.from_bytes(
    SHA256("<sha>|V2A|Tier0|latent_parent|<replicate_index>".encode("utf-8")).digest()[:8],
    "big")                                    # S2, separate namespace

# <sha>             = full 40-char lowercase hex of THIS package's pre-registration commit
# <grid_cell_id>    = a cell id from §6.2 (never contains width or mode)
# <replicate_index> = 0-based, in [0, R)
# one world_seed  -> one SyntheticWorld per (grid_cell_id, replicate);
#   width + spread_mode index into that one world (nested-prefix permutation, §9.7);
#   they never re-seed.
```

**DECISION (cold review): RNG instantiation.** Pin exactly how `world_seed` drives
`build_world(...)` — either `np.random.SeedSequence(world_seed).spawn(...)` for
independent A/C/background streams, or a single `default_rng(world_seed)` with a frozen
draw order. Must match `tier0_generator.build_world`'s contract.

### 6.5 Replicate count `R` — DECISION (cold review)

Development used R=10 (width) / 20 (latent), giving rate resolution 0.10 / 0.05.
Confirmatory needs finer resolution than the §7 thresholds it must decide.
**PROPOSED: R = 200** (resolution 0.005). Confirm or adjust cold.

### 6.6 Confirmatory ≠ development (hard)

Development seeds `0..9` / `0..19` are **burned** — never reused. Confirmatory seeds
come only from `<sha>` (§6.4), which does not exist until this package is committed.
`master_seed = 0` and the docs=60 grid from the PROPOSED_UNPILOTED design are line B
and do not apply here.

---

## §7. PASS / FAIL / STOP (PROPOSED forms + pilot evidence + decisions)

Each criterion is stated as a **form** + the **pilot evidence** + the **decision** left
for cold review. Thresholds are derived from the development pilot (DRAFT §12) and are
**not tuned to make any cell pass** — setting a threshold to a cell's observed value in
order to pass it is forbidden (card §1).

**Threshold comparisons are inclusive** (no interpretive slack; `thin_halfcorp` at side
C = 0.80 therefore passes full-width exactly at the boundary):

```text
width=0 pass:     risk_rate <= 0.10
full-width pass:  degradation_rate >= 0.80
S2 pass:          risk_rate_a >= 0.90 AND risk_rate_c >= 0.90
```

### 7.1 S1 — monotonicity (implementation invariant)

- **Form:** zero within-replicate monotonicity reversals, every cell, every mode.
- **Pilot:** 0 / 0 (all 11 cells).
- **PROPOSED:** threshold = exactly 0. A reversal is an **implementation defect**
  (DRAFT §9 makes risk monotone by construction) → retain run, fix defect, rerun — **not**
  a method failure.

### 7.2 S1 width=0 — empirical power (selectivity must hold with no spreading)

- **Form:** `P(RISK)` at width 0 ≤ θ₀ (per side, symmetric mode).
- **Pilot (symmetric, width 0, A/C):** `base` 0.0/0.0, `strong` 0.0/0.0,
  `thin` 0.1/0.1, `thin_halfcorp` 0.0/0.0, `thin_double` 0.0/0.1, `thin_half_n4` 0.0/0.0,
  probes 0.0/0.0 — **except `thin_noise4` 0.3/0.2**.
- **PROPOSED:** θ₀ = 0.10 on the **base regime** (`base`, `strong`, `thin`).
- **DECISION (cold review):** the exact θ₀ **and its scope**. If θ₀ = 0.10 is applied to
  every cell, `thin_noise4` (0.3) fails at width 0 — decide consciously whether
  `thin_noise4` is in scope for the width-0 power claim or is a documented high-noise
  boundary. Do **not** raise θ₀ merely to absorb it.

### 7.3 S1 full width — broad-mechanism degradation (THE load-bearing decision)

- **Form:** `P(RISK)` at full width (24) ≥ θ_full (per side, symmetric).
- **Pilot (symmetric, full width, A/C):**

  ```text
  base 0.9/1.0   thin 1.0/1.0   strong 0.9/1.0   thin_halfcorp 0.9/0.8
  thin_double 1.0/1.0   thin_noise4 1.0/0.9   probe_20_1_2 1.0/0.9      <- base regime: 0.8-1.0
  thin_half_n4 0.4/0.4   probe_20_h_2 0.5/0.5   probe_20_h_4 0.4/0.4    <- thin x half x high-noise
  probe_25_h_4 0.5/0.4                                                    corner: 0.4-0.5
  ```

- **PROPOSED (claim-driven, NOT tuned):** θ_full = **0.80**. The base regime clearly
  meets it (0.8–1.0); it expresses the actual claim "a broad mechanism degrades".
- **CONSEQUENCE, stated plainly:** under θ_full = 0.80 the **contract cell
  `thin_half_n4` (0.40) FAILS** → **Tier 0 FAILS** at that cell. This is the known
  low-power boundary (VERIFICATION_LOG OP1: the mediated statistic misses very thin,
  distant bridges). It is an **honest method-failure** (DRAFT §13) — logged as-is, no
  Tier 1, no post-hoc tuning.
- **DECISION (cold review) — yours, not mine:**
  1. Freeze θ_full from the claim (≈0.80) and accept that confirmatory Tier 0 is,
     on current evidence, **expected to fail at `thin_half_n4`** — a legitimate
     first-class result; **or**
  2. revisit the *claim/scope or the statistic* — but only via a **NEW card with a new
     pre-registration**, never by lowering θ_full to 0.40 here (that is tuning-to-pass,
     and reclassifying `thin_half_n4` to characterization is explicitly forbidden).
  I recommend option 1 (freeze the principled bar, let the honest result fall out). The
  choice is a governance decision and is **STOP** for me.

### 7.4 S2 — latent parent (domain-driven non-selectivity must degrade)

- **Form:** `P(RISK)` ≥ θ_S2 on both sides.
- **Pilot:** risk_rate_a = 1.00, risk_rate_c = 0.95.
- **PROPOSED:** θ_S2 = 0.90 (both sides). Pilot meets it. **DECISION:** confirm θ_S2.

### 7.5 S3 — coverage / resolution

- **Form:** 100% `UNASSESSABLE: INSUFFICIENT_RANK_RESOLUTION` for n_profiled < 19.
- **Status:** deterministic; already proven by `test_s3_*` and the gate arithmetic.
  PASS by construction — no stochastic estimate needed.

**Hard consequence (make explicit):**

```text
S3 / coverage:
If n_ontology < 19, the side is deterministically UNASSESSABLE before scoring.
If n_profiled < 19, the side is UNASSESSABLE after profile resolution.
Missing profiles can only reduce assessability, never increase it.
```

**Coverage boundary discovered by real-artifact validation (not an alarm, not a failure).**
Raynaud disease (`D011928`) has 11 one-parent-up branch peers under the frozen MeSH 2026
selector. Since V2-A uses `alpha_rank_nominal = 0.05`, the derived minimum profiled peer
count is `n_min = ceil(1 / alpha) - 1 = 19`. Therefore, Raynaud-side selectivity is
UNASSESSABLE at the ontology level before profile availability is even considered. This is
not a defect: it is the intended fail-closed coverage behavior. It does, however, define a
real scope boundary of V2-A at `ONE_PARENT_UP`: endpoints with small ontology neighborhoods
cannot receive a rank-selectivity verdict at this alpha/radius.

`UNASSESSABLE` is therefore not a rare abstraction — it can apply to canonical LBD cases
(Raynaud among them). Recorded here, before confirmatory, deliberately: better said now
than discovered after the fact.

---

## STOP / discipline reminders (carried loudly)

- **No confirmatory run before** this package is cold-reviewed and committed as the
  operational pre-registration.
- **Confirmatory seeds ONLY** from that commit's SHA (§6.4). Dev seeds `0..9`/`0..19`
  are burned; `master_seed=0` and the docs=60 design's SHA must never seed line A.
- **Code freezes before data.** `bridge.py` blob `1969f43d…` unchanged; any mechanism
  change is a new card.
- **`thin_half_n4` is a frozen contract cell.** Its failure = Tier 0 failure. No
  post-hoc reclassification.
- Even a PASS yields at most `EXPERIMENTAL_TIER0_ONLY`, shadow/audit-only. A real gate
  needs a separate Tier 1.

## Open inputs still REQUIRED before commit (governance — not mine)

1. ~~MeSH 2026 artifact URL + SHA-256~~ — **PRESENT & VERIFIED.** `desc2026.xml`
   (release 2026) is in place; its SHA-256 `9b034cad…cc5ba` recomputes and matches the
   tracked `desc2026.sha256`, which also records the source URL
   (`nlmpubs.nlm.nih.gov/.../desc2026.xml`) and `accessed_at 2026-07-05`. Recording
   these into §2.2 and committing (the freeze) remains governance. The 300 MB `.xml`
   itself is gitignored; the `.sha256` stays tracked as the provenance record.
2. Final numeric **freezes**: §6.5 `R`; §6.4 RNG instantiation; §7 θ₀ (+scope), θ_full
   (+the §7.3 decision), θ_S2.
3. **Cold-review sign-off** (§8), then commit — and only then confirmatory.

---

## §8. Cold-review protocol (sign-off gate before commit)

Cold review = an independent, fresh-eyes read of **this whole package as one object**,
BEFORE the commit that freezes it. Read it cold; do not skim; a partial read is not a
review. Every reviewer signs off in writing; any unresolved item blocks the commit.
Changing any threshold after sign-off **re-opens** the review.

### 8.1 Reviewers and what each one owns

**R1 — Methodologist / statistician** (owns §7):
- each criterion form is derived from the *claim*, not tuned to a cell's observed value;
- the §7.3 decision (θ_full and the fate of contract cell `thin_half_n4`) is made
  explicitly — **no** lowering θ_full to 0.40, **no** reclassifying `thin_half_n4`;
- θ₀ (+scope, incl. `thin_noise4`), θ_S2, and R give adequate resolution;
- S1 monotonicity is an implementation invariant (defect→fix, not method-fail); S3 is
  deterministic.

**R2 — Engineer / reproducibility** (owns §6.3–§6.6):
- seed derivation (§6.4) is unambiguous and reproducible: encoding, endianness,
  closed `<grid_cell_id>` set, `<replicate_index>` range, `<sha>` format;
- the RNG-instantiation decision matches `tier0_generator.build_world`;
- width/mode are read indices only; generator invariants (DRAFT §9) hold; confirmatory
  seeds are disjoint from the burned dev seeds `0..9` / `0..19`;
- code is frozen before data: `bridge.py` blob `1969f43d…`, gate and `peer_selection`
  unchanged.

**R3 — Provenance / data** (owns §0 and §2.2):
- MeSH: `desc2026.xml` sha256 matches the tracked `desc2026.sha256`; URL, release,
  accessed_at recorded; the artifact is the frozen source (gitignored, not pushed);
- the dev-pilot artifact matches the #8 anchors (0/0, 1.0/0.95, 0.4/0.4);
- corpus / date filters and the frozen `grid_cell_id` set are as stated.

**R4 — Governance owner (the human)** (owns the irreversible calls):
- approves the load-bearing §7.3 decision and all numeric freezes;
- confirms that committing this package as the operational pre-registration **is** the
  freeze;
- holds the STOP: no confirmatory run — and no seed derivation — before that commit.

### 8.2 Sign-off gate

```text
[x] R1 methodologist  — §7 forms, thresholds, §7.3 decision       (signed 2026-07-06)
[x] R2 engineer       — §6 seed rule, RNG, generator invariants   (signed 2026-07-06)
[x] R3 provenance     — MeSH sha match + URL, dev-pilot #8 anchors (signed 2026-07-06)
[x] R4 governance     — θ_full=0.80 kept incl. expected thin_half_n4 FAIL; commit = freeze (signed 2026-07-06)
```

All four checked → record the sign-off → **commit** the operational pre-registration →
its commit SHA becomes `<sha>` in §6.4 → **only then** derive confirmatory seeds and run.
Not before. A FAIL at confirmatory (e.g. `thin_half_n4` under θ_full) is logged as-is —
no Tier 1, no tuning.

---

## §9. Cold-review findings and resolutions (recorded 2026-07-06)

Cold review performed on the whole package as one object. **R3 (provenance) signed off**
(sha match, #8 anchors, line A). R1/R2 findings and their resolutions are below. The
resolutions are **governance-approved by R4** (the human, 2026-07-06) but remain
**PROPOSED — the freeze is the §8 commit, not applied here.** No threshold has been tuned to
a cell's value; no confirmatory seed is derived.

### 9.1 Decision record (approved; folds into §6/§7 at commit)

| Item | Approved resolution |
|---|---|
| §7.1 monotonicity | threshold = **0 exactly**; a reversal is an implementation defect (fix+rerun), not a method failure. |
| §7.2 θ₀ | **0.10**, scope = **base regime** {`base`,`strong`,`thin`}. `thin_noise4` (0.3 @ w0) is **characterization** (high-noise boundary), outside the width-0 power claim. θ₀ not raised to absorb it. |
| §7.3 θ_full | **0.80** (claim bar; base regime is 0.9–1.0). Fail-set at 0.80 = {**`thin_half_n4`**, `probe_20_h_2`, `probe_20_h_4`, `probe_25_h_4`}; `thin_halfcorp` passes only at the exact 0.80 boundary (side C = 0.80). **The frozen contract cell `thin_half_n4` (0.40) FAILS ⇒ confirmatory Tier 0 is expected to FAIL**, logged as-is. No lowering θ_full, no reclassifying `thin_half_n4`. |
| §7.4 θ_S2 | **0.90** both sides (pilot 1.00 / 0.95). |
| §7.5 S3 | deterministic; PASS by unit tests `test_s3_*` + gate arithmetic. **No coverage (<19) cell added to the grid** (M3); the Raynaud coverage boundary is documented (§7.5). |
| §6.5 R | **R = 200** (resolution 0.005), accepted **with the ~6–7 h real-V1 runtime** (dev R=10 ≈ 20 min × 20; E2). |
| §6.4 RNG | `build_world(seed=world_seed)` → the generator's **existing frozen** `np.random.default_rng(seed)` (verified: `tier0_generator.build_world` takes `seed: int`). No `SeedSequence.spawn` variant; the earlier "RNG DECISION" is closed (E1). |
| S1 modes (M1) | PASS criteria apply to **`symmetric` only**. `a_only` / `c_only` sweeps are **reported-only (characterization)** — no one-sided threshold is invented, since the dev pilot established none. |
| ties (M4) | conservative-tie behaviour is covered by deterministic `test_s3_*` / the gate; referenced, no separate stochastic criterion. |

### 9.2 Findings detail

- **R3 — provenance: PASS.** `desc2026.xml` sha256 == recorded == pinned `9b034cad…`;
  dev artifact matches #8 anchors (0/0, 1.0/0.95, 0.4/0.4); config confirms line A
  (docs=20, n_peers=24); URL + accessed_at recorded.
- **E1 (§6.4, resolved):** RNG was a false-open item — `build_world` already fixes it to
  `default_rng(seed)` with a frozen draw order. §6.4 simplifies to "pass `world_seed` as
  `build_world`'s `seed`".
- **E2 (§6.5, accepted):** R=200 on real V1 is a multi-hour run (~6–7 h). Approved with eyes
  open; if the run proves impractical, changing R re-opens the review (it changes §7
  resolution), not a silent edit.
- **E3 (§6.4, note):** `grid_cell_id`+`replicate` uniquely fixes a world **because
  cardinality is fixed at 24**. Consistent with M3 (no coverage cell). If a `<19` cell is
  ever added, `grid_cell_id` must encode cardinality — new card.
- **M1 (§7, resolved):** the grid generates 3 modes but only `symmetric` carries PASS
  criteria; `a_only`/`c_only` are reported-only. This removes the ambiguity flagged in
  review.
- **M2 (§7.3, resolved):** θ_full level fixes the whole fail-set, not just the contract
  cell — enumerated above. `thin_halfcorp` at the 0.80 knife-edge is recorded.
- **M3 (§7.5, resolved):** no coverage cell in the grid; S3 rests on deterministic tests +
  the documented real-artifact (Raynaud) boundary.
- **M4 (§7, resolved):** ties reference added.

### 9.3 Confirm before this feeds the commit

The load-bearing R4 calls recorded above are momentous — in particular **θ_full = 0.80 ⇒
contract cell `thin_half_n4` fails ⇒ confirmatory Tier 0 is expected to FAIL**, and the
**characterization** classifications (`thin_noise4`; `a_only`/`c_only`). These are recorded
as your approval (2026-07-06). If any differs from your intent, name it and it will be
corrected **before** any commit. Freeze remains the §8 commit — not applied here.

### 9.4 Sign-off (2026-07-06)

Cold review complete; the §9.3 confirmation is satisfied. R1–R4 signed off by the
governance owner, in the owner's words:

- **R1 Scope — OK.** Line A, docs=20, V2-A shadow/audit-only. Line B / docs=60 stays a
  separate future card.
- **R2 PASS — OK.** θ₀=0.10, θ_full=0.80, θ_S2=0.90. S3 deterministic, not generator.
  `thin_half_n4` stays a contract cell.
- **R3 Seeds/RNG — OK.** R=200 accepted. RNG = existing `default_rng(seed)`. Seed per
  (grid_cell, replicate), not per width; width/mode are reads from the one world.
- **R4 STOP — OK.** If confirmatory fails via `thin_half_n4`, that is a method failure /
  honest null — not an implementation defect and not grounds for tuning.

**θ_full = 0.80 stands, even though it implies an expected FAIL on `thin_half_n4`.** This is
the deliberate point where Axon shows methodological backbone: the threshold is not lowered
because a hard cell misses it, the cell is not moved to characterization, and the negative
result is logged as a first-class result.

**Status: cold-review ready / signed off.** The freeze is still the commit (§8): committing
this document as the operational pre-registration generates `<sha>` for §6.4 and is the
irreversible act — the governance owner's button, not performed here.
