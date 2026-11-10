"""Search boxes pass owner text through the declared reads, never SQL grammar."""
from datetime import datetime, timezone

import pytest

from holdspeak import operations
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.memory_service import MemoryService
from holdspeak.services.recall_service import RecallService
from holdspeak.services.refinement_application_service import RefinementApplicationService
from holdspeak.services.refinement_thought_service import INBOX_DIRECTORY_ID, RefinementThoughtService

OWNER = Principal(PrincipalKind.OWNER, "search-owner")
QUERIES = ('follow-up', 'q3-plan', '"quoted"', 'title:alpha', 'alpha*', '(alpha)',
           'AND', 'OR', 'NOT', 'NEAR', '"unfinished', '*', '(', '"', '%', '_', '\\')
TEXT = 'follow-up q3-plan "quoted" title:alpha alpha* (alpha) AND OR NOT NEAR "unfinished 50% x_y path\\name'


@pytest.fixture
def reads(tmp_path):
    db = Database(tmp_path / "search.db")
    db.meetings.save_meeting(MeetingState(
        id="literal", title="Literal", started_at=datetime.now(timezone.utc),
        segments=[TranscriptSegment(speaker="Me", text=TEXT, start_time=0, end_time=1)],
    ))
    db.meetings.save_meeting(MeetingState(
        id="unrelated", title="Unrelated", started_at=datetime.now(timezone.utc),
        segments=[TranscriptSegment(speaker="Me", text="alpha only", start_time=0, end_time=1)],
    ))
    DecisionRecordService(db).create(OWNER, decision_text=TEXT, source_type="desk",
                                     source_id="literal-source", record_id="literal-record")
    DecisionRecordService(db).create(OWNER, decision_text="Unrelated decision", source_type="desk",
                                     source_id="unrelated-source", record_id="unrelated-record")
    db.notes.upsert(note_id="literal-note", title=TEXT, body_markdown=TEXT, tags=[],
                    last_modified="2026-11-10T12:00:00Z")
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thought = RefinementThoughtService(db).create(
        OWNER, request_id="literal", raw_text="Search context", source={"kind": "typed"},
        initial_note={"id": "working", "title": "Working"},
    )
    registry = operations.bind_available({
        "meeting_service": MeetingService(db), "memory_service": MemoryService(db),
        "recall_service": RecallService(db),
        "refinement_service": RefinementApplicationService(db, coordinator=None),
    })
    yield registry, db, thought
    db.close()


@pytest.mark.parametrize("query", QUERIES)
def test_meeting_list_treats_find_as_text(reads, query):
    registry, _, _ = reads
    result = registry.invoke(OWNER, "meeting.list", {"query": query})
    assert isinstance(result["meetings"], list)
    if query in ('follow-up', 'q3-plan', 'AND', 'OR', 'NOT', 'NEAR'):
        assert [row["id"] for row in result["meetings"]] == ["literal"]
    if query in ('*', '(', '"', '%', '_', '\\'):
        assert result["meetings"] == []  # FTS punctuation has no tokens.


@pytest.mark.parametrize("query", QUERIES)
def test_memory_search_accepts_literal_find_text(reads, query):
    registry, _, _ = reads
    result = registry.invoke(OWNER, "memory.search", {"query": query})
    assert isinstance(result["hits"], list)
    if query in ('follow-up', 'q3-plan'):
        assert "meeting:literal" in {row["source_ref"] for row in result["hits"]}
    if query == '_':
        assert {row["source_ref"] for row in result["hits"]} == {"decision_record:literal-record"}
    if query in ('*', '(', '"', '%', '\\'):
        assert result["hits"] == []


@pytest.mark.parametrize("query", QUERIES)
def test_memory_recall_accepts_literal_find_text(reads, query):
    registry, _, _ = reads
    result = registry.invoke(OWNER, "memory.recall", {"query": query})
    assert isinstance(result["meetings"], list)
    if query in ('%', '_', '\\'):
        assert [row["id"] for row in result["current"]] == ["literal-record"]
    if query in ('follow-up', 'q3-plan'):
        assert result["meetings"]


@pytest.mark.parametrize("query", QUERIES)
def test_thought_context_list_accepts_literal_find_text(reads, query, monkeypatch):
    from holdspeak.mcp.families import thought as family

    _, db, thought = reads
    monkeypatch.setattr(family, "_service", lambda: RefinementApplicationService(db, coordinator=None))
    result = family.dispatch("thought.list_context", {"thought_id": thought["id"], "query": query}, OWNER)
    assert isinstance(result["results"], list)
    assert any(row["ref"] == "note:literal-note" for row in result["results"])


def test_meeting_find_does_not_interpret_boolean_or_column_syntax(reads):
    registry, _, _ = reads
    for query in ('alpha OR absent', 'alpha NOT only', 'text:alpha', 'NEAR(alpha only)'):
        assert registry.invoke(OWNER, "meeting.list", {"query": query})["meetings"] == []


def test_thread_repository_uses_the_same_literal_fts_boundary(reads):
    _, db, _ = reads
    thread = db.threads.create_thread(title="Literal")
    message = db.threads.append_message(thread.id, role="user")
    db.threads.append_part(message.id, kind="text", text=TEXT)
    for query in QUERIES:
        result = db.threads.search(query)
        if query in ('follow-up', 'q3-plan', 'AND', 'OR', 'NOT', 'NEAR'):
            assert [row["thread_id"] for row in result] == [thread.id]
