"""PHILO-4-04 atlas contract for the ratified triaged headline walk.

The case must create brief material through production routes, exercise both
Arrival shelf verbs on the face, and retain a producer-backed identity for the
parent walk to inspect.  The final observation is the static handled receipt;
headline/date retention is checked from the generated brief id's DB snapshot
by ``scripts/graph_walk.py``.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase3.json"
CASE_ID = "case.philo404.arrival_triaged_headline.all_handled"
LATEST = "/api/brief/latest"


def _case() -> dict:
    atlas = json.loads(ATLAS.read_text())
    return next(case for case in atlas["cases"] if case["id"] == CASE_ID)


def test_triaged_headline_case_is_a_two_row_face_walk() -> None:
    case = _case()

    assert case["applicability"] == "applicable"
    assert sorted(case["viewports"]) == [393, 1440]
    assert case["expected"]["observe_at"] == "[data-testid=arrival-brief-handled]"
    assert case["expected"]["predicate"] == {
        "kind": "readable_text",
        "value": "ALL 2 HANDLED",
    }

    setup = case["setup"]
    decision_creates = [
        step for step in setup
        if step.get("kind") == "api"
        and step.get("method") == "POST"
        and step.get("path") == "/api/decisions"
    ]
    assert [step["body"]["status"] for step in decision_creates] == [
        "proposed",
        "proposed",
    ]
    assert [step["body"]["title"] for step in decision_creates] == [
        "Graph walk triage headline Ack",
        "Graph walk triage headline Defer",
    ]

    assert any(
        step.get("kind") == "ui"
        and step.get("action") == "click"
        and step.get("selector") == "[data-testid=arrival-brief-generate]"
        for step in setup
    )
    assert any(
        step.get("kind") == "api"
        and step.get("method") == "GET"
        and step.get("path") == LATEST
        and step.get("capture_as") == "first_brief_id"
        and step.get("capture_path") == "id"
        for step in setup
    )
    assert any(
        step.get("kind") == "api"
        and step.get("method") == "GET"
        and step.get("path") == LATEST
        and step.get("capture_as") == "first_headline"
        and step.get("capture_path") == "headline"
        for step in setup
    )

    # The shelf writes must be owner gestures on the owning Arrival row.  The
    # first row is Acked in setup; the remaining row is Deferred as the trigger.
    assert any(
        step.get("kind") == "ui"
        and step.get("action") == "click"
        and "arrival-brief-row" in step.get("selector", "")
        and "triage headline Ack" in step.get("selector", "")
        and ":has-text('Ack')" in step.get("selector", "")
        for step in setup
    )
    trigger = case["trigger"]
    assert trigger["kind"] == "ui"
    assert trigger["action"] == "click"
    assert "arrival-brief-row" in trigger["selector"]
    assert "triage headline Defer" in trigger["selector"]
    assert ":has-text('Defer')" in trigger["selector"]
    assert not any(
        step.get("kind") == "api"
        and "/brief/items/" in step.get("path", "")
        for step in setup
    )


def test_triaged_headline_case_reads_latest_for_retention() -> None:
    case = _case()
    expected = case["expected"]
    reads = {(read["method"], read["path"]) for read in expected["reads"]}

    assert ("GET", LATEST) in reads
    assert ("GET", "/api/brief/shelf") in reads
    checks = [
        step for step in case["setup"]
        if step.get("kind") == "check"
        and step.get("observe_at") == f"protocol: GET {LATEST}"
    ]
    assert checks
    assert checks[-1]["predicate"] == {
        "kind": "protocol_field",
        "path": "/headline",
        "value": "{first_headline}",
    }
    assert "THIS WEEK" in expected["words"]
    assert "stored headline and date" in expected["words"]
