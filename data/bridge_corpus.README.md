# ABC-bridge corpus — provenance

`bridge_corpus.json` is a FROZEN, pre-1986 PubMed corpus for the ABC-bridge recovery
test (Swanson's Raynaud / fish-oil closed discovery). Committed so the pipeline is
reproducible without network access.

## Source

Fetched from [NCBI PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
by [`scripts/fetch_bridge_corpus.py`](../scripts/fetch_bridge_corpus.py).

| Field | Value |
|---|---|
| Fetch date | 2026-06-25 |
| Date filter | `1900:1985[dp]` (pre-1986 — before Swanson's 1986 discovery) |
| Records | 717, **all with MeSH** |
| Substrate | MeSH descriptors (controlled vocabulary) |

### Why pre-1986

Swanson published the Raynaud / fish-oil connection in 1986. Restricting to
publications **before 1986** makes this a genuine CLOSED discovery: papers written
after the discovery may explicitly link the two literatures, which would leak the
answer (a direct A–C link) into a test that must run through intermediate B-terms.

### Literatures (roles)

| Label | Role | Query (AND `1900:1985[dp]`) |
|---|---|---|
| `raynaud` | A (discovery) | `Raynaud` |
| `fish_oil` | C (discovery) | `"fish oil" OR "fish oils" OR eicosapentaenoic OR "dietary fish"` |
| `scleroderma` | control (directly-similar) | `scleroderma` |
| `dental_caries` | control (unrelated) | `"dental caries"` |
| `asthma, epilepsy, glaucoma, psoriasis, tuberculosis, hepatitis, appendicitis, cataract` | background | one focused disease each |

Background literatures (IDF + random-literature-pair null) are **disjoint** from A/C
and the controls — A and C never inflate their own IDF.

## Honesty / scope

- B-terms are **discovered by the method**, never assigned here. Only A/C/control/
  background literature *labels* are assigned.
- Each record carries its PMID (`source`), so every downstream claim traces back to
  the original article. MeSH and titles are openly accessible via the E-utilities API.
- This corpus is illustrative input for a **methodological validation** (does the
  method recover a known bridge?), **not** a scientific claim about these papers.
- Re-running `fetch_bridge_corpus.py` may return different records as PubMed is
  re-indexed; the committed JSON is the canonical artifact.
