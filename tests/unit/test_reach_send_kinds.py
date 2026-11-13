"""What Telegram sends, kind by kind (Settings ▸ Reach ▸ What it sends).

Each kind that can travel has its own word under Telegram's rung, saved by
the one reach save (``reach.save``, ``PUT /api/reach``) in the one ``reach``
policy row, and read back in the status with the words it can take. A kind
with no word of its own goes as it did before: at once. Telegram is a fake
transport; nothing here calls Telegram.
"""
from __future__ import annotations

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import reach_commands
from holdspeak.services.reach_service import ReachRefused
from tests.unit.test_reach_commands import DAY, _sends, desk, held, texts  # noqa: F401
from tests.unit.test_reach_telegram import keystore  # noqa: F401
from tests.unit.test_reach_telegram_setup import OWNER

AGENT = Principal(PrincipalKind.AGENT, "agent-1")


def _row(status: dict, kind: str) -> dict:
    (row,) = [row for row in status["ladder"]["sends"] if row["kind"] == kind]
    return row


def test_the_status_names_each_kind_with_its_word_and_the_words_it_takes(tmp_path) -> None:
    d = desk(tmp_path)
    status = d.reach.status(OWNER)
    assert [row["kind"] for row in status["ladder"]["sends"]] == ["question", "tool_call", "send", "failed", "due"]
    question = _row(status, "question")
    assert question["mode"] == "at_once" and question["now"] == "at_once"
    assert [mode["label"] for mode in question["modes"]] == ["At once", "In the digest", "Off"]
    # A notice is a part of the desk's one number in the digest: it has no Off.
    assert [mode["value"] for mode in _row(status, "send")["modes"]] == ["at_once", "digest"]
    due = _row(status, "due")
    assert due["mode"] == "digest" and [mode["value"] for mode in due["modes"]] == ["digest", "off"]
    assert due["fact"]
    assert "six messages in 10 minutes" in status["ladder"]["cap_words"]
    assert "count only" in status["ladder"]["people_words"]
    assert status["digest"]["brief"] == "on"


def test_a_kind_is_saved_by_the_one_reach_save_and_the_others_stay(tmp_path) -> None:
    d = desk(tmp_path)
    d.reach.save_settings(OWNER, {"kinds": {"send": "digest"}})
    d.reach.save_settings(OWNER, {"kinds": {"due": "off"}, "later_means": "tomorrow"})
    settings = d.reach.settings()
    assert settings["kinds"] == {"send": "digest", "due": "off"}
    assert settings["later_means"] == "tomorrow" and settings["telegram"] == "at_once"
    status = d.reach.status(OWNER)
    assert _row(status, "send")["now_words"] == "In the digest" and _row(status, "question")["now"] == "at_once"


def test_a_word_a_kind_does_not_take_is_refused_and_nothing_changes(tmp_path) -> None:
    d = desk(tmp_path)
    for patch in ({"kinds": {"send": "off"}}, {"kinds": {"due": "at_once"}}, {"kinds": {"meeting": "at_once"}},
                  {"kinds": "at_once"}, {"brief": "sometimes"}):
        with pytest.raises(ReachRefused):
            d.reach.save_settings(OWNER, patch)
    assert d.reach.settings()["kinds"] == {} and d.reach.settings()["brief"] == "on"


def test_only_the_owner_saves_a_kind(tmp_path) -> None:
    d = desk(tmp_path)
    with pytest.raises(Exception) as refused:
        d.reach.save_settings(AGENT, {"kinds": {"send": "digest"}})
    assert getattr(refused.value, "code", "") in ("owner_only", "owner_required") or "owner" in str(refused.value).lower()
    assert d.reach.settings()["kinds"] == {}


def test_a_send_that_is_in_the_digest_does_not_travel_one_by_one(tmp_path) -> None:
    d = desk(tmp_path)
    _sends(d.reads, 2)
    d.reach.save_settings(OWNER, {"kinds": {"send": "digest"}})
    before = len(d.bot.of("sendMessage"))
    assert d.reach.tick()["noticed"] == []
    assert texts(d.bot, before) == []
    # At once again: each one is new and travels.
    d.reach.save_settings(OWNER, {"kinds": {"send": "at_once"}})
    assert d.reach.tick()["noticed"] == ["send:0", "send:1"]


def test_a_tool_call_that_is_in_the_digest_is_not_asked_in_the_chat(tmp_path, monkeypatch) -> None:
    d = desk(tmp_path)
    handle, _answers = held(monkeypatch)
    d.reads.hold(handle)
    d.reach.save_settings(OWNER, {"kinds": {"tool_call": "digest"}})
    before = len(d.bot.of("sendMessage"))
    assert [ref for ref in d.reach.tick().get("noticed", []) if ref.startswith("held:")] == []
    assert not [text for text in texts(d.bot, before) if "Email Dana" in text]
    d.reach.save_settings(OWNER, {"kinds": {"tool_call": "at_once"}})
    assert "held:call-1" in d.reach.tick()["noticed"]


def test_telegrams_rung_is_over_every_kind(tmp_path) -> None:
    d = desk(tmp_path)
    d.reach.save_settings(OWNER, {"telegram": "digest"})
    status = d.reach.status(OWNER)
    assert {row["kind"]: row["now"] for row in status["ladder"]["sends"]} == {
        "question": "digest", "tool_call": "digest", "send": "digest", "failed": "digest", "due": "digest"}
    assert _row(status, "question")["mode"] == "at_once", "his own word stays; the rung is over it"
    d.reach.save_settings(OWNER, {"telegram": "off"})
    assert {row["now"] for row in d.reach.status(OWNER)["ladder"]["sends"]} == {"off"}


def test_due_things_off_takes_their_line_out_of_the_brief_and_today_keeps_it(tmp_path) -> None:
    d = desk(tmp_path)
    now = d.reach.now()
    with_due = d.reach._day_lines(d.tg, now)
    assert [line for line in with_due if "due today" in line], "the recorded day has things due"
    d.reach.save_settings(OWNER, {"kinds": {"due": "off"}})
    due = d.reach.send_mode("due") != "off"
    assert not [line for line in d.reach._day_lines(d.tg, now, due=due) if "due today" in line]
    # /today is his own ask: it says what is due.
    assert [line for line in reach_commands.today_lines(d.reads.answer, d.reads.needs, now) if "due today" in line]


def test_the_daily_brief_off_sends_no_digest_at_its_hour(tmp_path) -> None:
    d = desk(tmp_path)
    hour = d.reach.digest_hour()
    local = d.reach.now().astimezone().replace(hour=hour, minute=5)
    d.clock.at = local.astimezone().isoformat()
    assert not d.reach.is_quiet(d.reach.now())
    items = {"program:p:s:core": {"kind": "core_question", "program_title": "Payments ledger cutover", "ordinal": 4}}
    d.reach.save_settings(OWNER, {"brief": "off"})
    before = len(d.bot.of("sendMessage"))
    assert d.reach._maybe_digest(d.tg, d.reach.now(), d.reach.quiet(), items) is None
    assert texts(d.bot, before) == []
    d.reach.save_settings(OWNER, {"brief": "on"})
    assert d.reach._maybe_digest(d.tg, d.reach.now(), d.reach.quiet(), items) is not None
    (sent,) = texts(d.bot, before)
    assert "Payments ledger cutover" in sent


def test_a_question_that_is_off_is_not_in_the_digests_list(tmp_path) -> None:
    d = desk(tmp_path)
    hour = d.reach.digest_hour()
    d.clock.at = d.reach.now().astimezone().replace(hour=hour, minute=5).isoformat()
    items = {"program:p:s:core": {"kind": "core_question", "program_title": "Payments ledger cutover", "ordinal": 4}}
    d.reach.save_settings(OWNER, {"kinds": {"question": "off"}})
    before = len(d.bot.of("sendMessage"))
    d.reach._maybe_digest(d.tg, d.reach.now(), d.reach.quiet(), items)
    assert not [text for text in texts(d.bot, before) if "Payments ledger cutover" in text]
