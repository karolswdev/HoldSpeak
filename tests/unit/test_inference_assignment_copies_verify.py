"""Assignment copies verify (owner's desk 2026-10-29: Engines read "Not read").

The chat copy backfills in ``holdspeak/db/reconcile.py`` once copied the
source chain's ``payload_json`` and ``sha256`` verbatim, so each copy named
the source id and scope and every read of the assignments answered 409
``inference_assignment_integrity_invalid``. These tests seed the owner's
exact bad rows (from a copy of his database) and prove the startup reconcile
repairs them once, and that both copy sites now write verifiable rows.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.db.reconcile import (
    ASSIGNMENT_COPY_REPAIR_FAMILY,
    _backfill_chat_practice_assignments,
    _backfill_chat_route_assignments,
    reconcile_schema,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile

OWNER = Principal(PrincipalKind.OWNER, "copies-verify-owner")

# The owner's rows, verbatim from his database copy (2026-10-29).
SOURCE_ID = "ia_1ef791f1d703456795272742009a91e7"
CREATED_AT = "2026-10-20T18:45:18.155398Z"
SOURCE_SHA = "sha256:fbe5c879b293d96b331316a0e39e51e2fcf80fe341ef5bdc1bb5538ebf97c12b"
SOURCE_PAYLOAD = (
    '{"created_at":"2026-10-20T18:45:18.155398Z","entries":[{"ordinal":1,'
    '"profile_id":"agent-codex","profile_revision":1,"profile_schema_version":2}],'
    '"id":"ia_1ef791f1d703456795272742009a91e7","retry_policy_id":null,"revision":1,'
    '"schema":"InferenceAssignment@1","scope":{"capability_id":"ask.answer","kind":"capability"}}'
)
OWNER_ROWS = (
    ("capability:ask.answer", SOURCE_ID, "ask.answer"),
    ("capability:chat.compact", "ia_59efefcad633420eae8b5103f3e79082", "chat.compact"),
    ("capability:chat.guardrail", "ia_42c0fdc956664134996c8dc179d82f2b", "chat.guardrail"),
    ("capability:chat.turn", "ia_67121ebd162f4f5687bc91a074593cf5", "chat.turn"),
)
BAD_KEYS = ["capability:chat.compact", "capability:chat.guardrail", "capability:chat.turn"]


@pytest.fixture
def db(tmp_path: Path) -> Database:
    database = Database(tmp_path / "copies.db")
    _profile(database, "agent-codex")
    return database


def _seed_owner_shape(db: Database) -> None:
    with db._connection() as conn:
        for key, assignment_id, capability_id in OWNER_ROWS:
            conn.execute(
                """INSERT INTO inference_assignment_revisions
                   (assignment_id, revision, assignment_key, scope_kind, scope_id,
                    subject_kind, selector_kind, capability_id, group_id,
                    retry_policy_id, payload_json, sha256, created_at, made_by)
                   VALUES (?,1,?,'global','','','capability',?,'',NULL,?,?,?,'owner')""",
                (assignment_id, key, capability_id, SOURCE_PAYLOAD, SOURCE_SHA, CREATED_AT),
            )
            conn.execute(
                "INSERT INTO inference_assignment_heads VALUES (?,?,1,0,?)",
                (key, assignment_id, CREATED_AT),
            )
            conn.execute(
                "INSERT INTO inference_assignments VALUES (?,?,1,'agent-codex',1,2,1)",
                (f"{assignment_id}:1:1", assignment_id),
            )
        conn.commit()


def _verify_every_head(db: Database) -> list[str]:
    service = InferenceAssignmentService(db)
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT r.*, h.assignment_key AS head_key, h.assignment_id AS head_id,
                      h.revision AS head_revision, h.cleared AS head_cleared
                 FROM inference_assignment_heads h JOIN inference_assignment_revisions r
                   ON r.assignment_id=h.assignment_id AND r.revision=h.revision
                WHERE h.cleared=0 ORDER BY h.assignment_key"""
        ).fetchall()
        for row in rows:
            service._assignment_material(conn, row, require_active_head=True)
    return [str(row["head_key"]) for row in rows]


def _snapshot(db: Database) -> tuple:
    with db._connection() as conn:
        return tuple(
            tuple(conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall())
            for table in (
                "inference_assignment_heads",
                "inference_assignment_revisions",
                "inference_assignments",
                "inference_assignment_migrations",
            )
        )


def test_owner_bad_copies_fail_before_the_repair(db: Database) -> None:
    _seed_owner_shape(db)
    with pytest.raises(Exception) as caught:
        InferenceAssignmentService(db).list_assignments(OWNER)
    assert getattr(caught.value, "code", "") == "inference_assignment_integrity_invalid"


def test_reconcile_repairs_the_owner_copies_once(db: Database) -> None:
    _seed_owner_shape(db)
    with db._connection() as conn:
        reconcile_schema(conn)
        conn.commit()

    assert _verify_every_head(db) == [key for key, _, _ in OWNER_ROWS]
    listed = InferenceAssignmentService(db).list_assignments(OWNER)["assignments"]
    assert len(listed) == 4
    InferenceAssignmentService(db).assignment_summary(OWNER)

    with db._connection() as conn:
        marker = conn.execute(
            "SELECT marker_revision, result_json FROM inference_assignment_migrations "
            "WHERE family=?",
            (ASSIGNMENT_COPY_REPAIR_FAMILY,),
        ).fetchone()
        heads = dict(
            conn.execute(
                "SELECT assignment_key, revision FROM inference_assignment_heads"
            ).fetchall()
        )
        old = conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_revisions WHERE payload_json=?",
            (SOURCE_PAYLOAD,),
        ).fetchone()[0]
    assert marker[0] == 1
    assert json.loads(marker[1])["repaired_keys"] == BAD_KEYS
    # The bad revisions stay as history; the heads moved to revision 2.
    assert old == 4
    assert heads == {
        "capability:ask.answer": 1,
        "capability:chat.compact": 2,
        "capability:chat.guardrail": 2,
        "capability:chat.turn": 2,
    }
    assert InferenceAssignmentService(db).migration_marker(
        OWNER, family=ASSIGNMENT_COPY_REPAIR_FAMILY
    )["result"]["repaired_keys"] == BAD_KEYS

    before = _snapshot(db)
    with db._connection() as conn:
        reconcile_schema(conn)
        conn.commit()
    assert _snapshot(db) == before


def test_both_copy_sites_write_verifiable_rows(db: Database) -> None:
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "seed-ask",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "agent-codex", "profile_revision": 1}],
        },
    )
    with db._connection() as conn:
        _backfill_chat_route_assignments(conn)
        _backfill_chat_practice_assignments(conn)
        conn.commit()

    assert _verify_every_head(db) == [
        "capability:ask.answer",
        "capability:chat.compact",
        "capability:chat.guardrail",
        "capability:chat.turn",
    ]
    InferenceAssignmentService(db).list_assignments(OWNER)
    with db._connection() as conn:
        ids = {
            row[0]
            for row in conn.execute("SELECT assignment_id FROM inference_assignment_heads")
        }
        repairs = conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations WHERE family=?",
            (ASSIGNMENT_COPY_REPAIR_FAMILY,),
        ).fetchone()[0]
    assert len(ids) == 4  # every copy has its own id
    assert repairs == 0
