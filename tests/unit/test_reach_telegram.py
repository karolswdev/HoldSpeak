"""PG-DIRECTION DIR5: Telegram reach (DIRECTION-2026-10-31.md §5, §8).

Over ``tests/fixtures/reach/telegram.updates.json`` (the Bot API's shapes;
see its ``_source``), replayed through the ``caller=`` seam: pairing by a
one-time code (a second chat cannot pair, an unpaired chat reads nothing),
the bot token moved from the config file into the keystore once, the
message in at most eight lines with the choices and Later as buttons, a tap
that decides once with ``via=telegram``, Merge's second tap, Later's row and
"later 2h", text replies by rule, a free sentence as a shaping sentence, the
never-sent fence, the egress record (the token never in it), and no poll
when unpaired or off. Every keystore read is the rig's key file in HOME.
"""
from __future__ import annotations

import copy
import json
import logging
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import telegram_reach
from holdspeak.services.briefing_service import BriefingService
from holdspeak.services.reach_service import ReachService
from holdspeak.services.telegram_reach import TelegramReach, TelegramRefused, fence, render
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

FIXTURE = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "reach" / "telegram.updates.json")
                     .read_text(encoding="utf-8"))
TOKEN = "6000000001:AAH-fake-token-for-the-rig-only-0123456789"
OWNER_CHAT = FIXTURE["owner_chat"]["id"]
AGENT = Principal(PrincipalKind.AGENT, "agent-1")


def _fill(value: Any, **fields: Any) -> Any:
    if isinstance(value, dict):
        return {key: _fill(item, **fields) for key, item in value.items()}
    if isinstance(value, list):
        return [_fill(item, **fields) for item in value]
    if isinstance(value, str):
        for key, item in fields.items():
            if value == "{" + key + "}":
                return item
            value = value.replace("{" + key + "}", str(item))
    return value


def update(name: str, **fields: Any) -> dict[str, Any]:
    return _fill(copy.deepcopy(FIXTURE["updates"][name]), **fields)


class FakeBot:
    """The Bot API, answering with the fixture's shapes."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.next_id = 100
        self.tokens: list[str] = []

    def __call__(self, token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.tokens.append(token)
        self.calls.append((method, json.loads(json.dumps(params))))
        if method == "sendMessage":
            self.next_id += 1
            return _fill(copy.deepcopy(FIXTURE["answers"]["sendMessage"]), message_id=self.next_id,
                         text=params.get("text", ""))
        if method == "editMessageText":
            return _fill(copy.deepcopy(FIXTURE["answers"]["editMessageText"]), message_id=params["message_id"],
                         text=params.get("text", ""))
        return copy.deepcopy(FIXTURE["answers"].get(method) or {"ok": True})

    def of(self, method: str) -> list[dict[str, Any]]:
        return [params for name, params in self.calls if name == method]


@pytest.fixture(autouse=True)
def keystore(tmp_path, monkeypatch):
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "home" / "channel-keys.json"))
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "on")
    return tmp_path / "home" / "channel-keys.json"


class Desk:
    def __init__(self, tmp_path: Path, control: str = "yolo") -> None:
        self.rig = Rig(tmp_path)
        self.bot = FakeBot()
        self.briefing = BriefingService(self.rig.db, programs=lambda: self.rig.service)
        self.reach = ReachService(self.rig.db, programs=lambda: self.rig.service, briefing=self.briefing,
                                  telegram=lambda: self.telegram)
        self.briefing._reach = self.reach
        self.telegram = TelegramReach(self.rig.db, caller=self.bot, briefing=self.briefing, reach=self.reach,
                                      programs=lambda: self.rig.service, link=lambda path: f"https://hub.tail.ts.net{path}")
        self.briefing.settle = self.telegram.settle
        self.briefing._telegram = lambda: self.telegram
        self.control = control

    def pair(self) -> None:
        self.telegram.save_token(OWNER, TOKEN)
        code = self.telegram.start_pairing(OWNER)["code"]
        assert self.telegram.handle_update(update("pair", code=code))["ok"] is True

    def core(self) -> tuple[str, dict[str, Any]]:
        rig = self.rig
        pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                                 repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                                 control=self.control)["id"]
        rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store it.", "owns": ["src/a.py"]}])
        rig.service.start(OWNER, pid)
        rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
        rig.tick()
        item = next(item for item in rig.service.needs_you_items() if item["kind"] == "core")
        return pid, item

    def merge(self) -> tuple[str, dict[str, Any]]:
        rig = self.rig
        pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.",
                                 repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", control="secure",
                                 template="")["id"]
        rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "Do it.", "owns": ["a.py"]}])
        rig.service.start(OWNER, pid)
        rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
        rig.tick(3)
        item = next(item for item in rig.service.needs_you_items() if item["kind"] == "merge")
        return pid, item

    def tap(self, message: dict[str, Any], data: str, name: str = "tap") -> dict[str, Any]:
        return self.telegram.handle_update(update(name, message_id=message["message_id"], text=message["text"],
                                                  data=data))


# ── pairing ──────────────────────────────────────────────────────────


def test_pairing_is_one_time_and_one_chat(tmp_path, keystore) -> None:
    desk = Desk(tmp_path)
    tg = desk.telegram
    assert tg.should_poll() is False  # no token, nothing to poll
    with pytest.raises(TelegramRefused) as no_token:
        tg.start_pairing(OWNER)
    assert no_token.value.code == "token_missing"
    assert tg.save_token(OWNER, TOKEN) == {"token": "keystore"}
    assert tg.should_poll() is False  # a token, no chat, no code: nothing polls
    with pytest.raises(TelegramRefused):
        tg.start_pairing(AGENT)
    made = tg.start_pairing(OWNER)
    assert len(made["code"]) == 6 and made["code"].isdigit() and made["words"] == f"{made['code'][:3]} {made['code'][3:]}"
    assert made["say"] == f"Send /pair {made['words']} to your bot"
    assert tg.should_poll() is True and tg.status()["pairing"]["expires_at"] == made["expires_at"]
    # A wrong code from another chat pairs nothing.
    assert tg.handle_update(update("pair_other", code="000000"))["ok"] is False
    assert telegram_reach.paired_chat() is None
    # The first chat with the code is the owner chat; the code is spent.
    assert tg.handle_update(update("pair", code=made["code"].replace("", " ").strip()))["ok"] is True
    chat = telegram_reach.paired_chat()
    assert chat["id"] == str(OWNER_CHAT) and chat["name"] == "Karol"
    assert tg.status()["paired"]["name"] == "Karol" and tg.status()["pairing"] is None
    # A second chat can never pair while one is paired, even with the code.
    assert tg.handle_update(update("pair_other", code=made["code"]))["ok"] is False
    assert telegram_reach.paired_chat()["id"] == str(OWNER_CHAT)
    with pytest.raises(TelegramRefused) as twice:
        tg.start_pairing(OWNER)
    assert twice.value.code == "already_paired"
    # The chat and the token are in the keystore file inside HOME, not in a config.
    stored = json.loads(keystore.read_text())["HoldSpeak Reach"]
    assert stored["reach.telegram.bot_token"] == TOKEN and json.loads(stored["reach.telegram.chat"])["name"] == "Karol"
    tg.unpair(OWNER)
    assert telegram_reach.paired_chat() is None and tg.should_poll() is False


def test_an_unpaired_chat_reads_nothing(tmp_path) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    desk.bot.calls.clear()
    assert desk.telegram.handle_update(update("text_other"))["action"] == "rejected"
    (sent,) = desk.bot.of("sendMessage")
    assert sent["chat_id"] == str(FIXTURE["other_chat"]["id"]) and sent["text"] == "This chat is not paired."
    made = desk.telegram.brief(f"program:{pid}:{item['id']}")
    package_id = made["id"]
    desk.bot.calls.clear()
    out = desk.telegram.handle_update(update("tap_other", data=f"r1|{package_id}|go_on"))
    assert out["action"] == "rejected"
    assert desk.bot.calls == [("answerCallbackQuery", {"callback_query_id": "5382bfdwdsb323b2e0", "text": "Not paired."})]
    assert [i["kind"] for i in desk.rig.service.needs_you_items()] == ["core"]  # nothing decided


def test_the_bot_token_moves_from_the_config_file_into_the_keystore_once(tmp_path, keystore, caplog) -> None:
    class Section:
        bot_token = TOKEN
        pairing_code = "123456"
        allowed_chat_ids = [str(OWNER_CHAT)]

    class Config:
        cadence_telegram = Section()
        saved = 0

        def save(self) -> None:
            Config.saved += 1

    config = Config()
    telegram_reach._repaired = False
    with caplog.at_level(logging.INFO, logger="holdspeak.services.telegram_reach"):
        assert telegram_reach.repair_token(lambda: config) is True
        assert telegram_reach.repair_token(lambda: config) is False  # once
    assert config.cadence_telegram.bot_token == "" and config.cadence_telegram.pairing_code == ""
    assert Config.saved == 1
    assert telegram_reach.bot_token() == TOKEN and telegram_reach.token_where() == "keystore"
    assert telegram_reach.paired_chat()["id"] == str(OWNER_CHAT)
    moved = [r.getMessage() for r in caplog.records if "moved the bot token" in r.getMessage()]
    assert moved == ["telegram: moved the bot token from the config file into the keystore"]
    assert TOKEN not in caplog.text
    # The Cadence surface reads the keystore now.
    resolved = telegram_reach.cadence_config(config.cadence_telegram)
    assert resolved.bot_token == TOKEN and resolved.allowed_chat_ids == [str(OWNER_CHAT)]


# ── the message ──────────────────────────────────────────────────────


def test_the_message_is_the_brief_with_the_choices_later_and_the_page_link(tmp_path) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    desk.bot.calls.clear()
    made = desk.telegram.brief(f"program:{pid}:{item['id']}")
    (sent,) = desk.bot.of("sendMessage")
    lines = sent["text"].split("\n")
    assert len(lines) <= 10, lines
    assert lines[0].startswith("Overnight on the home box · step 1 · waits ")
    # The owner's BRIEF RULE (2026-10-31): the page's lines in the page's order.
    assert lines[1] == "Goal: Stop the stalls."
    assert lines[2].startswith("Step 1")
    assert "files no step owns (b.py)" in lines[3]
    assert lines[4] == "Let the step go on with this, or park it?"
    assert "Go on: The step goes on with this change." in lines
    assert any(line.startswith("Park: Stop this step.") for line in lines), lines
    assert lines[-1].startswith("Open the page: https://hub.tail.ts.net/b/")
    assert "parse_mode" not in sent  # plain text: a title cannot break Markdown
    keyboard = sent["reply_markup"]["inline_keyboard"]
    assert [b["text"] for b in keyboard[0]] == ["Go on", "Park", "Later ▾"]
    assert all(len(b["callback_data"].encode()) <= 64 for b in keyboard[0])
    # Where it went is on the package (never the text: the link holds the token).
    package = desk.briefing.store.get(made["id"])
    assert package["sent"][0]["via"] == "telegram" and package["sent"][0]["message_id"] == desk.bot.next_id
    assert "text" not in package["sent"][0]
    # The Needs you row's line reads it: the page says sent to Telegram.
    turn = desk.rig.program(pid)["your_turn_items"][0]
    assert turn["page"]["sent"]["via"] == "telegram"


def test_what_is_never_sent(tmp_path) -> None:
    with pytest.raises(TelegramRefused) as diff:
        fence("diff --git a/x b/x\n@@ -1 +1 @@")
    assert diff.value.code == "never_sent"
    with pytest.raises(TelegramRefused):
        fence(f"the bot is {TOKEN}")
    with pytest.raises(TelegramRefused):
        fence("-----BEGIN OPENSSH PRIVATE KEY-----")
    assert "hunter2" not in fence('step 3 "password": "hunter2"')
    body = {"head": "A · step 1", "question": "Authorization: Bearer abc.def.ghi", "choices": [], "changed": []}
    assert "abc.def.ghi" not in render(body, None, __import__("datetime").datetime.now().astimezone())


# ── a tap decides once ───────────────────────────────────────────────


def _message(desk: Desk) -> dict[str, Any]:
    sent = desk.bot.of("sendMessage")[-1]
    return {"message_id": desk.bot.next_id, "text": sent["text"]}


def test_a_tap_decides_once_from_telegram_and_the_message_settles(tmp_path, caplog) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    pid, item = desk.core()
    made = desk.telegram.brief(f"program:{pid}:{item['id']}")
    message = _message(desk)
    desk.bot.calls.clear()
    with caplog.at_level(logging.DEBUG):
        out = desk.tap(message, f"r1|{made['id']}|go_on")
    assert out["action"] == "answered" and out["words"].startswith("Decided: Go on · ")
    lines = [row for row in desk.rig.program(pid)["checkpoints"] if row.get("via") == "telegram"]
    assert lines and lines[0]["line"].startswith("Go on: ") and lines[0]["line"].endswith("· decided from Telegram")
    (edited,) = desk.bot.of("editMessageText")
    assert edited["text"].split("\n")[-1] == out["words"] and "reply_markup" not in edited  # the buttons go
    assert "Open the page: https://hub.tail.ts.net/b/" in edited["text"]
    assert "core" not in [i["kind"] for i in desk.rig.service.needs_you_items()]
    # The page shows it decided; a second tap hears "answered already".
    assert desk.briefing.store.get(made["id"])["answers"][item_ref(pid, item)]["via"] == "telegram"
    again = desk.tap(message, f"r1|{made['id']}|park")
    assert again["action"] == "refused" and again["code"] == "answered_already"
    assert again["words"].startswith("Answered already: Go on · "), again["words"]
    assert TOKEN not in caplog.text and all(token == TOKEN for token in desk.bot.tokens)


def item_ref(pid: str, item: dict[str, Any]) -> str:
    return f"program:{pid}:{item['id']}"


def test_an_answer_on_the_page_settles_the_telegram_message(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    pid, item = desk.core()
    made = desk.briefing.make(OWNER, [item_ref(pid, item)], send="telegram")
    desk.bot.calls.clear()
    desk.briefing.answer(made["token"], item_ref(pid, item), "park")
    (edited,) = desk.bot.of("editMessageText")
    assert edited["text"].split("\n")[-1].startswith("Decided: Park · ")
    assert edited["text"].endswith("· from the briefing page")


def test_merge_asks_a_second_tap_in_place(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.merge()
    made = desk.telegram.brief(item_ref(pid, item))
    message = _message(desk)
    desk.bot.calls.clear()
    first = desk.tap(message, f"r1|{made['id']}|merge")
    assert first["action"] == "second_tap"
    (edited,) = desk.bot.of("editMessageText")
    assert "to main?" in edited["text"]
    assert [b["text"] for b in edited["reply_markup"]["inline_keyboard"][0]] == ["Merge", "Not now"]
    assert desk.rig.step(pid, 1)["state"] == "merge_ask"  # one tap merged nothing
    # Two minutes pass: the second tap is too late and nothing merges.
    real = time.monotonic
    monkeypatch.setattr(telegram_reach.time, "monotonic", lambda: real() + 121)
    late = desk.tap({**message, "text": edited["text"]}, f"r1|{made['id']}|merge!")
    assert late["action"] == "second_tap_expired" and desk.rig.step(pid, 1)["state"] == "merge_ask"
    monkeypatch.setattr(telegram_reach.time, "monotonic", real)
    desk.tap(message, f"r1|{made['id']}|merge")
    done = desk.tap(message, f"r1|{made['id']}|merge!")
    assert done["action"] == "answered", done
    assert desk.rig.step(pid, 1)["state"] in ("merged", "done")


def test_later_opens_its_row_and_a_time_defers(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    pid, item = desk.core()
    made = desk.telegram.brief(item_ref(pid, item))
    message = _message(desk)
    desk.bot.calls.clear()
    assert desk.tap(message, f"r1|{made['id']}|later")["action"] == "later_menu"
    (edited,) = desk.bot.of("editMessageText")
    assert [b["text"] for b in edited["reply_markup"]["inline_keyboard"][0]] == ["1 h", "13:00", "Tonight", "Tomorrow"]
    out = desk.tap(message, f"r1|{made['id']}|L:in_1h")
    assert out["action"] == "answered" and out["words"].startswith("Later · back at ")
    row = desk.reach.later_rows.get(item_ref(pid, item))
    assert row["via"] == "telegram" and row["package_id"] == made["id"]
    assert desk.rig.program(pid)["your_turn_items"][0]["later"]["via"] == "telegram"


# ── replies in words ─────────────────────────────────────────────────


def test_replies_are_read_by_rule(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    pid, item = desk.core()
    desk.telegram.brief(item_ref(pid, item))
    desk.bot.calls.clear()
    assert desk.telegram.handle_update(update("reply", text="waive: it is fine"))["action"] == "waive_refused"
    assert desk.bot.of("sendMessage")[-1]["text"].startswith("Waive on the page, with your reason.")
    out = desk.telegram.handle_update(update("reply", text="later 2h"))
    assert out["action"] == "answered" and out["words"].startswith("Later · back at ")
    assert desk.reach.later_rows.get(item_ref(pid, item))["via"] == "telegram"


def test_yes_takes_the_way_forward(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    pid, item = desk.core()
    desk.telegram.brief(item_ref(pid, item))
    out = desk.telegram.handle_update(update("reply", text="Yes"))
    assert out["action"] == "answered" and out["choice"] == "go_on"
    assert "core" not in [i["kind"] for i in desk.rig.service.needs_you_items()]


def test_a_free_sentence_is_a_shaping_sentence_with_apply(tmp_path, monkeypatch) -> None:
    from tests.integration.program_shape_seed import SENTENCES, seed
    from tests.unit.test_program_shaper import reply, wire_engine

    desk = Desk(tmp_path)
    engine = wire_engine(desk.rig, monkeypatch)
    pid = seed(desk.rig)
    desk.pair()
    # A sent package on that Program (the seed has no held item of its own).
    desk.briefing.store.add(package_id="pkg-000000000001", kind="item", refs=[f"program:{pid}:x:core"],
                            body={"ref": f"program:{pid}:x:core", "program_id": pid, "head": "The hub", "choices": []},
                            token_hash="0" * 64, created_at=_now(), expires_at=_now(hours=24))
    desk.briefing.store.set_sent("pkg-000000000001", [{"via": "telegram", "at": _now(), "message_id": 55}])
    engine.replies = [reply("shape")]
    desk.bot.calls.clear()
    out = desk.telegram.handle_update(update("reply", text=SENTENCES["shape"]))
    assert out["action"] == "shape_preview" and out["rows"] == 4
    sent = desk.bot.of("sendMessage")[-1]
    assert sent["text"].startswith("Change: ") and len(sent["text"].split("\n")) <= 8
    assert [b["text"] for b in sent["reply_markup"]["inline_keyboard"][0]] == ["Apply", "Not this"]
    applied = desk.tap({"message_id": 102, "text": sent["text"]}, sent["reply_markup"]["inline_keyboard"][0][0]
                       ["callback_data"])
    assert applied == {"action": "shape_applied", "applied": True}
    assert any(step["title"] for step in desk.rig.program(pid)["steps"] if step["ordinal"] == 4)


def _now(hours: int = 0) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


# ── off, unpaired, the ladder, the egress record ─────────────────────


def test_off_means_no_poll_and_no_send(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    desk.pair()
    pid, item = desk.core()
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "off")
    desk.bot.calls.clear()
    assert desk.telegram.should_poll() is False and desk.telegram.live() is False
    with pytest.raises(TelegramRefused):
        desk.telegram.brief(item_ref(pid, item))
    assert desk.reach.tick()["sent"] == []
    assert desk.bot.calls == []


def test_the_ladder_sends_once_at_once_and_waits_in_quiet_hours(tmp_path) -> None:
    from tests.integration.program_rig import local_noon

    noon = local_noon()  # never the digest's hour, whatever hour the test runs
    desk = Desk(tmp_path, control="normal")
    desk.reach._clock = lambda: noon.isoformat()
    desk.pair()
    pid, item = desk.core()
    desk.reach.quiet = lambda: (0, 0)  # no quiet hours
    desk.bot.calls.clear()
    first = desk.reach.tick()
    assert len(first["sent"]) == 1 and len(desk.bot.of("sendMessage")) == 1
    assert desk.reach.tick()["sent"] == []  # never twice for one item
    # In quiet hours nothing is sent.
    desk.telegram.unpair(OWNER)
    desk2 = Desk(tmp_path / "two", control="normal")
    desk2.reach._clock = lambda: noon.isoformat()
    desk2.pair()
    desk2.core()
    desk2.reach.quiet = lambda: (noon.hour, (noon.hour + 2) % 24)
    desk2.bot.calls.clear()
    assert desk2.reach.tick()["sent"] == [] and desk2.bot.of("sendMessage") == []


def test_every_send_is_egress_and_the_token_is_never_in_the_record(tmp_path, monkeypatch) -> None:
    import holdspeak.db.core as db_core
    from holdspeak.kernel import runtime as kernel_runtime
    from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS, LOCAL_OWNER

    desk = Desk(tmp_path, control="normal")
    monkeypatch.setattr(db_core, "_db", desk.rig.db)
    EGRESS_EXECUTIONS._results.clear()
    broker = kernel_runtime._configure(desk.rig.db)
    urls: list[str] = []

    class Response:
        def __init__(self, body: bytes) -> None:
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return self.body

    def urlopen(request, timeout=10):
        urls.append(request.full_url)
        method = request.full_url.rsplit("/", 1)[1]
        params = json.loads(request.data)
        answer = FIXTURE["answers"].get(method) or {"ok": True}
        return Response(json.dumps(_fill(copy.deepcopy(answer), message_id=101, text=params.get("text", ""))).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    desk.telegram._call = telegram_reach.call_reach
    desk.telegram.save_token(OWNER, TOKEN)
    telegram_reach._write(telegram_reach.CHAT_SLOT, json.dumps({"id": str(OWNER_CHAT), "name": "Karol"}))
    pid, item = desk.core()
    desk.telegram.brief(item_ref(pid, item))
    results = list(EGRESS_EXECUTIONS._results.values())
    assert results and results[-1]["connector_id"] == "reach-telegram"
    assert results[-1]["destination"] == f"telegram:sendmessage:{OWNER_CHAT}"
    assert results[-1]["data_classes"] == ["reach_package"]
    full = broker.read([f"operation:{results[-1]['operation_id']}"], "full", "committed", LOCAL_OWNER)
    assert TOKEN not in json.dumps(full, default=str) and TOKEN not in json.dumps(results, default=str)
    assert urls and TOKEN in urls[0]  # joined into the URL at call time only
    # The hub's database holds no token (the page's or the bot's).
    with desk.rig.db._connection() as conn:
        dump = "\n".join(conn.iterdump())
    assert TOKEN not in dump
