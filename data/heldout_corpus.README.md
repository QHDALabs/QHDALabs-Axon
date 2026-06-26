# Held-out ABC-bridge corpus — provenance

`heldout_corpus.json` is a FROZEN, pre-1988 PubMed corpus for the HELD-OUT ABC-bridge
test (migraine / magnesium — Swanson's second documented bridge, 1988). Committed so
the test is reproducible without network access.

## Source

Fetched from [NCBI PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
by [`scripts/fetch_heldout_corpus.py`](../scripts/fetch_heldout_corpus.py).

| Field | Value |
|---|---|
| Fetch date | 2026-06-26 |
| Date filter | `1900:1987[dp]` (strictly pre-1988 — before Swanson's migraine/magnesium publication) |
| Records | 710, **all with MeSH** |
| Substrate | MeSH descriptors |

### Why pre-1988

Swanson published the migraine / magnesium connection in 1988. Restricting to
publications **before 1988** keeps this a genuine held-out closed discovery: no
post-discovery paper can leak a direct A–C link.

### Literatures (roles)

| Label | Role | Query (AND `1900:1987[dp]`) |
|---|---|---|
| `migraine` | A (discovery) | `migraine` |
| `magnesium` | C (discovery) | `magnesium` |
| `cluster_headache` | control (directly-similar) | `"cluster headache"` |
| `dental_caries` | control (unrelated) | `"dental caries"` |
| `asthma, epilepsy, glaucoma, psoriasis, tuberculosis, hepatitis, appendicitis, cataract` | background | one focused disease each |

Background literatures (IDF + random-literature-pair null) are **disjoint** from A/C
and the controls. Same background pool as the Raynaud run, for comparability.

## Scope

This corpus is held-out validation input. The verifier was frozen and pre-registered
before this corpus was fetched (see `VERIFICATION_LOG.md`). B-terms are discovered by
the method; only literature labels are assigned here. The recorded outcome is a
**non-recovery** plus a control-separation failure — logged as-is, no tuning.
