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
    # DIR8a: the call keeps the reach rule's because for the call to read and record.
    assert phone._because[core["call_id"]] == {"rule": core["rule"], "kind": "core", "words": "a question",
                                               "level": "yolo", "reach": "core_question"}
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


# ── PHONE-APNS-KEY: his Apple push key through the real routes ──────────

def test_the_push_key_saves_through_the_routes_never_comes_back_and_the_test_push_reaches_the_fake_apns(
        hub, monkeypatch) -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from tests.fixtures.fake_apns import FakeApns

    pem = ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    with FakeApns(answers={"fake-push-token": (403, {"reason": "InvalidProviderToken"})}) as apns:
        _phone(hub, monkeypatch, push=None, apns_host=apns.url, number=_NoNumber())
        device = _paired(hub)
        before = hub.client.get("/api/phone/push")
        assert before.status_code == 200 and before.json()["push_state"] == "no_key", before.text
        assert hub.client.get("/api/phone/status").json()["devices"][0]["push_state"] == "no_key"
        for body in ({"p8": pem}, {"key_id": "KEY1234567"}, {"team_id": "TEAM123456"}):
            saved = hub.client.put("/api/phone/push", json=body)
            assert saved.status_code == 200, saved.text
            assert "PRIVATE KEY" not in saved.text
        after = hub.client.get("/api/phone/push")
        assert after.json() == {"present": {"p8": True, "key_id": True, "team_id": True},
                                "bundle_id": "dev.holdspeak.mobile", "host": "app_store", "push_state": "ready"}
        assert "PRIVATE KEY" not in after.text
        # Builds from: the choice is stored beside the key and comes back on the wire
        chosen = hub.client.put("/api/phone/push", json={"host": "development"})
        assert chosen.status_code == 200 and chosen.json()["host"] == "development", chosen.text
        assert hub.client.get("/api/phone/push").json()["host"] == "development"
        wrong = hub.client.put("/api/phone/push", json={"host": "testflight"})
        assert wrong.status_code == 400 and wrong.json()["code"] == "bad_host"
        assert hub.client.get("/api/phone/push").json()["host"] == "development"
        assert hub.client.get("/api/phone/status").json()["devices"][0]["push_state"] == "ready"
        refused = hub.client.put("/api/phone/push", json={"p8": "hello"})
        assert refused.status_code == 400 and refused.json()["code"] == "not_a_p8"
        tested = hub.client.post("/api/phone/push/test")
        assert tested.status_code == 200, tested.text
        assert tested.json()["answer"] == "refused" and tested.json()["status"] == 403
        assert [request["path"] for request in apns.requests] == ["/3/device/fake-push-token"]
        # a phone may not read, save or test the key
        assert device.get("/api/phone/push").status_code in (401, 403)
        assert device.post("/api/phone/push/test").status_code in (401, 403)


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


# ── PH12: the other reach kinds, at the places that write their rows ─────

def _level(monkeypatch: pytest.MonkeyPatch, level: str) -> None:
    """The desk's Control level, as the reach sites read it."""
    from holdspeak.phone import service as phone_module

    monkeypatch.setattr(phone_module, "_desk_level", lambda: level)


def _security_finding(hub: Any, tmp_path: Path) -> str:
    """A Program step whose review left a security finding for him: the
    Needs you row the heartbeat reads ("Finding on step 1 …")."""
    from holdspeak.services.program_service import default_program_service
    from tests.integration.program_rig import make_repo

    programs = default_program_service(_db(hub))
    made = programs.create(OWNER, title="Night work", repository=str(make_repo(tmp_path / "git")),
                           control="normal", check_command="true")
    programs.plan(OWNER, made["id"], steps=[{"title": "Login", "brief": "Fix the login form."}])
    program = programs.store.get_program(made["id"])
    program["state"] = "running"
    programs.store.save_program(program)
    step = programs.store.list_steps(made["id"])[0]
    step["state"] = "findings"
    step["findings"] = [{"id": "f1", "level": "REQUIRED", "text": "The admin route skips the security check",
                         "decision": None, "to_owner": True, "core": True}]
    step["facts"] = {**dict(step.get("facts") or {}), "findings_open": True}
    programs.save_step(step)
    return step["id"]


def _run_heartbeat(hub: Any) -> dict[str, Any]:
    response = hub.client.post("/api/settings/heartbeat/run-now")
    assert response.status_code == 200, response.text
    return response.json()


def test_a_security_finding_rings_urgent_at_yolo_from_the_heartbeat(hub, monkeypatch, tmp_path) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _level(monkeypatch, "yolo")
    step_id = _security_finding(hub, tmp_path)
    receipt = _run_heartbeat(hub)
    [reach] = receipt["phone_reaches"]
    assert reach["kind"] == "heartbeat_security" and reach["channel"] == "call" and not reach["held"]
    [call] = phone.store.list_calls()
    assert call["urgent"] and call["reason"].startswith("A security finding needs you: Finding on step 1")
    assert [p["kind"] for p in phone.push().sent] == ["call"]
    assert reach["origin_ref"].startswith("heartbeat:program:") and step_id in reach["origin_ref"]
    # Once per row: the next sweep does not ring again.
    assert "phone_reaches" not in _run_heartbeat(hub)
    with _db(hub)._connection() as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM kernel_operations").fetchall()]
    assert names.count("phone.reach") == 1


def test_a_security_finding_is_a_call_not_urgent_at_normal(hub, monkeypatch, tmp_path) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _level(monkeypatch, "normal")
    _security_finding(hub, tmp_path)
    [reach] = _run_heartbeat(hub)["phone_reaches"]
    assert reach["channel"] == "call"
    [call] = phone.store.list_calls()
    assert not call["urgent"]
    [event] = phone.store.events_of_type("reach", "2000-01-01")
    assert event["data"]["rule"] == "Normal: a security or data-loss finding rings"


def test_a_security_finding_is_a_message_at_secure(hub, monkeypatch, tmp_path) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _level(monkeypatch, "secure")
    _security_finding(hub, tmp_path)
    [reach] = _run_heartbeat(hub)["phone_reaches"]
    assert reach["channel"] == "message" and phone.store.list_calls() == []
    [message] = [row for row in phone.store.recent_messages() if row["origin_ref"].startswith("heartbeat:")]
    assert message["text"].startswith("A security finding needs you: Finding on step 1")
    assert [p["kind"] for p in phone.push().sent] == ["message"]


def test_a_row_about_nothing_unsafe_reaches_nobody(hub, monkeypatch, tmp_path) -> None:
    from holdspeak.phone.reach_sites import safety_of

    _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    assert safety_of({"title": "Finding on step 1: rename the helper", "program": {"kind": "finding"}}) == ""
    assert safety_of({"title": "Review the token budget"}) == ""  # not a finding, no tags
    assert safety_of({"title": "Rows", "tags": ["data-loss"]}) == "data loss"
    assert "phone_reaches" not in _run_heartbeat(hub)


def _meeting_with_asks(hub: Any) -> str:
    from datetime import datetime, timedelta

    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    _db(hub).meetings.save_meeting(MeetingState(
        id="m-phone-asks", started_at=start, ended_at=start + timedelta(minutes=30), title="Planning",
        intel=IntelSnapshot(timestamp=0.0, summary="Planned.", action_items=[
            ActionItem(task="Draft the migration runbook", owner="Priya"), ActionItem(task="Book the dry run")]),
        intel_status="completed"))
    return "m-phone-asks"


def test_a_meetings_asks_message_at_normal_once(hub, monkeypatch) -> None:
    from holdspeak.intel_queue_conductor import _on_meeting_ready

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _level(monkeypatch, "normal")
    meeting_id = _meeting_with_asks(hub)
    _on_meeting_ready(meeting_id)  # the hub's own callback when a meeting's intel is done
    [message] = [row for row in phone.store.recent_messages() if row["origin_ref"] == f"meeting:{meeting_id}:aftercare"]
    assert message["text"] == "Planning: 2 open items wait for you on the desk."
    assert [p["kind"] for p in phone.push().sent] == ["message"]
    reaches = phone.store.events_of_type("reach", "2000-01-01")
    assert [(e["data"]["kind"], e["data"]["rule"]) for e in reaches] == [
        ("aftercare", "Normal: a meeting's asks are a message")]
    _on_meeting_ready(meeting_id)  # a second ready reaches nothing
    assert len(phone.push().sent) == 1


def test_a_meetings_asks_wait_on_the_desk_at_secure(hub, monkeypatch) -> None:
    from holdspeak.intel_queue_conductor import _on_meeting_ready

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    _level(monkeypatch, "secure")
    _on_meeting_ready(_meeting_with_asks(hub))
    assert phone.store.recent_messages() == [] and phone.push().sent == []
    assert phone.store.events_of_type("reach", "2000-01-01") == []
    with _db(hub)._connection() as conn:
        names = [row[0] for row in conn.execute("SELECT name FROM kernel_operations").fetchall()]
    assert "phone.reach" not in names


def test_no_paired_phone_and_no_number_reaches_nothing(hub, monkeypatch) -> None:
    from holdspeak.intel_queue_conductor import _on_meeting_ready

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _level(monkeypatch, "normal")
    _on_meeting_ready(_meeting_with_asks(hub))
    assert phone.store.recent_messages() == [] and _needs_phone(hub) == []


AGENT_KEY = "claude:phone-session"
AGENT_QUESTION = "Which branch is the release on, main or release/2026-10?"


class _Waits:
    """A HoldSpeak-launched agent at its process edge: its launch record and
    its session in the registry, waiting with a question."""

    def __init__(self) -> None:
        from types import SimpleNamespace

        self.session = SimpleNamespace(
            agent="claude", session_id="phone-session", wait_id="wait-1", question=AGENT_QUESTION,
            awaiting_response=True, lifecycle="active", hook_event_name="Stop", notification_type=None)
        self.ledger = SimpleNamespace(list=lambda: [{
            "session_key": AGENT_KEY, "state": "launched", "launch_id": "launch-phone",
            "brief_text": "Fix the release notes.", "target": {}}])

    def sessions(self) -> list[Any]:
        return [self.session] if self.session is not None else []

    def launches(self) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(_ledger=self.ledger)


def _responder(hub: Any, tmp_path: Path, mode: str, waits: _Waits) -> Any:
    from holdspeak.services.agent_responder import AgentResponder, AnswerStore

    return AgentResponder(
        _db(hub), launches=waits.launches, sessions=waits.sessions, control_mode=lambda: mode,
        drafter=lambda **_kw: None,  # no model answered: the desk could not draft it
        store=AnswerStore(tmp_path / "agent_answers.json"), notify=lambda keys: None)


@pytest.fixture
def away():
    from holdspeak import desk_presence

    desk_presence.clear()  # no desk view said it was in front of him
    yield
    desk_presence.clear()


def test_an_undraftable_agent_question_messages_then_calls_after_10_minutes_away_at_normal(
        hub, monkeypatch, tmp_path, away) -> None:
    from datetime import timedelta

    from holdspeak.timestamps import utc_now

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    waits = _Waits()
    responder = _responder(hub, tmp_path, "neutral", waits)
    assert responder.triage([AGENT_KEY]) == {"notify": [AGENT_KEY], "decide": [AGENT_KEY]}
    assert responder.decide(AGENT_KEY)["draft"]["verdict"] == "real"
    [message] = [row for row in phone.store.recent_messages() if row["origin_ref"] == f"agent:{AGENT_KEY}:wait-1"]
    assert message["text"] == f"Claude asks: {AGENT_QUESTION}"
    assert [p["kind"] for p in phone.push().sent] == ["message"]
    assert phone.sweep() == []  # not 10 minutes yet
    later = utc_now() + timedelta(minutes=11)
    monkeypatch.setattr(phone, "_now", lambda: later)
    [called] = phone.sweep()
    assert called["channel"] == "call" and called["rule"].startswith("Normal: no reply in 10 minutes and he is away")
    assert [p["kind"] for p in phone.push().sent] == ["message", "call"]


def test_the_sweep_does_not_call_about_a_wait_he_answered_at_the_desk(hub, monkeypatch, tmp_path, away) -> None:
    from datetime import timedelta

    from holdspeak.timestamps import utc_now

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    waits = _Waits()
    responder = _responder(hub, tmp_path, "neutral", waits)
    responder.triage([AGENT_KEY])
    responder.decide(AGENT_KEY)
    waits.session = None  # he answered in the agent's pane: the wait ended
    later = utc_now() + timedelta(minutes=11)
    monkeypatch.setattr(phone, "_now", lambda: later)
    assert phone.sweep() == []
    assert [p["kind"] for p in phone.push().sent] == ["message"]


def test_an_undraftable_agent_question_rings_at_yolo(hub, monkeypatch, tmp_path, away) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    responder = _responder(hub, tmp_path, "yolo", _Waits())
    assert responder.triage([AGENT_KEY]) == {"notify": [], "decide": [AGENT_KEY]}
    responder.decide(AGENT_KEY)
    [call] = phone.store.list_calls()
    assert call["reason"] == "Claude has a question for you" and not call["urgent"]
    assert [p["kind"] for p in phone.push().sent] == ["call"]


def test_an_agent_question_at_secure_is_a_message(hub, monkeypatch, tmp_path, away) -> None:
    phone = _phone(hub, monkeypatch, number=_NoNumber())
    _paired(hub)
    responder = _responder(hub, tmp_path, "safe", _Waits())
    assert responder.triage([AGENT_KEY]) == {"notify": [AGENT_KEY], "decide": []}
    [reach] = phone.store.events_of_type("reach", "2000-01-01")
    assert reach["data"]["channel"] == "message" and reach["data"]["rule"] == "Secure: an agent's question is a message"
    assert phone.store.list_calls() == []


# ── PH13: the morning release ───────────────────────────────────────────

def test_a_message_queued_at_23_30_goes_out_when_quiet_hours_end_and_not_before(hub, monkeypatch, away) -> None:
    from datetime import datetime, timedelta, timezone

    from holdspeak.services.heartbeat_service import HeartbeatService

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    HeartbeatService(_db(hub)).update_settings({"quiet_hours": {"start": 23, "end": 7}})
    night = datetime.now().replace(hour=23, minute=30, second=0, microsecond=0).astimezone()
    clock = [night.astimezone(timezone.utc)]
    monkeypatch.setattr(phone, "_now", lambda: clock[0])

    first = phone.reach("agent_question", level="normal", text="Which branch is the release on?",
                        origin_ref="agent:night:1")
    clock[0] += timedelta(minutes=15)
    second = phone.reach("aftercare", level="normal", text="Planning: 2 open items wait for you on the desk.",
                         origin_ref="meeting:night:aftercare")
    assert first["queued"] and second["queued"] and phone.push().sent == []

    # The next morning by the WALL CLOCK, not by an offset: on the night the
    # clocks change (DST ends), 23:30 + 7 h 30 is 06:00 on the wall, still
    # inside quiet hours; the product reads wall time, so the test must too.
    morning = datetime.combine(night.date() + timedelta(days=1), datetime.min.time().replace(hour=7)).astimezone()
    clock[0] = (morning - timedelta(minutes=1)).astimezone(timezone.utc)  # 06:59
    phone.tick()
    assert phone.push().sent == []
    assert phone.store.get_message(first["msg_id"])["delivered_at"] is None

    clock[0] = morning.astimezone(timezone.utc)  # 07:00
    phone.tick()
    pushed = [json.loads(p["payload"]["event"]) for p in phone.push().sent]
    assert [p["kind"] for p in phone.push().sent] == ["message", "message"]  # one push each, in order
    assert [e["data"]["message"]["text"] for e in pushed] == [
        "Held overnight: Which branch is the release on?",
        "Held overnight: Planning: 2 open items wait for you on the desk.",
    ]
    assert [e["data"]["message"]["id"] for e in pushed] == [first["msg_id"], second["msg_id"]]
    delivered = [e for e in device.events() if e["type"] == "message.delivered"]
    assert [e["data"]["msg_id"] for e in delivered] == [first["msg_id"], second["msg_id"]]
    assert phone.store.list_calls() == []  # the 10 minutes start at the release, not at 23:30
    phone.tick()
    assert len(phone.push().sent) == 2  # once


# ── JRN6: the item's verbs on a phone message ───────────────────────────

def test_a_held_message_carries_the_items_verbs_and_a_press_on_the_paired_phone_decides(
        hub, monkeypatch, tmp_path) -> None:
    from holdspeak.services import program_service as program_module
    from holdspeak.services.program_service import ProgramService
    from tests.integration.program_rig import make_repo

    phone = _phone(hub, monkeypatch, number=_NoNumber())
    device = _paired(hub)
    programs = ProgramService(_db(hub), phone=lambda: phone)
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: programs)
    repo = make_repo(tmp_path / "git")
    made = programs.create(OWNER, title="Overnight on the home box", repository=str(repo), control="normal",
                           check_command="true")
    programs.plan(OWNER, made["id"], steps=[{"title": "Schema", "brief": "Add the table."}])
    program = programs.store.get_program(made["id"])
    program["state"] = "running"  # as Start leaves it; no agent runs in this hub
    programs.store.save_program(program)
    step = programs.store.list_steps(made["id"])[0]
    programs.runner().raise_core(program, step, "diff", "the fix needs holdspeak/db/")
    listed = device.get("/api/phone/messages")
    assert listed.status_code == 200, listed.text
    [message] = [row for row in listed.json()["messages"] if row.get("program_step_id") == step["id"]]
    actions = message["actions"]
    assert actions["kind"] == "core" and [c["label"] for c in actions["choices"]] == ["Go on", "Park"]
    assert actions["question"] == "Let the step go on with this, or park it?"
    # An unpaired token is refused; the paired phone's press is his press.
    stranger = hub.client.post(f"/api/phone/messages/{message['id']}/decide", json={"choice": "go_on"},
                               headers={"Authorization": "Bearer a.b.c", "X-HoldSpeak-Token": ""})
    assert stranger.status_code == 401
    pressed = device.post(f"/api/phone/messages/{message['id']}/decide", {"choice": "go_on"})
    assert pressed.status_code == 200, pressed.text
    assert pressed.json()["decided"] is True
    lines = [row["line"] for row in programs.store.list_checkpoints(made["id"])]
    assert any(line.startswith("Go on: ") and line.endswith("decided on your phone") for line in lines), lines
    # A second press hears that it is answered, in the page's words.
    again = device.post(f"/api/phone/messages/{message['id']}/decide", {"choice": "park"})
    assert again.status_code == 409 and again.json()["detail"].startswith("Answered at "), again.text
    assert again.json()["detail"].endswith("from your phone")
    # Once answered, the message carries no verbs.
    [after] = [row for row in device.get("/api/phone/messages").json()["messages"] if row["id"] == message["id"]]
    assert "actions" not in after
