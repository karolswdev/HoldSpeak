"""HS-153-03/05 -- chat.guardrail + chat.compact capability registration + backfill + runner tests."""
from __future__ import annotations

import sqlite3
import uuid

import pytest

from holdspeak.inference_capabilities import (
    InferenceCapabilityRegistry,
    UnknownInferenceCapability,
    builtin_capability_definitions,
    builtin_retry_policy_definitions,
)


# ── Registry / seal tests ────────────────────────────────────────────────


def test_chat_guardrail_seals_in_registry() -> None:
    """chat.guardrail is present in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.guardrail")
    assert definition.id == "chat.guardrail"
    assert definition.label == "Chat guardrail"
    assert definition.group_id == "thoughts_notes"
    assert definition.output_kind == "guardrail_evaluation"
    assert definition.source_module == "holdspeak.services.thread_practice"
    assert definition.requires.structured_output is True


def test_chat_compact_seals_in_registry() -> None:
    """chat.compact is present in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.compact")
    assert definition.id == "chat.compact"
    assert definition.label == "Chat compaction"
    assert definition.group_id == "thoughts_notes"
    assert definition.output_kind == "compaction_summary"
    assert definition.source_module == "holdspeak.services.thread_practice"
    assert definition.requires.structured_output is True


def test_chat_guardrail_is_assignable() -> None:
    """chat.guardrail has owner visibility (not future/internal)."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.guardrail")
    assert definition.owner_visibility == "owner"


def test_chat_compact_is_assignable() -> None:
    """chat.compact has owner visibility (not future/internal)."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.compact")
    assert definition.owner_visibility == "owner"


def test_chat_guardrail_grouped_with_chat_turn() -> None:
    """chat.guardrail is in the same group as chat.turn."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    guardrail = registry.require("chat.guardrail")
    turn = registry.require("chat.turn")
    assert guardrail.group_id == turn.group_id


def test_chat_compact_grouped_with_chat_turn() -> None:
    """chat.compact is in the same group as chat.turn."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    compact = registry.require("chat.compact")
    turn = registry.require("chat.turn")
    assert compact.group_id == turn.group_id


# ── Backfill tests ────────────────────────────────────────────────────────


def _schema_sql() -> str:
    from holdspeak.db.schema import SCHEMA_SQL
    return SCHEMA_SQL


def _seed_assignment(
    conn: sqlite3.Connection,
    capability_key: str,
    profile_id: str = "profile-1",
) -> str:
    assignment_id = "ia_" + uuid.uuid4().hex
    assignment_key = f"capability:{capability_key}"
    conn.execute(
        """INSERT INTO inference_assignment_revisions
           (assignment_id, revision, assignment_key, scope_kind, scope_id,
            subject_kind, selector_kind, capability_id, group_id,
            retry_policy_id, payload_json, sha256, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            assignment_id, 1, assignment_key,
            "global", "", "", "capability", capability_key, "",
            "retry.text.standard",
            '{"schema":"test"}', "sha256:test", "2026-08-30T00:00:00",
        ),
    )
    conn.execute(
        """INSERT INTO inference_assignment_heads
           (assignment_key, assignment_id, revision, cleared, updated_at)
           VALUES (?,?,?,0,?)""",
        (assignment_key, assignment_id, 1, "2026-08-30T00:00:00"),
    )
    conn.execute(
        """INSERT INTO inference_assignments
           (id, assignment_id, assignment_revision, profile_id,
            profile_revision, profile_schema_version, ordinal)
           VALUES (?,?,?,?,?,?,?)""",
        (f"{assignment_id}:1:1", assignment_id, 1, profile_id, 1, 2, 1),
    )
    return assignment_id


def _get_chain(conn: sqlite3.Connection, capability_key: str) -> list[dict]:
    assignment_key = f"capability:{capability_key}"
    head = conn.execute(
        "SELECT assignment_id, revision FROM inference_assignment_heads "
        "WHERE assignment_key=? AND cleared=0",
        (assignment_key,),
    ).fetchone()
    if head is None:
        return []
    rows = conn.execute(
        "SELECT profile_id, profile_revision, profile_schema_version, ordinal "
        "FROM inference_assignments WHERE assignment_id=? AND assignment_revision=? "
        "ORDER BY ordinal",
        (head[0], head[1]),
    ).fetchall()
    return [
        {"profile_id": r[0], "profile_revision": r[1],
         "profile_schema_version": r[2], "ordinal": r[3]}
        for r in rows
    ]


def _fresh_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(_schema_sql())
    return conn


def test_backfill_copies_chat_turn_chain_to_guardrail() -> None:
    """When chat.turn has an assignment, it is copied to chat.guardrail."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "chat.turn", profile_id="turn-profile")
    _backfill_chat_practice_assignments(conn)

    chain = _get_chain(conn, "chat.guardrail")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "turn-profile"


def test_backfill_copies_chat_turn_chain_to_compact() -> None:
    """When chat.turn has an assignment, it is copied to chat.compact."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "chat.turn", profile_id="turn-profile")
    _backfill_chat_practice_assignments(conn)

    chain = _get_chain(conn, "chat.compact")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "turn-profile"


def test_backfill_idempotent() -> None:
    """Running the backfill twice produces the same result."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "chat.turn", profile_id="turn-profile")
    _backfill_chat_practice_assignments(conn)
    _backfill_chat_practice_assignments(conn)  # second run is a no-op

    for cap in ("chat.guardrail", "chat.compact"):
        chain = _get_chain(conn, cap)
        assert len(chain) == 1
        assert chain[0]["profile_id"] == "turn-profile"


def test_backfill_never_overwrites_existing() -> None:
    """Existing chat.guardrail/chat.compact chains are never overwritten."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "chat.guardrail", profile_id="existing-guardrail")
    _seed_assignment(conn, "chat.compact", profile_id="existing-compact")
    _seed_assignment(conn, "chat.turn", profile_id="turn-profile")
    _backfill_chat_practice_assignments(conn)

    guardrail_chain = _get_chain(conn, "chat.guardrail")
    compact_chain = _get_chain(conn, "chat.compact")
    assert len(guardrail_chain) == 1
    assert guardrail_chain[0]["profile_id"] == "existing-guardrail"
    assert len(compact_chain) == 1
    assert compact_chain[0]["profile_id"] == "existing-compact"


def test_backfill_noop_when_no_chat_turn() -> None:
    """Nothing happens when chat.turn does not exist."""
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments

    conn = _fresh_db()
    _backfill_chat_practice_assignments(conn)

    assert _get_chain(conn, "chat.guardrail") == []
    assert _get_chain(conn, "chat.compact") == []


# ── Runner integration tests ──────────────────────────────────────────────


def test_run_guardrail_through_real_coordinator_with_fake_engine() -> None:
    """run_guardrail produces the expected structured output via the runner."""
    from unittest.mock import MagicMock, patch

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.thread_practice import run_guardrail

    principal = Principal(PrincipalKind.OWNER, "test-owner")

    fake_outcome = MagicMock()
    fake_outcome.result = {"violations": ["used cloud egress"], "warnings": ["broad scope"]}

    fake_runner = MagicMock()
    fake_runner.invoke.return_value = fake_outcome

    broker = MagicMock()
    broker.inference_runner = fake_runner

    with patch("holdspeak.kernel.runtime._as_principal") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(return_value=None)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = run_guardrail(
            broker, principal,
            thread_id="thread-1",
            messages=[{"role": "user", "content": "test"}],
            pending_calls=[{"name": "people.note.create", "arguments": {}}],
            guardrail={"instruction": "no cloud egress", "trigger_tools": ["people.*"]},
        )

    assert result == {"violations": ["used cloud egress"], "warnings": ["broad scope"]}
    fake_runner.invoke.assert_called_once()
    request = fake_runner.invoke.call_args[0][0]
    assert request.payload["thread_id"] == "thread-1"
    assert request.payload["guardrail"]["instruction"] == "no cloud egress"


def test_run_compact_through_real_coordinator_with_fake_engine() -> None:
    """run_compact produces the expected structured output via the runner."""
    from unittest.mock import MagicMock, patch

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.thread_practice import run_compact

    principal = Principal(PrincipalKind.OWNER, "test-owner")

    fake_outcome = MagicMock()
    fake_outcome.result = {"summary": "The conversation covered project planning."}

    fake_runner = MagicMock()
    fake_runner.invoke.return_value = fake_outcome

    broker = MagicMock()
    broker.inference_runner = fake_runner

    with patch("holdspeak.kernel.runtime._as_principal") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(return_value=None)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = run_compact(
            broker, principal,
            thread_id="thread-2",
            messages=[
                {"role": "user", "content": "discuss the project"},
                {"role": "assistant", "content": "Let's plan..."},
            ],
        )

    assert result == {"summary": "The conversation covered project planning."}
    fake_runner.invoke.assert_called_once()
    request = fake_runner.invoke.call_args[0][0]
    assert request.payload["thread_id"] == "thread-2"
    assert len(request.payload["messages"]) == 2


def test_run_guardrail_handles_missing_result() -> None:
    """When the engine returns no result dict, guardrail returns empty lists."""
    from unittest.mock import MagicMock, patch

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.thread_practice import run_guardrail

    principal = Principal(PrincipalKind.OWNER, "test-owner")

    fake_outcome = MagicMock()
    fake_outcome.result = None

    fake_runner = MagicMock()
    fake_runner.invoke.return_value = fake_outcome

    broker = MagicMock()
    broker.inference_runner = fake_runner

    with patch("holdspeak.kernel.runtime._as_principal") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(return_value=None)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = run_guardrail(
            broker, principal,
            thread_id="thread-3",
            messages=[],
            pending_calls=[],
            guardrail={},
        )

    assert result == {"violations": [], "warnings": []}


def test_run_compact_handles_missing_result() -> None:
    """When the engine returns no result dict, compact returns empty summary."""
    from unittest.mock import MagicMock, patch

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.thread_practice import run_compact

    principal = Principal(PrincipalKind.OWNER, "test-owner")

    fake_outcome = MagicMock()
    fake_outcome.result = "raw text, not a dict"

    fake_runner = MagicMock()
    fake_runner.invoke.return_value = fake_outcome

    broker = MagicMock()
    broker.inference_runner = fake_runner

    with patch("holdspeak.kernel.runtime._as_principal") as mock_ctx:
        mock_ctx.return_value.__enter__ = MagicMock(return_value=None)
        mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
        result = run_compact(
            broker, principal,
            thread_id="thread-4",
            messages=[],
        )

    assert result == {"summary": ""}
