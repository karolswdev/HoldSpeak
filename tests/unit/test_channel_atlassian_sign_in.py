"""PHILO-10-04 (Muad'Dib's ruling on #697, board 14 as ratified): a signed-out
Atlassian account is known BEFORE the dispatch boundary.

Story 02's GitHub channel reads its login before the boundary; the Jira and
Confluence channels now run the same switch-and-verify (``acli <product> auth
switch`` then ``status``, under the acli lock) before it: signed out is
REFUSED ``atlassian_not_signed_in`` with its receipt, no row crosses the
boundary and no create runs. A sign-out between that check and the send is
still the post-boundary known failure (``atlassian_not_logged_in``).

Through the REAL hub on an isolated HOME; only the process edge is canned
(story 02's rig, ``_philo10_cli.Canned``).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_cli import install, save  # noqa: E402
from _philo10_send import Hub, _boot, ops, prepare, room, send, sends  # noqa: E402

UNAUTH = "✗ Error: unauthorized: use 'acli jira auth login' to authenticate"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.mark.parametrize("channel", ["jira", "confluence"])
def test_a_signed_out_account_is_refused_before_the_boundary(hub: Hub, monkeypatch: pytest.MonkeyPatch,
                                                            channel: str) -> None:
    canned = install(monkeypatch)
    _pid, update = room(hub)
    dest = save(hub, channel)["destination"]["id"]
    sid = prepare(hub, update, dest)["send"]["id"]
    canned.answers[("acli", channel, "auth", "switch")] = lambda argv: (1, "", UNAUTH)
    answer = send(hub, {"send_id": sid})
    assert answer.status_code == 409 and answer.json()["code"] == "atlassian_not_signed_in", answer.text
    row = next(s for s in sends(hub) if s["id"] == sid)
    assert (row["state"], row["dispatch_started_at"], row["dispatch_seq"]) == ("prepared", None, None), row
    assert canned.creates() == []
    [operation] = [o for o in ops(hub, "channel.send")]
    assert operation["state"] == "refused", operation


def test_a_sign_out_after_the_check_is_the_post_boundary_known_failure(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    canned = install(monkeypatch)
    _pid, update = room(hub)
    dest = save(hub, "confluence")["destination"]["id"]
    sid = prepare(hub, update, dest)["send"]["id"]
    switches: list[int] = []

    def switch(argv: list[str]) -> Any:
        switches.append(1)
        return (0, "✓ Switched\n", "") if len(switches) == 1 else (1, "", UNAUTH)

    canned.answers[("acli", "confluence", "auth", "switch")] = switch
    answer = send(hub, {"send_id": sid})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert (body["outcome"], body["send"]["reason"]) == ("failed", "atlassian_not_logged_in"), body
    assert len(switches) == 2 and canned.creates() == []
