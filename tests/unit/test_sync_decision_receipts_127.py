"""Local-first sync coverage for durable decision receipts (HS-127-10)."""
from __future__ import annotations

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_receipt_service import DecisionReceiptService
from holdspeak.services.sync_service import SyncService

OWNER = Principal(PrincipalKind.OWNER, "receipt-sync-owner")


def test_sync_receipt_preserves_sources_work_revisions_and_tombstone(tmp_path) -> None:
    source_db = Database(tmp_path / "source.db")
    destination_db = Database(tmp_path / "destination.db")
    source = DecisionReceiptService(source_db)
    created = source.create(
        OWNER, decision_text="Use Kafka for durable events.", rationale="Ordered replay.",
        source_type="desk", source_id="desk-kafka",
    )
    source.link_work(OWNER, created["id"], "project", "Kafka migration")
    source.update_receipt(OWNER, created["id"], {"owner": "Karol"})
    with source_db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_receipt_sources
               (id, receipt_id, source_type, source_ref, created_at)
               VALUES ('source-kafka', ?, 'artifact', 'artifact-kafka', '2026-08-07T00:00:00+00:00')""",
            (created["id"],),
        )

    payload = SyncService(source_db).pull(OWNER)
    received = SyncService(destination_db).push(OWNER, payload)
    copied = DecisionReceiptService(destination_db).get(OWNER, created["id"])

    assert received["received"]["decision_receipts"] == 1
    assert copied is not None
    assert {(item["source_type"], item["source_ref"]) for item in copied["sources"]} == {("artifact", "artifact-kafka")}
    assert copied["work"][0]["work_ref"] == "Kafka migration"
    assert copied["revisions"][0]["field_name"] == "owner"

    with source_db._connection() as conn:
        conn.execute("UPDATE decision_receipts SET deleted = 1, updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?", (created["id"],))
    tombstone = SyncService(source_db).pull(OWNER)
    SyncService(destination_db).push(OWNER, tombstone)
    assert DecisionReceiptService(destination_db).get(OWNER, created["id"]) is None
