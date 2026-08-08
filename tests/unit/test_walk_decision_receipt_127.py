"""End-to-end service and MCP walk for HS-127 decision receipts."""
from __future__ import annotations

import json

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import resources, tools
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_receipt_service import DecisionReceiptService

OWNER = Principal(PrincipalKind.OWNER, "receipt-walk-owner")


def test_decision_receipt_walk_from_origins_through_mcp(tmp_path, monkeypatch) -> None:
    reset_database()
    db = Database(tmp_path / "receipt-walk.db")
    monkeypatch.setattr(tools, "get_database", lambda: db)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    monkeypatch.setattr(resources, "get_database", lambda: db)
    try:
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO meetings (id, started_at, title) VALUES ('meeting-127', '2026-08-07T09:00:00+00:00', 'Kafka choice')"
            )
            conn.execute(
                "INSERT INTO artifacts (id, meeting_id, artifact_type, title) VALUES ('artifact-127', 'meeting-127', 'decisions', 'Kafka choice')"
            )
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, decided_at, date_basis,
                   source_artifact_id, source_meeting_id, source_state, lifecycle,
                   created_at, updated_at, last_modified, deleted)
                   VALUES ('meeting-decision-127', 'Use Kafka for the event stream.',
                   'Ordered durable delivery.', '2026-08-07T09:01:00+00:00', 'meeting_date',
                   'artifact-127', 'meeting-127', 'linked', 'accepted',
                   '2026-08-07T09:01:00+00:00', '2026-08-07T09:01:00+00:00',
                   '2026-08-07T09:01:00+00:00', 0)"""
            )
        db.desk_decisions.upsert(
            decision_id="desk-decision-127", decision_markdown="Use Kafka with a schema registry."
        )
        service = DecisionReceiptService(db)

        meeting_receipt = service.create_from_meeting(OWNER, "meeting-decision-127")
        desk_receipt = service.create_from_desk(OWNER, "desk-decision-127")
        meeting_full = service.get(OWNER, meeting_receipt["id"])
        assert meeting_full is not None
        assert {source["source_type"] for source in meeting_full["sources"]} == {"meeting", "artifact"}
        assert set(meeting_receipt) == set(desk_receipt)

        service.link_work(OWNER, meeting_receipt["id"], "project", "Kafka migration")
        assert service.receipts_for_work(OWNER, "project", "Kafka migration")[0]["id"] == meeting_receipt["id"]
        assert meeting_receipt["id"] in {receipt["id"] for receipt in service.search(OWNER, "Why Kafka?")}

        sealed = service.supersede(OWNER, meeting_receipt["id"], desk_receipt["id"], "Schema registry added.")
        successor = service.get(OWNER, desk_receipt["id"])
        assert sealed["successor_id"] == desk_receipt["id"]
        assert successor is not None and successor["predecessor_id"] == meeting_receipt["id"]

        returned = tools.dispatch("decision_receipt.get", {"receipt_id": desk_receipt["id"]}, OWNER)
        assert returned["id"] == desk_receipt["id"]
        assert tools.dispatch("decision_receipt.search", {"query": "Why Kafka?"}, OWNER)
        payload = json.loads(resources.read_resource(f"holdspeak://decision-receipts/{desk_receipt['id']}", OWNER)["contents"][0]["text"])
        assert payload["id"] == desk_receipt["id"]
    finally:
        reset_database()
