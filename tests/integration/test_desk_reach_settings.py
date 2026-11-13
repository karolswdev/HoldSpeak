"""PG-DIRECTION DIR4 to DIR6 on the Programs rig: Later and Settings ▸ Reach, through the routes.

``GET /api/reach`` (the channels, the ladder, quiet hours, the digest, Later
means), ``PUT /api/reach``, ``PUT /api/reach/telegram/token`` (the keystore
file inside HOME), ``POST`` and ``DELETE /api/reach/telegram/pair``, ``POST
/api/reach/later`` (the Needs you row goes to the Later group), and ``POST
/api/reach/packages`` with ``send: telegram`` (the row's line says it was
sent). The Telegram Bot API is the fake bot of ``tests/unit/test_reach_telegram.py``
over the fixture's shapes; nothing leaves the machine.

The faces replay the answers recorded here (``web/src/desk/reach/__fixtures__/``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.services import briefing_service as briefing_module
from holdspeak.services import program_service as program_module
from holdspeak.services import reach_service as reach_module
from holdspeak.services import telegram_reach as telegram_module
from holdspeak.services.briefing_service import BriefingService
from holdspeak.services.needs_you_membership import compute_needs_you
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import TelegramReach
from holdspeak.web.routes.briefing import build_briefing_router
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.integration.test_desk_reach import ROOT, _fixture
from tests.unit.test_reach_telegram import TOKEN, FakeBot, update

FIXTURES = ROOT / "web" / "src" / "desk" / "reach" / "__fixtures__"


@pytest.fixture
def desk(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    monkeypatch.setenv("HOLDSPEAK_PHONE", "off")
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "off")
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Store the stall reason", "brief": "Store it.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "holdspeak/db/schema.py": "b\n"})
    rig.tick()
    bot = FakeBot()
    briefing = BriefingService(rig.db, programs=lambda: rig.service)
    holder: dict = {}
    reach = ReachService(rig.db, programs=lambda: rig.service, briefing=briefing, telegram=lambda: holder["tg"])
    telegram = TelegramReach(rig.db, caller=bot, briefing=briefing, reach=reach, programs=lambda: rig.service,
                             link=lambda path: f"https://hub.tail.ts.net{path}")
    holder["tg"] = telegram
    briefing._reach, briefing.settle, briefing._telegram = reach, telegram.settle, lambda: telegram
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    monkeypatch.setattr(reach_module, "default_reach_service", lambda db=None: reach)
    monkeypatch.setattr(telegram_module, "default_telegram_reach", lambda db=None: telegram)
    app = FastAPI()

    @app.middleware("http")
    async def _edge(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    app.include_router(build_briefing_router(None))  # type: ignore[arg-type]
    item = next(row for row in rig.service.needs_you_items() if row["kind"] == "core")
    return {"rig": rig, "pid": pid, "client": TestClient(app), "bot": bot, "telegram": telegram,
            "ref": f"program:{pid}:{item['id']}", "tmp": tmp_path}


def _record(name: str, answer, desk) -> None:
    _fixture(FIXTURES / name, answer, desk["tmp"], "no-page-token-in-this-answer")


def test_settings_reach_reads_and_saves_its_rows(desk) -> None:
    client = desk["client"]
    unpaired = client.get("/api/reach")
    assert unpaired.status_code == 200, unpaired.text
    body = unpaired.json()
    assert body["channels"]["telegram"]["paired"] is None and body["channels"]["telegram"]["token"] == "missing"
    assert body["ladder"]["telegram"] == "at_once" and body["later_means"] == "in_2h"
    assert body["quiet_hours"]["start"] == 22 and body["digest"]["at"] == "end_of_quiet"
    assert set(body["ladder"]["kinds"]) >= {"level", "core_question", "program_done"}
    _record("reach.unpaired.json", body, desk)

    refused = client.post("/api/reach/telegram/pair")
    assert refused.status_code == 409 and refused.json()["code"] == "token_missing"
    bad = client.put("/api/reach/telegram/token", json={"token": "not a token"})
    assert bad.status_code == 400 and bad.json()["code"] == "token_invalid"
    stored = client.put("/api/reach/telegram/token", json={"token": TOKEN})
    assert stored.json()["token"] == "keystore" and TOKEN not in client.get("/api/reach").text
    # The hub asked Telegram who the bot is before it kept the token.
    assert stored.json()["bot"] == {"name": "HoldSpeak", "username": "holdspeak_karol_bot", "checked": True}

    pairing = client.post("/api/reach/telegram/pair")
    assert pairing.status_code == 201
    code = pairing.json()["code"]
    # One link in Telegram connects the chat: he presses Start, no code to type.
    assert pairing.json()["link"] == f"https://t.me/holdspeak_karol_bot?start={code}"
    pairing_body = {**pairing.json(), "code": "482913", "words": "482 913", "say": "Send /pair 482 913 to your bot",
                    "link": "https://t.me/holdspeak_karol_bot?start=482913"}
    _record("reach.pairing.json", pairing_body, desk)
    pairing_open = client.get("/api/reach").json()
    assert pairing_open["channels"]["telegram"]["pairing"]["link"] == pairing.json()["link"]
    pairing_open["channels"]["telegram"]["pairing"]["link"] = pairing_body["link"]
    _record("reach.pairing_open.json", pairing_open, desk)
    assert desk["telegram"].handle_update(update("pair", code=code))["ok"] is True
    paired = client.get("/api/reach").json()
    assert paired["channels"]["telegram"]["paired"]["name"] == "Karol"
    assert paired["channels"]["telegram"]["token"] == "keystore"
    _record("reach.paired.json", paired, desk)

    # What it sends: one kind's word, the daily brief, and Telegram's rung over
    # every kind, each through the one save.
    rows = {row["kind"]: row for row in paired["ladder"]["sends"]}
    assert list(rows) == ["question", "tool_call", "send", "failed", "due"]
    assert rows["send"]["mode"] == "at_once" and paired["digest"]["brief"] == "on"
    kind = client.put("/api/reach", json={"kinds": {"send": "digest"}})
    assert kind.status_code == 200, kind.text
    assert {row["kind"]: row["mode"] for row in kind.json()["ladder"]["sends"]}["send"] == "digest"
    _record("reach.kind_send_digest.json", kind.json(), desk)
    assert client.put("/api/reach", json={"kinds": {"send": "never"}}).json()["code"] == "kind_mode_invalid"
    brief_off = client.put("/api/reach", json={"kinds": {"send": "at_once"}, "brief": "off"})
    assert brief_off.json()["digest"]["brief"] == "off"
    _record("reach.brief_off.json", brief_off.json(), desk)
    rung_off = client.put("/api/reach", json={"brief": "on", "telegram": "off"})
    assert {row["now"] for row in rung_off.json()["ladder"]["sends"]} == {"off"}
    assert {row["mode"] for row in rung_off.json()["ladder"]["sends"]} == {"at_once", "digest"}
    _record("reach.rung_off.json", rung_off.json(), desk)

    saved = client.put("/api/reach", json={"telegram": "after_10", "later_means": "end_of_quiet", "digest": 7})
    assert saved.status_code == 200, saved.text
    assert saved.json()["ladder"]["telegram"] == "after_10"
    assert saved.json()["digest"] == {"at": 7, "hour": 7, "brief": "on", "brief_words": "On"}
    _record("reach.saved.json", saved.json(), desk)
    assert client.put("/api/reach", json={"telegram": "loud"}).json()["code"] == "telegram_invalid"
    # DIR7: the ladder's Phone rung (the Phone app channel) as its own picker.
    phone_off = client.put("/api/reach", json={"phone_app": "off"})
    assert phone_off.status_code == 200 and phone_off.json()["channels"]["phone_app"]["on"] is False
    assert phone_off.json()["ladder"]["order"] == ["desk", "phone_app", "telegram", "call"]
    _record("reach.phone_off.json", phone_off.json(), desk)

    unpaired_again = client.delete("/api/reach/telegram/pair")
    assert unpaired_again.json() == {"paired": None}
    assert client.get("/api/reach").json()["channels"]["telegram"]["paired"] is None


def test_the_test_message_the_removal_and_use_here_over_http(desk) -> None:
    """The setup pane's three other acts, on their declared routes."""
    client, bot = desk["client"], desk["bot"]
    no_chat = client.post("/api/reach/telegram/test")
    assert no_chat.status_code == 409 and no_chat.json()["code"] == "telegram_not_connected"
    client.put("/api/reach/telegram/token", json={"token": TOKEN})
    code = client.post("/api/reach/telegram/pair").json()["code"]
    desk["telegram"].handle_update(update("pair", code=code))

    sent = client.post("/api/reach/telegram/test")
    assert sent.status_code == 200, sent.text
    assert sent.json()["last_test"]["sent_at"] and sent.json()["last_test"]["answered_at"] is None
    message = bot.of("sendMessage")[-1]
    desk["telegram"].handle_update(update("tap", message_id=bot.next_id, text=message["text"], data="r1|test|ok"))
    status = client.get("/api/reach").json()["channels"]["telegram"]
    assert status["last_test"]["answered_at"] and status["health"]["state"] == "connected"
    assert status["bot"]["username"] == "holdspeak_karol_bot" and status["keystore"] == "open"
    _record("reach.tested.json", client.get("/api/reach").json(), desk)

    here = client.post("/api/reach/telegram/use-here")
    assert here.status_code == 200 and here.json()["health"]["state"] == "not_checked"

    stale = client.post("/api/reach/telegram/remove", json={"username": "another_bot"})
    assert stale.status_code == 409 and stale.json()["code"] == "answer_stale"
    assert client.get("/api/reach").json()["channels"]["telegram"]["token"] == "keystore"
    gone = client.post("/api/reach/telegram/remove", json={"username": "holdspeak_karol_bot"})
    assert gone.status_code == 200 and gone.json() == {"token": "missing", "paired": None, "bot": None}
    removed = client.get("/api/reach").json()["channels"]["telegram"]
    assert removed["token"] == "missing" and removed["paired"] is None and removed["bot"] is None
    assert TOKEN not in client.get("/api/reach").text


def test_later_and_sent_to_telegram_reach_the_needs_you_row(desk) -> None:
    client, rig, ref = desk["client"], desk["rig"], desk["ref"]
    client.put("/api/reach/telegram/token", json={"token": TOKEN})
    code = client.post("/api/reach/telegram/pair").json()["code"]
    desk["telegram"].handle_update(update("pair", code=code))

    made = client.post("/api/reach/packages", json={"refs": [ref], "send": ["telegram"]})
    assert made.status_code == 201, made.text
    assert made.json()["telegram"]["message_id"] and "text" not in made.json()["telegram"]
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    row = next(item for item in needs["unmutedItems"] if item["ref"] == ref)
    assert row["program"]["page"]["sent"]["via"] == "telegram" and row["counted"] is True
    _record("needs_you.sent.json", {"items": [row]}, desk)

    later = client.post("/api/reach/later", json={"ref": ref, "later": "later 2h"})
    assert later.status_code == 200, later.text
    assert later.json()["words"].startswith("Later · back at ") and later.json()["via"] == "desk"
    needs = compute_needs_you(programs=rig.service.needs_you_items())
    row = next(item for item in needs["unmutedItems"] if item["ref"] == ref)
    assert row["later"]["via"] == "desk" and row["counted"] is False
    assert ref not in [member["ref"] for member in needs["members"]]
    _record("needs_you.later.json", {"items": [row]}, desk)
    bad = client.post("/api/reach/later", json={"ref": ref, "later": "after the standup"})
    assert bad.status_code == 400 and bad.json()["detail"] == "Say a time, for example 14:30."
    nothing = client.post("/api/reach/digest")
    assert nothing.status_code == 409 and nothing.json()["code"] == "nothing_waits"


def test_the_setup_pane_states_are_recorded(desk, monkeypatch) -> None:
    """Each state of Settings ▸ Reach ▸ Telegram, as the hub says it: the
    face replays these answers (``reach.<state>.json``) and types none."""
    client, telegram, bot = desk["client"], desk["telegram"], desk["bot"]
    instead: dict = {}

    def caller(token, method, params):
        if method in instead:
            bot.calls.append((method, dict(params)))
            return dict(instead[method])
        return bot(token, method, params)

    telegram._call = caller

    # A token that Telegram does not know: refused, with words, and not kept.
    instead["getMe"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    refused = client.put("/api/reach/telegram/token", json={"token": TOKEN})
    assert refused.status_code == 400 and refused.json()["code"] == "token_unknown"
    assert client.get("/api/reach").json()["channels"]["telegram"]["token"] == "missing"
    _record("reach.token_refused.json", refused.json(), desk)

    # Telegram does not answer: the token is kept, not checked yet.
    instead["getMe"] = {"ok": False, "description": "The read operation timed out"}
    assert client.put("/api/reach/telegram/token", json={"token": TOKEN}).status_code == 200
    unchecked = client.get("/api/reach").json()
    assert unchecked["channels"]["telegram"]["health"]["state"] == "not_checked"
    _record("reach.token_unchecked.json", unchecked, desk)

    # Telegram answers: the bot has a name; no chat yet, no code open.
    del instead["getMe"]
    assert client.put("/api/reach/telegram/token", json={"token": TOKEN}).status_code == 200
    checked = client.get("/api/reach").json()
    assert checked["channels"]["telegram"]["bot"]["username"] == "holdspeak_karol_bot"
    assert checked["channels"]["telegram"]["paired"] is None and checked["channels"]["telegram"]["pairing"] is None
    _record("reach.token_checked.json", checked, desk)

    code = client.post("/api/reach/telegram/pair").json()["code"]
    telegram.handle_update(update("pair", code=code))

    # The test is sent and not answered yet.
    assert client.post("/api/reach/telegram/test").status_code == 200
    test_sent = client.get("/api/reach").json()
    assert test_sent["channels"]["telegram"]["last_test"]["answered_at"] is None
    _record("reach.test_sent.json", test_sent, desk)

    # The chat stopped the bot (403 on a send).
    instead["sendMessage"] = {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}
    telegram.line("A line to the chat.")
    blocked = client.get("/api/reach").json()
    assert blocked["channels"]["telegram"]["health"]["state"] == "bot_blocked"
    _record("reach.bot_blocked.json", blocked, desk)
    del instead["sendMessage"]
    telegram.line("A line to the chat.")

    # Telegram does not answer the poll.
    instead["getUpdates"] = {"ok": False, "description": "The read operation timed out"}
    telegram.poll_once(None)
    unreachable = client.get("/api/reach").json()
    assert unreachable["channels"]["telegram"]["health"]["state"] == "unreachable"
    _record("reach.unreachable.json", unreachable, desk)

    # Another HoldSpeak reads this bot (409 on the poll).
    instead["getUpdates"] = {"ok": False, "error_code": 409, "description": "Conflict"}
    telegram.poll_once(None)
    another = client.get("/api/reach").json()
    assert another["channels"]["telegram"]["health"]["state"] == "another_desk"
    _record("reach.another_desk.json", another, desk)
    here = client.post("/api/reach/telegram/use-here")
    assert here.status_code == 200
    _record("reach.use_here.json", here.json(), desk)

    # Telegram does not accept the token (401 on the poll).
    instead["getUpdates"] = {"ok": False, "error_code": 401, "description": "Unauthorized"}
    telegram.poll_once(None)
    revoked = client.get("/api/reach").json()
    assert revoked["channels"]["telegram"]["health"]["state"] == "token_revoked"
    _record("reach.token_revoked.json", revoked, desk)

    # The keystore is not open.
    monkeypatch.setattr(telegram_module, "_store", lambda: None)
    locked = client.get("/api/reach").json()
    assert locked["channels"]["telegram"]["keystore"] == "locked"
    _record("reach.keystore_locked.json", locked, desk)
