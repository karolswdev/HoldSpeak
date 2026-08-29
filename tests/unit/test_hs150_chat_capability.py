"""HS-150-02 — chat.turn capability registration + backfill tests."""
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


# ── Registry tests ─────────────────────────────────────────────────────


def test_chat_turn_seals_in_registry() -> None:
    """chat.turn is present in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.turn")
    assert definition.id == "chat.turn"
    assert definition.label == "Desk chat"
    assert definition.group_id == "thoughts_notes"
    assert definition.output_kind == "chat_turn_answer"
    assert definition.source_module == "holdspeak.services.thread_service"


def test_recipe_chat_raises_unknown_in_registry() -> None:
    """recipe.chat is no longer in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    with pytest.raises(UnknownInferenceCapability, match="recipe.chat"):
        registry.require("recipe.chat")


def test_chat_turn_is_assignable() -> None:
    """chat.turn has owner visibility (not future/internal)."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.turn")
    assert definition.owner_visibility == "owner"


# ── Backfill tests ─────────────────────────────────────────────────────


def _schema_sql() -> str:
    """Minimal schema for assignment tables."""
    from holdspeak.db.schema import SCHEMA_SQL
    return SCHEMA_SQL


def _seed_assignment(
    conn: sqlite3.Connection,
    capability_key: str,
    profile_id: str = "profile-1",
) -> str:
    """Seed an assignment chain for the given capability key."""
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
            '{"schema":"test"}', "sha256:test", "2026-08-29T00:00:00",
        ),
    )
    conn.execute(
        """INSERT INTO inference_assignment_heads
           (assignment_key, assignment_id, revision, cleared, updated_at)
           VALUES (?,?,?,0,?)""",
        (assignment_key, assignment_id, 1, "2026-08-29T00:00:00"),
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
    """Read the current assignment entries for a capability key."""
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


def test_backfill_copies_recipe_chat_chain() -> None:
    """When recipe.chat has an assignment, it is copied to chat.turn."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "recipe.chat", profile_id="recipe-profile")
    _backfill_chat_route_assignments(conn)

    chain = _get_chain(conn, "chat.turn")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "recipe-profile"
    assert chain[0]["ordinal"] == 1


def test_backfill_copies_ask_answer_when_no_recipe_chat() -> None:
    """When recipe.chat is absent but ask.answer exists, ask.answer is copied."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "ask.answer", profile_id="ask-profile")
    _backfill_chat_route_assignments(conn)

    chain = _get_chain(conn, "chat.turn")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "ask-profile"


def test_backfill_prefers_recipe_chat_over_ask_answer() -> None:
    """recipe.chat takes precedence when both exist."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "recipe.chat", profile_id="recipe-profile")
    _seed_assignment(conn, "ask.answer", profile_id="ask-profile")
    _backfill_chat_route_assignments(conn)

    chain = _get_chain(conn, "chat.turn")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "recipe-profile"


def test_backfill_idempotent() -> None:
    """Running the backfill twice produces the same result."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "recipe.chat", profile_id="recipe-profile")
    _backfill_chat_route_assignments(conn)
    _backfill_chat_route_assignments(conn)  # second run is a no-op

    chain = _get_chain(conn, "chat.turn")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "recipe-profile"


def test_backfill_never_overwrites_existing_chat_turn() -> None:
    """An existing chat.turn chain is never overwritten."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _seed_assignment(conn, "chat.turn", profile_id="existing-profile")
    _seed_assignment(conn, "recipe.chat", profile_id="recipe-profile")
    _backfill_chat_route_assignments(conn)

    chain = _get_chain(conn, "chat.turn")
    assert len(chain) == 1
    assert chain[0]["profile_id"] == "existing-profile"


def test_backfill_noop_when_no_sources() -> None:
    """Nothing happens when neither recipe.chat nor ask.answer exists."""
    from holdspeak.db.reconcile import _backfill_chat_route_assignments

    conn = _fresh_db()
    _backfill_chat_route_assignments(conn)

    chain = _get_chain(conn, "chat.turn")
    assert chain == []
