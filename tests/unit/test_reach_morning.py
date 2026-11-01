"""PG-DIRECTION DIR7, the open half: one morning message.

DIRECTION-2026-10-31.md §5 "The digest": the morning brief of Cadence and the
night's "Since last night" become the digest's head, so there is one morning
message, not three. The one message carries the night's line, what waits on
him, and the Cadence brief's one line when a loop is due; Cadence's own daily
push stays quiet while Reach's Telegram rung is on.
"""
from __future__ import annotations

from holdspeak.cadence.models import OpenLoop
from holdspeak.services.reach_service import CADENCE_DAILY, carries_cadence
from tests.integration.program_rig import OWNER, local_noon
from tests.unit.test_reach_telegram import Desk, keystore  # noqa: F401  (the autouse keystore)


def _morning(tmp_path, *, mode: str = "digest") -> Desk:
    desk = Desk(tmp_path)
    desk.pair()
    reach = desk.reach
    noon = local_noon()  # the test reads no wall clock
    reach._clock = lambda: noon.isoformat()
    reach.quiet = lambda: (0, 0)  # no quiet hours
    reach.save_settings(OWNER, {"telegram": mode, "digest": noon.hour})
    desk.bot.calls.clear()
    return desk


def _loop(desk: Desk) -> None:
    desk.rig.db.cadence.upsert_loop(OpenLoop(source_type="proposal", source_id="p1",
                                             title="Create issue: watchdog", stale_score=16.0))


def _texts(desk: Desk) -> list[str]:
    return [row["text"] for row in desk.bot.of("sendMessage")]


def _carried(desk: Desk) -> str | None:
    policy = desk.rig.db.cadence.get_policy(CADENCE_DAILY)
    return (policy.config or {}).get("last_sent_date") if policy else None


def test_the_cadence_line_names_the_top_move_only_when_a_loop_is_due(tmp_path) -> None:
    desk = _morning(tmp_path)
    assert desk.reach.cadence_line() is None
    _loop(desk)
    line = desk.reach.cadence_line()
    assert line.startswith("Cadence: ") and line.endswith(" 1 open loop.")


def test_the_nights_line_carries_the_cadence_line_in_one_message(tmp_path) -> None:
    desk = _morning(tmp_path)
    _loop(desk)
    sent = desk.reach.night_line("program:p1:night:2026-11-02", "Dreaming · HoldSpeak\nSince last night: 1 step done")
    assert sent["sent"] is True
    (text,) = _texts(desk)
    assert "Since last night: 1 step done" in text and "\nCadence: " in text
    assert _carried(desk) == local_noon().strftime("%Y-%m-%d")
    # The tick at the same hour sends no second message: no digest, no Cadence line again.
    desk.reach.tick()
    assert len(_texts(desk)) == 1


def test_the_digest_carries_what_waits_and_the_cadence_line_once(tmp_path) -> None:
    desk = _morning(tmp_path)
    desk.core()
    _loop(desk)
    desk.bot.calls.clear()
    assert desk.reach.tick()["digest"] is not None
    (text,) = _texts(desk)
    assert text.startswith("1 waits on you") and "step 1" in text
    assert text.rstrip().splitlines()[-1].startswith("Cadence: ")
    desk.reach.tick()
    assert len(_texts(desk)) == 1


def test_only_a_due_loop_is_one_plain_line_and_nothing_due_sends_nothing(tmp_path) -> None:
    desk = _morning(tmp_path)
    assert desk.reach.tick()["digest"] is None and _texts(desk) == []
    _loop(desk)
    desk.reach.tick()
    (text,) = _texts(desk)
    assert text.startswith("Cadence: ") and "wait on you" not in text


def test_cadences_own_push_stays_quiet_while_reach_carries_it(tmp_path, monkeypatch) -> None:
    desk = _morning(tmp_path)
    assert carries_cadence(desk.rig.db) is True
    desk.reach.save_settings(OWNER, {"telegram": "off"})
    assert carries_cadence(desk.rig.db) is False
    desk.reach.save_settings(OWNER, {"telegram": "at_once"})
    monkeypatch.setenv("HOLDSPEAK_TELEGRAM", "off")
    assert carries_cadence(desk.rig.db) is False
