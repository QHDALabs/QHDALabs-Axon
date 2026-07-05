"""Validate the frozen production MeSH artifact against our Decision-1 parser/selector.

Fail-closed, offline, one-shot. It: (1) recomputes the SHA-256 of the MeSH descriptor
file and checks it against the recorded ``.sha256`` provenance record; (2) stream-parses
the whole file with the production parser (:func:`parse_descriptor_file`); (3) for the
pinned release, asserts the record count and the known shared-tree-number collisions;
(4) runs one-parent-up selection on a known endpoint (Raynaud Disease) and prints a peer
summary. Any mismatch exits non-zero.

The artifact itself is gitignored (~300 MB); run this locally against a downloaded copy:

    python scripts/validate_mesh_artifact.py --xml desc2026.xml --sha256 desc2026.sha256
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys

from axon.verification.peer_selection import parse_descriptor_file, select_one_parent_up

# Pinned expectations for the MeSH 2026 descriptor release.
PINNED_SHA256 = "9b034cad8bbd4d8d1ef43816d6fd78d33fada52eddff2a0b4455b1fca35cc5ba"
PINNED_RECORD_COUNT = 31110
PINNED_COLLISIONS = {
    "B03.300.390.400.001": ("D047991", "D048013"),
    "B03.510.415.400.001": ("D047991", "D048013"),
    "B03.510.460.410.001": ("D047991", "D048013"),
}
RAYNAUD_UI = "D011928"

_HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def _sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _recorded_sha256(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        match = _HEX64.search(handle.read().lower())
    if match is None:
        raise SystemExit(f"FAIL: no 64-hex sha256 found in {path!r}")
    return match.group(0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the MeSH descriptor artifact.")
    parser.add_argument("--xml", default="desc2026.xml")
    parser.add_argument("--sha256", default="desc2026.sha256")
    args = parser.parse_args()
    xml_path: str = args.xml
    sha_path: str = args.sha256

    recorded = _recorded_sha256(sha_path)
    computed = _sha256_of(xml_path)
    print(f"recorded sha256:  {recorded}")
    print(f"computed sha256:  {computed}")
    if computed != recorded:
        raise SystemExit("FAIL: computed sha256 does not match the recorded provenance")
    print("OK: artifact integrity matches its .sha256 record")

    tree = parse_descriptor_file(xml_path)
    n_descriptors = len(tree.uis())
    collisions = tree.tree_number_collisions()
    print(f"descriptors parsed: {n_descriptors}")
    print(f"shared tree-number collisions: {len(collisions)}")
    for tree_number, owners in collisions.items():
        print(f"  {tree_number} -> {list(owners)}")

    if computed == PINNED_SHA256:
        if n_descriptors != PINNED_RECORD_COUNT:
            raise SystemExit(
                f"FAIL: expected {PINNED_RECORD_COUNT} descriptors, got {n_descriptors}"
            )
        if collisions != PINNED_COLLISIONS:
            raise SystemExit("FAIL: collisions differ from the pinned MeSH 2026 set")
        print("OK: record count and known collisions match the pinned MeSH 2026 release")
    else:
        print("NOTE: sha differs from the pinned MeSH 2026 release; skipping pinned asserts")

    endpoint = tree.descriptor(RAYNAUD_UI)
    peers = select_one_parent_up(tree, RAYNAUD_UI)
    print(f"\nendpoint {RAYNAUD_UI} ({endpoint.name}) positions: {list(endpoint.tree_numbers)}")
    print(f"one-parent-up peers: {len(peers)}")
    print(f"  sample: {list(peers[:10])}")
    print("\nVALIDATION OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
