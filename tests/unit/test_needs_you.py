"""Needs-you: grouping, the drawer, the fixture week, newly-ready meetings and coverage.

Grouped by service (the fast diet, 2026-10-12). Moved verbatim from:
- test_philo17_needs_you_grouping.py
- test_philo14_a5_needs_drawer.py
- test_philo13_needs_you_fixture.py
- test_philo13_c3_ready.py
- test_phase200_attention_coverage.py
"""
from __future__ import annotations

# ── moved from tests/unit/test_philo17_needs_you_grouping.py ──
# PHILO-17 (needsyou): sources of one cause are ONE Needs-you row.
#
# The walker saw 34 rows: 31 GitHub/Jira sources that could not be checked,
# each its own row with a raw runner error, above the three rows that needed
# him. The hub now counts the sources of one cause once (``source_group_key``),
# names a plain cause when it has one, and keeps the raw line in ``reason``.

from datetime import datetime

from holdspeak.services.needs_you_aggregate import _watch_coverage
from holdspeak.services.needs_you_membership import source_group_key, unread_source_groups
from holdspeak.services.project_service import ProjectService

RAW = "To get started with GitHub CLI, please run:  gh auth login"


def _gap(n: int, *, provider: str = "github", token: str = "CANT CHECK", state: str = "failed",
         cause: str | None = "Not signed in", reason: str | None = None, verb: str = "Reconnect",
         href: str = "/settings", host: str = "github.com") -> dict:
    return {
        "source_id": f"watch:w{n}", "kind": "watch", "state": state, "provider": provider,
        "label": f"GitHub · acme/r{n}", "project_id": f"p{n}", "host": host,
        "reason": reason if reason is not None else (cause or RAW), "cause": cause,
        "repair": {"token": token, "verb": verb, "href": href},
    }


def test_thirty_sources_of_one_cause_and_one_repair_are_one_group() -> None:
    # Thirty Rooms; Reconnect goes to Settings for every one of them.
    coverage = [_gap(n) for n in range(30)]
    groups = unread_source_groups(coverage)
    assert len(groups) == 1
    assert len(groups[0]) == 30


def test_a_different_provider_token_or_cause_is_its_own_group() -> None:
    coverage = [
        _gap(1), _gap(2),
        _gap(3, provider="jira"),
        _gap(4, token="STALE", state="stale", cause="not checked recently"),
        _gap(5, cause="Tool not installed"),
        {"source_id": "x", "kind": "watch", "state": "available", "provider": "github"},
        _gap(6, state="quiet", token="QUIET UNTIL 08:00", cause="quiet until 08:00"),
    ]
    groups = unread_source_groups(coverage)
    # The available and the quiet sources are never counted.
    assert [len(g) for g in groups] == [2, 1, 1, 1]
    assert source_group_key(coverage[0]) == source_group_key(coverage[1])


def test_a_different_repair_destination_is_its_own_group() -> None:
    # Astra r1 (1): two paused Watches in two Rooms each open their own Room.
    a = _gap(1, state="unavailable", token="PAUSED", cause="paused", verb="Open source", href="/projects/pA")
    b = _gap(2, state="unavailable", token="PAUSED", cause="paused", verb="Open source", href="/projects/pB")
    assert len(unread_source_groups([a, b])) == 2


def test_a_different_egress_host_is_its_own_group() -> None:
    # Astra r1 (3): Retry on two Jira sites names two hosts.
    a = _gap(1, provider="jira", state="stale", token="STALE", cause="not checked recently",
             verb="Retry", href="/projects/p1", host="a.atlassian.net")
    b = {**a, "source_id": "watch:w2", "host": "b.atlassian.net"}
    assert len(unread_source_groups([a, b])) == 2


def test_unknown_causes_group_only_on_the_same_first_line() -> None:
    # Astra r1 (2): a 404 and a 429 are two problems, never one row.
    e404 = _gap(1, cause=None, reason="HTTP 404: Not Found (repos/acme/r1)")
    e429 = _gap(2, cause=None, reason="HTTP 429: rate limit exceeded")
    e429b = _gap(3, cause=None, reason="HTTP 429:  rate limit exceeded\nretry-after: 60")
    groups = unread_source_groups([e404, e429, e429b])
    assert [len(g) for g in groups] == [1, 2]


def test_a_signed_out_cli_reads_not_signed_in() -> None:
    assert ProjectService._plain_reason(RAW) == "Not signed in"
    assert "Not signed in" in ProjectService.PLAIN_REASONS


def test_watch_coverage_names_the_provider_and_a_plain_cause_only() -> None:
    now = datetime(2026, 10, 10, 9, 0)
    room = {"sources": {"state": "ok", "items": [
        {"watchId": "w1", "provider": "gh", "scope": "acme/r1", "state": "cant_check",
         "plainReason": "fatal: some raw runner line 0x7f"},
        {"watchId": "w2", "provider": "jira", "scope": "KAN", "state": "cant_check",
         "plainReason": "Jira rejected the query"},
        {"watchId": "w3", "provider": "github", "scope": "acme/r3", "state": "live",
         "checkedAt": "2026-10-09T01:00:00"},
    ]}}
    rows = {row["source_id"]: row for row in _watch_coverage(room, "p1", "Payments", now, 3600.0)}
    raw = rows["watch:w1"]
    assert raw["provider"] == "github" and raw["cause"] is None
    assert raw["reason"] == "fatal: some raw runner line 0x7f"
    assert rows["watch:w2"]["cause"] == "Jira rejected the query"
    stale = rows["watch:w3"]
    assert stale["state"] == "stale" and stale["cause"] == "not checked recently"


# ── moved from tests/unit/test_philo14_a5_needs_drawer.py ──
# PHILO-14 A5, Astra r1 on #935: the producer-backed fences of the Needs-you
# drawer's hub side.
#
# P1-1  A held call the hub cannot show whole. The hook sends the first 120
#       chars of the redacted call (a design limit: the whole command never
#       leaves the agent) and now the length of the redacted COMMAND it shows;
#       ``db.gate.command_view`` (one place, for the drawer, the lane and the
#       shade) says the head is cut and how many command characters are
#       missing (``argsCut`` / ``argsHidden``). The
#       drawer offers Deny and Open on such a row, never Approve. Fenced with a
#       real 198-char command through hook -> GateService -> kernel -> gate ->
#       membership.
# P1-3  One object, one count. An agent's ask on the item it was handed is
#       part of that item: one member, the ask listed with ``foldedInto``.
#       Fenced through the real hook ingestion (the agent registry) and
#       ``compose``.

import json
from typing import Any

import pytest

from holdspeak.coder_gate import ARGS_HEAD_CHARS, redact_call
from holdspeak.db.gate import HELD
from holdspeak.memory.defense import redact
from holdspeak.services import needs_you_membership as membership
from holdspeak.services.needs_you_membership import _read_gate_holds, compute_needs_you
from tests.unit.test_conductor_k3_coder_needs_you import (  # noqa: F401  (hooks is a fixture)
    OWNER,
    T0,
    _stub_other_hub_reads,
    hooks,
)
from tests.unit.test_agent_hand import db  # noqa: F401  (db is a fixture)
from tests.unit.test_philo14_c0_launch_lane import worktree  # noqa: F401  (a fixture)
from tests.unit.test_conductor_k5_supervision import _call, _mode, launched  # noqa: F401


def _gate_rows(rig: Any) -> list[dict[str, Any]]:
    holds = _read_gate_holds(rig.db, ledger=rig.launches)
    return [r for r in compute_needs_you(gate_holds=holds)["unmutedItems"] if r["kind"] == "gate"]


# ── P1-1 ──────────────────────────────────────────────────────────────


def test_a_198_char_command_is_a_cut_row_that_names_what_is_missing(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "safe")
    base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = "
    command = base + "7" * (198 - len(base) - 1) + "'"
    assert len(command) == 198, len(command)
    held = _call(launched, command)
    assert held.proposal.state == HELD
    canonical = json.dumps({"command": command, "description": "x"}, separators=(",", ":"), sort_keys=True)
    # The length is the REDACTED canonical text's (never the raw call's: the
    # raw length would tell the size of a redacted secret).
    whole = len(json.loads(redact(canonical))["command"])   # the shown command form
    assert whole == 198
    assert redact_call({"command": command, "description": "x"}).length == whole
    # The hook's body carries the number only (the census holds no tool_input there).
    assert launched.posted[-1]["args_len"] == whole and "tool_input" not in launched.posted[-1]
    # The hub stores the head only, and now the length of the whole call.
    assert len(held.proposal.args_head) == ARGS_HEAD_CHARS
    assert held.proposal.operation["args_len"] == whole
    [row] = [r for r in _gate_rows(launched) if r["ref"] == f"gate:{held.proposal.id}"]
    assert row["argsCut"] is True
    # Counted on the text the owner sees: the head holds 108 chars of the
    # command after `{"command":"`, so 90 of its 198 are unseen.
    shown = row["title"].removeprefix("Approve: ")
    assert len(shown) == ARGS_HEAD_CHARS - len('{"command":"') == 108
    assert row["argsHidden"] == 198 - 108 == 90
    # The shade reads the same view (GET /api/gate/proposals): the shown
    # command and the same hidden count.
    from holdspeak.principals import Principal, PrincipalKind
    shade = launched.gate.list_proposals(Principal(PrincipalKind.OWNER, "owner"), {"state": "held"})
    [card] = [p for p in shade["proposals"] if p["id"] == held.proposal.id]
    assert card["args_cut"] is True and card["args_hidden"] == 90 and command.startswith(card["args_shown"])
    # The row shows the command's own text, never the JSON around it.
    assert row["title"].startswith("Approve: psql -h staging-ledger")
    assert command.startswith(row["title"].removeprefix("Approve: "))


def test_a_short_command_is_whole_and_keeps_approve(launched, tmp_path, monkeypatch) -> None:  # noqa: F811
    _mode(tmp_path, monkeypatch, "safe")
    held = _call(launched, "ls /etc")
    [row] = [r for r in _gate_rows(launched) if r["ref"] == f"gate:{held.proposal.id}"]
    assert row["argsCut"] is False and row["argsHidden"] == 0
    assert row["title"] == "Approve: ls /etc"


def test_an_older_hook_with_no_length_reads_a_full_head_as_cut() -> None:
    head = "x" * ARGS_HEAD_CHARS
    assert membership._args_cut(head, None) == {"args_cut": True, "args_hidden": 0}
    # The shared view: lane, shade and Needs you read one function.
    from holdspeak.db.gate import command_view
    view = command_view('{"command":"' + "a" * 108, 198)
    assert view == {"command": "a" * 108, "args_cut": True, "args_hidden": 90}
    assert command_view('{"command":"ls /etc","description":"x"}', 7) == {"command": "ls /etc", "args_cut": False, "args_hidden": 0}
    assert membership._args_cut("short", None) == {"args_cut": False, "args_hidden": 0}


# ── P1-3 ──────────────────────────────────────────────────────────────


def _door_with_item() -> dict[str, Any]:
    return {"board": {"now": [{
        "id": "ai-runbook", "source": "action_item", "target_ref": "action_item:ai-runbook",
        "title": "Write the rollback runbook", "owner": None, "due": T0.date().isoformat(),
        "project_id": "p-ledger",
    }]}, "people_store_state": None}


def test_an_ask_on_a_handed_item_is_one_member(hooks, monkeypatch) -> None:  # noqa: F811
    _stub_other_hub_reads(monkeypatch)
    monkeypatch.setattr(membership, "_read_door", lambda db, p: _door_with_item())
    flights = [{"origin_ref": "action:ai-runbook", "session_key": "claude:s1", "state": "waiting", "close": None}]
    monkeypatch.setattr("holdspeak.services.agent_flights.agent_flights", lambda db, sessions=None, **k: flights)
    hooks.ask("The runbook needs a rollback owner. Jordan or Avery?", T0)
    answer = membership.compose(None, OWNER, {"items": [], "coverage": [], "complete": True},
                                muted_project_ids=[], now=T0)
    # One object, one count: the item is the member; the ask rides on it.
    assert [m["ref"] for m in answer["members"]] == ["ai-runbook"]
    assert answer["count"] == 1
    [ask] = [r for r in answer["items"] if r["source"] == "coder"]
    assert ask["foldedInto"] == "ai-runbook"
    assert sum(answer.get("projectCounts", {}).values()) <= answer["count"]


def test_an_ask_with_no_handed_item_stays_its_own_member(hooks, monkeypatch) -> None:  # noqa: F811
    _stub_other_hub_reads(monkeypatch)
    monkeypatch.setattr(membership, "_read_door", lambda db, p: _door_with_item())
    monkeypatch.setattr("holdspeak.services.agent_flights.agent_flights", lambda db, sessions=None, **k: [])
    hooks.ask("Keep the old migration?", T0)
    answer = membership.compose(None, OWNER, {"items": [], "coverage": [], "complete": True},
                                muted_project_ids=[], now=T0)
    assert sorted(m["ref"] for m in answer["members"]) == ["ai-runbook", "coder:claude:s1"]
    assert answer["count"] == 2


@pytest.mark.parametrize("state, folds", [("working", True), ("ended", False), ("expired", False)])
def test_only_a_live_flight_folds(state, folds) -> None:
    items = [
        {"id": "door:ai-1", "ref": "ai-1", "source": "action_item", "_doorCard": {"target_ref": "action_item:ai-1"}},
        {"id": "coder:claude:s1", "ref": "coder:claude:s1", "source": "coder", "sessionKey": "claude:s1"},
    ]
    membership.fold_asks(items, [{"origin_ref": "action:ai-1", "session_key": "claude:s1", "state": state}])
    assert bool(items[1].get("foldedInto")) is folds


def test_a_second_ask_of_the_same_session_folds_into_the_same_item() -> None:
    """Owner ruling 2026-10-07: one object, one row, always. A held call while
    the agent's question is folded is the same item's too: one member."""
    items = [
        {"id": "door:ai-1", "ref": "ai-1", "source": "action_item", "_doorCard": {"target_ref": "action_item:ai-1"}},
        {"id": "coder:claude:s1", "ref": "coder:claude:s1", "source": "coder", "sessionKey": "claude:s1"},
        {"id": "gate:p1", "ref": "gate:p1", "source": "gate", "sessionKey": "claude:s1"},
    ]
    membership.fold_asks(items, [{"origin_ref": "action:ai-1", "session_key": "claude:s1", "state": "waiting"}])
    assert [i.get("foldedInto") for i in items] == [None, "ai-1", "ai-1"]


def test_the_length_is_the_redacted_texts_never_the_raw_calls() -> None:
    """A secret's size never leaks through the length: the redacted text is
    what is measured."""
    secret = "sk-ant-api03-" + "A" * 80
    call = {"command": f"curl -H 'x-api-key: {secret}' https://example.invalid", "description": "x"}
    canonical = json.dumps(call, separators=(",", ":"), sort_keys=True)
    redacted = json.loads(redact(canonical))["command"]
    assert redacted != call["command"]  # the secret is redacted
    assert redact_call(call).length == len(redacted) != len(call["command"])



# ── Astra r2: the fold covers muted and waiting items too ─────────────


@pytest.mark.parametrize("case", ["muted", "waiting"])
def test_an_ask_on_a_muted_or_waiting_item_shows_the_item_counted_once(hooks, monkeypatch, case) -> None:  # noqa: F811
    """Owner ruling 2026-10-07: every ask folds into its item whatever the
    item's mute or wait; the item is shown with its ask and counted once."""
    _stub_other_hub_reads(monkeypatch)
    board = _door_with_item()
    card = board["board"].pop("now")[0]
    if case == "waiting":
        card.update(owner="Priya", due=None)
        board["board"]["waiting"] = [card]
    else:
        board["board"]["now"] = [card]
    monkeypatch.setattr(membership, "_read_door", lambda db, p: board)
    flights = [{"origin_ref": "action:ai-runbook", "session_key": "claude:s1", "state": "waiting", "close": None}]
    monkeypatch.setattr("holdspeak.services.agent_flights.agent_flights", lambda db, sessions=None, **k: flights)
    hooks.ask("The runbook needs a rollback owner. Jordan or Avery?", T0)
    muted = ["p-ledger"] if case == "muted" else []
    answer = membership.compose(None, OWNER, {"items": [], "coverage": [], "complete": True},
                                muted_project_ids=muted, now=T0)
    assert [m["ref"] for m in answer["members"]] == ["ai-runbook"], answer["members"]
    assert answer["count"] == 1
    [item] = [r for r in answer["items"] if r.get("ref") == "ai-runbook"]
    assert item["muted"] is False and item["waiting"] is False and item["askOverrides"] is True
    [ask] = [r for r in answer["items"] if r["source"] == "coder"]
    assert ask["foldedInto"] == "ai-runbook" and ask["muted"] is False


@pytest.mark.parametrize("case", ["muted", "waiting"])
def test_with_no_ask_a_muted_or_waiting_item_keeps_its_place(hooks, monkeypatch, case) -> None:  # noqa: F811
    _stub_other_hub_reads(monkeypatch)
    board = _door_with_item()
    if case == "waiting":
        card = board["board"].pop("now")[0]
        card.update(owner="Priya", due=None)
        board["board"]["waiting"] = [card]
    monkeypatch.setattr(membership, "_read_door", lambda db, p: board)
    monkeypatch.setattr("holdspeak.services.agent_flights.agent_flights", lambda db, sessions=None, **k: [])
    answer = membership.compose(None, OWNER, {"items": [], "coverage": [], "complete": True},
                                muted_project_ids=["p-ledger"] if case == "muted" else [], now=T0)
    assert answer["count"] == 0
    [item] = [r for r in answer["items"] if r.get("ref") == "ai-runbook"]
    assert not item.get("askOverrides")
    assert (item["muted"] is True) if case == "muted" else (item["waiting"] is True)


def test_the_lane_route_carries_the_cut_view(tmp_path, worktree, monkeypatch) -> None:  # noqa: F811
    """The lane route's `gated[]` (the lane's approval surface) carries the
    same view for the 198-char call the hook sends (the hook's own fields)."""
    from holdspeak.db import Database
    from tests.unit.test_philo14_c0_launch_lane import _lane

    lane_db = Database(tmp_path / "lane.db")
    client = _lane(tmp_path, lane_db, worktree, monkeypatch)
    base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = "
    command = base + "7" * (198 - len(base) - 1) + "'"
    call = redact_call({"command": command, "description": "x"})
    lane_db.gate.propose(
        proposal_id="toolu_cut", session_key="claude:s1", agent="claude", tool="Bash",
        args_sha256=call.sha256, args_head=call.head, cwd=str(worktree), ttl_seconds=240,
        operation={"args_len": call.length},
    )
    body = client.get("/api/agent/launches/launch_abc/lane").json()
    gated = {g["id"]: g for g in body["gated"]}
    assert gated["toolu_cut"]["args_cut"] is True and gated["toolu_cut"]["args_hidden"] == 90
    assert command.startswith(gated["toolu_cut"]["args_shown"]) and len(gated["toolu_cut"]["args_shown"]) == 108
    assert gated["toolu_1"]["args_cut"] is False  # the short call stays whole



# ── PHILO-15-09 (B11, the A5 ruling: headline = Dock badge = notch = rows) ──


def test_the_one_number_counts_every_row_the_drawer_draws(hooks, monkeypatch, tmp_path) -> None:  # noqa: F811
    """A seed with an unread source, a recording that arms and a folded
    question: the hub's count is the drawer's rows (1 member + 1 source +
    1 arming; the ask rides on its item's row and is not counted again)."""
    from holdspeak.db.core import Database

    _stub_other_hub_reads(monkeypatch)
    monkeypatch.setattr(membership, "_read_door", lambda db, p: _door_with_item())
    flights = [{"origin_ref": "action:ai-runbook", "session_key": "claude:s1", "state": "waiting", "close": None}]
    monkeypatch.setattr("holdspeak.services.agent_flights.agent_flights", lambda db, sessions=None, **k: flights)
    hooks.ask("The runbook needs a rollback owner. Jordan or Avery?", T0)
    hub = Database(tmp_path / "arming.db")
    rec = hub.scheduled_recordings.create(title="Standup", cron_expr="0 9 * * *")
    hub.scheduled_recordings.set_state(rec.id, "arming")
    unread = {"source_id": "gh:ledger", "kind": "project", "state": "failed", "observed_at": None,
              "label": "CI red on main", "project_id": "p-ledger"}
    seen = {"source_id": "jira:ops", "kind": "project", "state": "available", "observed_at": None}
    answer = membership.compose(hub, OWNER, {"items": [], "coverage": [unread, seen], "complete": False},
                                muted_project_ids=[], now=T0)
    [ask] = [r for r in answer["items"] if r["source"] == "coder"]
    assert ask["foldedInto"] == "ai-runbook"
    assert [m["ref"] for m in answer["members"]] == ["ai-runbook"]
    assert answer["arming"] == [{"scheduleId": rec.id, "title": "Standup", "armedAt": answer["arming"][0]["armedAt"]}]
    rows = len(answer["members"]) + len(membership.unread_sources(answer["coverage"])) + len(answer["arming"])
    assert rows == 3
    assert answer["count"] == rows


# ── moved from tests/unit/test_philo13_needs_you_fixture.py ──
# PHILO-13 H-A2: real producer and route boundaries for the oracle week.

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from holdspeak.db import Database
from scripts.philo13_needs_you_fixture import (
    A1_ID,
    A1_ROOM_TASK,
    A1_TASK,
    A2_TASK,
    A3_ID,
    A4_ID,
    D1_ID,
    DECISION_REF,
    FAILED_MEETING_ID,
    seed_week,
)


REPO = Path(__file__).resolve().parents[2]


def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "oracle-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home, home / "holdspeak.db"


def _board_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    board = payload["door"]["board"]  # type: ignore[index]
    return [
        row
        for lane in ("overdue", "now", "waiting", "unassigned")
        for row in board[lane]  # type: ignore[index]
    ]


def test_seed_accepts_existing_empty_hub_and_refuses_oracle_reseed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    db = Database(db_path)
    db.close()

    seeded = seed_week(db_path, home=home)
    assert seeded["mode"] == "seed"
    assert set(seeded["before"]) >= {
        "door", "needsYou", "roomItems", "assignments", "meetings", "heartbeat",
    }
    assert seeded["mutation"] == {
        "method": "PATCH",
        "path": f"/api/all-action-items/{A1_ID}",
        "body": {"status": "done"},
    }
    assert seeded["expectedRefs"] == [
        A1_ID, A2_TASK, A4_ID, DECISION_REF, "blocker:engines", FAILED_MEETING_ID,
    ]
    assert seeded["ids"]["project"].startswith("proj-")
    assert seeded["ids"]["project"] != "philo13-a2-project"
    assert seeded["ids"]["mutedProject"].startswith("proj-")
    assert seeded["producerEvidence"]["oracleWiring"]["roomA2ActionItemId"] == seeded["ids"]["A2"]

    with pytest.raises(FileExistsError, match="oracle meeting IDs"):
        seed_week(db_path, home=home)

    reopened = Database(db_path)
    try:
        assert reopened.meetings.get_meeting("philo13-a2-meeting") is not None
        assert reopened.meetings.get_meeting("philo13-a2-failed-meeting") is not None
        room_item = reopened.projects.get_project_item(seeded["ids"]["A1Room"])
        assert room_item is not None
        assert room_item["title"] == A1_ROOM_TASK
        assert room_item["title"] != A1_TASK
        assert room_item["lifecycle"] == "planned"
        assert room_item["due_at"] > seeded["now"][:10]
    finally:
        reopened.close()


def test_export_reads_same_real_ids_and_mutates_a1_through_http_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home, db_path = _isolated(tmp_path, monkeypatch)
    seeded = seed_week(db_path, home=home)

    from scripts.philo13_needs_you_fixture import export_week

    exported = export_week(db_path, home=home)
    assert exported["ids"] == seeded["ids"]
    assert exported["expectedRefs"] == seeded["expectedRefs"]
    assert exported["mutation"]["method"] == "PATCH"
    assert exported["mutation"]["path"] == f"/api/all-action-items/{seeded['ids']['A1']}"
    assert exported["mutation"]["status"] == 200

    before_rows = _board_rows(exported["before"])
    after_rows = _board_rows(exported["after"])
    assert seeded["ids"]["A1"] in {str(row["id"]) for row in before_rows}
    assert seeded["ids"]["A1"] not in {str(row["id"]) for row in after_rows}
    assert exported["before"]["roomItems"]
    a2_room = [row for row in exported["before"]["roomItems"] if row.get("ref") == A2_TASK]
    assert len(a2_room) == 1
    assert a2_room[0]["actionItemId"] == seeded["ids"]["A2"]
    assert A1_ROOM_TASK != A1_TASK
    assert not any(row.get("ref") == A1_ID for row in exported["before"]["roomItems"])
    assert any(str(row["id"]) == seeded["ids"]["A2"] for row in before_rows)
    assert not any(str(row["id"]) == D1_ID for row in before_rows)
    assert exported["before"]["needsYou"]["items"]


def test_dedup_probe_mints_same_title_door_and_room_rows_through_real_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Before this probe, the canonical week has no duplicate producer pair, so
    # a no-dedup browser mutant also returns six and escapes the C4 fence.
    home, db_path = _isolated(tmp_path, monkeypatch)

    from scripts.philo13_needs_you_fixture import dedup_probe

    probe = dedup_probe(db_path, home=home)
    assert probe["mode"] == "dedup-probe"
    assert probe["expectedRefs"] == [
        A1_ID, A2_TASK, A4_ID, DECISION_REF, "blocker:engines", FAILED_MEETING_ID,
    ]
    assert probe["expectedCount"] == 6
    assert probe["expectedMutantCount"] == 7

    evidence = probe["producerEvidence"]
    door = evidence["doorRoute"]
    room = evidence["roomRoute"]
    assert door["path"] == "/api/door"
    assert door["id"] == evidence["duplicateDoorRef"]
    assert door["title"] == A2_TASK
    assert room["path"] == "/api/desk/needs-you?fresh=1"
    assert room["ref"] == A2_TASK
    assert room["title"] == A2_TASK
    assert room["source"] == "commitment"
    assert room["projectId"] == evidence["duplicateProjectId"]
    assert room["actionItemId"] != evidence["duplicateDoorRef"]
    linked = evidence["linkedMeeting"]
    assert linked["route"] == (
        f"POST /api/projects/{evidence['duplicateProjectId']}/meetings/{linked['meetingId']}"
    )
    assert linked["projectId"] == evidence["duplicateProjectId"]
    assert linked["actionItemId"] == evidence["duplicateDoorRef"]
    assert linked["title"] == A2_TASK
    assert linked["success"] is True

    room_rows = [row for row in probe["before"]["roomItems"] if row.get("title") == A2_TASK]
    assert len(room_rows) == 1
    assert room_rows[0]["projectId"] == evidence["duplicateProjectId"]


def test_cli_stdout_is_json_and_export_keeps_seed_ids(tmp_path: Path) -> None:
    home = tmp_path / "cli-home"
    home.mkdir()
    db_path = home / "holdspeak.db"
    env = {**os.environ, "HOME": str(home), "PYTHONPATH": str(REPO)}

    def run(mode: str) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, str(REPO / "scripts/philo13_needs_you_fixture.py"), mode,
             "--db", str(db_path), "--home", str(home)],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert not completed.stderr
        return json.loads(completed.stdout)

    seeded = run("seed")
    exported = run("export")
    assert set(seeded) >= {"ids", "before", "mutation", "now", "producerEvidence"}
    assert exported["ids"] == seeded["ids"]
    assert exported["mutation"]["status"] == 200


# ── moved from tests/unit/test_philo13_c3_ready.py ──
# PHILO-13 C3: durable, newly-ready meeting attention.

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak import db as db_module
from holdspeak.intel import IntelResult
from holdspeak.meeting_session import (
    IntelSnapshot,
    MeetingSession,
    MeetingState,
    TranscriptSegment,
)
from holdspeak.services.meeting_service import MeetingService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.meetings.crud import build_crud_router


def _meeting(meeting_id: str, *, title: str, status: str = "ready") -> MeetingState:
    return MeetingState(
        id=meeting_id,
        title=title,
        started_at=datetime(2026, 10, 2, 12, 0),
        ended_at=datetime(2026, 10, 2, 12, 30),
        intel_status=status,
        intel_completed_at=datetime(2026, 10, 2, 12, 31),
        intel=IntelSnapshot(timestamp=1.0, summary=f"Stored summary for {meeting_id}"),
    )


def test_old_summary_is_not_unseen_but_new_ready_is_durable_and_readable(tmp_path: Path) -> None:
    db = Database(tmp_path / "c3-ready.db")
    try:
        db.meetings.save_meeting(_meeting("old", title="Old summary"))
        db.meetings.save_meeting(_meeting("old-2", title="Another old summary"))
        db.meetings.save_meeting(_meeting("new", title="New summary"))
        first_ready = db.meetings.mark_ready_unseen("new")

        assert [row["id"] for row in db.meetings.list_unread_ready()] == ["new"]

        db.meetings.mark_ready_read("new")
        assert first_ready is not None
        db.meetings.mark_ready_unseen("new", ready_at=first_ready["ready_at"])
        assert db.meetings.list_unread_ready() == []
        db.meetings.mark_ready_unseen("new", ready_at="new-completion-revision")
        assert [row["id"] for row in db.meetings.list_unread_ready()] == ["new"]
        db.meetings.mark_ready_read("new")
        reopened = Database(tmp_path / "c3-ready.db")
        try:
            assert reopened.meetings.list_unread_ready() == []
        finally:
            reopened.close()
    finally:
        db.close()


def test_ready_read_route_is_idempotent_and_survives_reload(tmp_path: Path) -> None:
    db = Database(tmp_path / "c3-ready-route.db")
    db.meetings.save_meeting(_meeting("m-route", title="Route meeting"))
    db.meetings.save_meeting(_meeting("old-open", title="Old summary"))
    db.meetings.mark_ready_unseen("m-route")
    app = FastAPI()
    app.include_router(
        build_crud_router(
            WebContext(get_state=lambda: {}, meeting_service=MeetingService(db))
        )
    )
    with TestClient(app) as client:
        listed = client.get("/api/meetings/ready")
        assert listed.status_code == 200, listed.text
        assert [row["id"] for row in listed.json()["meetings"]] == ["m-route"]
        first = client.post("/api/meetings/m-route/ready/read")
        second = client.post("/api/meetings/m-route/ready/read")
        old = client.post("/api/meetings/old-open/ready/read")
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert old.status_code == 200, old.text
        assert old.json()["ready_at"] is None
        assert first.json()["read"] is True
        assert client.get("/api/meetings/ready").json()["meetings"] == []
    db.close()


def test_real_bound_queue_completion_creates_unread_ready_marker(tmp_path: Path, monkeypatch) -> None:
    """The production queue completion, not a test-only helper, creates READY."""
    from tests.unit.test_meeting_deferred_admission import _queue_rig, _queued_meeting
    from holdspeak.intel_queue import _process_bound_intel_job
    from holdspeak.services.meeting_deferred_queue_binding import MeetingDeferredQueueBinder

    db, broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    state = _queued_meeting(db, "m-produced-ready")
    claimed = db.intel.claim_next_intel_job_bound(MeetingDeferredQueueBinder(broker))
    assert claimed is not None
    frames: list[str] = []

    assert _process_bound_intel_job(
        db,
        claimed,
        broker,
        on_meeting_ready=frames.append,
        retry_base_seconds=1,
        retry_max_seconds=1,
        retry_max_attempts=4,
    ) is True

    assert frames == [state.id]
    # Read the durable producer seam directly so this fence fails clearly on
    # the pre-C3 source even before repository convenience methods exist.
    with db._connection() as conn:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'meeting_ready_reads'"
        ).fetchone()
        assert table is not None, "real completion must have a durable readiness table"
        marker = conn.execute(
            "SELECT meeting_id, ready_at, read_at FROM meeting_ready_reads WHERE meeting_id = ?",
            (state.id,),
        ).fetchone()
    assert marker is not None
    assert marker["meeting_id"] == state.id
    assert marker["ready_at"]
    assert marker["read_at"] is None
    db.close()


def test_meeting_session_save_marks_only_meaningful_aftercare_before_callback(
    tmp_path: Path, monkeypatch
) -> None:
    """Ended empty saves stay quiet; meaningful aftercare is durable first."""
    db = Database(tmp_path / "c3-session-ready.db")
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    events: list[tuple[str, object]] = []

    def on_broadcast(kind: str, payload: object) -> None:
        if kind == "aftercare_ready":
            marker = db.meetings.list_unread_ready()
            assert marker and marker[0]["id"] == "meaningful"
            events.append((kind, payload))

    empty = MeetingSession(transcriber=None, on_broadcast=on_broadcast)
    empty._state = MeetingState(
        id="empty",
        title="Empty meeting",
        started_at=datetime(2026, 10, 2, 9, 0),
        ended_at=datetime(2026, 10, 2, 9, 30),
    )
    assert empty.save(tmp_path / "empty-json").database_saved is True
    assert events == []
    assert db.meetings.list_unread_ready() == []

    meaningful = MeetingSession(transcriber=None, on_broadcast=on_broadcast)
    meaningful._state = MeetingState(
        id="meaningful",
        title="Meaningful meeting",
        started_at=datetime(2026, 10, 2, 10, 0),
        ended_at=datetime(2026, 10, 2, 10, 30),
        intel=IntelSnapshot(
            timestamp=1.0,
            action_items=[
                {"id": "action-1", "task": "Ship the fix", "owner": "Me"}
            ],
        ),
    )
    assert meaningful.save(tmp_path / "meaningful-json").database_saved is True
    assert [kind for kind, _payload in events] == ["aftercare_ready"]
    assert [row["id"] for row in db.meetings.list_unread_ready()] == ["meaningful"]
    db.close()


def test_live_summary_only_success_persists_ready_before_frame_and_reload(
    tmp_path: Path, monkeypatch
) -> None:
    """A real live analysis result is durable before its frame and callback."""
    db_path = tmp_path / "c3-live-ready.db"
    db = Database(db_path)
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    frame_markers: list[list[dict[str, object]]] = []
    callback_markers: list[list[dict[str, object]]] = []

    def on_broadcast(kind: str, _payload: object) -> None:
        if kind == "intel_complete":
            frame_markers.append(db.meetings.list_unread_ready())

    def on_intel(_snapshot: IntelSnapshot) -> None:
        callback_markers.append(db.meetings.list_unread_ready())

    session = MeetingSession(
        transcriber=None,
        intel_enabled=True,
        on_intel=on_intel,
        on_broadcast=on_broadcast,
    )
    state = MeetingState(
        id="live-summary",
        title="Live summary",
        started_at=datetime(2026, 10, 3, 9, 0),
        segments=[TranscriptSegment("Summary only", "Me", 0.0, 1.0)],
    )
    session._state = state
    session._intel_live = True
    db.meetings.save_meeting(state)
    result = IntelResult(
        topics=[],
        action_items=[],
        summary="The meeting has a concise summary.",
        raw_response="{}",
    )
    monkeypatch.setattr(
        session,
        "_admitted_live_window",
        lambda _transcript, *, final, analysis_id: (
            SimpleNamespace(outcome="succeeded"),
            {"publication": "published", "analysis_id": analysis_id, "final": final},
            result,
        ),
    )

    session._run_intel_analysis()

    assert frame_markers and frame_markers[0][0]["id"] == state.id
    assert callback_markers and callback_markers[0][0]["id"] == state.id
    reopened = Database(db_path)
    try:
        assert [row["id"] for row in reopened.meetings.list_unread_ready()] == [state.id]
    finally:
        reopened.close()
    db.close()


def test_live_provider_failure_does_not_create_ready_marker(
    tmp_path: Path, monkeypatch
) -> None:
    """A refused live provider result never creates durable READY."""
    db = Database(tmp_path / "c3-live-failed.db")
    monkeypatch.setattr(db_module, "get_database", lambda *args, **kwargs: db)
    session = MeetingSession(
        transcriber=None,
        intel_enabled=True,
        intel_deferred_enabled=False,
    )
    state = MeetingState(
        id="live-failed",
        title="Failed live analysis",
        started_at=datetime(2026, 10, 3, 10, 0),
        segments=[TranscriptSegment("Provider fails", "Me", 0.0, 1.0)],
    )
    session._state = state
    session._intel_live = True
    db.meetings.save_meeting(state)
    monkeypatch.setattr(
        session,
        "_admitted_live_window",
        lambda _transcript, *, final, analysis_id: (
            SimpleNamespace(outcome="failed", error="provider unavailable"),
            None,
            None,
        ),
    )

    session._run_intel_analysis()

    assert db.meetings.list_unread_ready() == []
    db.close()


# ── moved from tests/unit/test_phase200_attention_coverage.py ──
# HS-200-07 (C4) — coverage and partial results.
#
# The aggregate carries a coverage record for EVERY expected source, an
# empty result is an all-clear only when coverage is complete, a failed
# source keeps its last-known unresolved items, and concurrent refreshes
# do one build.
#
# Run:
#     HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \
#         tests/unit/test_phase200_attention_coverage.py

import threading
import time
from datetime import datetime, timedelta
from typing import Any

import pytest

from holdspeak.services.needs_you_aggregate import (
    COVERAGE_KINDS,
    COVERAGE_STATES,
    LastKnownStore,
    NeedsYouCache,
    build_aggregate,
)

NOW = datetime(2026, 9, 6, 10, 0, 0)


# ── Fakes: the two callables build_aggregate depends on ──────────────


def _needs_item(title: str, severity: str = "danger", source: str = "github") -> dict:
    return {
        "source": source,
        "title": title,
        "why": f"WAITING ON YOU · {title}",
        "since": "2026-09-04T10:00:00",
        "url": f"https://example.invalid/{title}",
        "severity": severity,
    }


def _room(
    project_id: str,
    *,
    items: list[dict] | None = None,
    needs_state: str = "ok",
    observed_at: str = "2026-09-06T09:00:00",
    sources: list[dict] | None = None,
    meetings_state: str = "ok",
    commitments_state: str = "ok",
) -> dict:
    needs: dict[str, Any]
    if needs_state == "ok":
        needs = {"state": "ok", "items": items or [], "count": len(items or [])}
    else:
        needs = {"state": needs_state, "error_code": "needsYou_read_failed"}
    return {
        "project_id": project_id,
        "observed_at": observed_at,
        "needsYou": needs,
        "sources": {"state": "ok", "items": sources or [], "count": len(sources or [])},
        "meetings": ({"state": "ok", "items": []} if meetings_state == "ok"
                     else {"state": meetings_state, "error_code": "meetings_read_failed"}),
        "commitments": ({"state": "ok", "items": []} if commitments_state == "ok"
                        else {"state": commitments_state,
                              "error_code": "commitments_read_failed"}),
    }


def _watch(
    watch_id: str,
    *,
    state: str = "live",
    checked_at: str | None = "2026-09-06T09:30:00",
    provider: str = "github",
    scope: str = "karolswdev/HoldSpeak",
    plain_reason: str | None = None,
) -> dict:
    return {
        "watchId": watch_id,
        "provider": provider,
        "scope": scope,
        "state": state,
        "checkedAt": checked_at,
        "plainReason": plain_reason,
        "tokens": [],
    }


class Desk:
    """A fake ProjectService pair: list_projects + room, with failures."""

    def __init__(self, rooms: dict[str, dict], *, names: dict[str, str] | None = None) -> None:
        self._rooms = rooms
        self._names = names or {pid: pid.upper() for pid in rooms}
        self.raises: dict[str, BaseException] = {}
        self.list_raises: BaseException | None = None
        self.room_calls = 0

    def list_projects(self, principal: Any, filters: dict[str, Any] | None = None) -> list[dict]:
        if self.list_raises is not None:
            raise self.list_raises
        return [{"id": pid, "name": self._names[pid]} for pid in self._rooms]

    def room(self, principal: Any, project_id: str) -> dict:
        self.room_calls += 1
        if project_id in self.raises:
            raise self.raises[project_id]
        return self._rooms[project_id]


def _coverage_by_id(aggregate: dict) -> dict[str, dict]:
    return {row["source_id"]: row for row in aggregate["coverage"]}


# ── AC1: a failed / forbidden / stale / unavailable Project stays ────


class TestCoverageProjection:
    def test_one_failed_room_among_healthy_rooms_stays_in_coverage(self):
        desk = Desk({
            "alpha": _room("alpha", items=[_needs_item("PR 612")]),
            "beta": _room("beta", items=[]),
        }, names={"alpha": "Q4 Platform", "beta": "Governance"})
        desk.raises["beta"] = RuntimeError("watch table locked")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["project:alpha"]["state"] == "available"
        assert cov["project:beta"]["state"] == "failed", cov["project:beta"]
        assert cov["project:beta"]["label"] == "Governance"
        assert cov["project:beta"]["repair"] == {
            "token": "READ FAILED", "verb": "Retry", "href": "/projects/beta",
        }
        assert agg["complete"] is False

    def test_forbidden_room_is_forbidden_not_failed(self):
        desk = Desk({"alpha": _room("alpha", items=[])})
        desk.raises["alpha"] = PermissionError("principal may not read this Room")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["state"] == "forbidden"
        assert row["repair"]["token"] == "FORBIDDEN"
        assert row["repair"]["verb"] == "Open source"
        assert agg["complete"] is False

    def test_degraded_needs_you_section_is_a_failed_source(self):
        desk = Desk({"alpha": _room("alpha", needs_state="degraded")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["state"] == "failed"
        assert row["reason"] == "needsYou_read_failed"

    def test_every_failure_is_named_when_all_rooms_fail(self):
        desk = Desk({
            "alpha": _room("alpha"), "beta": _room("beta"), "gamma": _room("gamma"),
        })
        for pid in ("alpha", "beta", "gamma"):
            desk.raises[pid] = RuntimeError("connector down")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        assert agg["count"] == 0
        assert agg["complete"] is False
        assert len(agg["coverage"]) == 3
        assert {row["state"] for row in agg["coverage"]} == {"failed"}

    def test_project_list_unavailable_replays_every_remembered_source(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")])},
                    names={"alpha": "Q4 Platform"})
        first = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                principal=None, now=NOW, last_known=memory)
        assert first["complete"] is True

        desk.list_raises = RuntimeError("database is locked")
        second = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                 principal=None, now=NOW, last_known=memory)

        assert second["complete"] is False
        states = {row["source_id"]: row["state"] for row in second["coverage"]}
        assert states["projects"] == "failed"
        assert states["project:alpha"] == "failed"
        assert [row["title"] for row in second["items"]] == ["PR 612"]
        assert second["items"][0]["fromLastObservation"] is True

    def test_meeting_and_commitment_sections_are_expected_sources(self):
        desk = Desk({"alpha": _room("alpha", items=[], commitments_state="degraded")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["meeting:alpha"]["state"] == "available"
        assert cov["commitment:alpha"]["state"] == "failed"
        assert cov["commitment:alpha"]["kind"] == "commitment"
        assert agg["complete"] is False

    def test_watch_states_map_to_coverage_states(self):
        old = (NOW - timedelta(hours=30)).isoformat()
        desk = Desk({"alpha": _room("alpha", items=[], sources=[
            _watch("w-live"),
            _watch("w-stale", checked_at=old),
            _watch("w-paused", state="paused"),
            _watch("w-broken", state="cant_check",
                   plain_reason="The GitHub token expired"),
            _watch("w-never", checked_at=None),
        ])})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        cov = _coverage_by_id(agg)
        assert cov["watch:w-live"]["state"] == "available"
        assert cov["watch:w-stale"]["state"] == "stale"
        assert cov["watch:w-stale"]["observed_at"] == old
        assert cov["watch:w-paused"]["state"] == "unavailable"
        assert cov["watch:w-paused"]["repair"]["token"] == "PAUSED"
        assert cov["watch:w-broken"]["state"] == "failed"
        assert cov["watch:w-broken"]["reason"] == "The GitHub token expired"
        assert cov["watch:w-broken"]["repair"]["verb"] == "Reconnect"
        assert cov["watch:w-never"]["state"] == "unavailable"
        assert cov["watch:w-never"]["observed_at"] is None
        assert agg["complete"] is False

    def test_every_record_uses_the_contract_vocabulary(self):
        desk = Desk({"alpha": _room("alpha", items=[], sources=[_watch("w1")])})
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        for row in agg["coverage"]:
            assert row["state"] in COVERAGE_STATES, row
            assert row["kind"] in COVERAGE_KINDS, row
            assert "observed_at" in row and "repair" in row and "reason" in row


# ── AC2: aggregate computation time is not source freshness ──────────


class TestFreshnessIsNotComputationTime:
    def test_computed_at_is_the_aggregate_clock_not_the_source_clock(self):
        desk = Desk({"alpha": _room("alpha", items=[],
                                    observed_at="2026-09-05T07:00:00")})

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())

        # The aggregate clock, with the hub's offset (never a bare stamp).
        assert agg["computedAt"] == NOW.astimezone().isoformat()
        assert _coverage_by_id(agg)["project:alpha"]["observed_at"] == "2026-09-05T07:00:00"
        assert agg["computedAt"] != agg["coverage"][0]["observed_at"]

    def test_a_failed_source_keeps_the_time_of_its_last_success(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")],
                                    observed_at="2026-09-06T09:00:00")})
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        desk.raises["alpha"] = RuntimeError("connector down")

        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=datetime(2026, 9, 6, 11, 0),
                              last_known=memory)

        row = _coverage_by_id(agg)["project:alpha"]
        assert row["observed_at"] == "2026-09-06T09:00:00"
        assert agg["computedAt"] == datetime(2026, 9, 6, 11, 0).astimezone().isoformat()


# ── AC3: an empty partial result is not an all-clear ─────────────────


class TestEmptyResults:
    def test_empty_and_complete_is_an_all_clear(self):
        desk = Desk({"alpha": _room("alpha", items=[])})
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 0
        assert agg["complete"] is True

    def test_empty_and_partial_is_incomplete_coverage(self):
        desk = Desk({"alpha": _room("alpha", items=[]), "beta": _room("beta")})
        desk.raises["beta"] = RuntimeError("connector down")
        agg = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert agg["count"] == 0
        assert agg["complete"] is False
        assert any(row["state"] != "available" for row in agg["coverage"])


# ── AC4: known items stay traceable across failure and recovery ──────


class TestSeverityCannotDropByDisappearance:
    def test_a_failed_source_keeps_its_last_known_unresolved_items(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("CI red", "danger")])})
        first = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                principal=None, now=NOW, last_known=memory)
        assert first["count"] == 1

        desk.raises["alpha"] = RuntimeError("connector down")
        second = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                 principal=None, now=NOW, last_known=memory)

        assert second["count"] == 1, "a vanished source cannot drop a known item"
        item = second["items"][0]
        assert item["severity"] == "danger", "severity cannot fall by disappearance"
        assert item["fromLastObservation"] is True
        assert item["observedAt"] == "2026-09-06T09:00:00"

    def test_recovery_reconciles_by_stable_id_without_duplicates(self):
        memory = LastKnownStore()
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("CI red", "danger")])})
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        desk.raises["alpha"] = RuntimeError("connector down")
        carried = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                  principal=None, now=NOW, last_known=memory)
        carried_id = carried["items"][0]["id"]

        # The source recovers, still holding the same item.
        del desk.raises["alpha"]
        recovered = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                    principal=None, now=NOW, last_known=memory)

        assert recovered["count"] == 1, "the recovered item is not counted twice"
        assert recovered["items"][0]["id"] == carried_id
        assert "fromLastObservation" not in recovered["items"][0]
        assert recovered["complete"] is True

    def test_a_resolved_item_leaves_on_recovery(self):
        memory = LastKnownStore()
        rooms = {"alpha": _room("alpha", items=[_needs_item("CI red")])}
        desk = Desk(rooms)
        build_aggregate(list_projects=desk.list_projects, room=desk.room,
                        principal=None, now=NOW, last_known=memory)
        rooms["alpha"] = _room("alpha", items=[])

        recovered = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                                    principal=None, now=NOW, last_known=memory)

        assert recovered["count"] == 0
        assert recovered["complete"] is True

    def test_item_ids_are_stable_across_builds(self):
        desk = Desk({"alpha": _room("alpha", items=[_needs_item("PR 612")])})
        one = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        two = build_aggregate(list_projects=desk.list_projects, room=desk.room,
                              principal=None, now=NOW, last_known=LastKnownStore())
        assert one["items"][0]["id"] == two["items"][0]["id"]
        assert one["items"][0]["id"] == "alpha:github:PR 612"


# ── AC5: invalidation and concurrent refresh, bounded ────────────────


class TestCacheCoverage:
    def _builder(self, payload: dict, *, delay: float = 0.0):
        calls = {"n": 0}

        def build() -> dict:
            calls["n"] += 1
            if delay:
                time.sleep(delay)
            return dict(payload)

        return build, calls

    def test_concurrent_refresh_does_one_build_and_keeps_coverage(self):
        payload = {
            "count": 0, "projects": [], "items": [], "next": None,
            "computedAt": NOW.isoformat(), "stale": False, "sweepId": None,
            "coverage": [{"source_id": "project:alpha", "kind": "project",
                          "state": "failed", "observed_at": None,
                          "label": "Q4", "project_id": "alpha",
                          "reason": "down", "repair": {"token": "READ FAILED",
                                                       "verb": "Retry",
                                                       "href": "/projects/alpha"}}],
            "complete": False,
        }
        builder, calls = self._builder(payload, delay=0.05)
        cache = NeedsYouCache(builder, max_age_s=60.0)

        results: list[dict] = []
        errors: list[BaseException] = []

        def read() -> None:
            try:
                results.append(cache.get())
            except BaseException as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [threading.Thread(target=read) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, errors
        assert len(results) == 8
        assert calls["n"] == 1, f"single flight: expected 1 build, got {calls['n']}"
        assert cache.build_count == 1
        for result in results:
            assert result["complete"] is False
            assert len(result["coverage"]) == 1, "no source dropped by the race"

    def test_invalidate_then_a_failing_rebuild_serves_the_last_coverage_as_stale(self):
        payload = {
            "count": 1, "projects": ["alpha"],
            "items": [{"id": "alpha:github:CI red", "severity": "danger"}],
            "next": None, "computedAt": NOW.isoformat(), "stale": False,
            "sweepId": None,
            "coverage": [{"source_id": "project:alpha", "kind": "project",
                          "state": "available", "observed_at": "2026-09-06T09:00:00",
                          "label": "Q4", "project_id": "alpha", "reason": None,
                          "repair": None}],
            "complete": True,
        }
        state = {"fail": False}

        def builder() -> dict:
            if state["fail"]:
                raise RuntimeError("database is locked")
            return dict(payload)

        cache = NeedsYouCache(builder, max_age_s=60.0)
        assert cache.get()["complete"] is True

        state["fail"] = True
        cache.invalidate(sweep_id="sweep-2")
        served = cache.get()

        assert served["stale"] is True, "a stale read says so"
        assert served["count"] == 1, "invalidation did not drop the known item"
        assert served["coverage"][0]["observed_at"] == "2026-09-06T09:00:00"

    def test_a_failing_first_build_raises_rather_than_inventing_an_all_clear(self):
        def builder() -> dict:
            raise RuntimeError("database is locked")

        cache = NeedsYouCache(builder, max_age_s=60.0)
        with pytest.raises(RuntimeError):
            cache.get()

    def test_peek_reports_stale_after_invalidate(self):
        payload = {"count": 0, "projects": [], "items": [], "next": None,
                   "computedAt": NOW.isoformat(), "stale": False, "sweepId": None,
                   "coverage": [], "complete": True}
        builder, _ = self._builder(payload)
        cache = NeedsYouCache(builder, max_age_s=60.0)
        cache.get()
        cache.invalidate()
        peeked = cache.peek()
        assert peeked is not None and peeked["stale"] is True
