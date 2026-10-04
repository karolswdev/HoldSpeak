"""Memory reads a time phrase out of the question (MEMORY-DESIGN.md §3.2, §8 slice 2).

Every row is made by its real producer on a real hub (isolated HOME):
``save_meeting`` with its start time, the Room's update routes, the channel
routes with the file channel's real dispatch.  A send is stamped by the
producer at the wall clock; to put one in last week the test moves its three
time columns afterwards (the one step that is not a producer).

Memory is read through ``/api/memory/search`` (the HTTP route), the MCP tool
``memory.search``, the grounding call Ask uses, and ``MemoryRepository.search``.

The five time questions of the benchmark group (MEMORY-DESIGN.md §7; §8 does
not spell them out, so they are named here):

* T1 "what did I send Dana last week"
* T2 "what did we decide about the gateway in September"
* T3 "kestrel review yesterday"
* T4 "what happened since Monday"
* T5 "what did we discuss about the billing export two weeks ago"

The answer with no phrase is byte-identical to before: the benchmark's
``keyword_golden.json`` holds the full answer of 29 questions made by the
search code before the memory index existed, and
``tests/memory_bench/test_memory_bench.py`` compares value for value.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, room, send, send_body  # noqa: E402

from holdspeak.grounding import hydrate_refs_detailed  # noqa: E402
from holdspeak.meeting_session import MeetingState, TranscriptSegment  # noqa: E402
from holdspeak.memory.timeparse import parse_time_phrase  # noqa: E402
from holdspeak.runtime import composition  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _middle(phrase: str, now: datetime | None = None) -> tuple[datetime, datetime, datetime]:
    """``(time_from, middle, time_to)`` of a phrase, as the hub reads it."""
    found = parse_time_phrase(phrase, now)
    assert found is not None, phrase
    start = datetime.fromisoformat(found.time_from)
    end = datetime.fromisoformat(found.time_to)
    return start, start + (end - start) / 2, end


def _meeting(hub: Hub, meeting_id: str, at: datetime, text: str, title: str = "") -> None:
    """A meeting through the real producer.  A meeting's start is the hub's
    local wall time (a bare ISO time)."""
    hub.db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=at.astimezone().replace(tzinfo=None),
        title=title or meeting_id,
        segments=[TranscriptSegment(text=text, speaker="Avery", start_time=1.0, end_time=2.0)],
    ))


def _send_to_dana(hub: Hub, tmp_path: Path, name: str, key: str) -> str:
    _pid, update = room(hub, name=name, body="The cutover is on track.")
    dest = destination(hub, tmp_path / key, name="Dana")
    sent = send(hub, send_body(hub, "inline", update, dest, key))
    assert sent.status_code == 200, sent.text
    assert sent.json()["send"]["state"] == "sent"
    return sent.json()["send"]["id"]


def _move_send(hub: Hub, send_id: str, at: datetime) -> None:
    """Put a send at another time, in the producer's shape (``now_iso``)."""
    stamp = at.astimezone(timezone.utc).isoformat(timespec="seconds")
    with hub.db._connection() as conn:
        conn.execute(
            "UPDATE channel_sends SET created_at=?,dispatch_started_at=?,settled_at=? WHERE id=?",
            (stamp, stamp, stamp, send_id),
        )


def _route(hub: Hub, query: str, **params: Any) -> dict[str, Any]:
    found = hub.client.get("/api/memory/search", params={"query": query, **params})
    assert found.status_code == 200, found.text
    return found.json()


def _refs(answer: Any) -> list[str]:
    hits = answer["hits"] if isinstance(answer, dict) else answer.hits
    return [hit["source_ref"] if isinstance(hit, dict) else hit.source_ref for hit in hits]


# ── T1: the send from last week, ahead of an older one with the same words ──


def test_t1_what_did_i_send_dana_last_week(hub: Hub, tmp_path: Path) -> None:
    older = _send_to_dana(hub, tmp_path, "Atlas", "pcmd_send_old")
    newer = _send_to_dana(hub, tmp_path, "Atlas follow-up", "pcmd_send_new")
    start, middle, _end = _middle("last week")
    _move_send(hub, newer, middle)
    _move_send(hub, older, start - timedelta(days=30))

    # With no phrase the newer and the older are both answers; the order is
    # the keyword order of before.
    plain = _route(hub, "what did I send Dana", kind="send")
    assert set(_refs(plain)) == {f"send:{older}", f"send:{newer}"}
    assert "fusion" not in plain["ranking"]

    answer = _route(hub, "what did I send Dana last week", kind="send")
    assert _refs(answer) == [f"send:{newer}", f"send:{older}"]
    window = answer["ranking"]["fusion"]["time"]
    assert window["phrase"] == "last week"
    assert window["in_range"] == 1
    assert "time" in answer["ranking"]["fusion"]["retrievers"]

    # Every kind, not only sends: the send from last week is still first.
    assert _refs(_route(hub, "what did I send Dana last week"))[0] == f"send:{newer}"

    # Ask's relevance pass inherits it: the first send it hydrates is last week's.
    asked = hydrate_refs_detailed(
        hub.db, [], [], "summary", query="what did I send Dana last week", include_memory=True
    )
    sends = [block.ref for block in asked.blocks if block.kind == "send"]
    assert sends[0] == newer


# ── T2..T5: meetings at known times ──────────────────────────────────────


def test_t2_what_did_we_decide_in_september(hub: Hub) -> None:
    now = datetime.now().astimezone()
    start, middle, _end = _middle("in September", now)
    _meeting(hub, "m-sept", middle, "We decided the gateway moves to mutual TLS.")
    _meeting(hub, "m-before", start - timedelta(days=20), "We decided the gateway moves to mutual TLS.")

    found = hub.db.memory.search("what did we decide about the gateway in September", now=now)
    refs = _refs(found)
    assert refs.index("meeting:m-sept") < refs.index("meeting:m-before")
    assert refs[0] == "meeting:m-sept"


def test_t3_kestrel_review_yesterday(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("yesterday", now)
    _meeting(hub, "m-yesterday", middle, "The kestrel review went well.")
    _meeting(hub, "m-older", middle - timedelta(days=10), "The kestrel review went well.")
    # The newer-is-better rule of before puts the yesterday meeting first
    # anyway; the older one with MORE matching words would win without the
    # phrase.
    _meeting(hub, "m-older-loud", middle - timedelta(days=12), "Kestrel review: the kestrel review, kestrel.")

    plain = _refs(hub.db.memory.search("kestrel review", now=now))
    assert plain[0] == "meeting:m-older-loud"

    refs = _refs(hub.db.memory.search("kestrel review yesterday", now=now))
    assert refs[0] == "meeting:m-yesterday"
    assert set(refs[1:]) == {"meeting:m-older", "meeting:m-older-loud"}


def test_t4_what_happened_since_monday(hub: Hub) -> None:
    now = datetime.now().astimezone()
    start, _middle_at, _end = _middle("since Monday", now)
    _meeting(hub, "m-this-week", start + timedelta(hours=10), "Roadmap sync with the platform team.")
    _meeting(hub, "m-long-ago", start - timedelta(days=9), "Roadmap sync with the platform team.")

    found = hub.db.memory.search("what happened since Monday", now=now)
    # No word of the question is in either meeting: the time retriever
    # alone finds the one inside the range, and nothing outside it.
    assert _refs(found) == ["meeting:m-this-week"]
    assert found.hits[0].retrieval_origin == "time"
    assert "Roadmap sync" in found.hits[0].snippet


def test_t5_two_weeks_ago_through_the_mcp_tool(hub: Hub) -> None:
    _start, middle, _end = _middle("two weeks ago")
    _meeting(hub, "m-two-weeks", middle, "We discussed the billing export format.")
    _meeting(hub, "m-two-months", middle - timedelta(days=60), "We discussed the billing export format and the billing export owner.")

    is_error, answer = hub.mcp(
        "memory.search", {"query": "what did we discuss about the billing export two weeks ago"}
    )
    assert is_error is False, answer
    assert _refs(answer)[:2] == ["meeting:m-two-weeks", "meeting:m-two-months"]
    assert answer["ranking"]["fusion"]["time"]["phrase"] == "two weeks ago"


# ── the rules around the phrase ──────────────────────────────────────────


def test_the_phrase_is_not_a_keyword(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("last week", now)
    _meeting(hub, "m-release", middle, "The release notes are out.")
    _meeting(hub, "m-week", middle - timedelta(days=40), "The week was long and the last item slipped.")

    refs = _refs(hub.db.memory.search("release notes last week", now=now))
    assert refs == ["meeting:m-release"]  # "last" and "week" found nothing


def test_an_explicit_range_wins_over_the_phrase(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("last week", now)
    _meeting(hub, "m-release", middle, "The release notes are out.")
    _meeting(hub, "m-week", middle - timedelta(days=40), "The week was long and the last item slipped.")

    # The caller's range is used as given, and the phrase stays in the
    # question as words: today's behaviour for an explicit range.
    explicit = hub.db.memory.search(
        "release notes last week", time_from="2000-01-01T00:00:00", now=now
    ).to_dict()
    assert "fusion" not in explicit["ranking"]
    assert set(_refs(explicit)) == {"meeting:m-release", "meeting:m-week"}

    routed = _route(hub, "release notes last week", time_to="2100-01-01T00:00:00")
    assert "fusion" not in routed["ranking"]


def test_a_long_drafter_prompt_is_not_read_for_a_phrase(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("yesterday", now)
    _meeting(hub, "m-yesterday", middle, "The kestrel review went well.")
    prompt = "kestrel " + ("transcript words " * 40) + "we said yesterday"
    assert len(prompt) > 400
    found = hub.db.memory.search(prompt, now=now).to_dict()
    assert "fusion" not in found["ranking"]


def test_a_phrase_with_no_hit_in_range_keeps_the_answer(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("yesterday", now)
    _meeting(hub, "m-old", middle - timedelta(days=30), "The kestrel review went well.")
    found = hub.db.memory.search("kestrel review yesterday", now=now)
    assert _refs(found) == ["meeting:m-old"]
    assert found.fusion["time"]["in_range"] == 0


def test_a_phrase_alone_is_a_question(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("yesterday", now)
    _meeting(hub, "m-yesterday", middle, "The kestrel review went well.")
    answer = _route(hub, "yesterday")
    assert _refs(answer) == ["meeting:m-yesterday"]


def test_the_time_retriever_keeps_the_project_scope(hub: Hub) -> None:
    now = datetime.now().astimezone()
    _start, middle, _end = _middle("yesterday", now)
    pid = hub.client.post("/api/projects", json={"name": "Atlas"}).json()["project"]["id"]
    _meeting(hub, "m-in-project", middle, "Roadmap sync.")
    _meeting(hub, "m-elsewhere", middle, "Roadmap sync.")
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO meeting_projects(meeting_id,project_id) VALUES(?,?)", ("m-in-project", pid)
        )
    found = hub.db.memory.search("what happened yesterday", project_id=pid, now=now)
    assert _refs(found) == ["meeting:m-in-project"]
