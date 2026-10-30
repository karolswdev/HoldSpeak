"""Programs PG21: the verified provider matrix (RECIPE PG21).

One recorded stop per harness (``tests/fixtures/usage_limit_captures.json``)
is replayed through the screen watcher's real tick (a fake tmux runner, a
real database): the stop is kept per harness and the Engines fact turns
verified. The Claude Code line is a real capture from this Mac; the Codex
line is the documented wording (no real Codex stop was found).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.agent_context import limit_stops
from holdspeak.agent_context import screen_watch as watch
from holdspeak.agent_context.usage_limit import DOCUMENTED, notice_shape, read_limit
from holdspeak.db import Database, reset_database
from holdspeak.services.concierge_service import _limit_notice

CAPTURES = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "usage_limit_captures.json").read_text())
#: The first time the real Claude Code stop was seen on this Mac.
SEEN = datetime(2026, 10, 19, 13, 17, 36, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = Database(tmp_path / "limits.db")
    yield database
    reset_database()


def _runner(screens: dict[str, str]):
    def run(argv: list[str]) -> SimpleNamespace:
        target = argv[argv.index("-t") + 1]
        if target not in screens:
            return SimpleNamespace(returncode=1, stdout="", stderr="can't find pane")
        out = "" if argv[1] == "display-message" else screens[target]
        return SimpleNamespace(returncode=0, stdout=out + "\n", stderr="")
    return run


def _tick(db, screens: dict[str, str], now: datetime, store: watch.ScreenStore) -> None:
    records = [
        {"launch_id": name, "state": "launched", "session": name, "profile_id": f"{name}-default"}
        for name in screens
    ]
    watch.tick(store, records=records, sessions=[], db=db, runner=_runner(screens), now=now)


# ── the real capture through the parser ───────────────────────────────

def test_the_real_claude_code_stop_is_read_with_its_dated_reset() -> None:
    claude = CAPTURES["claude"]
    assert claude["real"] is True
    reading = read_limit("claude", claude["screen"], SEEN)
    assert reading is not None and reading.stopped and reading.rule == "claude.usage_limit"
    # "resets Oct 24 at 2am (America/Denver)": 02:00 MDT is 08:00 UTC.
    assert reading.until == datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)


def test_the_earlier_real_stop_with_a_bare_clock_rolls_to_the_next_2am() -> None:
    also = CAPTURES["claude"]["also_seen"]
    seen = datetime(2026, 10, 9, 16, 11, 33, tzinfo=timezone.utc)
    reading = read_limit("claude", also["line"], seen)
    assert reading is not None and reading.until == datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)


def test_the_kept_notice_is_its_shape() -> None:
    assert notice_shape(CAPTURES["claude"]["line"]) == "You've hit your weekly limit · resets <date> at <time> (<zone>)"
    assert notice_shape(CAPTURES["codex"]["line"]) == (
        "You've hit your usage limit. Upgrade to Pro (<link>) or try again in <n> hours <n> minutes."
    )


# ── the stop is kept per harness; the Engines fact turns verified ─────

def test_a_stop_on_the_screen_turns_its_harness_verified(db, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(watch.SCREEN_RULES_ENV, "on")
    assert _limit_notice(db, "claude") == {"limitNotice": {
        "verified": False, "notice": DOCUMENTED["claude"], "stoppedAt": None, "resetsAt": None,
    }}
    assert _limit_notice(db, "codex")["limitNotice"]["verified"] is False
    assert _limit_notice(db, "pi") == {}            # not in this slice

    store = watch.ScreenStore()
    _tick(db, {"claude": CAPTURES["claude"]["screen"]}, SEEN, store)
    claude = limit_stops.notice_wire(db, "claude")
    assert claude == {
        "verified": True,
        "notice": "You've hit your weekly limit · resets <date> at <time> (<zone>)",
        "stoppedAt": "2026-10-19T13:17:36Z",
        "resetsAt": "2026-10-24T08:00:00Z",
    }
    assert limit_stops.notice_wire(db, "codex")["verified"] is False

    # The same stop on the next reads keeps the time it was first seen.
    _tick(db, {"claude": CAPTURES["claude"]["screen"]}, SEEN + timedelta(seconds=4), store)
    assert limit_stops.notice_wire(db, "claude")["stoppedAt"] == "2026-10-19T13:17:36Z"

    later = SEEN + timedelta(hours=3)
    _tick(db, {"codex": CAPTURES["codex"]["screen"]}, later, store)
    codex = limit_stops.notice_wire(db, "codex")
    assert codex["verified"] is True and codex["stoppedAt"] == "2026-10-19T16:17:36Z"
    assert codex["resetsAt"] == "2026-10-19T18:30:36Z"     # try again in 2 hours 13 minutes


def test_a_share_warning_and_plain_work_are_not_kept(db, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(watch.SCREEN_RULES_ENV, "on")
    store = watch.ScreenStore()
    _tick(db, {"claude": "Approaching usage limit · 90% of your 5-hour limit used\n╭──╮\n│ > │\n╰──╯"}, SEEN, store)
    _tick(db, {"codex": "› all 12 tests passed\n› "}, SEEN, store)
    assert limit_stops.notice_wire(db, "claude")["verified"] is False
    assert limit_stops.notice_wire(db, "codex")["verified"] is False
