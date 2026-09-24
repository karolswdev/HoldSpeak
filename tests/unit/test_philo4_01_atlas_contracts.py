"""PHILO-4-01 round two — the ACTIVE atlas says what the built face says.

Astra's check on built (2026-09-24, BOUNCE): the face was right, but the
executable atlas still asked the rig for the retired words. These fences
read the active atlas files (``docs/internal/philo/graph/atlas*.json``) —
never the sealed passes or the retained observations, which keep the words
of their own revision — and fail when a case:

* expects ``Nothing material changed.`` (ratified replacement: ``No changes``);
* expects ``Generate brief FAILED`` (built: ``BRIEF DID NOT GENERATE · HTTP n``);
* observes ``.write-receipt-label`` for a brief generation (built: the BRIEF
  section's own status line, ``[data-testid=arrival-brief-generate-failed]``).

They also pin the two claims Astra named: the empty-brief claim names the
built words, and the reload claim points at the quiet branch (the headline
branch), not at the untriaged-rows branch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "docs/internal/philo/graph"
ATLAS_FILES = sorted(GRAPH.glob("atlas*.json"))
ACTIVE = [path for path in ATLAS_FILES if path.name != "atlas.schema.json"]
CHAIR = REPO / "web/src/desk/chair/ChairHome.tsx"
PRODUCER = REPO / "holdspeak/services/monday_brief_service.py"

RETIRED_WORDS = ("Nothing material changed", "Generate brief FAILED")
FAILED_TESTID = "arrival-brief-generate-failed"
FAILURE_CASE = "case.j10.route_brief_generate.load_failure"
EMPTY_CASES = (
    "case.j10.arrival_generate_brief.generated_empty",
    "case.j10.arrival_reload.reload_persisted",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _predicates(case: dict) -> list[tuple[str, dict]]:
    """Every (observe_at, predicate) a case asks the rig to evaluate."""
    found: list[tuple[str, dict]] = []
    for item in [*(case.get("preconditions") or []), *(case.get("setup") or [])]:
        if isinstance(item, dict) and item.get("kind") == "check":
            found.append((item.get("observe_at", ""), item.get("predicate") or {}))
    expected = case.get("expected") or {}
    if expected.get("predicate"):
        found.append((expected.get("observe_at", ""), expected["predicate"]))
    return found


def _is_brief_generation(case: dict) -> bool:
    trigger = case.get("trigger") or {}
    return ("edge.face.arrival_brief_generate" in (case.get("edge_ids") or [])
            or "arrival-brief-generate" in str(trigger.get("selector", "")))


@pytest.fixture(scope="module", params=ACTIVE, ids=lambda path: path.name)
def active_atlas(request: pytest.FixtureRequest) -> dict:
    return _load(request.param)


@pytest.fixture(scope="module")
def atlas() -> dict:
    return _load(GRAPH / "atlas.json")


def _case(atlas: dict, case_id: str) -> dict:
    return next(case for case in atlas["cases"] if case["id"] == case_id)


def test_no_active_case_expects_the_retired_words(active_atlas: dict) -> None:
    problems = [
        f"{case['id']}: {predicate.get('value')!r} at {observe_at!r}"
        for case in active_atlas["cases"]
        for observe_at, predicate in _predicates(case)
        if any(word in str(predicate.get("value", "")) for word in RETIRED_WORDS)
    ]
    assert not problems, problems


def test_no_brief_generation_case_observes_the_write_receipt_label(active_atlas: dict) -> None:
    problems = [
        f"{case['id']}: observes {observe_at!r}"
        for case in active_atlas["cases"]
        if _is_brief_generation(case)
        for observe_at, _predicate in _predicates(case)
        if ".write-receipt-label" in observe_at
    ]
    assert not problems, problems


def test_the_empty_cases_expect_the_producer_words(atlas: dict) -> None:
    assert 'return "No changes", finalized_sections' in PRODUCER.read_text()
    for case_id in EMPTY_CASES:
        expected = _case(atlas, case_id)["expected"]
        assert expected["predicate"] == {"kind": "text_contains", "value": "No changes"}, case_id
        assert expected["observe_at"] == "[data-testid=arrival-brief-headline]", case_id


def test_the_failure_case_observes_the_built_failure_line(atlas: dict) -> None:
    case = _case(atlas, FAILURE_CASE)
    expected = case["expected"]
    assert expected["observe_at"] == f"[data-testid={FAILED_TESTID}]"
    assert expected["predicate"]["kind"] == "text_contains"
    assert expected["predicate"]["value"].startswith("BRIEF DID NOT GENERATE · HTTP ")
    chair = CHAIR.read_text()
    assert f'data-testid="{FAILED_TESTID}"' in chair
    assert "BRIEF DID NOT GENERATE · ${generateFailed}" in chair
    # the fault is PERFORMED at the browser boundary on the one write
    faults = [step for step in case["setup"]
              if step.get("kind") == "boundary" and step.get("substitute") == "http_fault"]
    assert [(f["method"], f["path"]) for f in faults] == [("POST", "/api/brief/generate")]
    assert expected["predicate"]["value"].endswith(f"HTTP {faults[0]['status']}")


def _state(atlas: dict, state_id: str) -> dict:
    return next(state for state in atlas["states"] if state["id"] == state_id)


def test_the_empty_brief_claims_name_the_built_words(atlas: dict) -> None:
    for source in _state(atlas, "state.briefs.generated_empty")["sources"]:
        assert not any(word in source["claim"] for word in RETIRED_WORDS), source


def test_the_reload_claim_points_at_the_quiet_branch(atlas: dict) -> None:
    lines = CHAIR.read_text().splitlines()
    refs = [ref for ref in _state(atlas, "state.briefs.reload_persisted")["sources"]
            if ref["path"] == "web/src/desk/chair/ChairHome.tsx"]
    assert refs
    for ref in refs:
        window = "\n".join(lines[ref["line"] - 1: ref["line"] + 4])
        # the quiet branch draws the brief's own headline; the untriaged
        # branch (BriefSection rows) never does
        assert "arrival-brief-headline" in window, (ref, window)
        assert "BriefSection" not in window, (ref, window)
