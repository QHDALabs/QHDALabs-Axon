"""
One-off data-prep (NOT part of the `axon` package): fetch a FROZEN, pre-1986
PubMed corpus for the ABC-bridge recovery test, and commit it to data/.

Why pre-1986: Swanson's Raynaud/fish-oil discovery is from 1986. Restricting to
publications before 1986 makes this a genuine CLOSED discovery — papers written
after the discovery may explicitly link the two literatures (A-C), which would
leak the answer into the test. Pre-1986 there is no such direct link; any
connection must run through intermediate B-terms.

Substrate: MeSH descriptors (controlled vocabulary). Pre-1986 MEDLINE records
often lack abstracts but carry MeSH, so MeSH is the robust, cleaner B substrate.
The B-terms are DISCOVERED by the method; only the A/C/control/background literature
labels are assigned here (never the B-terms).

Reproducibility: the committed JSON is the canonical artifact; re-running may
return different records as PubMed is re-indexed. Records carry their PMID.

Usage:  python scripts/fetch_bridge_corpus.py
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
DATE = "1900:1985[dp]"
OUT = Path(__file__).resolve().parent.parent / "data" / "bridge_corpus.json"

# literature label -> (role, PubMed query). Roles: a / c / control / background.
# A and C are the discovery literatures; controls are negatives; background is a
# pool of focused, unrelated biomedical literatures (IDF + random-pair null),
# DISJOINT from A/C/controls.
LITERATURES = {
    "raynaud":      ("a",          'Raynaud'),
    "fish_oil":     ("c",          '"fish oil" OR "fish oils" OR eicosapentaenoic OR "dietary fish"'),
    "scleroderma":  ("control_sim", 'scleroderma'),          # clinically near Raynaud -> high direct sim
    "dental_caries": ("control_rand", '"dental caries"'),    # unrelated -> no bridge
    # background: focused, unrelated diseases
    "asthma":       ("background", 'asthma'),
    "epilepsy":     ("background", 'epilepsy'),
    "glaucoma":     ("background", 'glaucoma'),
    "psoriasis":    ("background", 'psoriasis'),
    "tuberculosis": ("background", 'tuberculosis'),
    "hepatitis":    ("background", 'hepatitis'),
    "appendicitis": ("background", 'appendicitis'),
    "cataract":     ("background", 'cataract'),
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
        print(f"{label:14s} ({role:13s}): {len(recs)} records, {with_mesh} with MeSH")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(corpus)} records -> {OUT}")


if __name__ == "__main__":
    main()
