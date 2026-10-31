"""Programs: the state machine, triage, the brief's "theirs", the MCP
authority, Needs you rows, Runs on (engine validation) and the idle gate."""
from __future__ import annotations

import pytest

from holdspeak.delivery.pi_launch import LibraryEngine, PiEngine
from holdspeak.principals import AgentCredentialStore, Principal, PrincipalKind
from holdspeak.services.needs_you_membership import program_items
from holdspeak.services.program_brief import compose, theirs
from holdspeak.services.program_service import (
    STEP_STATES, STEP_TRANSITIONS, ProgramRefused, triage_effort,
)
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

QWEN = LibraryEngine("engine-tailscale-karol-8080", "qwen3.8-27b on karol", PiEngine(
    endpoint="http://karol:8080/v1", model="qwen3.8-27b", context_window=32768, key_slot="",
    host="karol:8080", boundary="private"))
CHAT = LibraryEngine("engine-chat", "A chat engine", None, "engine_not_compatible")


def _engines(engine_id: str):
    return {QWEN.profile_id: QWEN, CHAT.profile_id: CHAT}.get(engine_id)


def _rig(tmp_path, **kw) -> Rig:
    return Rig(tmp_path, engines=_engines, **kw)


def _made(rig: Rig, **kw) -> str:
    return rig.service.create(OWNER, title="P", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                              control=kw.pop("control", "normal"), **kw)["id"]


# ── the state machine (design §4) ─────────────────────────────────────

def test_the_transition_table_covers_every_state_and_its_moves() -> None:
    assert set(STEP_TRANSITIONS) == set(STEP_STATES)
    for state, moves in STEP_TRANSITIONS.items():
        assert moves <= set(STEP_STATES), state
    # The rules of §4 in the table.
    assert "checking" in STEP_TRANSITIONS["working"]           # a turn end with a commit
    assert "merged" not in STEP_TRANSITIONS["checking"]        # never merged without a PR
    assert STEP_TRANSITIONS["merged"] == frozenset({"done"})
    assert STEP_TRANSITIONS["done"] == frozenset()
    assert "ready" in STEP_TRANSITIONS["parked"]               # Resume


def test_a_refused_move_raises(tmp_path) -> None:
    rig = _rig(tmp_path)
    pid = _made(rig)
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}])
    program = rig.service.store.get_program(pid)
    step = rig.service.store.list_steps(pid)[0]
    with pytest.raises(ProgramRefused) as refused:
        rig.service.transition(program, step, "merged")
    assert refused.value.code == "transition_invalid"


# ── triage (design §6: by rule) ──────────────────────────────────────

def test_triage_by_rule() -> None:
    assert triage_effort("Change one thing.", ["a.py"]) == "low"
    assert triage_effort("Refactor the store.", ["a.py"]) == "high"
    assert triage_effort("x", [f"f{i}.py" for i in range(13)]) == "high"
    assert triage_effort("Migrate the rows.", []) == "high"
    assert triage_effort("Two paragraphs.\n\nSecond.", ["a.py"]) == "medium"


def test_plan_size_auto_sets_effort(tmp_path) -> None:
    rig = _rig(tmp_path)
    pid = _made(rig)
    made = rig.service.plan(OWNER, pid, size="auto", steps=[
        {"title": "Small", "brief": "Rename it.", "owns": ["a.py"], "effort": "high"},
        {"title": "Big", "brief": "Refactor the runner."},
    ])
    assert [step["effort"] for step in made["steps"]] == ["low", "high"]


# ── the brief ────────────────────────────────────────────────────────

def test_the_brief_names_who_where_theirs_and_the_proof(tmp_path) -> None:
    rig = _rig(tmp_path)
    pid = _made(rig)
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Store", "brief": "Do the store.", "owns": ["holdspeak/db/programs.py"]},
        {"title": "Routes", "brief": "Do the routes.", "owns": ["holdspeak/web/routes/programs.py"]},
    ])
    steps = rig.service.store.list_steps(pid)
    steps[0]["state"] = "working"
    rig.service.store.save_step(steps[0])
    steps = rig.service.store.list_steps(pid)
    assert theirs(steps, steps[1]) == [{"ordinal": 1, "title": "Store", "files": ["holdspeak/db/programs.py"]}]
    assert theirs(steps, steps[0]) == []  # step 2 has not started: nothing of it is live
    brief = compose(rig.db, steps[1]["id"], control_mode="yolo", branch="program/p/2-routes")
    text = brief["text"]
    assert text.startswith("HoldSpeak on step 2 of 2 of the program “P”.")
    assert "not the owner's words" in text
    assert "Theirs, do not touch" in text and "holdspeak/db/programs.py" in text
    assert "Never report green without the log path." in text
    assert "program.checkpoint" in text and "program.step_done" in text
    assert "Branch: program/p/2-routes" in text
    assert brief["refs"] == [f"program_step:{steps[1]['id']}"]


# ── authority (design §7) ────────────────────────────────────────────

def _launch_principal(monkeypatch, launch_id: str) -> Principal:
    from holdspeak.mcp import palettes

    store = AgentCredentialStore()
    credential = store.issue(f"agent:launch:{launch_id}", palette=palettes.resolve_palette("CONDUCTOR"),
                             palette_name="CONDUCTOR", launch_id=launch_id)
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    return credential.principal


def test_mcp_authority_rules(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp import palettes
    from holdspeak.mcp.families import program as family

    rig = _rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    pid = _made(rig, control="secure")
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B"}])
    rig.service.start(OWNER, pid)
    one, two = rig.step(pid, 1), rig.step(pid, 2)

    conductor = palettes.resolve_palette("CONDUCTOR")
    assert {"program.create", "program.plan", "program.start", "program.checkpoint", "program.step_done",
            "program.get", "program.list"} <= conductor
    assert "program.decide" not in conductor and "program.overturn" not in conductor

    agent = _launch_principal(monkeypatch, one["launch_id"])
    # Its own step: yes. Another step: refused by name.
    family.dispatch("program.checkpoint", {"step_id": one["id"], "line": "20 of 31 done"}, agent)
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.checkpoint", {"step_id": two["id"], "line": "x"}, agent)
    assert refused.value.code == "not_your_step"
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.step_done", {"step_id": two["id"], "report": "x"}, agent)
    assert refused.value.code == "not_your_step"
    done = family.dispatch("program.step_done", {"step_id": one["id"], "report": "Files: a.py"}, agent)
    assert done["waits_for"] == "a new commit on the step's branch"
    # Only the owner decides or overturns; an agent never.
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.decide", {"program_id": pid, "step_id": one["id"], "kind": "merge",
                                           "choice": "merge"}, agent)
    assert refused.value.code == "owner_required"
    # An orchestrating agent runs only the Programs it made.
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.park", {"program_id": pid}, agent)
    assert refused.value.code == "not_your_program"
    own = family.dispatch("program.create", {"title": "Mine", "repository": str(rig.repo),
                                             "check_command": f"sh {FAKE_CHECK}"}, agent)
    family.dispatch("program.plan", {"program_id": own["id"], "steps": [{"title": "X"}]}, agent)
    assert family.dispatch("program.park", {"program_id": own["id"]}, agent)["state"] == "parked"
    lines = [c["line"] for c in rig.service.get(OWNER, pid)["checkpoints"] if c["by"] == "agent"]
    assert "20 of 31 done" in lines


# ── Needs you ────────────────────────────────────────────────────────

def test_program_items_carry_only_his_kinds(tmp_path) -> None:
    items = [
        {"kind": "answer", "program_id": "p", "step_id": "s", "id": "s:answer", "title": "Answer"},
        {"kind": "merge", "program_id": "p", "program_title": "The hub", "step_id": "s", "id": "s:merge",
         "title": "Merge step 1?", "choices": ["merge", "not_yet"], "ordinal": 1, "since": "2026-10-28T10:00:00Z"},
        {"kind": "core", "program_id": "p", "step_id": "s", "id": "s:core", "title": "A core question"},
    ]
    rows = program_items(items)
    assert [row["why"] for row in rows] == ["TO MERGE", "TO DECIDE"]
    merge = rows[0]
    assert merge["ref"] == "program:p:s:merge" and merge["group"] == "The hub" and merge["dueWord"] == "now"
    assert merge["program"]["decide"] == "/api/programs/p/steps/s/decide"
    assert merge["source"] == "program" and merge["openRef"] == "program:p"


# ── Runs on: the engine (pi only), validated by the library ──────────

def test_engine_validation_refuses_by_name(tmp_path) -> None:
    rig = _rig(tmp_path)
    with pytest.raises(ProgramRefused) as refused:
        _made(rig, default_profile="claude-default", default_engine=QWEN.profile_id)
    assert refused.value.code == "engine_needs_pi"
    with pytest.raises(ProgramRefused) as refused:
        _made(rig, default_profile="pi-default", default_engine="engine-nope")
    assert refused.value.code == "engine_unknown"
    with pytest.raises(ProgramRefused) as refused:
        _made(rig, default_profile="pi-default", default_engine=CHAT.profile_id)
    assert refused.value.code == "engine_not_compatible"
    with pytest.raises(ProgramRefused) as refused:
        _made(rig, default_profile="nobody-default")
    assert refused.value.code == "profile_unknown"
    pid = _made(rig, default_profile="pi-default", default_engine=QWEN.profile_id)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.plan(OWNER, pid, steps=[{"title": "A", "profile": "pi-default", "engine": "engine-nope"}])
    assert refused.value.code == "engine_unknown"
    program = rig.service.get(OWNER, pid)
    assert program["default"]["engine"] == {"id": QWEN.profile_id, "label": "qwen3.8-27b on karol",
                                            "short": "qwen", "model": "qwen3.8-27b"}


def test_the_overnight_template_runs_pi_on_the_home_engine_at_yolo(tmp_path) -> None:
    rig = _rig(tmp_path)
    program = rig.service.create(OWNER, title="Overnight", repository=str(rig.repo), template="overnight",
                                 check_command=f"sh {FAKE_CHECK}")
    assert program["control"] == "yolo" and program["prefer_idle"] is True
    assert program["default"]["profile"] == "pi-default" and program["default"]["engine"]["short"] == "qwen"
    assert program["reviewer"]["profile"] == "claude-default"


# ── the idle gate (prefer_idle) ──────────────────────────────────────

def test_a_pi_step_waits_for_its_idle_engine_then_dispatches(tmp_path) -> None:
    idle = {"now": False}
    rig = _rig(tmp_path, idle=lambda engine_id: (idle["now"], "qwen"))
    pid = _made(rig, default_profile="pi-default", default_engine=QWEN.profile_id, prefer_idle=True)
    rig.service.plan(OWNER, pid, steps=[{"title": "Overnight work"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    assert step["state"] == "ready" and step["state_word"] == "Ready · waiting for qwen"
    assert rig.hand.calls == []
    idle["now"] = True
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] in ("briefed", "working")
    kind, item, kwargs = rig.hand.calls[0]
    assert (kind, kwargs["profile"], kwargs["engine"]) == ("program_step", "pi-default", QWEN.profile_id)


def test_the_idle_gate_reads_the_engine_lanes(tmp_path) -> None:
    from holdspeak.engine_lanes import LANES

    rig = _rig(tmp_path)
    runner = rig.runner
    runner._idle = None
    with LANES.foreground([QWEN.lane_key]):
        assert runner.engine_idle(QWEN.profile_id) == (False, "qwen")
    assert runner.engine_idle(QWEN.profile_id) == (True, "qwen")


def test_a_hosted_pi_engine_with_no_spend_limit_is_a_core_question(tmp_path) -> None:
    hosted = LibraryEngine("engine-hosted", "Hosted model", PiEngine(
        endpoint="https://api.example.test/v1", model="big-1", context_window=8000, key_slot="slot",
        host="api.example.test", boundary="hosted"))
    rig = Rig(tmp_path, engines=lambda engine_id: hosted if engine_id == "engine-hosted" else None)
    pid = _made(rig, default_profile="pi-default", default_engine="engine-hosted", control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "Costs"}])
    rig.service.start(OWNER, pid)
    items = rig.service.needs_you_items()
    assert [item["kind"] for item in items] == ["core"]
    assert "no spend limit" in items[0]["title"]
    assert rig.hand.calls == []
    rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="core", choice="go_on")
    assert rig.hand.calls and rig.hand.calls[0][2]["engine"] == "engine-hosted"


def test_yolo_adds_a_step_an_agent_names_and_normal_asks(tmp_path, monkeypatch) -> None:
    for control, added in (("yolo", True), ("normal", False)):
        rig = _rig(tmp_path / control)
        pid = _made(rig, control=control)
        rig.service.plan(OWNER, pid, steps=[{"title": "A"}])
        rig.service.start(OWNER, pid)
        step = rig.step(pid, 1)
        agent = _launch_principal(monkeypatch, step["launch_id"])
        rig.service.step_done(agent, pid, step["id"], "done", follow_ups=["Write the docs"])
        program = rig.service.get(OWNER, pid)
        titles = [row["title"] for row in program["steps"]]
        if added:
            assert titles == ["A", "Write the docs"]
            row = next(r for r in program["decided_for_you"] if r["kind"] == "add_step")
            assert row["overturnable"]
            rig.service.overturn(OWNER, pid, row["id"])
            assert [r["title"] for r in rig.service.get(OWNER, pid)["steps"]] == ["A"]
        else:
            assert titles == ["A"]
            assert [item["kind"] for item in program["your_turn_items"]] == ["add_step"]


# ── PG15: a Program by his words, and its state in spoken words ───────

def test_find_by_his_words_never_makes_a_program(tmp_path) -> None:
    from holdspeak.services.program_service import name_words

    rig = _rig(tmp_path)
    night = _made(rig, template="overnight")
    rig.service.update(OWNER, night, title="Night build")
    phone = rig.service.create(OWNER, title="The phone app", repository=str(rig.repo),
                               check_command=f"sh {FAKE_CHECK}", control="normal")["id"]
    assert name_words("Start the overnight program on the hub") == ["start", "overnight"]
    assert rig.service.find(OWNER, name="the overnight program")["id"] == night  # by its template
    assert rig.service.find(OWNER, name="phone")["id"] == phone  # by its title
    assert rig.service.find(OWNER, program_id=phone)["id"] == phone
    with pytest.raises(ProgramRefused) as refused:
        rig.service.find(OWNER, name="the garden program")
    assert refused.value.code == "program_not_found"
    assert refused.value.detail == "There is no program with the name the garden program. I did not start a program."
    assert len(rig.service.list(OWNER)["programs"]) == 2


def test_spoken_state_says_steps_your_turn_and_the_last_decision() -> None:
    from holdspeak.services.program_service import spoken_state

    assert spoken_state({"title": "Phone app", "state": "drafting", "total": 0, "done": 0}) == "Phone app is not started."
    assert spoken_state({
        "title": "Phone app", "state": "waiting", "total": 3, "done": 1, "your_turn": 2, "asks": 0,
        "decided_for_you": [{"line": "Skipped the lint finding."}, {"line": "Older"}],
    }) == "Phone app waits on you: 1 of 3 steps are done. 2 things wait on you, and the last decision: Skipped the lint finding."
    assert spoken_state({"title": "X", "state": "running", "total": 1, "done": 0, "your_turn": 0}) == "X runs: 0 of 1 step is done."
