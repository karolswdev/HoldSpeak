"""The night spends no cloud tokens (ruling 2026-11-01; Astra's post-merge night case 8).

A night template's pi with no home engine in the model library would run on
the desk's ``agent.code`` assignment, which can be a cloud engine. The step
waits by name instead, and its review does not start on another engine.
"""
from __future__ import annotations

from holdspeak.services.program_runner import HOME_ENGINE_MISSING, ProgramRunner
from tests.integration.program_rig import FAKE_CHECK, OWNER
from tests.unit.test_program_dreaming import at, dream_desk


def test_a_night_step_with_no_home_engine_waits_by_name(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="dreaming")["id"]
    program = rig.service.store.get_program(pid)
    assert program["default_profile"] == "pi-default" and not program.get("default_engine")  # not in this library
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x", "owns": ["web/src/desk/a.ts"]}])
    rig.service.start(OWNER, pid)
    clock.now = at(0, 23, 31)
    rig.tick()
    assert [kind for kind, _id, _kw in rig.hand.calls if kind == "program_step"] == []
    step = rig.step(pid, 1)
    assert step["state"] == "ready" and HOME_ENGINE_MISSING in step["state_word"], step["state_word"]


def test_claude_code_chosen_for_the_night_runs_without_the_home_engine(tmp_path, monkeypatch) -> None:
    rig, clock = dream_desk(tmp_path, monkeypatch, at(0, 14))
    pid = rig.service.create(OWNER, title="Night", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             template="dreaming", default_profile="claude-default")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x", "owns": ["web/src/desk/a.ts"]}])
    rig.service.start(OWNER, pid)
    clock.now = at(0, 23, 31)
    rig.tick()
    assert [kind for kind, _id, _kw in rig.hand.calls if kind == "program_step"]


def test_the_rule_names_only_the_night_templates() -> None:
    missing = ProgramRunner._home_engine_missing
    assert missing({"template": "dreaming"}, "pi-default", None) is True
    assert missing({"template": "overnight"}, "pi-default", "") is True
    assert missing({"template": "dreaming"}, "pi-default", "engine-home") is False
    assert missing({"template": "dreaming"}, "claude-default", None) is False
    assert missing({"template": "fast-cycle"}, "pi-default", None) is False
