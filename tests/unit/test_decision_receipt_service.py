"""Tests for the durable decision receipt canon (HS-127-01)."""

from __future__ import annotations

import pytest

from holdspeak.db.core import Database, read_schema_version
from holdspeak.db.schema import SCHEMA_VERSION
from holdspeak.services.decision_receipt_service import DecisionReceiptService


def test_create_receipt_with_all_required_fields(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))

    receipt = service.create(
        None,
        decision_text="Use durable decision receipts.",
        rationale="The decision needs one traceable record.",
        alternatives="Keep decisions split across stores.",
        owner="Karol",
        review_date="2026-09-01",
        source_type="meeting",
        source_id="decision-123",
    )

    assert receipt["id"].startswith("receipt-")
    assert receipt["decision_text"] == "Use durable decision receipts."
    assert receipt["rationale"] == "The decision needs one traceable record."
    assert receipt["alternatives"] == "Keep decisions split across stores."
    assert receipt["owner"] == "Karol"
    assert receipt["review_date"] == "2026-09-01"
    assert receipt["lifecycle"] == "active"
    assert receipt["source_type"] == "meeting"
    assert receipt["source_id"] == "decision-123"
    assert receipt["created_at"] == receipt["updated_at"]


def test_get_receipt_returns_all_fields_and_links(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    receipt = service.create(
        None,
        decision_text="Ship the receipt schema.",
        source_type="desk",
        source_id="adr-127",
    )
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_receipt_sources
               (id, receipt_id, source_type, source_ref, created_at)
               VALUES ('source-1', ?, 'artifact', 'artifact-127', '2026-08-07T00:00:00+00:00')""",
            (receipt["id"],),
        )
        conn.execute(
            """INSERT INTO decision_receipt_work
               (id, receipt_id, work_type, work_ref, created_at)
               VALUES ('work-1', ?, 'project', 'HS-127', '2026-08-07T00:00:00+00:00')""",
            (receipt["id"],),
        )
        conn.execute(
            """INSERT INTO decision_receipt_revisions
               (id, receipt_id, field_name, old_value, new_value, created_at)
               VALUES ('revision-1', ?, 'owner', NULL, 'Karol', '2026-08-07T00:00:00+00:00')""",
            (receipt["id"],),
        )

    loaded = service.get(None, receipt["id"])

    assert loaded is not None
    assert loaded["id"] == receipt["id"]
    assert loaded["decision_text"] == "Ship the receipt schema."
    assert loaded["source_type"] == "desk"
    assert loaded["source_id"] == "adr-127"
    assert loaded["sources"] == [{
        "id": "source-1", "receipt_id": receipt["id"], "source_type": "artifact",
        "source_ref": "artifact-127", "created_at": "2026-08-07T00:00:00+00:00",
    }]
    assert loaded["work"][0]["work_ref"] == "HS-127"
    assert loaded["revisions"][0]["new_value"] == "Karol"


def test_list_receipts_returns_all_receipts(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    first = service.create(None, decision_text="First decision", source_type="meeting", source_id="dec-1")
    second = service.create(None, decision_text="Second decision", source_type="desk", source_id="adr-2")

    receipts = service.list_receipts(None)

    assert {receipt["id"] for receipt in receipts} == {first["id"], second["id"]}


def test_receipt_requires_decision_text_and_source_type(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))

    with pytest.raises(ValueError, match="decision_text is required"):
        service.create(None, decision_text="", source_type="meeting", source_id="dec-1")
    with pytest.raises(ValueError, match="source_type is required"):
        service.create(None, decision_text="A decision", source_type="", source_id="dec-1")


def test_schema_migrates_v40_to_v41(tmp_path):
    path = tmp_path / "v40.db"
    Database(path)
    with Database(path)._connection() as conn:
        conn.execute(
            """INSERT INTO notes (id, title, created_at, updated_at, last_modified)
               VALUES ('pre-v41-note', 'Keep me', '2026-08-07T00:00:00+00:00',
                       '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00')"""
        )
        conn.execute("DROP TABLE decision_receipt_revisions")
        conn.execute("DROP TABLE decision_receipt_work")
        conn.execute("DROP TABLE decision_receipt_sources")
        conn.execute("DROP TABLE decision_receipts")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (40)")

    migrated = Database(path)

    assert SCHEMA_VERSION == 41
    assert read_schema_version(path) == 41
    with migrated._connection() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                """SELECT name FROM sqlite_master WHERE type = 'table'
                   AND name LIKE 'decision_receipt%'"""
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in conn.execute(
                """SELECT name FROM sqlite_master WHERE type = 'index'
                   AND name LIKE 'idx_receipt_%'"""
            ).fetchall()
        }
    assert tables == {
        "decision_receipts", "decision_receipt_sources", "decision_receipt_work",
        "decision_receipt_revisions",
    }
    assert indexes == {
        "idx_receipt_sources_receipt", "idx_receipt_work_receipt",
        "idx_receipt_revisions_receipt",
    }
    with migrated._connection() as conn:
        assert conn.execute(
            "SELECT title FROM notes WHERE id = 'pre-v41-note'"
        ).fetchone()[0] == "Keep me"
