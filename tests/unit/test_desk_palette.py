"""The palette (⌘K), hub half: what the MEMORY band reads, on a real hub.

The test diet (2026-10-11) moved these facts out of the browser suite. The
palette's own drawing (the band, the two lines, the opener) is fenced in
vitest (web/src/desk/__tests__/paletteMemory.test.tsx,
paletteTwoLine.test.tsx, palette.app.test.tsx). This file proves the hub
answers the palette reads with the rows those faces draw: the same seeds the
browser tests used, made by the real producers, read through the real
routes on an isolated database.
"""
from __future__ import annotations

import hashlib
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

from holdspeak.meeting_session.models import MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _search(hub: Hub, query: str) -> list[dict[str, Any]]:
    found = hub.client.get("/api/memory/search", params={"query": query})
    assert found.status_code == 200, found.text
    return found.json()["hits"]


# ── a word inside a meeting (was tests/e2e/test_palette_memory_glass.py) ─────

WORD = "quokka"
TITLE = "Ledger cutover sync"
OLD_WORD, OLD_ARTIFACT = "wombat", "Second key notes"
OLD_MEETING_WORD, OLD_MEETING = "numbat", "Finance migration sync"


def _seed_memory(hub: Hub) -> None:
    """The browser test's seed, unchanged: one transcript-only word, and
    things older than the desk's lists (24 meetings, 24 artifacts)."""
    db = hub.db
    start = datetime.now().replace(microsecond=0) - timedelta(hours=3)
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=45), title=TITLE,
        segments=[
            TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me",
                              start_time=4.0, end_time=9.0),
            TranscriptSegment(text=f"The {WORD} invoice batch is late again.", speaker="Priya",
                              start_time=10.0, end_time=16.0),
        ]))
    db.meetings.save_meeting(MeetingState(
        id="m-other", started_at=start - timedelta(days=1), ended_at=start - timedelta(days=1, minutes=-30),
        title="Hiring review",
        segments=[TranscriptSegment(text="We open one more role.", speaker="Me", start_time=1.0, end_time=3.0)]))
    base = start - timedelta(days=40)
    for i in range(25):
        db.plugins.record_artifact(
            artifact_id=f"art-{i:02d}", meeting_id="m-other", artifact_type="notes",
            title=OLD_ARTIFACT if i == 0 else f"Follow-up notes {i:02d}", plugin_id="palette-glass", status="draft",
            body_markdown=f"The {OLD_WORD} ledger needs a second key." if i == 0 else f"Routine notes {i}.",
            updated_at=(base + timedelta(hours=i)).isoformat())   # art-00 is the oldest
    for i in range(26):
        at = base + timedelta(days=i)
        text = f"The {OLD_MEETING_WORD} migration waits for finance." if i == 0 else "Routine status."
        db.meetings.save_meeting(MeetingState(
            id=f"m-old-{i:02d}", started_at=at, ended_at=at + timedelta(minutes=20),
            title=OLD_MEETING if i == 0 else f"Status sync {i:02d}",
            segments=[TranscriptSegment(text=text, speaker="Me", start_time=1.0, end_time=3.0)]))


def test_a_transcript_word_finds_its_meeting(hub: Hub) -> None:
    """replaces: tests/e2e/test_palette_memory_glass.py::TestPaletteFindsAWordInsideAMeeting::test_a_transcript_word_finds_its_meeting_and_the_row_opens_it
    (hub half: /api/memory/search finds the word; the row's drawing and
    opener are paletteMemory.test.tsx)."""
    _seed_memory(hub)
    # The premise: the word is in no title and no speaker of the desk's list.
    listed = hub.client.get("/api/meetings", params={"limit": 24}).json()["meetings"]
    assert [m["id"] for m in listed if WORD in str(m).lower()] == []

    hits = _search(hub, WORD)
    refs = [h["source_ref"] for h in hits]
    assert refs.count("meeting:m-sync") >= 1, refs
    hit = next(h for h in hits if h["source_ref"] == "meeting:m-sync")
    assert hit["kind"] == "meeting" and hit["title"] == TITLE, hit
    assert WORD in hit["snippet"].lower(), hit
    # The row opens the meeting: its window reads the meeting by id.
    meeting = hub.client.get("/api/meetings/m-sync")
    assert meeting.status_code == 200, meeting.text
    assert f"The {WORD} invoice batch is late again." in meeting.text


@pytest.mark.parametrize("word,ref,shown", [
    (OLD_WORD, "artifact:art-00", f"The {OLD_WORD} ledger needs a second key."),
    (OLD_MEETING_WORD, "meeting:m-old-00", f"The {OLD_MEETING_WORD} migration waits for finance."),
])
def test_a_thing_older_than_its_desk_list_is_found_and_its_own_words_load(
    hub: Hub, word: str, ref: str, shown: str,
) -> None:
    """replaces: tests/e2e/test_palette_memory_glass.py::TestPaletteFindsAWordInsideAMeeting::test_a_thing_older_than_its_desk_list_opens_from_its_memory_row
    (hub half: the object is outside the desk's list, memory finds it, and
    the read the held loader makes carries its own words; the hold-then-open
    order is paletteMemory.test.tsx)."""
    _seed_memory(hub)
    kind, oid = ref.split(":", 1)
    if kind == "meeting":
        listed = hub.client.get("/api/meetings", params={"limit": 24}).json()["meetings"]
        assert oid not in [m["id"] for m in listed], "the object is inside the desk list; the repro proves nothing"
    else:
        pulled = hub.client.get("/api/sync/pull", params={"limit": 50}).json()["artifacts"]
        live = [a for a in pulled if not (a.get("meta") or {}).get("deleted")][:24]
        assert oid not in [(a.get("meta") or a).get("id") for a in live], "the artifact is inside the desk list"

    assert ref in [h["source_ref"] for h in _search(hub, word)]

    # The held loader's read (web/src/desk/api.ts loadHeld): a meeting by id,
    # an artifact from the pull.
    if kind == "meeting":
        body = hub.client.get(f"/api/meetings/{oid}")
        assert body.status_code == 200, body.text
        assert shown in body.text
    else:
        pulled = hub.client.get("/api/sync/pull", params={"limit": 50}).json()["artifacts"]
        row = next(a for a in pulled if (a.get("meta") or a).get("id") == oid)
        assert shown in str(row)


# ── keyword and meaning hits (was tests/e2e/test_palette_two_line_glass.py) ──

GOING_BACK = {"rollback", "back", "revert", "fallback", "undo"}


class GoingBackEngine:
    """The browser test's fixture engine: axis 0 is the concept "going back";
    the other seven axes are a small hashed bag of the remaining words."""

    model_id = "going-back-fixture@8"
    dim = 8
    boundary = "local"
    revision_id = "going-back-fixture"
    assignment_head = "going-back-fixture"

    def _vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        for word in re.findall(r"[a-z0-9]+", str(text).lower()):
            if word in GOING_BACK:
                vector[0] += 1.0
            else:
                vector[1 + hashlib.sha256(word.encode()).digest()[0] % 7] += 0.15
        norm = float(np.linalg.norm(vector)) or 1.0
        return vector / norm

    def embed_documents(self, texts):
        return np.vstack([self._vector(t) for t in texts]) if texts else np.zeros((0, self.dim), np.float32)

    def embed_query(self, text):
        return self._vector(text)


def test_keyword_and_meaning_hits_carry_their_origin_snippet_and_day(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """replaces: tests/e2e/test_palette_two_line_glass.py::TestPaletteTwoLineHit::test_keyword_and_meaning_hits_draw_two_lines
    (hub half: the real sweep with the fixture engine answers KEYWORD and
    MEANING hits with the fields the two-line row draws; the drawing and the
    plate contrast are paletteTwoLine.test.tsx)."""
    import holdspeak.memory.engine as memory_engine
    from holdspeak.memory.retain import rebuild

    engine = GoingBackEngine()
    monkeypatch.setattr(memory_engine, "resolve_embedder", lambda *_a, **_k: engine)
    db = hub.db
    atlas_at = datetime.now().replace(microsecond=0) - timedelta(days=4)
    db.meetings.save_meeting(MeetingState(
        id="m-atlas", started_at=atlas_at, ended_at=atlas_at + timedelta(minutes=30), title="Atlas weekly",
        segments=[TranscriptSegment(text="Priya takes the rollback plan; Marek reviews it on Thursday.",
                                    speaker="Priya", start_time=3.0, end_time=8.0)]))
    marek_at = atlas_at - timedelta(days=2)
    db.meetings.save_meeting(MeetingState(
        id="m-marek", started_at=marek_at, ended_at=marek_at + timedelta(minutes=25), title="1:1 Marek",
        segments=[TranscriptSegment(text="Marek asks who owns the fallback for Atlas.",
                                    speaker="Marek", start_time=2.0, end_time=6.0)]))
    db.notes.upsert(note_id="n-runbook", title="Rollback runbook draft", body_markdown="Steps for Thursday.")
    db.notes.upsert(note_id="n-cutover", title="Cutover after the freeze",
                    body_markdown="If the cutover fails, we go back to the old cluster in one step.")
    counts = rebuild(db, engine)
    assert counts["vectors"] >= 3, counts
    db.memory.set_embedder(engine)

    hits = {h["source_ref"]: h for h in _search(hub, "rollback")}
    keyword = hits.get("meeting:m-atlas")
    assert keyword, list(hits)
    assert keyword["title"] == "Atlas weekly", keyword
    assert keyword["retrieval_origin"] == "lexical", keyword            # drawn KEYWORD
    assert re.search(r"<mark>rollback</mark>", keyword["snippet"], re.I), keyword
    assert "Marek reviews it on Thursday." in keyword["snippet"], keyword
    # The day the row draws (MM-DD, local): the meeting's own day.
    assert datetime.fromisoformat(str(keyword["occurred_at"])).astimezone().date() == atlas_at.date(), keyword

    meaning = hits.get("note:n-cutover")
    assert meaning, list(hits)
    assert meaning["retrieval_origin"] == "vector", meaning              # drawn MEANING
    assert "go back to the old cluster" in meaning["snippet"], meaning
    assert "<mark>" not in meaning["snippet"], meaning                   # no word to mark
    assert re.match(r"\d{4}-\d{2}-\d{2}", str(meaning["occurred_at"])), meaning

    meaning_meeting = hits.get("meeting:m-marek")
    assert meaning_meeting and meaning_meeting["retrieval_origin"] == "vector", meaning_meeting


# ── Enter opens the note (was tests/e2e/test_palette_enter_opens_the_note_glass.py) ──

ENTER_TITLE = "Ledger cutover risks"


def _note_ids(hub: Hub) -> set[str]:
    """Every note the hub holds now (a thought is a note too)."""
    found = hub.client.get("/api/notes")
    assert found.status_code == 200, found.text
    return {n["id"] for n in found.json()["notes"]}


def test_the_reads_a_note_window_makes_write_no_note_and_develop_keeps_one(hub: Hub) -> None:
    """replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_enter_opens_the_note_the_first_row_names
    (hub half: what the window reads makes no thought and no note; the
    owner's Develop turns THAT note into a thought with no second note. The
    palette's Enter and the window it draws are palette.app.test.tsx, on the
    answers scripts/record_chrome_palette.py records from this same seed)."""
    c = hub.client
    note = c.post("/api/notes", json={"title": ENTER_TITLE, "body_markdown": "- rollback plan owner: Jordan", "tags": []})
    assert note.status_code in (200, 201), note.text
    note_id = note.json()["note"]["id"]
    held = _note_ids(hub)
    status = c.get(f"/api/thoughts/for-note/{note_id}").json()
    assert status["ownership"] == "ordinary", status
    assert _note_ids(hub) == held, "reading a note's thought status made a note"

    pre = status["source_precondition"]
    adopted = c.post("/api/thoughts/adopt", json={
        "request_id": "palette-enter-unit", "note_id": note_id,
        "expected_source_content_sha256": pre["content_sha256"],
        "expected_source_last_modified": pre["last_modified"]})
    assert adopted.status_code in (200, 201), adopted.text
    thought = adopted.json()["thought"]
    assert thought["working_note"]["id"] == note_id, thought    # the thought OF THAT NOTE
    assert thought["working_note"]["title"] == ENTER_TITLE, thought
    assert _note_ids(hub) == held, "Develop made a second note"

    after = c.get(f"/api/thoughts/for-note/{note_id}").json()
    assert after["ownership"] == "thought" and after["thought"]["id"] == thought["id"], after
    assert c.get(f"/api/thoughts/{thought['id']}/workbench").status_code == 200
    assert _note_ids(hub) == held, "the Thought window's reads made a note"


def test_the_no_note_made_check_sees_a_thought_made_in_the_gap(hub: Hub) -> None:
    """replaces: tests/e2e/test_palette_enter_opens_the_note_glass.py::TestEnterOpensTheFirstRow::test_the_check_fails_when_a_thought_is_made_in_the_gap
    (the proof of the check: a REAL thought made by POST /api/thoughts, the
    route a check of POST /api/notes alone did not see, adds a note to the
    list the check reads)."""
    hub.client.post("/api/notes", json={"title": ENTER_TITLE, "body_markdown": "x", "tags": []})
    held = _note_ids(hub)
    made = hub.client.post("/api/thoughts", json={"request_id": "palette-enter-injected",
                                                  "raw_text": "A thought made elsewhere"})
    assert made.status_code in (200, 201), made.text
    assert len(_note_ids(hub)) == len(held) + 1, "the injected thought made no note: the check would be blind"


# ── honest faces: a decision is a search hit of its own ───────────────────


def test_a_meeting_decision_is_found_by_its_words_as_a_decision(hub: Hub) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_a_decision_search_hit_opens_the_decision_and_adds_no_floor_icon (hub half)

    ⌘K asks /api/memory/search; the decision a meeting recorded comes back as
    a `decision:<id>` hit with its own words (the palette opens it in
    Intelligence → Decisions: paletteMemory.test.tsx)."""
    from test_desk_needs_you import _seed_honest_faces

    _seed_honest_faces(hub)
    lifecycle = hub.db.decisions.list(meeting_id="m-standup")[0]
    hits = _search(hub, "Freeze the old ledger")
    decision = [h for h in hits if h["kind"] == "decision"]
    assert [h["source_ref"] for h in decision] == [f"decision:{lifecycle.id}"], hits
    assert decision[0]["title"] == "Freeze the old ledger on Nov 5", decision
