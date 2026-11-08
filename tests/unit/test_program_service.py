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


def test_an_agent_never_plans_into_a_running_program(tmp_path, monkeypatch) -> None:
    """2026-11-08 (the audit Program added 13 steps to itself): an agent,
    its maker included, may not add, remove or move the steps of a running
    Program; the owner may. A new Program and a proposed fix stay open."""
    from holdspeak.mcp.families import program as family

    rig = _rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    pid = _made(rig, control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B", "after": [1]}])
    rig.service.start(OWNER, pid)
    one, two = rig.step(pid, 1), rig.step(pid, 2)
    agent = _launch_principal(monkeypatch, one["launch_id"])
    # The agent that made a Program is its writer; the lock holds it too.
    rig.service.store.save_program({**rig.service.store.get_program(pid), "created_by": f"launch:{one['launch_id']}"})
    text = rig.service.text_get(OWNER, pid)["text"]
    calls = [
        ("program.plan", {"program_id": pid, "steps": [{"title": "C"}]}),
        ("program.step_update", {"program_id": pid, "step_id": two["id"], "title": "B2"}),
        ("program.step_remove", {"program_id": pid, "step_id": two["id"]}),
        ("program.text_apply", {"program_id": pid, "text": text + "\nstep + C\n", "dry_run": False}),
    ]
    for name, args in calls:
        with pytest.raises(ProgramRefused) as refused:
            family.dispatch(name, dict(args), agent)
        assert refused.value.code == "plan_locked_while_running", name
        assert "Propose a fix, or make a new program." in str(refused.value.detail), name
    assert [row["title"] for row in rig.service.get(OWNER, pid)["steps"]] == ["A", "B"]
    # A dry run reads; the owner keeps every edit.
    family.dispatch("program.text_apply", {"program_id": pid, "text": text + "\nstep + C\n"}, agent)
    rig.service.plan(OWNER, pid, steps=[{"title": "C"}])
    rig.service.change_step(OWNER, pid, two["id"], title="B2")
    assert [row["title"] for row in rig.service.get(OWNER, pid)["steps"]] == ["A", "B2", "C"]
    # The audit-to-fix path: a new Program of its own.
    own = family.dispatch("program.create", {"title": "Fix", "repository": str(rig.repo),
                                             "check_command": f"sh {FAKE_CHECK}"}, agent)
    family.dispatch("program.plan", {"program_id": own["id"], "steps": [{"title": "X"}]}, agent)


def test_a_hand_that_wrote_nothing_never_ends_done(tmp_path) -> None:
    """2026-11-08 (steps ended Done with no diff): a commit that changes no
    file goes back to the agent once with the line; the second empty round
    parks the step (YOLO). A step that declares ``no_diff_ok`` passes."""
    from pathlib import Path

    from tests.integration.program_rig import git

    rig = _rig(tmp_path)
    pid = _made(rig, control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "A", "gate_merge": "none"},
                                        {"title": "B", "gate_merge": "none", "no_diff_ok": True}])
    rig.service.start(OWNER, pid)

    def empty(ordinal: int) -> None:
        launch = rig.step(pid, ordinal)["launch_id"]
        git(Path(rig.ledger.get(launch)["worktree_path"]), "commit", "--allow-empty", "-m", "nothing")
        rig.agent.end_turn(launch)
        rig.tick(3)

    empty(1)
    step = rig.step(pid, 1)
    assert step["state"] == "check_failed"
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid) if row["step_id"] == step["id"]]
    assert "The step wrote nothing" in lines
    assert any("the step wrote nothing" in text for _launch, text in rig.prompts)
    empty(1)
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and step["parked_reason"] == "The step wrote nothing twice"
    empty(2)
    assert rig.step(pid, 2)["state"] == "done"


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
    assert program["reviewer"]["profile"] == "pi-default" and program["reviewer"]["engine"]["short"] == "qwen"


@pytest.mark.parametrize("template", ["overnight", "dreaming"])
def test_the_night_spends_no_cloud_tokens_by_rule(tmp_path, template) -> None:
    """Ruling 2026-11-01: a night template builds and reviews with pi on the
    home engine, idle only, in 64k; Claude Code stays choosable through the
    profile."""
    from holdspeak.program_templates import HOME_ENGINE_PROFILE, get_template

    shape = get_template(template)["program"]
    assert (shape["default_profile"], shape["default_engine"]) == ("pi-default", HOME_ENGINE_PROFILE)
    assert (shape["reviewer_profile"], shape["reviewer_engine"]) == ("pi-default", HOME_ENGINE_PROFILE)
    assert shape["prefer_idle"] is True

    rig = _rig(tmp_path)
    program = rig.service.create(OWNER, title="Night", repository=str(rig.repo), template=template,
                                 check_command=f"sh {FAKE_CHECK}")
    assert program["default"]["profile"] == "pi-default" and program["default"]["engine"]["id"] == HOME_ENGINE_PROFILE
    assert program["reviewer"]["profile"] == "pi-default" and program["reviewer"]["engine"]["id"] == HOME_ENGINE_PROFILE
    assert program["prefer_idle"] is True
    if template == "dreaming":
        assert program["budget_tokens"] == 64 * 1024

    chosen = rig.service.create(OWNER, title="Night, Claude", repository=str(rig.repo), template=template,
                                check_command=f"sh {FAKE_CHECK}", default_profile="claude-default",
                                reviewer_profile="claude-default")
    assert chosen["default"]["profile"] == "claude-default" and chosen["default"]["engine"] is None
    assert chosen["reviewer"]["profile"] == "claude-default" and chosen["reviewer"]["engine"] is None


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
    assert "no spend note" in items[0]["title"]
    assert rig.hand.calls == []
    rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="core", choice="go_on")
    assert rig.hand.calls and rig.hand.calls[0][2]["engine"] == "engine-hosted"


def test_a_program_over_its_spend_note_still_runs_and_reads_the_note(tmp_path) -> None:
    """HS-S24 (D20/G24, disclosure-only): the amount he typed is stored with
    the Program and read back as one fact; a Program over it is handed."""
    hosted = LibraryEngine("engine-hosted", "Hosted model", PiEngine(
        endpoint="https://api.example.test/v1", model="big-1", context_window=8000, key_slot="slot",
        host="api.example.test", boundary="hosted"))
    rig = Rig(tmp_path, engines=lambda engine_id: hosted if engine_id == "engine-hosted" else None)
    pid = _made(rig, default_profile="pi-default", default_engine="engine-hosted", control="yolo",
                spend_limit_usd=0)
    program = rig.service.get(OWNER, pid)
    assert (program["spend_limit_usd"], program["spend_note"]) == (0, "spend note · 0 USD")
    rig.service.plan(OWNER, pid, steps=[{"title": "Costs more than the note"}])
    rig.service.start(OWNER, pid)
    assert rig.service.needs_you_items() == []
    assert rig.hand.calls and rig.hand.calls[0][2]["engine"] == "engine-hosted"
    rig.service.update(OWNER, pid, spend_limit_usd=12.5)
    assert rig.service.get(OWNER, pid)["spend_note"] == "spend note · 12.50 USD"
    rig.service.update(OWNER, pid, spend_limit_usd=None)
    assert rig.service.get(OWNER, pid)["spend_note"] is None


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


# ── HS-S51: one owner of the Program vocabulary and its refusal ───────

def test_old_and_new_import_paths_give_the_same_objects() -> None:
    from holdspeak.services import program_definitions as definitions
    from holdspeak.services import program_service as service
    from holdspeak.services.errors import ServiceError

    for name in definitions.__all__:
        assert getattr(service, name) is getattr(definitions, name), name
    assert service.ProgramRefused is definitions.ProgramRefused
    assert issubclass(definitions.ProgramRefused, ServiceError)
    refused = definitions.ProgramRefused("step_frozen", "No.", field="brief")
    assert (refused.code, refused.detail, refused.context) == ("step_frozen", "No.", {"status": 409, "field": "brief"})
    with pytest.raises(service.ProgramRefused):
        raise refused
    with pytest.raises(definitions.ProgramRefused):
        definitions.via_of("pigeon")


def test_the_http_envelope_of_a_refusal_from_the_new_module_is_unchanged() -> None:
    import asyncio
    import json

    from holdspeak.services.program_definitions import ProgramRefused as Refused
    from holdspeak.web.routes.programs import _call

    def refuse() -> None:
        raise Refused("step_frozen", "The brief is frozen.", field="brief", reason="The agent has read it")

    answer = asyncio.run(_call(refuse))
    assert answer.status_code == 409
    assert json.loads(answer.body) == {"error": "step_frozen", "code": "step_frozen",
                                       "detail": "The brief is frozen.", "field": "brief",
                                       "reason": "The agent has read it"}
    answer = asyncio.run(_call(lambda: (_ for _ in ()).throw(Refused("via_invalid", "No.", status=400))))
    assert answer.status_code == 400


def test_the_mcp_by_name_refusal_is_an_answer_through_the_new_module(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp.families import program as family
    from holdspeak.services import program_definitions as definitions

    rig = _rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    _made(rig)
    said = family.dispatch("program.start", {"name": "the garden program"}, OWNER)
    assert said == {"found": False, "started": False,
                    "spoken": "There is no program with the name the garden program. I did not start a program."}
    with pytest.raises(definitions.ProgramRefused) as refused:
        family.dispatch("program.get", {"program_id": "program-missing"}, OWNER)
    assert refused.value.code == "program_not_found"


def test_the_definitions_module_does_not_reach_the_program_runtime() -> None:
    import subprocess
    import sys

    probe = ("import sys, holdspeak.services.program_definitions; "
             "print(' '.join(sorted(m for m in sys.modules if m.startswith('holdspeak'))))")
    loaded = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True).stdout.split()
    for runtime in ("program_service", "program_runner", "program_text"):
        assert f"holdspeak.services.{runtime}" not in loaded, loaded


def test_no_module_imports_a_definition_through_the_program_service() -> None:
    # HS-S51 repoint: a definition comes from program_definitions; the service
    # import carries only runtime names (_LOCK, ProgramService, ...).
    import ast
    from pathlib import Path

    from holdspeak.services import program_definitions as definitions

    package = Path(definitions.__file__).resolve().parents[1]
    wrong = []
    for path in sorted(package.rglob("*.py")):
        if path == package / "services" / "program_service.py":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("program_service"):
                names = sorted({alias.name for alias in node.names} & set(definitions.__all__))
                if names:
                    wrong.append(f"{path.relative_to(package)}:{node.lineno} {names}")
    assert not wrong, wrong
    assert (package / "services" / "brief_words.py").read_text().count("program_service") == 0


# ── Create plans itself (2026-11-08) ──────────────────────────────────
# The planner's answers are the recorded real replies of the home engine
# (tests/fixtures/program_plan_reply.json, case j1), replayed through the
# runner's engine seam, as in tests/unit/test_program_planner.py.

def _goal_desk(tmp_path, monkeypatch, control: str, *, engine: bool = True):
    from tests.integration.program_plan_seed import CASES, create
    from tests.integration.program_rig import give_quick_check
    from tests.unit.test_program_planner import case, replies
    from tests.unit.test_program_shaper import wire_engine

    rig = Rig(tmp_path)
    give_quick_check(rig.repo)
    rig.engine = wire_engine(rig, monkeypatch) if engine else None
    if engine:
        rig.engine.replies = replies("j1")
    rig.pid = create(rig, {**CASES["j1"], "control": control}, file_bytes=case("j1")["file_bytes"])
    return rig


def _claim(rig: Rig, pid: str) -> dict:
    from holdspeak.services.program_service import PLAN_GOAL_KIND

    rows = [row for row in rig.service.store.list_checkpoints(pid) if row.get("kind") == PLAN_GOAL_KIND]
    assert len(rows) == 1, rows
    return rows[0]


def test_create_with_a_goal_at_yolo_plans_and_starts_on_one_tick_with_no_press(tmp_path, monkeypatch) -> None:
    rig = _goal_desk(tmp_path, monkeypatch, "yolo")
    assert rig.program(rig.pid)["steps"] == [] and _claim(rig, rig.pid)["choice"] == "pending"
    rig.tick()
    program = rig.program(rig.pid)
    assert len(program["steps"]) == 4, program["steps"]
    assert (program["state"], program["control"]) == ("running", "yolo")  # his Control stays as made
    assert len(rig.engine.prompts) == 1  # one planner call
    claim = _claim(rig, rig.pid)
    assert (claim["choice"], claim["line"], claim["by"]) == ("planned", "Planned 4 steps from the goal", "engine")
    started = [row for row in rig.service.store.list_checkpoints(rig.pid) if row["line"] == "Started the program"]
    assert [row["by"] for row in started] == ["engine"]
    assert rig.hand.calls, "the first step is handed"
    rig.tick()
    assert len(rig.engine.prompts) == 1, "never planned again"


def test_create_with_a_goal_at_normal_plans_and_leaves_start_to_him(tmp_path, monkeypatch) -> None:
    rig = _goal_desk(tmp_path, monkeypatch, "normal")
    rig.tick()
    program = rig.program(rig.pid)
    assert len(program["steps"]) == 4 and (program["state"], program["control"]) == ("drafting", "normal")
    assert _claim(rig, rig.pid)["choice"] == "planned"
    assert not [row for row in rig.service.store.list_checkpoints(rig.pid) if row["line"] == "Started the program"]
    assert rig.hand.calls == []
    # The one press left: Start.
    assert rig.service.start(OWNER, rig.pid)["state"] == "running"


def test_create_with_an_empty_goal_is_not_planned(tmp_path, monkeypatch) -> None:
    from holdspeak.services.program_service import PLAN_GOAL_KIND
    from tests.unit.test_program_shaper import wire_engine

    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    pid = _made(rig, control="yolo")
    rig.tick(2)
    assert rig.program(pid)["steps"] == [] and rig.program(pid)["state"] == "drafting"
    assert rig.engine.prompts == []
    assert not [row for row in rig.service.store.list_checkpoints(pid) if row.get("kind") == PLAN_GOAL_KIND]


def test_a_program_with_steps_is_never_planned_from_its_goal(tmp_path, monkeypatch) -> None:
    from holdspeak.services.program_service import PLAN_GOAL_NOT_NEEDED

    rig = _goal_desk(tmp_path, monkeypatch, "yolo")
    rig.service.plan(OWNER, rig.pid, steps=[{"title": "By hand", "brief": "x"}])
    rig.tick(2)
    program = rig.program(rig.pid)
    assert [step["title"] for step in program["steps"]] == ["By hand"] and program["state"] == "drafting"
    assert rig.engine.prompts == []
    claim = _claim(rig, rig.pid)
    assert (claim["choice"], claim["line"]) == ("skipped", PLAN_GOAL_NOT_NEEDED)


def test_spoken_rows_waiting_on_the_desk_are_never_planned_over(tmp_path, monkeypatch) -> None:
    from holdspeak.services import program_spoken

    rig = _goal_desk(tmp_path, monkeypatch, "yolo")
    program_spoken.put_on_desk(rig.service, rig.pid, {"changes": [], "base": ""}, "add a step for the indexes")
    try:
        rig.tick()
        assert rig.engine.prompts == [] and rig.program(rig.pid)["steps"] == []
        assert program_spoken.on_desk(rig.pid) is not None, "his spoken rows stay in the well"
        assert _claim(rig, rig.pid)["choice"] == "skipped"
        assert not [row for row in rig.program(rig.pid)["checkpoints"] if row.get("kind") == "plan_goal"]
    finally:
        program_spoken.reset()


def test_a_goal_the_engine_cannot_plan_says_so_once_and_waits_for_plan_it(tmp_path, monkeypatch) -> None:
    rig = _goal_desk(tmp_path, monkeypatch, "yolo", engine=False)
    rig.tick()
    claim = _claim(rig, rig.pid)
    assert claim["choice"] == "not_planned" and claim["line"].startswith("The steps were not planned · "), claim
    program = rig.program(rig.pid)
    assert program["steps"] == [] and program["state"] == "drafting"
    rig.tick()
    assert _claim(rig, rig.pid)["line"] == claim["line"]


# ── the person review ask goes through the channel (2026-11-08) ──────

def _person_review_at_pr(tmp_path):
    class People:
        def display_names(self):
            return {"p-alice": "Alice"}

        def get_relationship(self, principal, person_id):
            return {"display_name": "Alice", "owner_aliases": ["alice-gh"]}

    rig = Rig(tmp_path, people=lambda: People())
    pid = rig.service.create(OWNER, title="Reviewed", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="fast-cycle", for_person_id="p-alice", control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Ask Alice", "brief": "x", "gate_review": "person"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"b.txt": "b\n"})
    rig.tick(2)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", step
    return rig, pid, step


def _save_destination(rig: Rig, name: str, folder) -> str:
    from holdspeak.db.channels import ChannelDestinationsRepository
    from holdspeak.services.channel_contract import channel

    target = channel("file").target_at_save(str(folder))
    with rig.db._connection() as conn:
        ChannelDestinationsRepository.insert_in_transaction(
            conn, destination_id=f"dest-{name.lower()}", name=name, channel="file", account={}, target=target,
            synced=False)
    return f"dest-{name.lower()}"


def test_the_review_ask_is_prepared_through_the_channel_for_the_persons_destination(tmp_path) -> None:
    rig, pid, step = _person_review_at_pr(tmp_path)
    folder = tmp_path / "alice-out"
    folder.mkdir()
    destination = _save_destination(rig, "Alice", folder)
    asked = rig.service.decide(OWNER, pid, step["id"], kind="ask_review", choice="prepare")
    sends = rig.db.channel_sends.list_for_document(f"note:program-review-ask-{step['id']}")
    assert [(row["destination_id"], row["state"]) for row in sends] == [(destination, "prepared")]
    assert (asked["prepared"].get("send") or {}).get("id") == sends[0]["id"]
    note = rig.db.notes.get(f"program-review-ask-{step['id']}")
    assert note is not None and "could you review PR" in note.body_markdown
    assert rig.service.store.get_step(step["id"])["facts"].get("review_ask_at")
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert "Prepared the review ask for Alice" in lines
    assert not list(folder.iterdir()), "prepared, never sent"


def test_a_refused_review_ask_prepare_says_why_and_marks_nothing_prepared(tmp_path) -> None:
    rig, pid, step = _person_review_at_pr(tmp_path)
    asked = rig.service.decide(OWNER, pid, step["id"], kind="ask_review", choice="prepare")
    assert asked["prepared"] is None and asked["refused"] == "Save one destination named Alice"
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    assert "The ask was not prepared · Save one destination named Alice" in lines
    assert "Prepared the review ask for Alice" not in lines
    assert not rig.service.store.get_step(step["id"])["facts"].get("review_ask_at")
    assert [item["kind"] for item in rig.service.needs_you_items()] == ["ask_review"]
