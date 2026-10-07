"""PHILO-14 A5, Astra r1 on #935: the producer-backed fences of the Needs-you
drawer's hub side.

P1-1  A held call the hub cannot show whole. The hook sends the first 120
      chars of the redacted call (a design limit: the whole command never
      leaves the agent) and now its whole length; the needs-you row says the
      head is cut and how much is missing (``argsCut`` / ``argsHidden``). The
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
    whole = len(redact(canonical))
    assert redact_call({"command": command, "description": "x"}).length == whole
    # The hook's body carries the number only (the census holds no tool_input there).
    assert launched.posted[-1]["args_len"] == whole and "tool_input" not in launched.posted[-1]
    # The hub stores the head only, and now the length of the whole call.
    assert len(held.proposal.args_head) == ARGS_HEAD_CHARS
    assert held.proposal.operation["args_len"] == whole
    [row] = [r for r in _gate_rows(launched) if r["ref"] == f"gate:{held.proposal.id}"]
    assert row["argsCut"] is True
    assert row["argsHidden"] == whole - ARGS_HEAD_CHARS
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
    redacted = redact(canonical)
    assert redacted != canonical  # the secret is redacted
    assert redact_call(call).length == len(redacted) != len(canonical)

