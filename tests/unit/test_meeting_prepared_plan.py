"""Betterment capture C5: which Results a meeting prepares.

The plan reads what the meeting SAID: a meeting that asks for an ADR gets
the ADR drafter, one that names a stakeholder update gets the update
drafter, one that asks for a diagram gets the diagram. A meeting that asks
for none prepares only the follow-up (the local draft, not a plugin).
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.meeting_plugins import prepared_plan

SEED = Path(__file__).resolve().parents[2] / "docs" / "internal" / "betterment" / "capture" / "rig" / "seed"


def test_an_adr_action_schedules_the_adr_drafter() -> None:
    assert prepared_plan("Me: Jun, please write the ADR for this by Wednesday.") == ["adr_drafter"]


def test_the_architecture_review_schedules_the_adr_and_the_update() -> None:
    text = (SEED / "architecture-review.txt").read_text(encoding="utf-8")
    assert prepared_plan(text) == ["adr_drafter", "stakeholder_update_drafter"]


def test_a_diagram_request_schedules_the_diagram() -> None:
    assert prepared_plan("Mira: Can someone draw the architecture before Friday?") == ["mermaid_architecture"]


def test_a_meeting_that_asks_for_no_draft_prepares_none() -> None:
    for name in ("payments-platform-sync.txt", "one-on-one-theo.txt"):
        assert prepared_plan((SEED / name).read_text(encoding="utf-8")) == [], name
    # "adr" inside a word is not an ADR.
    assert prepared_plan("The address book import is done.") == []
