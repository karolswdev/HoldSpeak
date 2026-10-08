"""PHILO-14 A5, Astra r1 on #935: the producer-backed fences of the Needs-you
drawer's hub side.

P1-1  A held call the hub cannot show whole. The hook sends the first 120
      chars of the redacted call (a design limit: the whole command never
      leaves the agent) and now the length of the redacted COMMAND it shows;
      ``db.gate.command_view`` (one place, for the drawer, the lane and the
      shade) says the head is cut and how many command characters are
      missing (``argsCut`` / ``argsHidden``). The
      drawer offers Deny and Open on such a row, never Approve. Fenced with a
      real 198-char command through hook -> GateService -> kernel -> gate ->
      membership.
P1-3  One object, one count. An agent's ask on the item it was handed is
      part of that item: one member, the ask listed with ``foldedInto``.
      Fenced through the real hook ingestion (the agent registry) and
      ``compose``.
"""
from __future__ import annotations

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
