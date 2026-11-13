"""An answer from Telegram decides only the question it was given to, and an
update is read one time.

Review 14a (2026-11-13) of the long-poll fix. The poll had timed out on every
round for ten days, so almost no update arrived; now they arrive, a backlog
too. Three things mattered at once: a plain "yes" was applied to "the one open
question" (a queued "yes" for question A could approve question B); a handler
that raised still moved the cursor (the update was lost) and a restart could
read an update again; and the loop waited 30 s more when a back-off ended
during the tick.
"""
from __future__ import annotations

import threading
import time
from typing import Any

from holdspeak.services import reach_service, telegram_reach
from holdspeak.services.telegram_reach import TelegramReach
from tests.unit.test_reach_telegram import (  # noqa: F401  (keystore: the autouse fixture)
    Desk, item_ref, keystore, reply_to, update,
)


def _held(desk: Desk, title: str) -> tuple[str, dict[str, Any]]:
    """A held ``core`` question of a Program with this title (``Desk.core`` with a title)."""
    from tests.integration.program_rig import FAKE_CHECK, OWNER

    rig = desk.rig
    pid = rig.service.create(OWNER, title=title, goal="Stop the stalls.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control=desk.control)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store it.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "core")
    return pid, item


def _asked(desk: Desk, title: str = "Overnight on the home box") -> tuple[str, int]:
    """One held question sent to Telegram: (its ref, its message id)."""
    pid, item = _held(desk, title)
    ref = item_ref(pid, item)
    desk.telegram.brief(ref)
    return ref, desk.bot.next_id


def _waits(desk: Desk, ref: str) -> bool:
    """This question's Program still has its ``core`` question open."""
    return any(row["kind"] == "core" for row in desk.rig.program(ref.split(":")[1])["your_turn_items"])


# ── a decision needs its question ────────────────────────────────────


def test_a_plain_yes_decides_nothing_and_the_bot_says_how_to_answer(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref, _message_id = _asked(desk)
    desk.bot.calls.clear()

    out = desk.telegram.handle_update(update("reply", text="Yes"))

    assert out["action"] == "no_package"
    assert desk.bot.of("sendMessage")[-1]["text"] == telegram_reach.NO_TARGET_WORDS
    assert _waits(desk, ref), "the one open question still waits"


def _buttons(desk: Desk) -> list[str]:
    rows = (desk.bot.of("sendMessage")[-1].get("reply_markup") or {}).get("inline_keyboard") or []
    return [button["text"] for row in rows for button in row]


def test_an_answer_word_with_a_question_open_gets_only_the_how_to_line(tmp_path) -> None:
    """The rule of #2296 comes first: a person who types "yes" means the
    question. No note or Ask is offered, and nothing is kept or decided."""
    from holdspeak.services import reach_inbound

    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref, _message_id = _asked(desk)
    label = str(desk.bot.of("sendMessage")[-1]["reply_markup"]["inline_keyboard"][0][0]["text"])
    for word in ("yes", "No.", "ok", "later", label):          # a choice word of the open question too
        desk.bot.calls.clear()
        out = desk.telegram.handle_update(update("reply", text=word))
        assert out["action"] == "no_package", word
        assert [call["text"] for call in desk.bot.of("sendMessage")] == [telegram_reach.NO_TARGET_WORDS], word
        assert _buttons(desk) == [], word
    assert reach_inbound.waiting_count(desk.telegram) == 0, "no words wait for a press"
    assert _waits(desk, ref), "the question still waits"


def test_a_sentence_with_a_question_open_is_offered_and_says_a_question_waits(tmp_path) -> None:
    from holdspeak.services import reach_inbound

    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref, _message_id = _asked(desk)
    desk.bot.calls.clear()

    out = desk.telegram.handle_update(update("reply", text="Remember to move the freeze to Friday"))

    assert out["action"] == "thought"
    said = desk.bot.of("sendMessage")[-1]["text"]
    assert "Remember to move the freeze to Friday" in said
    assert reach_inbound.QUESTION_WAITS_WORDS in said
    assert _buttons(desk) == ["Keep as a note", "Ask my desk"]
    assert _waits(desk, ref), "the words decide nothing: the question still waits"


def test_a_reply_answers_the_question_it_replies_to_and_never_another(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref_a, message_a = _asked(desk, "Question A")
    ref_b, _message_b = _asked(desk, "Question B")  # B opened later
    assert _waits(desk, ref_a) and _waits(desk, ref_b)

    out = desk.telegram.handle_update(reply_to(desk, "Yes", message_id=message_a))

    assert out["action"] == "answered" and out["choice"] == "go_on"
    assert not _waits(desk, ref_a), "A is answered"
    assert _waits(desk, ref_b), "B, which opened later, still waits"


def test_a_reply_to_a_message_that_asked_nothing_decides_nothing(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref, _message_id = _asked(desk)
    desk.bot.calls.clear()

    out = desk.telegram.handle_update(reply_to(desk, "Yes", message_id=4242))

    assert out["action"] == "no_package"
    assert desk.bot.of("sendMessage")[-1]["text"] == telegram_reach.NO_TARGET_WORDS
    assert _waits(desk, ref)


def test_a_message_written_before_the_question_was_asked_does_not_answer_it(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    ref, message_id = _asked(desk)
    desk.bot.calls.clear()
    an_hour_ago = int(time.time()) - 3600

    out = desk.telegram.handle_update(reply_to(desk, "Yes", message_id=message_id, date=an_hour_ago))

    assert out["action"] == "too_old"
    assert desk.bot.of("sendMessage")[-1]["text"] == telegram_reach.OLD_MESSAGE_WORDS
    assert _waits(desk, ref)


# ── an update is read one time ───────────────────────────────────────


class _Queue:
    """A Bot API whose getUpdates gives the updates not yet confirmed by an
    offset, as Telegram does; every other method goes to the rig's fake bot."""

    def __init__(self, desk: Desk, updates: list[dict[str, Any]]) -> None:
        self.desk, self.updates, self.offsets = desk, updates, []

    def __call__(self, token: str, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method != "getUpdates":
            return self.desk.bot(token, method, params)
        offset = params.get("offset")
        self.offsets.append(offset)
        return {"ok": True, "result": [row for row in self.updates
                                       if offset is None or int(row["update_id"]) >= int(offset)]}


def _texts(desk: Desk) -> list[str]:
    return [params["text"] for params in desk.bot.of("sendMessage")]


def test_an_update_whose_handler_raises_is_read_again_then_skipped_with_one_line(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    bad = update("reply", text="first")
    bad["update_id"] = 700
    good = update("reply", text="second")
    good["update_id"] = 701
    desk.telegram._call = _Queue(desk, [bad, good])
    handled: list[int] = []
    real = desk.telegram.handle_update

    def handle(row: dict[str, Any]) -> dict[str, Any]:
        handled.append(int(row["update_id"]))
        if row["update_id"] == 700:
            raise RuntimeError("the handler broke")
        return real(row)

    monkeypatch.setattr(desk.telegram, "handle_update", handle)
    desk.bot.calls.clear()

    first = desk.telegram.poll_once(None)
    assert first is None and desk.telegram.last_poll_ok is False, "the cursor stays on the update; the loop waits"
    assert handled == [700], "the update after it waits its turn"
    second = desk.telegram.poll_once(first)
    assert second is None and handled == [700, 700]
    assert telegram_reach.SKIPPED_WORDS not in _texts(desk)

    third = desk.telegram.poll_once(second)

    assert handled == [700, 700, 700, 701], "three tries, then the queue moves on"
    assert third == 702
    assert _texts(desk).count(telegram_reach.SKIPPED_WORDS) == 1
    assert desk.telegram.skipped_updates()["count"] == 1


def test_an_update_read_before_a_restart_is_not_read_again(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path, control="normal")
    desk.pair()
    once = update("reply", text="hello")
    once["update_id"] = 800
    desk.telegram._call = _Queue(desk, [once])
    assert desk.telegram.poll_once(None) == 801

    # A restart: a new service object over the same database, no offset kept,
    # and Telegram gives the unconfirmed update again.
    restarted = TelegramReach(desk.rig.db, caller=_Queue(desk, [once]), briefing=desk.briefing, reach=desk.reach,
                              programs=lambda: desk.rig.service)
    handled: list[int] = []
    monkeypatch.setattr(restarted, "handle_update", lambda row: handled.append(int(row["update_id"])) or {})

    assert restarted.poll_once(None) == 801, "the cursor still moves past it"
    assert handled == [], "the replayed update is passed over"


# ── the loop ─────────────────────────────────────────────────────────


def test_the_wait_after_a_round_with_no_good_poll() -> None:
    from holdspeak.services.reach_service import idle_wait

    assert idle_wait(False, -5.0) == reach_service.IDLE_WAIT, "polling is off: the idle wait"
    assert idle_wait(True, 4.0) == 4.0, "a back-off still runs: what is left of it"
    assert idle_wait(True, 400.0) == reach_service.IDLE_WAIT, "the tick still runs every 30 s"
    assert idle_wait(True, -0.1) == 0.0, "the back-off ended during the tick: poll at once"


class _OnceFailing:
    """The first poll fails; every later poll answers (and then waits a
    moment, as a long poll does)."""

    def __init__(self) -> None:
        self.polls: list[float] = []
        self.last_poll_ok = True

    def should_poll(self) -> bool:
        return True

    def poll_once(self, offset: Any) -> Any:
        self.polls.append(time.monotonic())
        self.last_poll_ok = len(self.polls) > 1
        if self.last_poll_ok:
            time.sleep(0.05)
        return offset


def test_the_loop_polls_at_once_when_the_back_off_ended_during_the_tick(tmp_path, monkeypatch) -> None:
    desk = Desk(tmp_path)
    telegram = _OnceFailing()
    desk.reach._telegram = lambda: telegram
    monkeypatch.setattr(reach_service.PollBackoff, "FIRST", 0.05)
    desk.reach.tick = lambda: time.sleep(0.3)  # the tick outlasts the back-off

    desk.reach.start()
    try:
        deadline = time.monotonic() + 5
        while len(telegram.polls) < 2 and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        desk.reach.stop()
        thread: threading.Thread = desk.reach._thread
        thread.join(timeout=5)

    assert len(telegram.polls) >= 2, "the loop waited its 30 s idle wait after the back-off had ended"
    assert telegram.polls[1] - telegram.polls[0] < 3
