"""Local-first sync coverage for durable decision records (HS-127-10)."""
from __future__ import annotations

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.sync_service import SyncService

OWNER = Principal(PrincipalKind.OWNER, "record-sync-owner")


def test_sync_record_preserves_sources_work_revisions_and_tombstone(tmp_path) -> None:
    source_db = Database(tmp_path / "source.db")
    destination_db = Database(tmp_path / "destination.db")
    source = DecisionRecordService(source_db)
    created = source.create(
        OWNER, decision_text="Use Kafka for durable events.", rationale="Ordered replay.",
        source_type="desk", source_id="desk-kafka",
    )
    source.link_work(OWNER, created["id"], "project", "Kafka migration")
    source.update_record(OWNER, created["id"], {"owner": "Karol"})
    with source_db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_record_sources
               (id, record_id, source_type, source_ref, created_at)
               VALUES ('source-kafka', ?, 'artifact', 'artifact-kafka', '2026-08-07T00:00:00+00:00')""",
            (created["id"],),
        )

    payload = SyncService(source_db).pull(OWNER)
    received = SyncService(destination_db).push(OWNER, payload)
    copied = DecisionRecordService(destination_db).get(OWNER, created["id"])

    assert received["received"]["decision_records"] == 1
    assert copied is not None
    assert {(item["source_type"], item["source_ref"]) for item in copied["sources"]} == {("artifact", "artifact-kafka")}
    assert copied["work"][0]["work_ref"] == "Kafka migration"
    assert copied["revisions"][0]["field_name"] == "owner"

    with source_db._connection() as conn:
        conn.execute("UPDATE decision_records SET deleted = 1, updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?", (created["id"],))
    tombstone = SyncService(source_db).pull(OWNER)
    SyncService(destination_db).push(OWNER, tombstone)
    assert DecisionRecordService(destination_db).get(OWNER, created["id"]) is None
