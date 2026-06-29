"""
One-off data-prep tool (NOT part of the `axon` package; never imported by it).

Fetches a small, fixed corpus of real, openly available abstracts from the arXiv
API across two distinct domains, so cross-domain lexical proximity is actually
testable, and writes them to ``data/corpus_mvp.json``.

Reproducibility: the committed JSON is the canonical artifact. This script
documents exactly how it was produced. Re-running it may return newer papers
(arXiv grows), so the committed file — not a live fetch — is what the pipeline
reads. Record the fetch date in data/corpus_mvp.README.md.

Honesty: we do not invent abstracts. Every record carries its arXiv id as source.
Only metadata + abstract text is stored (openly available via the arXiv API).

Usage:
    python scripts/fetch_corpus.py
"""

from __future__ import annotations

import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
API = "http://export.arxiv.org/api/query"

# (arXiv category, human-readable domain label, how many to keep)
QUERIES = [
    ("astro-ph.CO", "astrophysics", 20),
    ("q-bio.NC", "neuroscience", 20),
]

OUT = Path(__file__).resolve().parent.parent / "data" / "corpus_mvp.json"


def _normalize(text: str) -> str:
    return " ".join(text.split())


def fetch_category(cat: str, domain: str, n: int) -> list[dict[str, str]]:
    # sortBy=submittedDate gives a stable-ish, well-defined ordering at fetch time.
    url = (
        f"{API}?search_query=cat:{cat}"
        f"&start=0&max_results={n + 5}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read().decode("utf-8", "replace")
    root = ET.fromstring(raw)

    records: list[dict[str, str]] = []
    for entry in root.findall(f"{ATOM}entry"):
        arxiv_url = (entry.findtext(f"{ATOM}id") or "").strip()
        arxiv_id = arxiv_url.rsplit("/", 1)[-1]  # e.g. 2406.01234v1
        title = _normalize(entry.findtext(f"{ATOM}title") or "")
        abstract = _normalize(entry.findtext(f"{ATOM}summary") or "")
        if not arxiv_id or not abstract:
            continue
        records.append(
            {
                "id": arxiv_id,
                "source": f"arXiv:{arxiv_id}",
                "domain": domain,
                "category": cat,
                "title": title,
                "text": abstract,
            }
        )
        if len(records) >= n:
            break

    # Deterministic order within a domain: by arXiv id.
    records.sort(key=lambda r: r["id"])
    return records


def main() -> None:
    corpus: list[dict[str, str]] = []
    for i, (cat, domain, n) in enumerate(QUERIES):
        if i > 0:
            time.sleep(3)  # be polite to the arXiv API
        got = fetch_category(cat, domain, n)
        print(f"{cat} ({domain}): {len(got)} abstracts")
        corpus.extend(got)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(corpus)} records -> {OUT}")


if __name__ == "__main__":
    main()
