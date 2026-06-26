# Method card — PROXIMITY (lexical MVP)

> Status is defined once in `RELATION_STATUS[RelationKind.PROXIMITY]`
> (`src/axon/types.py`) and tabulated in [RELATION_STATUS.md](../../RELATION_STATUS.md).
> This card is narrative; the machine-checked status lives in the enum.

**Status (from the enum):** `SAFE_LOW_YIELD` · validation `SAFE_NO_DISCOVERY_CLAIM` ·
general use **yes**.

## Purpose
Propose and verify lexical/distributional proximity between documents (TF-IDF cosine),
as a relation that survives an explicit null with multiple-testing control.

## Implemented?
Yes. `RandomPairProximityVerifier` (empirical random-pair null) + Benjamini-Hochberg
FDR. Featurizer is swappable (`TfidfFeaturizer` today).

## Validated?
Validation state `SAFE_NO_DISCOVERY_CLAIM`: methodologically clean and calibrated —
fail-closed, honest null, FDR-controlled; no false positives demonstrated. It makes
**no** out-of-sample discovery claim (on a small corpus it correctly surfaces little).
This is the SAFER mechanism, not a lower-quality one.

## Known failures / limits
Low yield: on small corpora, with FDR across all pairs, it may surface nothing. That
is by design (rejecting false positives), not a defect.

## Allowed use
Per `RELATION_STATUS[RelationKind.PROXIMITY].allowed_use`: any discovery, open or
closed.

## Forbidden use
Per `RELATION_STATUS[RelationKind.PROXIMITY].forbidden_use`: none.

## Next validation
Optional: richer featurizers (embeddings) behind the same null contract; yield studies
on larger corpora. No safety blocker.
