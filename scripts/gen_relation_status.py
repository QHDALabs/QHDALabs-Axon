"""
Generate RELATION_STATUS.md from the single source of truth (RELATION_STATUS in
src/axon/types.py). Run after changing the enum:

    python scripts/gen_relation_status.py

tests/test_relation_status.py asserts the committed file matches this output, so the
table can never silently drift from the enum.
"""

from __future__ import annotations

from pathlib import Path

from axon.types import render_relation_status_markdown

OUT = Path(__file__).resolve().parent.parent / "RELATION_STATUS.md"


def main() -> None:
    OUT.write_text(render_relation_status_markdown(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
