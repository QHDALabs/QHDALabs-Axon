# Method card — ABC_BRIDGE (current implementation)

> Status is defined once in `RELATION_STATUS[RelationKind.ABC_BRIDGE]`
> (`src/axon/types.py`) and tabulated in [RELATION_STATUS.md](../../RELATION_STATUS.md).
> This card is narrative; the machine-checked status lives in the enum. The relation
> kind is `ABC_BRIDGE` — there is no "V1/V2" in the type identity; versioning of the
> implementation lives in this card's content.

**Status (from the enum):** `EXPERIMENTAL_CLOSED_ONLY` · validation `HELD_OUT_FAILED` ·
general use **no**.

## Purpose
Swanson closed discovery: connect two literatures A and C that share little surface
vocabulary, through intermediate B-terms present in both (low direct A-C similarity,
high B-mediated connectivity).

## Implemented?
Yes (current implementation). `AbcBridgeVerifier` with two explicit nulls
(random-literature-pair + shuffled-B over the common pool, B re-selected per replica),
a proximity gate (`direct_max`), and FDR. Registered for `RelationKind.ABC_BRIDGE`.

## Validated?
Validation state `HELD_OUT_FAILED`. In-sample CLOSED recovery of the pre-specified
Raynaud/fish-oil bridge works (q=0.0345). A pre-registered HELD-OUT test
(migraine/magnesium) did **not** generalize.

## Known failures
- **OP1 — limited power on thin mediation:** the true, very distant migraine/magnesium
  bridge does not beat its nulls (p≈0.12).
- **OP2 — the gate does not separate siblings:** a sibling literature (cluster headache)
  slipped under `direct_max=0.30` (direct_sim=0.283) and would be falsely accepted as a
  stronger bridge than the true target. In open discovery this is a systematic
  false-positive on closely-related literatures.

(See VERIFICATION_LOG.md, the held-out result entry, for numbers.)

## Allowed use
Per `RELATION_STATUS[RelationKind.ABC_BRIDGE].allowed_use`: closed discovery with a
pre-specified A-C pair.

## Forbidden use
Per `RELATION_STATUS[RelationKind.ABC_BRIDGE].forbidden_use`: open discovery / scanning
many candidate C's (would mass-produce false bridges via the sibling false-positive).

## Next validation
A redesign addressing OP1 (thin-mediation power) and OP2 (sibling separation) is a
SEPARATE research round with its own pre-registration and held-out test — not part of
this implementation, and not drafted here. The held-out card for migraine/magnesium is
spent; a redesign needs a new held-out case.
