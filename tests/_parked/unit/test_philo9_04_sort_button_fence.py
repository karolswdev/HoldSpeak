"""PHILO-9-04: the sort headers are the library Button -- a structural fence.

UX-CANON §A.1: every verb is the library Button; a raw ``<button>`` is a
bounce. The glass (tests/e2e/test_philo9_04_desk_debts_glass.py) reads the
rendered class at 1440 and 393; this fence reads the species' source, so a
mutation that re-adds a raw ``<button>`` to the sortable table turns it red
without a browser (the second test proves the fence can fail).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPECIES = REPO / "web/src/desk/components/DeskSortableTable.tsx"

_RAW = re.compile(r"<button\b")


def raw_buttons(source: str) -> list[int]:
    """Line numbers of raw lower-case ``<button`` elements in a TSX source."""
    return [i for i, line in enumerate(source.splitlines(), 1) if _RAW.search(line)]


def test_the_sortable_table_has_no_raw_button() -> None:
    source = SPECIES.read_text()
    assert raw_buttons(source) == [], f"raw <button> in {SPECIES.name}: lines {raw_buttons(source)}"
    assert "<Button" in source and 'from "../../components/signal/Signal"' in source


def test_a_raw_button_mutation_turns_the_fence_red() -> None:
    source = SPECIES.read_text()
    mutated = source.replace("<Button", '<button type="button"', 1)
    assert mutated != source
    assert raw_buttons(mutated), "the fence did not see a re-added raw <button>"
