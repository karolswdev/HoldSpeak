"""The shared grounding helper (HS-87-04).

The AC: the same refs hydrate byte-identically through ask and steer —
one helper, a test pins parity. Plus the steer composition: fenced
provenance blocks, the cap named at compose time, the count line.
"""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak.grounding import (
    STEER_CONTEXT_CAP_BYTES,
    GroundingBlock,
    compose_steer,
    hydrate_grounding_blocks,
    hydrate_refs,
)


class _FakeIntel:
    def __init__(self, summary: str, actions: list[str]) -> None:
        self.summary = summary
        self._actions = actions

    def to_dict(self):
        return {"action_items": [{"task": a} for a in self._actions]}


class _FakeMeeting:
    def __init__(self, title, day, summary="", actions=None, segments=None) -> None:
        self.title = title
        self.started_at = SimpleNamespace(date=lambda: SimpleNamespace(isoformat=lambda: day))
        self.intel = _FakeIntel(summary, actions or []) if summary else None
        self.segments = segments or []


class _FakeArtifact:
    def __init__(self, title, body, meeting_id=None) -> None:
        self.title = title
        self.body_markdown = body
        self.meeting_id = meeting_id


class _FakeDB:
    def __init__(self, meetings=None, artifacts=None) -> None:
        self._m = meetings or {}
        self._a = artifacts or {}
        self.meetings = SimpleNamespace(get_meeting=lambda mid: self._m.get(mid))
        self.plugins = SimpleNamespace(get_artifact=lambda aid: self._a.get(aid))


def _db():
    return _FakeDB(
        meetings={
            "m1": _FakeMeeting("Kickoff", "2026-07-01", summary="We shipped.", actions=["ping ops"]),
            "parent": _FakeMeeting("Kickoff", "2026-07-01"),
        },
        artifacts={"a1": _FakeArtifact("Decisions", "Ship Friday.", meeting_id="parent")},
    )


# --- parity: one hydration truth ------------------------------------------


def test_hydrate_refs_and_ask_blocks_share_the_text() -> None:
    db = _db()
    raw, unknown = hydrate_refs(db, ["m1"], ["a1"], "summary")
    ask_blocks, ids, titles, ask_unknown = hydrate_grounding_blocks(
        db, ["m1"], ["a1"], "summary"
    )
    assert unknown == [] == ask_unknown
    # The raw block's text is EXACTLY what ask's formatted block wraps.
    assert raw[0].text in ask_blocks[0]
    assert raw[1].text in ask_blocks[1]
    assert ids == ["m1", "a1"]
    assert titles == ["Kickoff", "Decisions"]


def test_ask_headers_stay_byte_identical() -> None:
    blocks, _ids, _titles, _unknown = hydrate_grounding_blocks(
        _db(), ["m1"], ["a1"], "summary"
    )
    assert blocks[0].startswith("[MEETING: Kickoff — 2026-07-01]")
    assert blocks[1].startswith("[ARTIFACT: Decisions — Kickoff]")


def test_unknown_refs_come_back_named() -> None:
    _blocks, unknown = hydrate_refs(_db(), ["ghost"], ["nope"], "summary")
    assert set(unknown) == {"ghost", "nope"}


# --- steer composition -----------------------------------------------------


def test_compose_message_only_is_untouched() -> None:
    result = compose_steer("just this", [])
    assert result["status"] == "ok"
    assert result["text"] == "just this"
    assert result["context_bytes"] == 0


def test_compose_fences_each_object_with_provenance_and_counts() -> None:
    blocks = [
        GroundingBlock("meeting", "m1", "Kickoff", "2026-07-01", "We shipped."),
        GroundingBlock("artifact", "a1", "Decisions", "Kickoff", "Ship Friday."),
    ]
    result = compose_steer("what changed?", blocks)
    text = result["text"]
    assert text.startswith("what changed?\n\n")  # message first
    assert '--- from meeting: "Kickoff" (2026-07-01) ---' in text
    assert "We shipped." in text
    assert '--- from artifact: "Decisions" (Kickoff) ---' in text
    assert text.rstrip().endswith("(2 objects grounded)")
    assert result["refs"] == ["meeting:m1", "artifact:a1"]


def test_compose_singular_count_line() -> None:
    blocks = [GroundingBlock("meeting", "m1", "Kickoff", "", "body")]
    assert compose_steer("q", blocks)["text"].rstrip().endswith("(1 object grounded)")


def test_compose_over_cap_refuses_naming_the_size() -> None:
    big = "x" * (STEER_CONTEXT_CAP_BYTES + 100)
    blocks = [GroundingBlock("artifact", "a1", "Big", "", big)]
    result = compose_steer("q", blocks)
    assert result["status"] == "over_cap"
    assert result["context_bytes"] > result["cap_bytes"]
    assert "text" not in result  # nothing composed to send


def test_compose_at_the_cap_boundary_is_ok() -> None:
    # A block whose fenced size lands just under the cap composes.
    body = "y" * 100
    blocks = [GroundingBlock("artifact", "a1", "Small", "", body)]
    result = compose_steer("q", blocks, cap_bytes=STEER_CONTEXT_CAP_BYTES)
    assert result["status"] == "ok"
