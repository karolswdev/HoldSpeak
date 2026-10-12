"""PHILO-15 lane 17 (B51) on a real hub: a merge on GitHub reaches the Room
receipt within one poll, with no press.

The hub is the real ``MeetingWebServer`` (uvicorn on a real port, its
startup tasks running, the PR poll among them). The launch is K2's real
hand-to-agent launch with K4's real follow-through; ``gh`` is faked at its
process boundary (the rig's runner) and answers the rehearsal's real PR #1.
The poll period is cut from 120 s to 1 s. The test opens the PR, starts the
hub, flips the PR to merged on the fake GitHub and reads
``/api/coders/sessions`` (what the Room receipt reads) until the flight is
merged, by the PR's own title, with the item closed. Nobody presses Run now.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import pytest

from tests.unit.test_agent_hand import _seed
from tests.unit.test_conductor_k4_follow_through import _status, _sweep
from tests.unit.test_philo15_17_merge_reaches_update import REAL_PR1, _real_pr, _rehearsal_launch

pytestmark = [pytest.mark.timeout(120)]

TOKEN = "philo15-17-pr-poll"


def _flights(url: str) -> list[dict]:
    request = urllib.request.Request(
        f"{url}/api/coders/sessions?include_ended=false", headers={"X-HoldSpeak-Token": TOKEN},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return list(json.loads(response.read()).get("flights") or [])


def test_a_merge_lands_on_the_room_receipt_within_one_poll(tmp_path: Path, monkeypatch) -> None:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.delivery import factory_launch, follow_through
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    db = get_database()
    _seed(db)

    rig = _rehearsal_launch(tmp_path, db, monkeypatch)
    # The hub reads this launch ledger (the flights) and polls with this
    # follow-through (its gh is the fake); every 1 s instead of 120 s.
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", tmp_path / "launches.json")
    monkeypatch.setattr(follow_through, "default_follow_through", lambda _db: rig.observer)
    monkeypatch.setattr(follow_through, "POLL_SECONDS", 1)

    rig.gh.prs = [_real_pr(rig.branch, rig.head, "OPEN")]
    _sweep(rig)  # the agent's PR is open and kept on the launch
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    try:
        url = server.start()
        [flight] = _flights(url)
        assert flight["state"] == "pr_open" and flight["pr"]["title"] == REAL_PR1["title"]

        rig.gh.calls.clear()
        rig.gh.prs = [_real_pr(rig.branch, rig.head, "MERGED")]  # merged on GitHub
        merged_at = time.monotonic()
        deadline = merged_at + 10.0
        while time.monotonic() < deadline:
            [flight] = _flights(url)
            if flight["state"] == "merged" and flight.get("close") == "closed":
                break
            time.sleep(0.2)
        landed = time.monotonic() - merged_at
        assert flight["state"] == "merged", flight
        assert flight["close"] == "closed"
        assert landed < 5.0, f"the receipt took {landed:.1f}s with a 1 s poll"
        # The Room receipt's words: the PR's own title, number and link.
        assert flight["pr"] == {
            "number": 1, "url": REAL_PR1["url"], "state": "merged", "title": REAL_PR1["title"],
        }
        assert flight["merged_at"] == REAL_PR1["mergedAt"]
        assert _status(db, "ai_1") == "done"
        views = [c for c in rig.gh.calls if c[:3] == ["gh", "pr", "view"]]
        assert views and all(c[3] == REAL_PR1["url"] for c in views), "one gh pr view per poll"
        assert not [c for c in rig.gh.calls if c[:3] == ["gh", "pr", "list"]], "no Run now, no sweep"
    finally:
        server.stop()
        rig.tmux.ended = True
        reset_database()
