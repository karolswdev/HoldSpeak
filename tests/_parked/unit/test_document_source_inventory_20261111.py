# PARKED: real producer coverage supersedes the fixed source inventory.
from holdspeak.services.document_sources import DOCUMENT_SOURCES

def test_registry_declares_the_stored_kinds() -> None:
    assert tuple(DOCUMENT_SOURCES) == (
        "project_update",
        "monday_brief",
        "desk_decision",
        "meeting_decision",
        "decision_record",
        "meeting_summary",
        "meeting_digest",
        "meeting_followup",
        "artifact",
        "note",
        "project_nudge",
    )
