"""Conductor ref hydration (HS-118-02).

The conductor's _hydrate_item_grounding() now forwards meeting_ids,
artifact_ids, AND refs through the shared hydration pipeline. Tests pin:
zone ref hydration, mixed grounding (all three types), cap enforcement
with correct drop ordering, and invalid ref handling.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any

from holdspeak.workbench_conductor import _hydrate_item_grounding
from holdspeak.grounding import GROUNDING_MAX_REFS


# --- Fake objects -----------------------------------------------------------


class _FakeIntel:
    def __init__(self, summary: str, actions: list[str] | None = None) -> None:
        self.summary = summary
        self._actions = actions or []

    def to_dict(self):
        return {"action_items": [{"task": a} for a in self._actions]}


class _FakeMeeting:
    def __init__(self, title: str, day: str, summary: str = "", segments=None) -> None:
        self.title = title
        self.started_at = SimpleNamespace(date=lambda: SimpleNamespace(isoformat=lambda: day))
        self.intel = _FakeIntel(summary) if summary else None
        self.segments = segments or []


class _FakeArtifact:
    def __init__(self, title: str, body: str, meeting_id: str | None = None) -> None:
        self.title = title
        self.body_markdown = body
        self.meeting_id = meeting_id


class _FakeNote:
    def __init__(self, title: str, body: str) -> None:
        self.title = title
        self.body_markdown = body


class _FakeZone:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeDirMembership:
    def __init__(self, primitive_id: str) -> None:
        self.primitive_id = primitive_id


class _FakeDB:
    """Minimal fake DB supporting meetings, artifacts, notes, and zones."""

    def __init__(
        self,
        meetings: dict[str, Any] | None = None,
        artifacts: dict[str, Any] | None = None,
        notes: dict[str, Any] | None = None,
        zones: dict[str, Any] | None = None,
        zone_members: dict[str, list[str]] | None = None,
    ) -> None:
        self._m = meetings or {}
        self._a = artifacts or {}
        self._n = notes or {}
        self._z = zones or {}
        self._zm = zone_members or {}
        self.meetings = SimpleNamespace(get_meeting=lambda mid: self._m.get(mid))
        self.plugins = SimpleNamespace(get_artifact=lambda aid: self._a.get(aid))
        self.notes = SimpleNamespace(get=lambda nid: self._n.get(nid))
        self.directories = SimpleNamespace(get=lambda did: self._z.get(did))
        self.directory_memberships = SimpleNamespace(
            list_for_directory=lambda did: [
                _FakeDirMembership(pid) for pid in self._zm.get(did, [])
            ]
        )


# --- Zone ref hydration -----------------------------------------------------


def test_zone_ref_hydrates_member_content() -> None:
    """A zone ref expands to its member notes' content."""
    db = _FakeDB(
        notes={
            "n1": _FakeNote("Note one", "First note body"),
            "n2": _FakeNote("Note two", "Second note body"),
        },
        zones={"dir_abc": _FakeZone("My zone")},
        zone_members={"dir_abc": ["note:n1", "note:n2"]},
    )
    grounding = json.dumps({"refs": ["zone:dir_abc"]})
    result = _hydrate_item_grounding(db, grounding)
    assert result.startswith("[GROUNDING]")
    assert "First note body" in result
    assert "Second note body" in result


def test_zone_ref_with_no_other_refs() -> None:
    """refs alone (no meeting_ids or artifact_ids) still hydrates."""
    db = _FakeDB(
        notes={"n1": _FakeNote("Solo", "Only note")},
        zones={"z1": _FakeZone("Zone A")},
        zone_members={"z1": ["note:n1"]},
    )
    grounding = json.dumps({"refs": ["zone:z1"]})
    result = _hydrate_item_grounding(db, grounding)
    assert "[GROUNDING]" in result
    assert "Only note" in result


# --- Mixed grounding (all three types) --------------------------------------


def test_mixed_grounding_all_three_types() -> None:
    """meeting_ids + artifact_ids + refs all hydrate in the same prompt."""
    db = _FakeDB(
        meetings={"m1": _FakeMeeting("Standup", "2026-08-01", summary="Shipped v2.")},
        artifacts={"a1": _FakeArtifact("RFC", "The proposal body")},
        notes={"n1": _FakeNote("Plan", "Quarterly plan")},
        zones={"z1": _FakeZone("Planning")},
        zone_members={"z1": ["note:n1"]},
    )
    grounding = json.dumps({
        "meeting_ids": ["m1"],
        "artifact_ids": ["a1"],
        "refs": ["zone:z1"],
    })
    result = _hydrate_item_grounding(db, grounding)
    assert "[GROUNDING]" in result
    # All three types' content present
    assert "Shipped v2." in result
    assert "The proposal body" in result
    assert "Quarterly plan" in result


def test_prompt_ordering_meetings_then_artifacts_then_refs() -> None:
    """Hydrated blocks appear in stable order: meetings, artifacts, refs."""
    db = _FakeDB(
        meetings={"m1": _FakeMeeting("Meeting A", "2026-08-01", summary="Meeting content")},
        artifacts={"a1": _FakeArtifact("Artifact B", "Artifact content")},
        notes={"n1": _FakeNote("Note C", "Note content")},
        zones={"z1": _FakeZone("Zone")},
        zone_members={"z1": ["note:n1"]},
    )
    grounding = json.dumps({
        "meeting_ids": ["m1"],
        "artifact_ids": ["a1"],
        "refs": ["zone:z1"],
    })
    result = _hydrate_item_grounding(db, grounding)
    # Meeting block appears before artifact block, artifact before zone
    meeting_pos = result.index("Meeting content")
    artifact_pos = result.index("Artifact content")
    note_pos = result.index("Note content")
    assert meeting_pos < artifact_pos < note_pos


# --- Cap enforcement ---------------------------------------------------------


def test_cap_enforcement_drops_refs_first(caplog) -> None:
    """When total > 16, refs are dropped last-added-first, then artifacts."""
    # 10 meetings + 5 artifacts + 5 refs = 20 total, need to drop 4
    meetings = {}
    for i in range(10):
        mid = f"m{i}"
        meetings[mid] = _FakeMeeting(f"M{i}", "2026-08-01", summary=f"Summary {i}")

    artifacts = {}
    for i in range(5):
        aid = f"a{i}"
        artifacts[aid] = _FakeArtifact(f"Art{i}", f"Body {i}")

    notes = {}
    for i in range(5):
        nid = f"n{i}"
        notes[nid] = _FakeNote(f"Note{i}", f"Note body {i}")
        # Each note ref is its own direct note ref, not a zone
    db = _FakeDB(meetings=meetings, artifacts=artifacts, notes=notes)

    grounding = json.dumps({
        "meeting_ids": [f"m{i}" for i in range(10)],
        "artifact_ids": [f"a{i}" for i in range(5)],
        "refs": [f"note:n{i}" for i in range(5)],
    })

    with caplog.at_level(logging.WARNING, logger="holdspeak.workbench_conductor"):
        result = _hydrate_item_grounding(db, grounding)

    # Cap warning logged
    assert any("cap exceeded" in r.message.lower() for r in caplog.records), (
        f"Expected cap warning, got: {[r.message for r in caplog.records]}"
    )

    # All 10 meetings preserved
    for i in range(10):
        assert f"Summary {i}" in result

    # Only first artifact survives (5 refs dropped = not enough, still need 4-5=wait...
    # 20 - 16 = 4 excess. Drop 4 from refs (last-added-first): n4, n3, n2, n1.
    # Remaining: 10 meetings + 5 artifacts + 1 ref (note:n0) = 16. All fit.
    assert "Note body 0" in result  # n0 kept
    assert "Note body 4" not in result  # n4 dropped


def test_cap_drops_artifacts_after_refs_exhausted(caplog) -> None:
    """When refs alone can't absorb the excess, artifact_ids are dropped too."""
    # 14 meetings + 3 artifacts + 2 refs = 19 total, need to drop 3
    meetings = {}
    for i in range(14):
        mid = f"m{i}"
        meetings[mid] = _FakeMeeting(f"M{i}", "2026-08-01", summary=f"MS{i}")

    artifacts = {}
    for i in range(3):
        artifacts[f"a{i}"] = _FakeArtifact(f"Art{i}", f"AB{i}")

    notes = {}
    for i in range(2):
        notes[f"n{i}"] = _FakeNote(f"Note{i}", f"NB{i}")

    db = _FakeDB(meetings=meetings, artifacts=artifacts, notes=notes)

    grounding = json.dumps({
        "meeting_ids": [f"m{i}" for i in range(14)],
        "artifact_ids": [f"a{i}" for i in range(3)],
        "refs": [f"note:n{i}" for i in range(2)],
    })

    with caplog.at_level(logging.WARNING, logger="holdspeak.workbench_conductor"):
        result = _hydrate_item_grounding(db, grounding)

    # 19 - 16 = 3 excess. Drop 2 refs (n1, n0), then 1 artifact (a2).
    # Remaining: 14 meetings + 2 artifacts (a0, a1) + 0 refs = 16
    assert any("cap exceeded" in r.message.lower() for r in caplog.records)

    # All 14 meetings preserved
    for i in range(14):
        assert f"MS{i}" in result

    # a0 and a1 kept, a2 dropped
    assert "AB0" in result
    assert "AB1" in result
    assert "AB2" not in result

    # Both refs dropped
    assert "NB0" not in result
    assert "NB1" not in result


def test_under_cap_no_warning(caplog) -> None:
    """When total <= 16, no warning logged and all refs hydrate."""
    db = _FakeDB(
        meetings={"m1": _FakeMeeting("M1", "2026-08-01", summary="S1")},
        artifacts={"a1": _FakeArtifact("A1", "B1")},
    )
    grounding = json.dumps({"meeting_ids": ["m1"], "artifact_ids": ["a1"]})

    with caplog.at_level(logging.WARNING, logger="holdspeak.workbench_conductor"):
        result = _hydrate_item_grounding(db, grounding)

    assert "S1" in result
    assert "B1" in result
    assert not any("cap exceeded" in r.message.lower() for r in caplog.records)


# --- Invalid ref handling ----------------------------------------------------


def test_invalid_qualified_ref_skipped_with_warning(caplog) -> None:
    """A malformed or nonexistent qualified ref is skipped gracefully."""
    db = _FakeDB(
        meetings={"m1": _FakeMeeting("Good", "2026-08-01", summary="Good content")},
    )
    grounding = json.dumps({
        "meeting_ids": ["m1"],
        "refs": ["badformat", "note:nonexistent"],
    })

    with caplog.at_level(logging.WARNING, logger="holdspeak.workbench_conductor"):
        result = _hydrate_item_grounding(db, grounding)

    # The valid meeting still hydrates
    assert "Good content" in result
    # Unknown refs logged
    assert any("unknown ref" in r.message.lower() for r in caplog.records)


def test_all_refs_invalid_returns_empty() -> None:
    """When every ref is invalid/nonexistent, hydration returns empty."""
    db = _FakeDB()
    grounding = json.dumps({"refs": ["note:ghost"]})
    result = _hydrate_item_grounding(db, grounding)
    # No blocks produced, so empty string
    assert result == ""


def test_nonexistent_zone_ref_skipped() -> None:
    """A zone ref pointing to a nonexistent zone is skipped gracefully."""
    db = _FakeDB(
        meetings={"m1": _FakeMeeting("OK", "2026-08-01", summary="Valid")},
    )
    grounding = json.dumps({
        "meeting_ids": ["m1"],
        "refs": ["zone:nonexistent"],
    })
    result = _hydrate_item_grounding(db, grounding)
    assert "Valid" in result  # meeting still hydrates


# --- Edge cases --------------------------------------------------------------


def test_empty_grounding_returns_empty() -> None:
    assert _hydrate_item_grounding(_FakeDB(), "{}") == ""
    assert _hydrate_item_grounding(_FakeDB(), "") == ""
    assert _hydrate_item_grounding(_FakeDB(), "null") == ""


def test_refs_only_grounding() -> None:
    """refs alone (no meeting_ids or artifact_ids) hydrate correctly."""
    db = _FakeDB(
        notes={"n1": _FakeNote("Ref-only", "Content via ref")},
    )
    grounding = json.dumps({"refs": ["note:n1"]})
    result = _hydrate_item_grounding(db, grounding)
    assert "[GROUNDING]" in result
    assert "Content via ref" in result
