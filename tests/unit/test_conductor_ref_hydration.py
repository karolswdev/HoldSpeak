"""Conductor ref hydration (HS-118-02).

The conductor's _hydrate_item_grounding() now forwards meeting_ids,
artifact_ids, AND refs through the shared hydration pipeline. Tests pin:
zone ref hydration, mixed grounding (all three types), cap enforcement
without silent truncation, and named invalid-source failures.
"""

from __future__ import annotations

import json
import logging
import pytest
from types import SimpleNamespace
from typing import Any

from holdspeak.workbench_conductor import _hydrate_item_grounding
from holdspeak.grounding import GROUNDING_MAX_REFS
from holdspeak.services.errors import ServiceError


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


@pytest.mark.parametrize("grounding", [
    {"meeting_ids": ["missing-meeting"]},
    {"artifact_ids": ["missing-artifact"]},
    {"refs": ["note:missing-note"]},
    {"meeting_ids": ["valid"], "refs": ["note:missing-note"]},
])
def test_explicit_source_missing_refuses_entire_item_grounding(grounding):
    db = _FakeDB(meetings={"valid": _FakeMeeting("Valid", "2026-08-01", summary="Partial evidence")})
    with pytest.raises(ServiceError) as raised:
        _hydrate_item_grounding(db, json.dumps(grounding))
    assert raised.value.code == "grounding_source_unavailable"


def test_explicit_source_read_error_refuses_without_partial_grounding(monkeypatch):
    db = _FakeDB(notes={"valid": _FakeNote("Valid", "Partial evidence")})
    def unreadable(*args, **kwargs):
        raise OSError("test source cannot be read")
    monkeypatch.setattr(db.notes, "get", unreadable)
    with pytest.raises(ServiceError) as raised:
        _hydrate_item_grounding(db, json.dumps({"refs": ["note:valid"]}))
    assert raised.value.code == "grounding_source_unavailable"


def test_over_limit_explicit_sources_refuse_without_silent_truncation():
    with pytest.raises(ServiceError) as raised:
        _hydrate_item_grounding(_FakeDB(), json.dumps({"meeting_ids": [f"m{i}" for i in range(GROUNDING_MAX_REFS + 1)]}))
    assert raised.value.code == "grounding_over_limit"


@pytest.mark.parametrize("answer", ["unknown", "error"])
def test_empty_attachment_lists_do_not_require_optional_recall(monkeypatch, answer):
    def recall(*args, **kwargs):
        if answer == "error":
            raise OSError("optional recall unavailable")
        return [], [], [], ["note:old-memory"]
    monkeypatch.setattr("holdspeak.grounding.hydrate_grounding_blocks", recall)
    assert _hydrate_item_grounding(_FakeDB(), '{"refs":[],"meeting_ids":[],"artifact_ids":[]}', query="Review work") == ""


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


@pytest.mark.parametrize("counts", [(10, 5, 5), (14, 3, 2)])
def test_cap_enforcement_refuses_mixed_sources_instead_of_dropping(counts) -> None:
    meetings, artifacts, refs = counts
    grounding = {
        "meeting_ids": [f"m{i}" for i in range(meetings)],
        "artifact_ids": [f"a{i}" for i in range(artifacts)],
        "refs": [f"note:n{i}" for i in range(refs)],
    }
    with pytest.raises(ServiceError) as raised:
        _hydrate_item_grounding(_FakeDB(), json.dumps(grounding))
    assert raised.value.code == "grounding_over_limit"
    assert f"{sum(counts)}/{GROUNDING_MAX_REFS}" in raised.value.detail


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


@pytest.mark.parametrize("refs", [["badformat", "note:nonexistent"], ["note:ghost"], ["zone:nonexistent"]])
def test_invalid_qualified_ref_refuses_with_its_identity(refs) -> None:
    db = _FakeDB(meetings={"m1": _FakeMeeting("Good", "2026-08-01", summary="Good content")})
    grounding = json.dumps({"meeting_ids": ["m1"], "refs": refs})
    with pytest.raises(ServiceError) as raised:
        _hydrate_item_grounding(db, grounding)
    assert raised.value.code == "grounding_source_unavailable"
    assert all(ref in raised.value.detail for ref in refs)


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
