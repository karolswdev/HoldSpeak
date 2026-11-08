"""An Automation's event start is a watch (2026-11-08, the watch fold).

The end-to-end case (a recorded gh answer driven through the watch's
evaluation to a minted occurrence, its run and its result) is
``tests/integration/test_desk_workbenches.py::
test_an_event_choice_turns_its_start_on_and_its_occurrence_runs_without_a_press``.
These pin the pieces: the rule vocabulary, the start's lifecycle and the
one-occurrence-per-event rule.
"""
from __future__ import annotations

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.watch_service import AUTOMATION_INTENT_PREFIX, WatchService
from holdspeak.watch_condition_matcher import match_condition
from holdspeak.watch_validation import validate_action

OWNER = Principal(PrincipalKind.OWNER, "watch-automation-test")


def _pr(state: str) -> list[dict]:
    return [{"number": 7, "title": "Ship it", "url": "https://github.com/o/r/pull/7", "state": state}]


def test_event_type_is_a_rule_field() -> None:
    merged = {"event_type": "github.pr.merged", "facts": {"changed": {"state": ["open", "merged"]}}}
    assert match_condition({"field": "event_type", "comparison": "equals", "value": "github.pr.merged"}, [merged])
    assert match_condition({"field": "event_type", "comparison": "equals", "value": "github.pr.*"}, [merged])
    assert not match_condition({"field": "event_type", "comparison": "equals", "value": "jira.*"}, [merged])
    assert match_condition({"field": "event_type", "comparison": "in", "value": ["github.pr.merged"]}, [merged])


def test_automation_run_names_its_automation() -> None:
    assert validate_action({"kind": "automation.run", "workbench_id": "wb"}) == []
    assert validate_action({"kind": "automation.run"})
    assert validate_action({"kind": "project.observe", "workbench_id": "wb"})


def _rig(tmp_path, monkeypatch, rows: dict, *, instruction: str = "Write the release note.") -> tuple[Database, WatchService, list]:
    """The watch and the Programs service are real; the step's one model
    call is the seam (``program_prompt.run_claimed``)."""
    from holdspeak.services import program_prompt

    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")  # no tick: the start's own wait runs the step
    db = Database(tmp_path / "watch-automation.db")
    db.workbenches.upsert(workbench_id="wb-merge", name="On merge", instruction=instruction)
    service = WatchService(db, snapshot_fetcher=lambda *_a, **_k: rows["now"])
    ran: list = []

    def fake_run(_runner, program, step, **_kwargs):  # noqa: ANN001
        ran.append((program, step))
        program_prompt.release(step["id"])

    monkeypatch.setattr(program_prompt, "run_claimed", fake_run)
    return db, service, ran


def test_one_event_starts_one_program_and_runs_it_once(tmp_path, monkeypatch) -> None:
    rows = {"now": _pr("open")}
    db, service, ran = _rig(tmp_path, monkeypatch, rows)
    watch = service.start_automation_event(
        OWNER, workbench_id="wb-merge", preset_id="github-pr-merged", repository="o/r")
    assert (watch["intent"], watch["state"]) == (AUTOMATION_INTENT_PREFIX + "wb-merge", "active")
    assert [w["event_pattern"] for w in service.automation_event_watches("wb-merge")] == ["github.pr.merged"]
    assert ran == []  # the baseline is quiet

    rows["now"] = _pr("merged")
    service.evaluate_once(OWNER, watch["id"])
    [(program, step)] = ran
    assert program["title"] == "Ship it" and program["origin_ref"] == "workbench:wb-merge"
    assert step["kind"] == "prompt"
    assert "Write the release note." in step["brief_markdown"] and "github.pr.merged" in step["brief_markdown"]
    [row] = service.automation_event_history(OWNER, workbench_id="wb-merge", watch_id=watch["id"])
    assert (row["program_id"], row["event_type"]) == (program["id"], "github.pr.merged")
    assert db.workbench_items.list_for_workbench("wb-merge") == []  # no occurrence item

    service.evaluate_once(OWNER, watch["id"])
    assert len(ran) == 1  # the same event never runs twice

    # The same choice again finds the same start; off pauses it.
    again = service.start_automation_event(
        OWNER, workbench_id="wb-merge", preset_id="github-pr-merged", repository="o/r")
    assert again["id"] == watch["id"]
    off = service.set_automation_event_enabled(
        OWNER, workbench_id="wb-merge", watch_id=watch["id"], enabled=False)
    assert off["state"] == "paused"


def test_a_source_that_cannot_be_read_refuses_and_nothing_is_on(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "unreadable.db")
    db.workbenches.upsert(workbench_id="wb-merge", name="On merge", instruction="Write it.")

    def broken(*_a, **_k):
        raise RuntimeError("gh is not signed in")

    service = WatchService(db, snapshot_fetcher=broken)
    with pytest.raises(RuntimeError, match="gh is not signed in"):
        service.start_automation_event(
            OWNER, workbench_id="wb-merge", preset_id="github-pr-merged", repository="o/r")
    [watch] = service.automation_event_watches("wb-merge")
    assert watch["state"] == "paused" and watch["last_error"] == "gh is not signed in"


def test_an_automation_with_no_instruction_runs_the_events_words(tmp_path, monkeypatch) -> None:
    rows = {"now": _pr("open")}
    _db, service, ran = _rig(tmp_path, monkeypatch, rows, instruction="")
    watch = service.start_automation_event(
        OWNER, workbench_id="wb-merge", preset_id="github-pr-merged", repository="o/r")
    rows["now"] = _pr("merged")
    service.evaluate_once(OWNER, watch["id"])
    [(_program, step)] = ran
    assert step["brief_markdown"].startswith("Something happened: Ship it.")
    assert "github.pr.merged" in step["brief_markdown"]
