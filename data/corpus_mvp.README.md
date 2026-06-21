# MVP corpus — provenance

`corpus_mvp.json` is a small, fixed corpus of **real, openly available** abstracts
used for the MVP end-to-end run (proximity relations, random-pair null, FDR). It is
committed so the pipeline is reproducible without network access.

## Source

Fetched from the [arXiv API](https://info.arxiv.org/help/api/index.html) by
[`scripts/fetch_corpus.py`](../scripts/fetch_corpus.py).

| Field | Value |
|---|---|
| Fetch date | 2026-06-21 |
| Records | 40 (20 + 20) |
| Domain A | `astrophysics` — arXiv category `astro-ph.CO` |
| Domain B | `neuroscience` — arXiv category `q-bio.NC` |
| Ordering | `sortBy=submittedDate&sortOrder=descending`, then sorted by arXiv id within each domain |

Two deliberately distinct domains so that **cross-domain** lexical proximity is
actually testable (and mostly expected to be null).

## Record schema

```json
{
  "id": "2606.19452v1",
  "source": "arXiv:2606.19452v1",
  "domain": "astrophysics",
  "category": "astro-ph.CO",
  "title": "…",
  "text": "… abstract …"
}
```

`text` is the abstract (whitespace-normalized). `title` is kept as metadata.

## Honesty / licensing

- Abstracts are reproduced as fetched; **none are invented**. Each record carries its
  arXiv id as `source`, so every downstream claim traces back to the original paper.
- arXiv abstracts and metadata are openly accessible via the public API. This corpus
  is used only as illustrative input for an engineering demo — **no scientific claim**
  is made about these papers or any relation among them.
- Re-running `fetch_corpus.py` may return newer papers (arXiv grows); the committed
  JSON, not a live fetch, is the canonical artifact the pipeline reads.
