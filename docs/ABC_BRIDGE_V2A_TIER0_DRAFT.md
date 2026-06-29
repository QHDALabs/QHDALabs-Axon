# ABC_BRIDGE V2-A - Tier 0 Protocol Draft

**Status:** `DRAFT - NOT FROZEN`

This document is a design and pilot protocol. It is not yet a pre-registration.
It becomes a pre-registration only after the development pilot is complete, the
confirmatory grid and pass criteria are written numerically, and the final document
is committed before any confirmatory seed is executed.

## 1. Claim

V2-A is a one-sided, trust-removing audit. It does not identify mediation,
siblings, confounding, or true bridges. It asks whether pair selectivity has been
demonstrated against pre-specified endpoint substitutions.

```text
RISK           = PAIR_SELECTIVITY_NOT_DEMONSTRATED
NOT_DETECTED   = pair selectivity demonstrated for this side;
                 no trust is added
UNASSESSABLE   = coverage or rank resolution is insufficient;
                 fail closed
```

V2-A is shadow-only through Tier 0. It cannot modify a real verification result.

## 2. Limits

- **L1 - Co-occurrence non-identifiability.** A domain marker and a mechanism can
  be observationally identical on term profiles.
- **L2 - Ontology-relative construct drift.** Every verdict is relative to the
  frozen MeSH release; applying a later ontology to a historical corpus is
  modern-ontology-assisted.
- **L3 - Broad-mechanism non-identifiability.** A genuine mechanism shared across
  branch peers is degraded together with domain-driven non-selectivity. V2-A
  validates only pair-selective candidates.
- **L4 - Exchangeability assumption.** The rank-test error interpretation is
  nominal and conditional on branch-peer exchangeability. MeSH siblinghood does
  not guarantee statistical exchangeability.

## 3. Deterministic peer selection

Production peer selection uses a frozen MeSH descriptor XML artifact.

```text
for every tree position of endpoint X:
    parent = immediate parent of that tree position
    branch = every descendant descriptor under parent
    remove X and every descriptor in X's descendant subtree
union branches across all tree positions
deduplicate by DescriptorUI
```

`ONE_PARENT_UP` therefore means sibling **subgraphs**, not only immediate sibling
children. The rule never ascends to a grandparent.

Two counts remain separate:

```text
n_ontology = descriptors returned by the ontology rule
n_profiled = returned descriptors with a valid V1 literature profile
n_missing  = n_ontology - n_profiled
n_rank     = n_profiled
```

Missing profiles are not converted to zero scores. A valid profile whose fresh
pair score is genuinely zero remains in the rank denominator.

## 4. Frozen V1 dependency

Every original and substituted pair is scored by a fresh call to:

```python
propose_bridge(
    context,
    a_label,
    c_label,
    stoplist=DEFAULT_MESH_STOPLIST,
    max_df=0.5,
    idf_min=1.0,
)
```

The current V1 blob is `1969f43d8fb172f40bc4c878d519f406ac7499f2`.
V2-A does not modify `bridge.py`, reuse the original B set, call the V1 verifier,
or recompute V1 nulls. It reads only the fresh candidate's mediated score.

## 5. Rank assessment

For one endpoint side:

```text
m0 = mediated(A, C)
D  = fresh mediated scores after substituting each profiled peer
n  = |D|
k  = count(d >= m0 for d in D)       # ties count against selectivity
p_rank_nominal = (k + 1) / (n + 1)
alpha_rank_nominal = 0.05
```

```text
n_min = ceil(1 / alpha_rank_nominal) - 1 = 19
n < 19  -> UNASSESSABLE: INSUFFICIENT_PROFILED_PEERS
p <= .05 -> NOT_DETECTED
p >  .05 -> RISK
```

The A and C distributions are never merged. No marginal-mass normalization is
applied.

## 6. Aggregation

No degradation requires both sides to demonstrate selectivity. Risk on either
side is sufficient to degrade.

```text
A NOT_DETECTED + C NOT_DETECTED -> NO_DEGRADATION
A RISK                           -> PAIR_SELECTIVITY_NOT_DEMONSTRATED_A
C RISK                           -> PAIR_SELECTIVITY_NOT_DEMONSTRATED_C
A RISK + C RISK                  -> PAIR_SELECTIVITY_NOT_DEMONSTRATED_BOTH
any UNASSESSABLE without RISK    -> COVERAGE degradation for that side
```

This is an intersection-union test for no degradation and OR aggregation for
risk. Alpha is not split between sides.

## 7. Exchangeability audit

The following are emitted but never used to change the verdict:

```text
document count
total profile mass
mean MeSH descriptors per document
publication year range and median
```

## 8. Test boundaries

```text
Layer 0 - direct fixtures
          mediated arithmetic, rank, ties, n_min, aggregation

Layer 1 - frozen real-MeSH fixtures
          one parent, sibling subgraphs, polyhierarchy, subtree exclusion,
          DescriptorUI deduplication, traversal-order independence

Layer 2 - emergent Tier 0 generator
          paired width curves and latent-parent behavior

Layer 3 - one wiring test
          real MeSH fragment -> PeerSelector -> PeerSet -> synthetic profiles
          -> selectivity annotation
```

Only Layer 2 is Tier 0 behavioral evidence. Layer 3 checks integration only.

## 9. Generator definition

The generator emits documents and MeSH assignments. The real `LiteratureStore`
computes unnormalized profiles:

```text
w_L[t] = mean term count over L documents * background IDF[t]
```

Term families:

```text
P_A, P_C  endpoint-domain terms
M         cross-literature mechanism terms
U_X       terms private to literature X
G         generic terms
N         noise terms
```

Documents are generated by independent term-inclusion draws. These are additive
counts, not a normalized mixture. Adding one family never removes another family.

Generator invariants:

1. Background documents and background-derived IDF are fixed for every width in
   one replicate.
2. Background is disjoint from A, C, and all peers.
3. Every M term has fixed positive background document frequency, with
   `0 < background_df_ratio[M] <= 0.5` and `idf[M] >= 1.0`.
4. Every G term occurs above `max_df=0.5`, guaranteeing generic filtering.
5. Width never adds documents. M is injected into existing peer documents.
6. All non-M assignments remain byte-identical across widths.
7. A single frozen random peer permutation is generated per side and replicate.
   Widths are nested prefixes of that permutation.
8. A, C, their M assignments, and `m0` remain fixed across the width sweep.

Under these invariants, adding width can only increase one newly exposed peer's
mediated score. Within-replicate rank risk is therefore monotone by construction;
any reversal is an implementation defect.

## 10. Generator scenarios

### S1a - one-sided spreading

Two mirrored sweeps:

```text
S1a-A: width_A varies; width_C = 0
S1a-C: width_A = 0; width_C varies
```

This exercises one-sided risk and OR aggregation.

### S1b - symmetric spreading

```text
width_A = width_C = width
```

At width zero, both sides should demonstrate selectivity in the calibrated pilot
regime. As width expands, side risks and aggregate degradation are reported
separately.

### S2 - latent parent

A, C, and both peer branches share P. M is absent. The expected construct-level
result is pair selectivity not demonstrated.

### S3 - coverage and resolution

Profiled peer counts below 19 must produce `UNASSESSABLE` deterministically.

## 11. Pilot firewall

The current numeric generator configuration and seeds are development-only.

```text
Phase 1 - generator pilot
    visible development seeds
    calibrate term-family sizes, inclusion rates, noise regimes, document counts
    output is NOT Tier 0 evidence

Phase 2 - freeze
    write exact numeric grid
    write numeric pass criteria
    write untouched confirmatory seed derivation
    cold review
    commit pre-registration

Phase 3 - confirmatory Tier 0
    execute once
    log result as-is
```

Development seeds can never appear in the confirmatory run. Confirmatory seeds
must not be executed, previewed, or replaced before the pre-registration commit.

## 12. Pass-criterion requirements before freezing

The final pre-registration must replace every qualitative phrase with an exact
rule. At minimum:

```text
S1: zero within-replicate monotonicity reversals
S1 width=0: one pre-specified empirical power requirement
S1 full width: one pre-specified broad-mechanism degradation requirement
S2: one pre-specified latent-parent degradation requirement
S3: 100% UNASSESSABLE for n_profiled < 19
```

Only empirically unavoidable thresholds may remain. Their values and rationale
must come from the development pilot and be frozen before confirmatory execution.

## 13. STOP

An implementation defect is different from a method failure:

```text
implementation defect:
    code demonstrably violates this frozen specification
    retain the failed run in the audit trail
    fix only the defect
    rerun the complete confirmatory grid with unchanged inputs

method failure:
    code conforms to the specification but a frozen pass criterion fails
    STOP
    no Tier 1
    any redesign requires a new card
```

On Tier 0 pass, status becomes `EXPERIMENTAL_TIER0_ONLY`. The module remains
shadow/audit-only. Only a separate independent Tier 1 can authorize real gating.

## 14. Still unresolved in this draft

The development pilot must determine, without using confirmatory seeds:

```text
exact term-family sizes
document counts and imbalance cells
P, M, U, G, and N inclusion rates
LOW and MEDIUM noise definitions
replicate count
targeted thin-M x imbalance and thin-M x noise cells
numeric endpoint and S2 pass criteria
confirmatory seed derivation
MeSH 2026 artifact URL and SHA-256
```

Until these fields are filled and cold-reviewed, this document remains a draft.

The targeted `thin M x half-size peers x medium noise` interaction is a contract
cell. It cannot be downgraded to characterization-only based on development output.
