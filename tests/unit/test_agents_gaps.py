"""Betterment AG7/AG8 gaps.

- Answer an agent whose hooks are off from its row: his keys reach its pane
  only while the prompt he saw is still on the screen (recorded rig screens).
- Hand again: a new agent continues in the item's own worktree after its
  earlier agent stopped; a running one still refuses.
- #1316, the other order: a tmux server that started after the launch is a
  restart; the session watcher stops the launch instead of completing it.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.agent_context import screen_watch as watch
from holdspeak.agent_context.screen_rules import read_screen

SCREENS = Path(__file__).resolve().parents[1] / "fixtures" / "agent_screens"
T0 = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def _screen(name: str) -> tuple[str, str]:
    meta = json.loads((SCREENS / f"{name}.json").read_text(encoding="utf-8"))
    return (SCREENS / f"{name}.txt").read_text(encoding="utf-8").rstrip("\n"), meta["title"]


class _Ledger:
    def __init__(self, *rows):
        self.rows = {r["launch_id"]: dict(r) for r in rows}

    def get(self, launch_id):
        return self.rows.get(launch_id)


def _tmux(screen_name: str):
    """A tmux stand-in that shows one recorded screen in pane %9."""
    screen, title = _screen(screen_name)
    calls: list[list[str]] = []

    def run(argv):
        calls.append(argv)
        if argv[1] == "list-panes":
            return SimpleNamespace(returncode=0, stdout="%9\n", stderr="")
        if argv[1] == "capture-pane":
            return SimpleNamespace(returncode=0, stdout=screen + "\n", stderr="")
        if argv[1] == "display-message":
            return SimpleNamespace(returncode=0, stdout=title + "\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="no")

    return run, calls


def _store(*names: str) -> watch.ScreenStore:
    store = watch.ScreenStore()
    for i, name in enumerate(names):
        screen, title = _screen(name)
        store.observe("launch:l1", agent="claude", target="hs-l1", verdict=read_screen("claude", screen, title=title),
                      screen=screen, title=title, now=T0 + timedelta(seconds=2 * i))
    return store


RUNNING = {"launch_id": "l1", "state": "launched", "session": "hs-l1"}


def test_allow_on_a_screen_prompt_sends_enter_to_its_pane() -> None:
    store = _store("claude-rig-working", "claude-rig-permission")
    since = watch.screen_wire(store.get("launch:l1"), T0)["since"]
    runner, _calls = _tmux("claude-rig-permission")
    sent: list[dict] = []
    answer = watch.answer_launch("l1", since=since, keys=["Enter"], ledger=_Ledger(RUNNING), store=store,
                                 runner=runner, send=lambda **kw: sent.append(kw) or {"operation_id": "op1"}, now=T0)
    assert answer["status"] == "delivered" and answer["pane_id"] == "%9"
    assert sent == [{"pane": "%9", "keys": ["Enter"], "session_key": "launch:l1", "agent": "claude"}]


def test_a_numbered_choice_is_its_digit_and_a_typed_answer_is_text() -> None:
    store = _store("claude-rig-working", "claude-rig-asks")
    since = watch.screen_wire(store.get("launch:l1"), T0)["since"]
    runner, _ = _tmux("claude-rig-asks")
    sent: list[dict] = []
    watch.answer_launch("l1", since=since, text=" 1 ", ledger=_Ledger(RUNNING), store=store, runner=runner,
                        send=lambda **kw: sent.append(kw) or {}, now=T0)
    assert sent[0]["text"] == "1"
    store = _store("claude-rig-working", "claude-rig-permission")
    runner, _ = _tmux("claude-rig-permission")
    watch.answer_launch("l1", since=watch.screen_wire(store.get("launch:l1"), T0)["since"], keys=["2"],
                        ledger=_Ledger(RUNNING), store=store, runner=runner,
                        send=lambda **kw: sent.append(kw) or {}, now=T0)
    assert sent[1]["keys"] == [{"literal": "2"}]


@pytest.mark.parametrize("case", ["stale_since", "prompt_left", "unknown_key", "not_running"])
def test_nothing_is_sent_when_the_prompt_changed(case: str) -> None:
    store = _store("claude-rig-working", "claude-rig-permission")
    since = watch.screen_wire(store.get("launch:l1"), T0)["since"]
    runner, _ = _tmux("claude-rig-done" if case == "prompt_left" else "claude-rig-permission")
    record = {**RUNNING, "state": "complete"} if case == "not_running" else RUNNING
    sent: list[dict] = []
    with pytest.raises(watch.ScreenAnswerRefused) as refused:
        watch.answer_launch(
            "l1", since="2026-01-01T00:00:00Z" if case == "stale_since" else since,
            keys=["rm -rf"] if case == "unknown_key" else ["Enter"],
            ledger=_Ledger(record), store=store, runner=runner, send=lambda **kw: sent.append(kw), now=T0)
    assert refused.value.code == {"stale_since": "wait_not_current", "prompt_left": "wait_not_current",
                                  "unknown_key": "unknown_key", "not_running": "launch_not_running"}[case]
    assert sent == []


# ── Hand again ────────────────────────────────────────────────────────

from tests.unit.test_agent_hand import OWNER, _rig, _wait_for, db  # noqa: E402,F401


def test_hand_again_continues_in_the_items_own_worktree(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    from holdspeak.services.agent_hand_service import AgentHandRefused

    rig = _rig(tmp_path, db, monkeypatch)
    first = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(first["launch_id"]), "state", "registered")
    (rig.worktree / "work-in-progress.txt").write_text("his agent's unfinished work\n")
    # While its agent runs, the item's worktree is taken.
    with pytest.raises(AgentHandRefused) as refused:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert refused.value.code == "worktree_duplicate"
    rig.service._first.close()
    rig.launches.update(first["launch_id"], state="stopped_by_restart", stopped={"by": "restart"})
    rig.tmux.sessions.clear()
    again = rig.hand.hand(OWNER, "action", "ai_1")
    assert again["status"] == "launched" and again["launch_id"] != first["launch_id"]
    second = rig.launches.get(again["launch_id"])
    assert second["worktree_id"] == record["worktree_id"] and second["branch"] == record["branch"]
    assert (rig.worktree / "work-in-progress.txt").read_text() == "his agent's unfinished work\n"


def test_hand_again_names_only_the_items_own_stopped_launch(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    from holdspeak.delivery.factory_launch import LaunchRefused

    rig = _rig(tmp_path, db, monkeypatch)
    first = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(first["launch_id"]), "state", "registered")
    source = rig.registry.sources()[0] if hasattr(rig.registry, "sources") else rig.source
    request = {"origin_ref": {"kind": "action", "id": "ai_other"},
               "worktree": {"mode": "existing", "worktree_id": record["worktree_id"], "again_of": first["launch_id"]}}
    with pytest.raises(LaunchRefused) as refused:
        rig.service._resolve_worktree(request, source)
    assert refused.value.reason == "hand_again_refused"


# ── #1316: a tmux server that started after the launch ────────────────


def test_a_tmux_server_younger_than_the_launch_is_a_restart(tmp_path, db, monkeypatch) -> None:  # noqa: F811
    from tests.unit import test_agent_hand

    rig = _rig(tmp_path, db, monkeypatch)
    launch_id = rig.hand.hand(OWNER, "action", "ai_1")["launch_id"]
    _wait_for(lambda: rig.launches.get(launch_id), "state", "registered")
    real_call = test_agent_hand._Tmux.__call__
    later = int(datetime.now(timezone.utc).timestamp()) + 3600

    def call(self, argv, cwd=None):
        if argv[:2] == ["tmux", "list-sessions"]:
            return self._ok(f"{later}\n")
        return real_call(self, argv, cwd)

    monkeypatch.setattr(test_agent_hand._Tmux, "__call__", call)
    rig.tmux.sessions.clear()   # tmux restarted: the launch's session is gone
    rig.tmux.meta.clear()
    stopped = _wait_for(lambda: rig.launches.get(launch_id), "state", "stopped_by_restart")
    assert stopped["stopped"]["by"] == "restart"
