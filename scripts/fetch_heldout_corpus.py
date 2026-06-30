"""
One-off data-prep (NOT part of the `axon` package): fetch a FROZEN, pre-1988 PubMed
corpus for the HELD-OUT ABC-bridge test (migraine / magnesium), committed to data/.

Held-out: the verifier is frozen (see the pre-registration entry in
VERIFICATION_LOG.md). This script only builds the corpus; it changes nothing in the
statistic. Date filter 1900:1987[dp] is strictly pre-1988 — before Swanson's
migraine/magnesium publication — so no post-discovery A-C link can leak.

Substrate: MeSH descriptors (same as the Raynaud run). B-terms are discovered by the
method; only literature labels are assigned here.

Usage:  python scripts/fetch_heldout_corpus.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
DATE = "1900:1987[dp]"
OUT = Path(__file__).resolve().parent.parent / "data" / "heldout_corpus.json"

# literature label -> (role, PubMed query). Disjoint background pool, same as the
# Raynaud run for comparability.
LITERATURES = {
    "migraine":        ("a",            'migraine'),
    "magnesium":       ("c",            'magnesium'),
    "cluster_headache": ("control_sim",  '"cluster headache"'),   # same headache class -> high direct sim
    "dental_caries":   ("control_rand", '"dental caries"'),       # unrelated -> no bridge
    "asthma":          ("background",   'asthma'),
    "epilepsy":        ("background",   'epilepsy'),
    "glaucoma":        ("background",   'glaucoma'),
    "psoriasis":       ("background",   'psoriasis'),
    "tuberculosis":    ("background",   'tuberculosis'),
    "hepatitis":       ("background",   'hepatitis'),
    "appendicitis":    ("background",   'appendicitis'),
    "cataract":        ("background",   'cataract'),
}
RETMAX = 60


def _get(url: str) -> bytes:
    data: bytes = urllib.request.urlopen(url, timeout=60).read()
    return data


def esearch(term: str, retmax: int) -> list[str]:
    q = urllib.parse.urlencode(
        {"db": "pubmed", "term": f"({term}) AND {DATE}", "retmax": retmax, "retmode": "json"}
    )
    data = json.loads(_get(BASE + "esearch.fcgi?" + q))
    return list(data["esearchresult"]["idlist"])


def efetch(ids: list[str]) -> list[dict[str, object]]:
    q = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
    root = ET.fromstring(_get(BASE + "efetch.fcgi?" + q))
    records: list[dict[str, object]] = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID") or ""
        year = art.findtext(".//PubDate/Year") or ""
        title = (art.findtext(".//ArticleTitle") or "").strip()
        mesh = [m.text for m in art.findall(".//MeshHeading/DescriptorName") if m.text]
        abstract = " ".join(
            (t.text or "") for t in art.findall(".//Abstract/AbstractText")
        ).strip()
        if pmid and mesh:
            records.append({"pmid": pmid, "year": year, "title": title,
                            "mesh": mesh, "abstract": abstract})
    return records


def main() -> None:
    corpus: list[dict[str, object]] = []
    for label, (role, term) in LITERATURES.items():
        ids = esearch(term, RETMAX)
        time.sleep(0.4)
        recs = efetch(ids) if ids else []
        time.sleep(0.4)
        for r in recs:
            corpus.append({
                "id": r["pmid"],
                "source": f"PMID:{r['pmid']}",
                "literature": label,
                "role": role,
                "year": r["year"],
                "title": r["title"],
                "mesh": r["mesh"],
                "text": r["abstract"],
            })
        with_mesh = sum(1 for r in recs if r["mesh"])
        print(f"{label:16s} ({role:13s}): {len(recs)} records, {with_mesh} with MeSH")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(corpus)} records -> {OUT}")


if __name__ == "__main__":
    main()
