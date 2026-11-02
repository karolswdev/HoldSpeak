"""IMP4 "Never wider than the parent" (BROCREW-IMPORT-2026-11-01.md, closes the open ruling).

An agent's Program, an agent's change of its control (update or the text),
a handoff, a race entrant and a sub-agent's launch run at a control no wider
than what made them (Secure < Normal < YOLO). The owner's own press is never
capped.
"""
from __future__ import annotations

import json

import pytest

from holdspeak.principals import AgentCredentialStore
from holdspeak.services.control_level import mode_for_request
from holdspeak.services.program_service import NO_WIDER, ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig


def _desk(tmp_path, monkeypatch, mode: str) -> None:
    config = tmp_path / "config.json"
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", config)
    config.write_text(json.dumps({"control_mode": mode}), encoding="utf-8")


def _orchestrator(monkeypatch):
    from holdspeak.mcp import palettes

    store = AgentCredentialStore()
    agent = store.issue("agent:orchestrator", palette=palettes.resolve_palette("CONDUCTOR"), palette_name="CONDUCTOR",
                        launch_id="L-orch").principal
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    return agent


def _lines(rig: Rig, pid: str) -> list[str]:
    return [row["line"] for row in rig.program(pid)["checkpoints"]]


def test_an_agents_program_is_made_no_wider_than_the_desk_it_runs_under(tmp_path, monkeypatch) -> None:
    _desk(tmp_path, monkeypatch, "neutral")
    rig = Rig(tmp_path)
    agent = _orchestrator(monkeypatch)
    made = rig.service.create(agent, title="Mine", repository=str(rig.repo), control="yolo",
                              check_command=f"sh {FAKE_CHECK}")
    assert made["control"] == "normal"
    assert "Made at Normal: a program runs no wider than what made it" in _lines(rig, made["id"])
    # Narrower is always fine.
    assert rig.service.create(agent, title="Safe", repository=str(rig.repo), control="secure",
                              check_command=f"sh {FAKE_CHECK}")["control"] == "secure"


def test_an_agent_cannot_widen_its_program_and_the_owner_can(tmp_path, monkeypatch) -> None:
    _desk(tmp_path, monkeypatch, "neutral")
    rig = Rig(tmp_path)
    agent = _orchestrator(monkeypatch)
    pid = rig.service.create(agent, title="Mine", repository=str(rig.repo), control="normal",
                             check_command=f"sh {FAKE_CHECK}")["id"]
    with pytest.raises(ProgramRefused) as refused:
        rig.service.update(agent, pid, control="yolo")
    assert refused.value.code == "control_wider" and refused.value.detail.startswith(NO_WIDER)
    assert rig.program(pid)["control"] == "normal" and NO_WIDER in _lines(rig, pid)
    rig.service.update(agent, pid, control="secure")  # narrowing is the agent's to do
    assert rig.program(pid)["control"] == "secure"
    rig.service.update(OWNER, pid, control="yolo")  # his press is never refused
    assert rig.program(pid)["control"] == "yolo"
    rig.service.update(agent, pid, control="yolo")  # not wider than it is now
    assert rig.program(pid)["control"] == "yolo"


def test_the_text_cannot_widen_it_either(tmp_path, monkeypatch) -> None:
    _desk(tmp_path, monkeypatch, "safe")
    rig = Rig(tmp_path)
    agent = _orchestrator(monkeypatch)
    pid = rig.service.create(agent, title="Mine", repository=str(rig.repo), control="secure",
                             check_command=f"sh {FAKE_CHECK}")["id"]
    text = rig.service.text_get(agent, pid)["text"]
    wide = text.replace("control secure", "control yolo")
    assert wide != text
    answer = rig.service.text_apply(agent, pid, wide, dry_run=False)
    row = next(row for row in answer["changes"] if row["code"] == "control_wider")
    assert row["verdict"] == "refused" and row["reason"].startswith(NO_WIDER)
    assert not answer["applied"] and rig.program(pid)["control"] == "secure" and NO_WIDER in _lines(rig, pid)


def test_a_step_agent_a_handoff_a_race_entrant_and_a_helper_run_no_wider(tmp_path, monkeypatch) -> None:
    _desk(tmp_path, monkeypatch, "yolo")
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Careful", repository=str(rig.repo), control="secure",
                             check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x", "race": 2}, {"title": "Two", "brief": "y"}])
    steps = rig.service.store.list_steps(pid)
    # A step's launch (a handoff is the same step's next launch; a race
    # entrant is a step of the same Program) runs at the Program's control.
    for step in steps:
        request = {"origin_ref": {"kind": "program_step", "id": step["id"]}}
        assert mode_for_request(request, db=rig.db) == "safe"
    # A sub-agent (a helper of that launch) runs at its parent launch's level.
    row = steps[0]
    row["launch_id"] = "L-step"
    rig.service.store.save_step(row)
    assert mode_for_request({"helper_of": "L-step"}, db=rig.db) == "safe"
    # The step's agent may not make a wider Program than its own.
    from holdspeak.mcp import palettes

    store = AgentCredentialStore()
    step_agent = store.issue("agent:launch:L-step", palette=palettes.resolve_palette("CONDUCTOR"),
                             palette_name="CONDUCTOR", launch_id="L-step").principal
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    made = rig.service.create(step_agent, title="Its own", repository=str(rig.repo), control="yolo",
                              check_command=f"sh {FAKE_CHECK}")
    assert made["control"] == "secure"


def test_a_helper_is_never_wider_than_its_starter(tmp_path, monkeypatch) -> None:
    """Astra's post-merge check (2026-11-01): on a YOLO desk a Normal step's
    helper resolved its level through the desk (YOLO), so its own
    ``program.create(control="yolo")`` made a YOLO Program. A helper's level
    is its starter's, and never wider than the level it was started at."""
    from holdspeak.mcp import palettes
    from holdspeak.services.control_level import level_for_launch, mode_for_launch

    _desk(tmp_path, monkeypatch, "yolo")
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Careful", repository=str(rig.repo), control="normal",
                             check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    [step] = rig.service.store.list_steps(pid)
    step["launch_id"] = "L-step"
    rig.service.store.save_step(step)

    records = {
        "L-help": {"launch_id": "L-help", "helper_of": "L-step", "control_mode": "neutral"},
        "L-help2": {"launch_id": "L-help2", "helper_of": "L-help", "control_mode": "yolo"},
        "L-tight": {"launch_id": "L-tight", "helper_of": "L-step", "control_mode": "safe"},
        "L-desk": {"launch_id": "L-desk", "control_mode": "yolo"},
    }

    class _Ledger:
        def get(self, launch_id):
            return records.get(launch_id)

    monkeypatch.setattr("holdspeak.delivery.factory_launch.LaunchLedger", lambda *a, **k: _Ledger())
    assert level_for_launch("L-help", db=rig.db) == "normal"
    assert level_for_launch("L-help2", db=rig.db) == "normal"  # a helper's helper: still its root's
    assert level_for_launch("L-tight", db=rig.db) == "secure"  # started narrower: stays narrower
    assert mode_for_launch("L-help", db=rig.db) == "neutral"
    assert level_for_launch("L-desk", db=rig.db) == "yolo"  # not a helper: the desk

    store = AgentCredentialStore()
    helper = store.issue("agent:launch:L-help2", palette=palettes.resolve_palette("CONDUCTOR"),
                         palette_name="CONDUCTOR", launch_id="L-help2").principal
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    made = rig.service.create(helper, title="Its own", repository=str(rig.repo), control="yolo",
                              check_command=f"sh {FAKE_CHECK}")
    assert made["control"] == "normal"
    with pytest.raises(ProgramRefused) as refused:
        rig.service.update(helper, made["id"], control="yolo")
    assert refused.value.code == "control_wider"
