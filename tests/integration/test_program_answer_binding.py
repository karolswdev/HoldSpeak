"""Desk answers stay with the step and ledger revision the owner read."""
from __future__ import annotations

import pytest

from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import OWNER, Rig
from tests.integration.test_desk_programs import _client


def _binding(rig, pid, sid):
    wire = rig.program(pid)
    return {"step_id": sid, "revision": wire["revision"],
            "checkpoint_id": max((int(row["id"]) for row in wire["checkpoints"]), default=0)}


def _seed(tmp_path):
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Keep the answer", repository=str(rig.repo), control="secure")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "Keep one."}, {"title": "Two", "brief": "Keep two."}])
    return rig, pid, rig.step(pid, 1)["id"]


def test_a_park_answer_refuses_a_changed_ledger_without_a_program_state_change(tmp_path, monkeypatch):
    rig, pid, sid = _seed(tmp_path)
    binding = _binding(rig, pid, sid)
    rig.service.checkpoint(OWNER, pid, sid, "New evidence after the question opened")
    client = _client(rig, monkeypatch)
    answer = client.post(f"/api/programs/{pid}/park", json={"binding": binding})
    assert answer.status_code == 409, answer.json()
    assert answer.json()["code"] == "answer_stale"
    assert rig.program(pid)["state"] == "drafting"
    # Other channels have no new mandatory field.
    assert client.post(f"/api/programs/{pid}/park", json={}).status_code == 200


def test_a_decision_cannot_use_another_steps_binding(tmp_path):
    rig, pid, sid = _seed(tmp_path)
    other = rig.step(pid, 2)["id"]
    with pytest.raises(ProgramRefused, match="changed"):
        rig.service.decide(OWNER, pid, other, kind="core", choice="go_on", binding=_binding(rig, pid, sid))
    assert rig.step(pid, 2)["state"] == "planned"


def test_text_apply_rechecks_the_question_revision_even_when_text_did_not_change(tmp_path, monkeypatch):
    rig, pid, sid = _seed(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    binding = _binding(rig, pid, sid)
    rig.service.checkpoint(OWNER, pid, sid, "The agent supplied new evidence")
    client = _client(rig, monkeypatch)
    answer = client.post(f"/api/programs/{pid}/text", json={"text": text, "base": text, "dry_run": False, "binding": binding})
    assert answer.status_code == 409, answer.json()
    assert answer.json()["code"] == "answer_stale"
    assert rig.service.text_get(OWNER, pid)["text"] == text


def test_live_window_tape_is_recorded_through_the_real_service(tmp_path, monkeypatch):
    """One program before/after each press. No hand-written response bodies."""
    import json
    import os
    from pathlib import Path

    from tests.integration.program_rig import FAKE_CHECK

    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Keep the program moving", goal="Keep the work and its proof together.",
                             repository=str(rig.repo), template="fast-cycle", control="yolo",
                             check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Store the stall reason", "brief": "Store the reason on the step.", "owns": ["reason.txt"]},
        {"title": "Show the reason", "brief": "Show the saved reason.", "after": [1], "owns": ["show.txt"]},
        {"title": "Write the recap", "brief": "Keep the recap in the project.", "after": [2], "owns": ["recap.txt"]},
    ])
    # The same list producer supplies the six-state master in the glass.
    def sibling(title):
        return rig.service.create(OWNER, title=title, repository=str(rig.repo), template="fast-cycle",
                                  control="yolo", check_command=f"sh {FAKE_CHECK}")["id"]
    calls = sibling("Calls on the home box")
    rig.service.plan(OWNER, calls, steps=[{"title": "Read the call log", "brief": "Read the call log.", "owns": ["calls.txt"]}])
    rig.service.start(OWNER, calls)
    earlier = sibling("Ship the wizard")
    rig.service.plan(OWNER, earlier, steps=[{"title": "Keep the fields", "brief": "Keep the entered fields."}])
    rig.service.park(OWNER, earlier)
    for title in ("Move the People routes", "Draft replies"):
        history = sibling(title)
        rig.service.plan(OWNER, history, steps=[{"title": title, "history": {"pr_number": 12, "merged_at": "2026-11-10T12:00:00+00:00"}}])
    night = sibling("Triage the inbox")
    rig.service.plan(OWNER, night, steps=[{"title": "Read the inbox", "brief": "Read the kept inbox.", "owns": ["inbox.txt"]}])
    rig.service.update(OWNER, night, night="23:00–07:00")
    rig.service.start(OWNER, night)
    client = _client(rig, monkeypatch)
    tape = {"drafting": client.get(f"/api/programs/{pid}").json()}
    tape["drafting_text"] = client.get(f"/api/programs/{pid}/text").json()
    changed_text = tape["drafting_text"]["text"].replace("program Keep the program moving", "program Keep the program moving today")
    text_body = {"text": changed_text, "base": tape["drafting_text"]["text"], "binding": _binding(rig, pid, "")}
    tape["text_preview"] = client.post(f"/api/programs/{pid}/text", json={**text_body, "dry_run": True}).json()
    tape["text_applied"] = client.post(f"/api/programs/{pid}/text", json={**text_body, "dry_run": False}).json()
    assert tape["text_applied"]["applied"]
    rig.service.start(OWNER, pid)
    rig.tick()
    tape["running_list"] = client.get("/api/programs").json()
    tape["running_text"] = client.get(f"/api/programs/{pid}/text").json()
    tape["running"] = client.get(f"/api/programs/{pid}").json()
    sid = rig.step(pid, 1)["id"]
    rig.service.checkpoint(OWNER, pid, sid, "Read the saved step reason")
    tape["running_next"] = client.get(f"/api/programs/{pid}").json()
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"reason.txt": "The reason stays.\n", "extra.txt": "Also changed.\n"})
    rig.tick()
    tape["waiting"] = client.get(f"/api/programs/{pid}").json()
    tape["waiting_list"] = client.get("/api/programs").json()
    assert tape["waiting"]["your_turn_items"][0]["kind"] == "core"
    binding = _binding(rig, pid, sid)
    rig.service.checkpoint(OWNER, pid, sid, "The check has new evidence")
    tape["stale_program"] = client.get(f"/api/programs/{pid}").json()
    stale = client.post(f"/api/programs/{pid}/steps/{sid}/decide", json={"kind": "core", "choice": "go_on", "binding": binding})
    assert stale.status_code == 409
    tape["stale_answer"] = stale.json()
    tape["go_on"] = client.post(f"/api/programs/{pid}/steps/{sid}/decide", json={"kind": "core", "choice": "go_on", "binding": _binding(rig, pid, sid)}).json()
    assert "program" in tape["go_on"]
    rig.tick(3)
    tape["advanced"] = client.get(f"/api/programs/{pid}").json()
    tape["advanced_list"] = client.get("/api/programs").json()
    tape["parked"] = client.post(f"/api/programs/{pid}/park", json={"binding": _binding(rig, pid, sid)}).json()
    tape["parked_list"] = client.get("/api/programs").json()
    tape["resumed"] = client.post(f"/api/programs/{pid}/resume", json={}).json()
    for ordinal, filename in ((2, "show.txt"), (3, "recap.txt")):
        rig.tick(3)
        step = rig.step(pid, ordinal)
        assert step["launch_id"], step
        rig.agent.finish(step["launch_id"], {filename: "The result stays.\n"})
        rig.tick(4)
    tape["done"] = client.get(f"/api/programs/{pid}").json()
    assert tape["done"]["state"] == "done"
    tape["tonight"] = client.get(f"/api/programs/{night}").json()
    tape["list"] = client.get("/api/programs").json()
    tape["text"] = client.get(f"/api/programs/{pid}/text").json()
    path = Path(__file__).resolve().parents[2] / "web/src/desk/programs/__fixtures__/program.live10.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps(tape, sort_keys=True, separators=(",", ":")) + "\n")
    assert path.exists(), "Record this producer with HOLDSPEAK_WIRE_WRITE=1"
