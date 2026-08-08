"""Tests for the durable decision receipt canon (HS-127-01)."""

from __future__ import annotations

from datetime import date, timedelta

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


def test_update_receipt_records_each_changed_field_without_erasing_original(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    receipt = service.create(
        None,
        decision_text="Keep the original decision.",
        rationale="Initial rationale.",
        source_type="desk",
        source_id="desk-127",
    )

    updated = service.update_receipt(
        None, receipt["id"], {"rationale": "Revised rationale."}
    )
    loaded = service.get(None, receipt["id"])

    assert updated["rationale"] == "Revised rationale."
    assert loaded is not None
    assert loaded["decision_text"] == "Keep the original decision."
    assert [(revision["field_name"], revision["old_value"], revision["new_value"])
            for revision in loaded["revisions"]] == [
        ("rationale", "Initial rationale.", "Revised rationale.")
    ]


def test_affected_work_links_are_listed_in_both_directions_and_removable(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    receipt = service.create(
        None, decision_text="Govern HS-127.", source_type="desk", source_id="desk-work"
    )

    link = service.link_work(None, receipt["id"], "project", "HS-127")
    duplicate = service.link_work(None, receipt["id"], "project", "HS-127")

    assert duplicate["id"] == link["id"]
    assert service.list_work(None, receipt["id"]) == [link]
    assert [item["id"] for item in service.receipts_for_work(None, "project", "HS-127")] == [
        receipt["id"]
    ]
    assert service.unlink_work(None, receipt["id"], "project", "HS-127") is True
    assert service.list_work(None, receipt["id"]) == []
    assert service.receipts_for_work(None, "project", "HS-127") == []


def test_due_for_review_includes_overdue_and_excludes_future_receipts(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    overdue = service.create(
        None,
        decision_text="Review the overdue decision.",
        review_date=(date.today() - timedelta(days=1)).isoformat(),
        source_type="desk",
        source_id="desk-overdue",
    )
    service.create(
        None,
        decision_text="Review the future decision.",
        review_date=(date.today() + timedelta(days=1)).isoformat(),
        source_type="desk",
        source_id="desk-future",
    )

    due = service.due_for_review(None)

    assert [receipt["id"] for receipt in due] == [overdue["id"]]


def test_supersede_seals_predecessor_and_preserves_both_receipts(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    predecessor = service.create(
        None, decision_text="Use the original plan.", source_type="desk", source_id="desk-old"
    )
    successor = service.create(
        None, decision_text="Use the replacement plan.", source_type="desk", source_id="desk-new"
    )
    service.link_work(None, predecessor["id"], "project", "HS-127")

    sealed = service.supersede(
        None, predecessor["id"], successor["id"], "Requirements changed."
    )
    loaded_successor = service.get(None, successor["id"])

    assert sealed["lifecycle"] == "superseded"
    assert sealed["successor_id"] == successor["id"]
    assert sealed["supersession_reason"] == "Requirements changed."
    assert sealed["work"][0]["work_ref"] == "HS-127"
    assert loaded_successor is not None
    assert loaded_successor["predecessor_id"] == predecessor["id"]
    assert loaded_successor["decision_text"] == "Use the replacement plan."
    with pytest.raises(ValueError, match="sealed"):
        service.update_receipt(None, predecessor["id"], {"rationale": "Rewrite history."})


def _accepted_meeting_decision(db: Database, decision_id: str = "dec-127") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis, source_artifact_id,
                   source_meeting_id, source_state, lifecycle, created_at, updated_at,
                   last_modified, deleted
               ) VALUES (?, 'Use receipt-backed decisions.', 'One durable canon.',
                         '2026-08-07T00:00:00+00:00', 'meeting_date', 'artifact-127',
                         'meeting-127', 'linked', 'accepted', '2026-08-07T00:00:00+00:00',
                         '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00', 0)""",
            (decision_id,),
        )


def test_create_from_meeting_mints_idempotent_receipt_with_lineage(tmp_path):
    db = Database(tmp_path / "receipts.db")
    _accepted_meeting_decision(db)
    source_before = db.decisions.get("dec-127").to_dict()
    service = DecisionReceiptService(db)

    receipt = service.create_from_meeting(None, "dec-127")
    repeated = service.create_from_meeting(None, "dec-127")
    loaded = service.get(None, receipt["id"])

    assert receipt["source_type"] == "meeting"
    assert receipt["source_id"] == "dec-127"
    assert receipt["decision_text"] == "Use receipt-backed decisions."
    assert receipt["rationale"] == "One durable canon."
    assert repeated["id"] == receipt["id"]
    assert loaded is not None
    assert {(source["source_type"], source["source_ref"]) for source in loaded["sources"]} == {
        ("meeting", "meeting-127"),
        ("artifact", "artifact-127"),
    }
    assert db.decisions.get("dec-127").to_dict() == source_before


def _meeting_evidence(db: Database, *, with_segment: bool, artifact_id: str = "artifact-evidence") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-evidence", "2026-08-07T09:00:00+00:00", "Receipt evidence"),
        )
        if artifact_id:
            conn.execute(
                """INSERT INTO artifacts (id, meeting_id, artifact_type, title)
                   VALUES (?, 'meeting-evidence', 'decisions', 'Decision capture')""",
                (artifact_id,),
            )
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis, source_timestamp,
                   provenance_label, source_artifact_id, source_meeting_id,
                   source_state, lifecycle, created_at, updated_at, last_modified, deleted
               ) VALUES (
                   'dec-evidence', 'Ship the receipt evidence.', NULL,
                   '2026-08-07T09:00:30+00:00', 'transcript_moment', 30.0,
                   'reported', ?, 'meeting-evidence', 'linked', 'accepted',
                   '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00',
                   '2026-08-07T00:00:00+00:00', 0
               )""",
            (artifact_id,),
        )
        if with_segment:
            conn.execute(
                """INSERT INTO segments (meeting_id, text, speaker, start_time, end_time)
                   VALUES ('meeting-evidence', 'Ship the receipt evidence.', 'Mina', 20.0, 40.0)"""
            )


def test_create_from_meeting_persists_exact_segment_evidence(tmp_path):
    db = Database(tmp_path / "receipts.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionReceiptService(db)

    receipt = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, receipt["id"])

    assert loaded is not None
    sources = {source["source_type"]: source for source in loaded["sources"]}
    assert sources["meeting"]["source_ref"] == "meeting-evidence"
    assert sources["artifact"]["source_ref"] == "artifact-evidence"
    assert sources["segment"]["text"] == "Ship the receipt evidence."
    assert sources["segment"]["speaker"] == "Mina"


def test_create_from_meeting_without_segments_keeps_meeting_only(tmp_path):
    db = Database(tmp_path / "receipts.db")
    _meeting_evidence(db, with_segment=False, artifact_id="")
    service = DecisionReceiptService(db)

    receipt = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, receipt["id"])

    assert loaded is not None
    assert [(source["source_type"], source["source_ref"]) for source in loaded["sources"]] == [
        ("meeting", "meeting-evidence")
    ]


def test_get_receipt_resolves_source_details(tmp_path):
    db = Database(tmp_path / "receipts.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionReceiptService(db)

    receipt = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, receipt["id"])

    assert loaded is not None
    sources = {source["source_type"]: source for source in loaded["sources"]}
    assert sources["meeting"]["title"] == "Receipt evidence"
    assert sources["meeting"]["date"] == "2026-08-07T09:00:00+00:00"
    assert sources["artifact"]["artifact_type"] == "decisions"
    assert sources["segment"]["details"]["speaker"] == "Mina"


def test_provenance_resolution_failure_still_mints_receipt(tmp_path, monkeypatch):
    db = Database(tmp_path / "receipts.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionReceiptService(db)

    def fail_resolution(decision_id: str):
        raise RuntimeError("transcript unavailable")

    monkeypatch.setattr(db.decisions, "resolve_decision_moment", fail_resolution)
    receipt = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, receipt["id"])

    assert loaded is not None
    assert {source["source_type"] for source in loaded["sources"]} == {"meeting", "artifact"}


def test_create_from_desk_mints_idempotent_receipt(tmp_path):
    db = Database(tmp_path / "receipts.db")
    db.desk_decisions.upsert(
        decision_id="desk-127",
        title="Receipt origin",
        status="accepted",
        deciders=["Karol", "Mina"],
        context_markdown="Decisions need one durable canon.",
        decision_markdown="Use receipt-backed decisions.",
        alternatives=[{"name": "Separate stores", "reason": "Harder to trace"}],
        consequences_markdown="Sources remain authoritative.",
    )
    source_before = db.desk_decisions.get("desk-127").to_dict()
    service = DecisionReceiptService(db)

    receipt = service.create_from_desk(None, "desk-127")
    repeated = service.create_from_desk(None, "desk-127")

    assert receipt["source_type"] == "desk"
    assert receipt["source_id"] == "desk-127"
    assert receipt["decision_text"] == "Use receipt-backed decisions."
    assert receipt["rationale"] == (
        "Decisions need one durable canon.\n\nSources remain authoritative."
    )
    assert receipt["alternatives"] == '[{"name": "Separate stores", "reason": "Harder to trace"}]'
    assert receipt["owner"] == "Karol, Mina"
    assert repeated["id"] == receipt["id"]
    assert db.desk_decisions.get("desk-127").to_dict() == source_before


def test_receipts_from_each_origin_have_the_same_shape(tmp_path):
    db = Database(tmp_path / "receipts.db")
    _accepted_meeting_decision(db)
    db.desk_decisions.upsert(
        decision_id="desk-127",
        decision_markdown="Choose the receipt origin.",
    )
    service = DecisionReceiptService(db)

    meeting_receipt = service.create_from_meeting(None, "dec-127")
    desk_receipt = service.create_from_desk(None, "desk-127")

    assert set(meeting_receipt) == set(desk_receipt)


def test_create_from_meeting_rejects_unknown_decision(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))

    with pytest.raises(KeyError, match="missing-decision"):
        service.create_from_meeting(None, "missing-decision")


def test_receipt_requires_decision_text_and_source_type(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))

    with pytest.raises(ValueError, match="decision_text is required"):
        service.create(None, decision_text="", source_type="meeting", source_id="dec-1")
    with pytest.raises(ValueError, match="source_type is required"):
        service.create(None, decision_text="A decision", source_type="", source_id="dec-1")


def test_search_finds_kafka_in_decision_text_and_linked_work(tmp_path):
    service = DecisionReceiptService(Database(tmp_path / "receipts.db"))
    kafka = service.create(
        None,
        decision_text="Use Kafka for the event stream.",
        rationale="Durable ordered delivery.",
        source_type="desk",
        source_id="desk-kafka",
    )
    work_link = service.create(
        None,
        decision_text="Track the streaming migration.",
        source_type="desk",
        source_id="desk-work-link",
    )
    service.link_work(None, work_link["id"], "project", "Kafka migration")

    matches = service.search(None, "Why Kafka?")

    assert matches[0]["id"] == kafka["id"]
    assert {receipt["id"] for receipt in matches} == {kafka["id"], work_link["id"]}


def test_schema_migrates_v40_to_v42(tmp_path):
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

    assert SCHEMA_VERSION == 42
    assert read_schema_version(path) == 42
    with migrated._connection() as conn:
        assert "deleted" in {row[1] for row in conn.execute("PRAGMA table_info(decision_receipts)")}
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
