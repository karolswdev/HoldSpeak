"""Programs PG-REQ §8 (2026-10-31): adjust a Program while it runs.

Each frozen field refuses with its reason; a move renumbers every step and
rewrites every ``after``; insert before a started step refuses; an
amendment waits for a turn boundary and goes into the brief file; an
orchestrating agent's change goes up the ladder.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.principals import AgentCredentialStore
from holdspeak.services.program_service import (
    FROZEN_BAR, FROZEN_MERGED, FROZEN_READ, FROZEN_SET, ProgramRefused, step_fields,
)
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git


def _program(rig: Rig, control: str = "normal") -> str:
    return rig.service.create(OWNER, title="Adjust", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                              control=control)["id"]


def _titles(rig: Rig, pid: str) -> list[tuple[int, str, list[int]]]:
    return [(step["ordinal"], step["title"], step["after"]) for step in rig.program(pid)["steps"]]


def test_the_frozen_table_by_state() -> None:
    editable, frozen = step_fields({"state": "planned"})
    assert "amend" not in editable and frozen == {} and "position" in editable
    editable, frozen = step_fields({"state": "working", "gate_review": "none"})
    assert {"title", "amend", "runs_on_then", "gate_review", "review_depth", "gate_merge", "requirements"} <= set(editable)
    assert frozen == {"brief": FROZEN_READ, "owns": FROZEN_READ, "after": FROZEN_READ, "effort": FROZEN_SET,
                      "agent": FROZEN_SET, "race": FROZEN_SET, "gate_check": FROZEN_BAR, "position": FROZEN_SET}
    _editable, frozen = step_fields({"state": "review", "gate_review": "agent"})
    assert frozen["gate_review"] == FROZEN_BAR and frozen["review_depth"] == FROZEN_READ
    editable, frozen = step_fields({"state": "pr_open"})
    assert set(editable) == {"title", "gate_merge", "requirements", "for_person", "may_call"}
    assert frozen["amend"] == FROZEN_READ
    editable, frozen = step_fields({"state": "merged"})
    assert editable == ["title"] and set(frozen.values()) == {FROZEN_MERGED}


def test_each_frozen_field_refuses_with_its_reason(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A", "brief": "Do A."}, {"title": "B", "after": [1]}])
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    assert one["frozen"]["brief"] == FROZEN_READ and "amend" in one["editable"]
    for field, value, reason in [("brief", "Other.", FROZEN_READ), ("owns", ["x.py"], FROZEN_READ),
                                 ("after", [], FROZEN_READ), ("effort", "high", FROZEN_SET),
                                 ("profile", "codex", FROZEN_SET), ("race", 2, FROZEN_SET),
                                 ("gate_check", False, FROZEN_BAR), ("before", "end", FROZEN_SET)]:
        with pytest.raises(ProgramRefused) as refused:
            rig.service.change_step(OWNER, pid, one["id"], **{field: value})
        assert refused.value.code == "step_frozen", field
        assert refused.value.context["reason"] == reason, field
        assert reason in refused.value.detail or "Add the step after it" in refused.value.detail, field
    # What a started step still takes: the title, the review raised, the merge.
    rig.service.change_step(OWNER, pid, one["id"], title="A, renamed", gate_review="agent", gate_merge="owner")
    one = rig.step(pid, 1)
    assert (one["title"], one["gate"]["review"], one["gate"]["merge"]) == ("A, renamed", "agent", "owner")
    assert one["branch"] == "program/adjust/1-a"  # the branch keeps its name
    with pytest.raises(ProgramRefused) as refused:  # the bar does not come down
        rig.service.change_step(OWNER, pid, one["id"], gate_review="none")
    assert refused.value.code == "step_frozen" and refused.value.context["reason"] == FROZEN_BAR


def test_a_move_renumbers_and_remaps_after(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B"}, {"title": "C", "after": [1]},
                                        {"title": "D", "after": [2]}])
    a, b, c, _d = (rig.step(pid, n) for n in (1, 2, 3, 4))
    rig.service.change_step(OWNER, pid, c["id"], before=b["id"])
    assert _titles(rig, pid) == [(1, "A", []), (2, "C", [1]), (3, "B", []), (4, "D", [3])]
    rig.service.change_step(OWNER, pid, b["id"], before=a["id"])
    assert _titles(rig, pid) == [(1, "B", []), (2, "A", []), (3, "C", [2]), (4, "D", [1])]
    with pytest.raises(ProgramRefused) as refused:  # C comes after A: A cannot go below it
        rig.service.change_step(OWNER, pid, a["id"], before="end")
    assert refused.value.code == "order_invalid"
    assert _titles(rig, pid) == [(1, "B", []), (2, "A", []), (3, "C", [2]), (4, "D", [1])]


def test_a_step_does_not_move_above_a_step_it_comes_after(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B", "after": [1]}])
    a, b = rig.step(pid, 1), rig.step(pid, 2)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.change_step(OWNER, pid, b["id"], before=a["id"])
    assert refused.value.code == "order_invalid"
    assert refused.value.detail == "Step 2 comes after step 1: it cannot move above it."
    assert _titles(rig, pid) == [(1, "A", []), (2, "B", [1])]


def test_insert_before_takes_the_place_and_the_step_waits(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B", "after": [1]}, {"title": "C", "after": [2]}])
    c = rig.step(pid, 3)
    rig.service.plan(OWNER, pid, steps=[{"title": "The loop watch"}], before=c["id"])
    assert _titles(rig, pid) == [(1, "A", []), (2, "B", [1]), (3, "The loop watch", [2]), (4, "C", [2, 3])]
    rig.service.start(OWNER, pid)
    first = rig.step(pid, 1)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.plan(OWNER, pid, steps=[{"title": "Too late"}], before=first["id"])
    assert refused.value.code == "step_frozen" and refused.value.detail == "Step 1 started. Add the step after it."


def test_a_started_step_that_changes_number_keeps_its_branch(tmp_path) -> None:
    rig = Rig(tmp_path, working_at_once=1)  # B waits for a free agent: Ready, not started
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B"}])
    rig.service.start(OWNER, pid)
    a, b = rig.step(pid, 1), rig.step(pid, 2)
    assert a["state"] == "briefed" and b["state"] == "ready", (a["state"], b["state"])
    rig.service.change_step(OWNER, pid, b["id"], before=a["id"])
    steps = rig.program(pid)["steps"]
    moved = next(step for step in steps if step["id"] == a["id"])
    assert moved["ordinal"] == 2 and moved["branch"] == a["branch"] == "program/adjust/1-a"
    assert any(c["line"] == "Step 1 is now step 2" and c["step_id"] == a["id"] for c in rig.program(pid)["checkpoints"])


def test_an_amendment_waits_for_a_turn_boundary(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes", "brief": "31 handlers."}])
    with pytest.raises(ProgramRefused) as refused:
        rig.service.amend(OWNER, pid, rig.step(pid, 1)["id"], "Keep the 14-day rule")
    assert refused.value.code == "step_not_started"
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    rig.service.amend(OWNER, pid, one["id"], "Keep the 14-day rule")
    one = rig.step(pid, 1)
    assert [(a["by"], a["line"], a["sent_at"]) for a in one["amendments"]] == [("owner", "Keep the 14-day rule", None)]
    tree = Path(rig.ledger.get(one["launch_id"])["worktree_path"])
    brief = (tree / ".holdspeak" / "brief.md").read_text()
    assert "Added by the owner at " in brief and "Keep the 14-day rule" in brief
    assert git(tree, "status", "--porcelain") == ""  # kept out of git: the check's clean tree holds
    rig.tick()
    assert not any("14-day" in text for _l, text in rig.prompts)  # working: never typed mid-turn
    rig.agent.end_turn(one["launch_id"])
    rig.tick()
    assert any(text.startswith("The owner on step 1: Keep the 14-day rule") for _l, text in rig.prompts)
    one = rig.step(pid, 1)
    assert one["amendments"][0]["sent_at"] and one["state"] == "working"
    # The next turn end with a commit is read as usual.
    rig.agent.finish(one["launch_id"], {"a.py": "1\n"})
    rig.tick()
    assert rig.step(pid, 1)["state"] not in ("working", "briefed")
    from holdspeak.services.program_brief import compose

    assert "Added by the owner: Keep the 14-day rule" in compose(rig.db, one["id"])["text"]


def test_an_orchestrators_change_goes_up_the_ladder(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp import palettes
    from holdspeak.mcp.families import program as family

    rig = Rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    store = AgentCredentialStore()
    agent = store.issue("agent:orchestrator", palette=palettes.resolve_palette("CONDUCTOR"), palette_name="CONDUCTOR",
                        launch_id="L-orch").principal
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    made = family.dispatch("program.create", {"title": "Mine", "repository": str(rig.repo), "control": "normal",
                                              "check_command": f"sh {FAKE_CHECK}"}, agent)
    pid = made["id"]
    family.dispatch("program.plan", {"program_id": pid, "steps": [{"title": "A"}, {"title": "B"}]}, agent)
    b = rig.step(pid, 2)
    family.dispatch("program.step_update", {"program_id": pid, "step_id": b["id"], "title": "B, better"}, agent)
    assert rig.step(pid, 2)["title"] == "B"
    item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "step_change")
    assert item["choices"] == ["apply", "skip"] and item["title"].startswith("The orchestrator changes step 2")
    family.dispatch("program.decide", {"program_id": pid, "kind": "step_change", "choice": "apply",
                                       "proposal_id": item["proposal_id"]}, OWNER)
    assert rig.step(pid, 2)["title"] == "B, better"
    # YOLO applies it and says so; Overturn while the step is still planned.
    family.dispatch("program.update", {"program_id": pid, "control": "yolo"}, agent)
    family.dispatch("program.step_update", {"program_id": pid, "step_id": b["id"], "title": "B, best"}, agent)
    assert rig.step(pid, 2)["title"] == "B, best"
    decided = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "step_change")
    rig.service.overturn(OWNER, pid, decided["id"])
    assert rig.step(pid, 2)["title"] == "B, better"
    # An amendment at Normal is his to send.
    family.dispatch("program.update", {"program_id": pid, "control": "normal"}, agent)
    family.dispatch("program.start", {"program_id": pid}, agent)
    one = rig.step(pid, 1)
    family.dispatch("program.amend", {"program_id": pid, "step_id": one["id"], "line": "Use the new index"}, agent)
    item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "step_amend")
    assert item["choices"] == ["send", "skip"] and not rig.step(pid, 1)["amendments"]
    rig.service.decide(OWNER, pid, one["id"], kind="step_amend", choice="send", proposal_id=item["proposal_id"])
    assert [a["by"] for a in rig.step(pid, 1)["amendments"]] == ["agent"]
