"""Phone (2026-10-28): the whole channel through the real hub (design §13, PH-HUB).

The hub is the real ``MeetingWebServer`` on an isolated HOME and database
(``tests/unit/test_desk_needs_you._boot``). The phone is the fake device
(``tests/fixtures/fake_phone_device.py``): it pairs through the real routes,
reads and streams the event log, answers or ignores a call, replies. A call
on the number runs through the Calls rig: the fake ai-phone CLI (a real
separate process, ``tests/fixtures/fake_ai_phone.py``) and the Calls turn
loop with a scripted turn (the engine is not under test here).
"""
from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from holdspeak.principals import Principal, PrincipalKind
from tests.fixtures.fake_phone_device import FakePhoneDevice
from tests.unit.test_desk_needs_you import _boot

pytestmark = pytest.mark.timeout(120, method="thread")

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
AGENT = Principal(PrincipalKind.AGENT, "agent-test")
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FAKE = FIXTURES / "fake_ai_phone.py"
PASSPHRASE = "blue heron"
NUMBER = "+12125550142"


class _NoNumber:
    def number(self) -> str:
        return ""

    def available(self) -> tuple[bool, str]:
        return False, "your number is not set in Settings ▸ Calls"

    def sms_available(self) -> bool:
        return False


class ScriptedTurns:
    """The call's turn: says what a hand answers, after ``delay`` seconds."""

    def __init__(self, answers: list[str], *, delay: float = 0.0) -> None:
        self.answers = list(answers)
        self.delay = delay
        self.context = ""
        self.asked: list[str] = []

    def new_thread(self, title: str) -> str:
        return "thread-call"

    def set_context(self, context: str) -> None:
        self.context = context

    async def run(self, thread_id: str, text: str, *, holds: Callable[[list[dict[str, Any]]], None]) -> dict[str, Any]:
        self.asked.append(text)
        if self.delay:
            await asyncio.sleep(self.delay)
        return {"text": self.answers.pop(0) if self.answers else "Done.", "used": {}, "error": None}

    def hold_words(self, tool_call_id: str, tool: str) -> str:
        return "Change your desk"

    def decide(self, tool_call_id: str, decision: str) -> bool:
        return True


@pytest.fixture
def hub(tmp_path, monkeypatch):
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _phone(hub: Any, monkeypatch: pytest.MonkeyPatch, **kwargs: Any) -> Any:
    """The hub's one Phone service, with a null push and short ring timers."""
    from holdspeak.phone import service as phone_module
    from holdspeak.phone.push import NullPush

    kwargs.setdefault("push", NullPush())
    kwargs.setdefault("ring_seconds", 0.4)
    kwargs.setdefault("rering_seconds", 0.4)
    service = phone_module.PhoneService(_db(hub), **kwargs)
    monkeypatch.setattr(phone_module, "_DEFAULT", service)
    monkeypatch.setattr(phone_module, "_DEFAULT_DB", _db(hub))
    return service


def _db(hub: Any) -> Any:
    from holdspeak.db import get_database
    from holdspeak.runtime import composition

    return composition.db_or(get_database)


def _paired(hub: Any) -> FakePhoneDevice:
    response = hub.client.post("/api/phone/pair")
    assert response.status_code == 201, response.text
    body = response.json()
    qr = json.loads(body["qr_payload"])
    assert qr["pair_token"] == body["token"] and qr["hub_urls"], qr
    device = FakePhoneDevice(hub.client)
    device.pair(qr["pair_token"])
    return device


def _wait(predicate: Callable[[], Any], seconds: float = 15.0) -> Any:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("the hub did not get there in time")


def _needs_phone(hub: Any) -> list[dict[str, Any]]:
    response = hub.client.get("/api/desk/needs-you?fresh=1")
    assert response.status_code == 200, response.text
    return [row for row in response.json()["items"] if row.get("source") == "phone"]


# ── messages ────────────────────────────────────────────────────────────

def test_a_paired_phone_gets_the_message_replies_and_get_replies_reads_it_once(hub, monkeypatch) -> None:
    from holdspeak.mcp.tools import dispatch

    phone = _phone(hub, monkeypatch)
    device = _paired(hub)
    assert hub.client.get("/api/phone/devices").json()["devices"][0]["name"] == "Karol's iPhone"

    sent = dispatch("phone.send_message", {"text": "The nightly build is red. Retry it now?"}, AGENT)
    assert sent["direction"] == "to_phone"
    [pushed] = phone.push().sent
    assert pushed["kind"] == "message" and pushed["device_id"] == device.device_id
    # The push is signed with the device's own secret: the app can check it.
    from holdspeak.phone.push import sign

    assert pushed["payload"]["sig"] == sign(device.push_secret, pushed["payload"]["event"])

    events = device.events()
    [message] = FakePhoneDevice.messages_in(events)
    assert message["text"] == "The nightly build is red. Retry it now?"
    device.read(message["id"])
    device.reply("Yes, retry it.", message["id"])

    first = dispatch("phone.get_replies", {"wait_s": 0}, AGENT)
    assert [row["text"] for row in first["replies"]] == ["Yes, retry it."]
    assert first["replies"][0]["reply_to"] == message["id"]
    again = dispatch("phone.get_replies", {"wait_s": 0}, AGENT)
    assert again["replies"] == [] and "Silence is never consent" in again["note"]
    # The desk's own read shows the reply threaded under the question.
    thread = hub.client.get("/api/phone/messages").json()["messages"]
    assert [row["direction"] for row in thread] == ["to_phone", "from_phone"]


def test_get_replies_waits_for_the_reply_instead_of_polling(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch)
    device = _paired(hub)
    asked = phone.send_from_desk("Merge the runbook PR?")
    threading.Timer(0.3, lambda: device.reply("Merge it.", asked["id"])).start()
    started = time.monotonic()
    got = phone.get_replies(10)
    assert [row["text"] for row in got["replies"]] == ["Merge it."]
    assert time.monotonic() - started < 8


# ── calls ───────────────────────────────────────────────────────────────

def _fake_ai_phone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, listens: list[dict[str, Any]]) -> Path:
    from holdspeak.calls import aiphone

    script = tmp_path / "scenario.json"
    script.write_text(json.dumps({"listen": listens}))
    state = tmp_path / "fake-state.json"
    monkeypatch.setenv("FAKE_AI_PHONE_SCRIPT", str(script))
    monkeypatch.setenv("FAKE_AI_PHONE_STATE", str(state))
    monkeypatch.setenv(aiphone.COMMAND_ENV, f"{sys.executable} {FAKE}")
    monkeypatch.setenv(aiphone.HOME_ENV, str(tmp_path / "ai-phone-home"))
    return state


def _calls_config(home: Path) -> None:
    import holdspeak.config as config_module

    path = Path(config_module.CONFIG_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text()) if path.exists() else {}
    data["calls"] = {"enabled": False, "passphrase": PASSPHRASE, "allowed_numbers": [NUMBER]}
    path.write_text(json.dumps(data))


@pytest.fixture
def calls_loop():
    """The hub's loop for Calls: a real event loop on its own thread."""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    yield loop
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)


def _said(state: Path) -> list[str]:
    out = []
    for entry in json.loads(state.read_text())["log"]:
        if entry[0] == "say":
            out.append(entry[1])
        elif entry[0] == "hangup" and "--say" in entry:
            out.append(entry[entry.index("--say") + 1])
    return out


def test_phone_call_on_the_number_runs_through_calls_and_returns_the_transcript_and_decision(
        hub, monkeypatch, tmp_path, calls_loop) -> None:
    from holdspeak.calls.service import CallsService
    from holdspeak.mcp.tools import dispatch
    from holdspeak.phone.transport_number import NumberTransport

    _calls_config(tmp_path)
    state = _fake_ai_phone(tmp_path, monkeypatch, [
        {"kind": "heard", "text": "Blue heron."},
        {"kind": "heard", "text": "Yes, merge it."},
        {"kind": "heard", "text": "That's all, thanks."},
    ])
    turns = ScriptedTurns(["Good. I will merge the runbook step."])
    calls = CallsService()
    calls.configure(db=lambda: _db(hub), turns=lambda: turns, broadcast=lambda *_: None)
    calls.bind_loop(calls_loop)
    phone = _phone(hub, monkeypatch, number=NumberTransport(lambda: calls))

    answer = dispatch("phone.call", {
        "reason": "The runbook step is green and reviewed and waits to merge.",
        "context": "Tell him the step is green. Ask: merge it now? Do not decide for him.",
    }, OWNER)

    assert answer["state"] == "ended", answer
    assert answer["decision"] == {"kind": "answer", "answer": "approve", "words": "Yes, merge it."}
    assert {"who": "you", "text": "Yes, merge it."} in answer["transcript"]
    assert answer["end_reason"] and answer["duration_s"] is not None
    said = _said(state)
    assert said[0] == "Hello. Say your passphrase."  # the Calls gate, as built
    assert said[1].startswith("This is HoldSpeak. I am calling because the runbook step is green")
    assert turns.context.startswith("Tell him the step is green")  # the context briefs the turn
    row = phone.store.list_calls()[0]
    assert row["transport"] == "number" and row["calls_turn_id"] and row["state"] == "ended"
    assert json.loads(state.read_text())["log"][0][:2] == ["call", NUMBER]


def test_a_slow_hand_says_working_on_it_and_answers_as_a_message_after_the_hang_up(
        hub, monkeypatch, tmp_path, calls_loop) -> None:
    from holdspeak.calls import runner
    from holdspeak.calls.service import CallsService
    from holdspeak.phone.transport_number import NumberTransport

    monkeypatch.setattr(runner, "ANSWER_LATER_SECONDS", 0.3)
    monkeypatch.setattr(runner, "KEEPALIVE_SECONDS", 0.1)
    _calls_config(tmp_path)
    state = _fake_ai_phone(tmp_path, monkeypatch, [
        {"kind": "heard", "text": "Blue heron."},
        {"kind": "heard", "text": "What did CI say on the runbook PR?"},
        {"kind": "heard", "text": "That's all, thanks."},
    ])
    turns = ScriptedTurns(["CI is green on the runbook PR."], delay=2.5)
    calls = CallsService()
    calls.configure(db=lambda: _db(hub), turns=lambda: turns, broadcast=lambda *_: None)
    calls.bind_loop(calls_loop)
    phone = _phone(hub, monkeypatch, number=NumberTransport(lambda: calls))

    answer = phone.call(OWNER, reason="You asked me to call", wait=True)
    assert answer["state"] == "ended"
    assert runner.WORKING_ON_IT in _said(state)
    later = _wait(lambda: [row for row in phone.store.recent_messages()
                           if (row.get("origin_ref") or "").startswith("call:")])
    assert later[0]["direction"] == "to_phone" and later[0]["text"] == "CI is green on the runbook PR."


def test_a_call_the_phone_does_not_answer_becomes_a_missed_message_and_a_needs_you_row(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    device.answer_calls = False
    made = phone.call(OWNER, reason="The deploy waits for your go", wait=False)
    assert made["state"] == "ringing"
    invite = [e for e in device.events() if e["type"] == "call.invite"]
    assert invite and invite[0]["data"]["expires_at"]
    assert any(p["kind"] == "call" for p in phone.push().sent)  # the VoIP push rang it
    _wait(lambda: phone.store.get_call(made["call_id"])["state"] == "missed"
          and phone.store.recent_messages())
    [missed] = [row for row in phone.store.recent_messages() if row["origin_ref"] == f"phone_call:{made['call_id']}"]
    assert missed["text"] == "Missed call: The deploy waits for your go. Reply here, or call the desk."
    [row] = _needs_phone(hub)
    assert row["title"] == "Missed call: The deploy waits for your go" and row["phone"]["kind"] == "missed_call"
    assert [verb["label"] for verb in row["phone"]["verbs"]] == ["Call again", "Answer here"]
    # Answer here: his reply at the desk ends the row and reaches the waiting agent.
    answer = row["phone"]["verbs"][1]
    hub.client.post(answer["href"], json={**answer["body"], "text": "Go."})
    assert _needs_phone(hub) == []
    assert [r["text"] for r in phone.get_replies(0)["replies"]] == ["Go."]


def test_an_urgent_call_rings_once_more_then_is_missed(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    made = phone.call(OWNER, reason="Production lost data", urgent=True)
    _wait(lambda: phone.store.get_call(made["call_id"])["state"] == "missed"
          and phone.timers.rings(made["call_id"]) == 2
          and any(r["origin_ref"] == f"phone_call:{made['call_id']}" for r in phone.store.recent_messages()))
    invites = [e for e in device.events() if e["type"] == "call.invite"]
    assert len(invites) == 2


def test_an_answered_call_is_accepted_and_ended_by_the_phone(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    made = phone.call(OWNER, reason="A question on the plan")
    taken = device.handle(device.events())
    assert taken == [made["call_id"]]
    ended = device.end(made["call_id"])
    assert ended.status_code == 200 and ended.json()["state"] == "ended" and ended.json()["end_reason"] == "hung_up"
    assert device.get(f"/api/phone/calls/{made['call_id']}").json()["state"] == "ended"


def test_an_agents_call_waits_for_his_press_in_needs_you(hub, monkeypatch) -> None:
    from holdspeak.mcp.tools import dispatch

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    held = dispatch("phone.call", {"reason": "The schema step wants to drop a column."}, AGENT)
    assert held["state"] == "held" and "Needs you" in held["words"]
    [row] = _needs_phone(hub)
    assert row["title"] == "Call you about the schema step wants to drop a column?"
    call_now = row["phone"]["verbs"][0]
    assert call_now["label"] == "Call now"
    assert hub.client.post(call_now["href"]).json()["state"] == "ringing"
    assert phone.store.get_call(held["call_id"])["state"] == "ringing"


# ── reach and quiet hours ───────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _daytime(hub, request):
    """The rig's quiet hours default to 22–08 (the desk's one store), so a
    test that expects a reach at night was red between 22:00 and 08:00
    (2026-10-29, found by the Line lane's quick check at 05:54). Every test
    here starts outside quiet hours; the quiet-hours test moves them back
    over now itself."""
    from holdspeak.services.heartbeat_service import HeartbeatService
    from holdspeak.timestamps import local_now

    hour = local_now().hour
    HeartbeatService(_db(hub)).update_settings({"quiet_hours": {"start": (hour + 3) % 24, "end": (hour + 4) % 24}})



def _quiet_now(db: Any) -> None:
    from holdspeak.services.heartbeat_service import HeartbeatService
    from holdspeak.timestamps import local_now

    hour = local_now().hour
    HeartbeatService(db).update_settings({"quiet_hours": {"start": hour, "end": (hour + 1) % 24}})


def test_quiet_hours_hold_a_message_and_let_an_urgent_call_through(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _quiet_now(_db(hub))
    held = phone.reach("agent_question", level="normal", text="Which branch is the release?",
                       origin_ref="agent:test:1")
    assert held["held"] and held["queued"] and held["line"] == "Reached you: a message, held for the morning"
    assert phone.push().sent == []  # nothing buzzed at night
    assert phone.store.get_message(held["msg_id"])["delivered_at"] is None
    urgent = phone.reach("heartbeat_security", level="yolo", text="A token leaked in the build log.",
                         origin_ref="heartbeat:finding:1")
    assert urgent["channel"] == "call" and urgent["urgent"] and not urgent["held"]
    assert [p["kind"] for p in phone.push().sent] == ["call"]
    # Every reach is a phone.reach kernel operation with its rule.
    with _db(hub)._connection() as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM kernel_operations").fetchall()]
    assert names.count("phone.reach") == 2


def test_the_rules_per_level_through_the_service(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    assert phone.reach("program_done", level="secure", text="Done.", origin_ref="p:1")["held"]
    assert phone.reach("program_done", level="normal", text="Done.", origin_ref="p:2")["channel"] == "message"
    core = phone.reach("core_question", level="yolo", text="Drop the old table?", origin_ref="p:3", may_call=True)
    assert core["channel"] == "call"
    phone.end(core["call_id"])
    again = phone.reach("core_question", level="yolo", text="Drop the old table?", origin_ref="p:3", may_call=True)
    assert again["held"] and "minutes ago" in again["why"]  # never twice in 5 minutes


def test_a_programs_core_question_reaches_the_phone_with_a_decided_for_you_line(hub, monkeypatch, tmp_path) -> None:
    from holdspeak.services.program_service import ProgramService
    from tests.integration.program_rig import make_repo

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    programs = ProgramService(_db(hub), phone=lambda: phone)
    repo = make_repo(tmp_path / "git")
    made = programs.create(OWNER, title="Night work", repository=str(repo), control="normal", check_command="true")
    programs.plan(OWNER, made["id"], steps=[{"title": "Schema", "brief": "Add the table."}])
    program = programs.store.get_program(made["id"])
    step = programs.store.list_steps(made["id"])[0]
    programs.runner().raise_core(program, step, "diff", "a migration drops or rewrites rows")
    [message] = [row for row in phone.store.recent_messages() if row["program_step_id"] == step["id"]]
    assert message["text"].startswith("Night work, step 1: a question for you.")
    decided = programs.get(OWNER, made["id"])["decided_for_you"]
    reach = next(row for row in decided if row["kind"] == "reach")
    assert reach["line"] == "Reached you: a message" and reach["rule"] == "Normal: a core question is a message first"


# ── the event log, revoke, the switch ───────────────────────────────────

def test_the_event_log_replays_from_after_seq_after_a_reconnect(hub, monkeypatch) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    first, _ = device.stream(after_seq=0, until=lambda e: e.get("type") == "device.paired")
    assert first[0]["type"] == "hello" and first[0]["data"]["last_seq"] >= 1
    seen = device.last_seq
    phone.send_from_desk("One.")
    phone.send_from_desk("Two.")
    again, _ = device.stream(after_seq=seen, until=lambda e: e.get("data", {}).get("message", {}).get("text") == "Two.")
    texts = [e["data"]["message"]["text"] for e in again if e["type"] == "message.new"]
    assert texts == ["One.", "Two."]
    assert all(e["seq"] > seen for e in again if e.get("seq"))
    # live: an event written while the socket is open arrives on it
    live, _ = device.stream(between=lambda: phone.send_from_desk("Three."),
                            until=lambda e: e.get("data", {}).get("message", {}).get("text") == "Three.")
    assert live[-1]["data"]["message"]["text"] == "Three."


def test_a_revoked_phone_gets_401_and_its_socket_closes(hub, monkeypatch) -> None:
    _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    assert device.get("/api/phone/messages").status_code == 200
    assert device.get("/api/phone/status").status_code == 401  # an owner route
    revoked: list[Any] = []
    got, closed = device.stream(between=lambda: revoked.append(hub.client.delete(f"/api/phone/devices/{device.device_id}")))
    assert revoked[0].status_code == 200, revoked[0].text
    assert closed is not None and getattr(closed, "code", None) == 4401, (got, closed)
    assert device.get("/api/phone/messages").status_code == 401
    assert device.post("/api/phone/messages", {"text": "hi"}).status_code == 401
    # no hub token, no device token: refused
    assert hub.client.get("/api/phone/events", headers={"Authorization": "", "X-HoldSpeak-Token": ""}).status_code == 401
    # a device may not do the owner's verbs
    assert device.post("/api/phone/pair").status_code in (401, 403)


@pytest.fixture
def hub_off(tmp_path, monkeypatch):
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition

    monkeypatch.setenv("HOLDSPEAK_PHONE", "off")
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_phone_off_registers_nothing(hub_off) -> None:
    hub = hub_off
    assert hub.client.get("/api/phone/status").status_code == 404
    assert hub.client.post("/api/phone/pair").status_code == 404
    from holdspeak.mcp.tools import dispatch
    from holdspeak.phone.service import PhoneRefused

    with pytest.raises(PhoneRefused, match="off"):
        dispatch("phone.status", {}, OWNER)
    from holdspeak.phone.service import default_phone_service

    assert default_phone_service(_db(hub)).needs_you_items() == []
