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
    tape["running_frame"] = next(payload for kind, payload in reversed(rig.frames) if kind == "program_changed")
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
    tape["advanced_frame"] = next(payload for kind, payload in reversed(rig.frames) if kind == "program_changed")
    rig.service.checkpoint(OWNER, pid, rig.step(pid, 2)["id"], "Read the saved step reason")
    tape["advanced_next"] = client.get(f"/api/programs/{pid}").json()
    tape["advanced_next_frame"] = next(payload for kind, payload in reversed(rig.frames) if kind == "program_changed")
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


def test_remove_is_the_same_declared_operation_over_http(tmp_path, monkeypatch):
    rig, pid, sid = _seed(tmp_path)
    answer = _client(rig, monkeypatch).delete(f"/api/programs/{pid}/steps/{sid}")
    assert answer.status_code == 200, answer.json()
    assert all(row["id"] != sid for row in rig.program(pid)["steps"])


def test_briefing_page_keeps_the_read_question_and_can_read_a_fresh_one(tmp_path):
    from tests.unit.test_reach_packages import _core, _briefing, _ref

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    ref = _ref(pid, item)
    made = briefing.make(OWNER, [ref])
    shown = briefing.read(made["token"])["items"][0]
    rig.service.checkpoint(OWNER, pid, item["step_id"], "New proof after the page was read")
    with pytest.raises(ProgramRefused) as stale:
        briefing.answer(made["token"], ref, "go_on", binding=shown.get("binding"))
    assert stale.value.code == "answer_stale"
    assert stale.value.detail == "This question changed. Read it again."
    assert rig.program(pid)["your_turn_items"][0]["kind"] == "core"
    fresh = briefing.read(made["token"])["items"][0]
    assert fresh["binding"]["program_id"] == pid
    assert fresh["binding"]["step_id"] == item["step_id"]
    assert fresh["binding"] != shown["binding"]
    assert briefing.answer(made["token"], ref, "go_on", binding=fresh["binding"])["item"]["state"] == "decided"


def test_telegram_callback_carries_the_message_question_not_a_newer_one(tmp_path, monkeypatch):
    from tests.unit.test_reach_telegram import Desk, _message

    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    made = desk.telegram.brief(f"program:{pid}:{item['id']}")
    message = _message(desk)
    desk.rig.service.checkpoint(OWNER, pid, item["step_id"], "New proof after Telegram sent the question")
    answer = desk.tap(message, f"r1|{made['id']}|go_on")
    assert answer["action"] == "refused", answer
    assert answer["code"] == "answer_stale"
    assert answer["words"] == "This question changed. Read it again."
    assert desk.rig.program(pid)["your_turn_items"][0]["kind"] == "core"
    assert any("This question changed. Read it again." in row["text"] for row in desk.bot.of("editMessageText"))


def test_phone_message_identity_keeps_its_frozen_question_binding(tmp_path, monkeypatch):
    from holdspeak.phone import actions
    from holdspeak.phone.service import PhoneService
    from tests.unit.test_reach_packages import _core, _briefing

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    monkeypatch.setattr(actions, "_briefing", lambda db: briefing)
    phone = PhoneService(rig.db)
    monkeypatch.setattr(phone, "_quiet", lambda: True)
    message = phone.send_from_desk("The step waits on you", origin_ref=f"program_step:{item['step_id']}:core",
                                   program_step_id=item["step_id"])
    shown = phone.messages()["messages"][0]["actions"]
    rig.service.checkpoint(OWNER, pid, item["step_id"], "New proof after the phone received the question")
    assert phone.messages()["messages"][0]["actions"] == shown
    with pytest.raises(ProgramRefused) as stale:
        phone.decide(message["id"], "go_on")
    assert stale.value.code == "answer_stale"
    assert stale.value.detail == "This question changed. Read it again."
    assert rig.program(pid)["your_turn_items"][0]["kind"] == "core"


def test_call_answer_carries_the_question_that_was_read_aloud(tmp_path):
    from holdspeak.calls.decide import DeskHeld
    from tests.unit.test_reach_packages import _core, _briefing, _ref

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    shown = briefing.compose(_ref(pid, item))
    rig.service.checkpoint(OWNER, pid, item["step_id"], "New proof while the call waited for an answer")
    with pytest.raises(ProgramRefused) as stale:
        briefing.decide_item(OWNER, shown["ref"], "go_on", via="call", binding=shown.get("binding"))
    assert stale.value.code == "answer_stale"
    assert rig.program(pid)["your_turn_items"][0]["kind"] == "core"


def test_program_seats_keep_requirement_edits_language_and_answer_notes(tmp_path, monkeypatch):
    """The new inspector seats replay these real operation answers in T2."""
    import json
    import os
    from pathlib import Path

    rig, pid, sid = _seed(tmp_path)
    client = _client(rig, monkeypatch)
    out = {"program": client.get(f"/api/programs/{pid}").json()}
    added = client.post(f"/api/programs/{pid}/requirements", json={"text": "Keep the answer with its question.", "kind": "word", "step_id": sid})
    assert added.status_code == 201, added.json()
    out["requirement_added"] = added.json()
    rid = added.json()["requirement_id"]
    edited = client.patch(f"/api/programs/{pid}/requirements/{rid}", json={"text": "Keep the answer and its note."})
    assert edited.status_code == 200, edited.json()
    out["requirement_edited"] = edited.json()
    raced = client.post(f"/api/programs/{pid}/steps/{sid}/race", json={"n": 3})
    assert raced.status_code == 200, raced.json()
    out["race_three"] = raced.json()
    language = client.patch(f"/api/programs/{pid}", json={"goal": "Keep each question and answer together.", "prefer_idle": True, "may_call": True, "allowed_profiles": ["claude-default", "codex-default"], "may_handoff": True, "spend_limit_usd": 40, "review_depth": "delta", "night": "23:00–07:00"})
    assert language.status_code == 200, language.json()
    out["language_saved"] = language.json()
    binding = rig.service._answer_binding(rig.service._program(pid), rig.service._step(rig.service._program(pid), sid))
    answered = client.post(f"/api/programs/{pid}/requirements/{rid}/decide", json={"choice": "met", "line": "I read the result.", "binding": binding})
    assert answered.status_code == 200, answered.json()
    out["requirement_answered"] = answered.json()
    parked = client.post(f"/api/programs/{pid}/park", json={"note": "Wait until the review is ready.", "binding": rig.service._answer_binding(rig.service._program(pid), None)})
    assert parked.status_code == 200, parked.json()
    out["park_note"] = parked.json()
    assert any("Wait until the review is ready." in row["line"] for row in out["park_note"]["checkpoints"])
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        (Path(__file__).resolve().parents[2] / "web/src/desk/programs/__fixtures__/program.seats10.json").write_text(json.dumps(out, sort_keys=True) + "\n")


def test_a_core_answer_keeps_its_optional_note_in_the_rendered_ledger(tmp_path):
    from tests.unit.test_reach_packages import _core
    rig, pid, item = _core(tmp_path)
    program = rig.service._program(pid)
    binding = rig.service._answer_binding(program, rig.service._step(program, item["step_id"]))
    answer = rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on", reason="I read the extra change.", binding=binding)
    assert any(row["line"] == "Answer note: I read the extra change." for row in answer["program"]["checkpoints"])


def test_a_removed_steps_question_has_the_same_named_stale_refusal(tmp_path):
    rig, pid, sid = _seed(tmp_path)
    program = rig.service._program(pid)
    binding = rig.service._answer_binding(program, rig.service._step(program, sid))
    rig.service.remove_step(OWNER, pid, sid)
    with pytest.raises(ProgramRefused) as stale:
        rig.service.decide(OWNER, pid, sid, kind="core", choice="go_on", binding=binding)
    assert stale.value.code == "answer_stale"
    assert stale.value.detail == "This question changed. Read it again."


def test_a_spoken_text_apply_keeps_the_question_read_back_before_yes(tmp_path, monkeypatch):
    from tests.integration.program_shape_seed import SENTENCES, seed
    from tests.unit.test_program_shaper import reply, wire_engine
    from holdspeak.services import program_spoken

    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig, control="normal")
    engine.replies = [reply("shape")]
    held = program_spoken.prepare(rig.service, OWNER, {"program_id": pid, "sentence": SENTENCES["shape"]})
    assert held and held["state"] == "asked"
    before = rig.service.text_get(OWNER, pid)["text"]
    rig.service.checkpoint(OWNER, pid, rig.step(pid, 1)["id"], "New proof after the changes were read aloud")
    with pytest.raises(ProgramRefused) as stale:
        program_spoken.run(rig.service, OWNER, {**held, "state": "yes"})
    assert stale.value.code == "answer_stale"
    assert stale.value.detail == "This question changed. Read it again."
    assert rig.service.text_get(OWNER, pid)["text"] == before
