"""Fixture-driven dry-run harness for connector packs.

HS-11-02. The phase-9 first-party connectors (gh, jira,
calendar_activity) plus future phase-11 connector packs all
flow through `holdspeak.activity_connector_preview.dry_run()`.
This module turns that into a fixture format so connector
behaviour can be locked down without real browser profiles,
real GitHub/Jira accounts, or live network calls.

Fixture format (JSON):

    {
      "id": "gh-happy-path",
      "connector": "gh",
      "limit": 10,
      "activity_records": [
        {
          "source_browser": "safari",
          "url": "https://github.com/anthropic/holdspeak/pull/7",
          "title": "PR 7",
          "domain": "github.com",
          "entity_type": "github_pull_request",
          "entity_id": "anthropic/holdspeak#7",
          "last_seen_at": "2026-04-30T10:00:00"
        }
      ],
      "expect": {
        "kind": "cli_enrichment",
        "capabilities": ["annotations"],
        "command_count": 1,
        "annotation_count": 1,
        "candidate_count": 0,
        "permission_notes_contain": ["disabled"],
        "warnings_contain": [],
        "truncated": false
      }
    }

The harness:

  - Seeds the activity_records into a temp DB.
  - Snapshots `activity_annotations` and
    `activity_meeting_candidates` row counts.
  - Runs `dry_run(db, fixture.connector, limit=fixture.limit)`.
  - Asserts the payload's shape matches the fixture's `expect`
    block.
  - Re-snapshots row counts and asserts neither moved.

On failure the assertion message renders a side-by-side diff
of the actual `dry_run().to_payload()` vs the fixture's
expected shape so the operator can see exactly what drifted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from .activity_connector_preview import dry_run
from .db import MeetingDatabase

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "connectors"


# ───────────────────────── Fixture model ─────────────────────────


@dataclass(frozen=True)
class ActivityRecordSeed:
    """One activity_records row to upsert before dry-run."""

    url: str
    source_browser: str = "safari"
    source_profile: str = ""
    title: Optional[str] = None
    domain: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    last_seen_at: Optional[str] = None  # ISO-8601


@dataclass(frozen=True)
class ConnectorFixtureExpectation:
    """Expected shape of the dry-run payload.

    Each field is optional. If a field is `None`, the harness
    skips that assertion. This lets a fixture express only the
    invariants it cares about — e.g. an empty-ledger fixture
    asserts `command_count: 0` + a specific `warnings_contain`
    string without locking down `kind` again (already covered
    elsewhere).
    """

    kind: Optional[str] = None
    capabilities: Optional[list[str]] = None
    enabled: Optional[bool] = None
    cli_required: Optional[Optional[str]] = None
    cli_available: Optional[Optional[bool]] = None
    command_count: Optional[int] = None
    annotation_count: Optional[int] = None
    candidate_count: Optional[int] = None
    permission_notes_contain: list[str] = field(default_factory=list)
    warnings_contain: list[str] = field(default_factory=list)
    truncated: Optional[bool] = None


@dataclass(frozen=True)
class ConnectorFixture:
    """One fixture loaded from disk."""

    id: str
    connector: str
    limit: int
    activity_records: tuple[ActivityRecordSeed, ...]
    expect: ConnectorFixtureExpectation
    source: Optional[Path] = None


# ─────────────────────────── Loading ─────────────────────────────


def load_fixture(path: Path) -> ConnectorFixture:
    """Parse a JSON fixture file into a `ConnectorFixture`."""
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"fixture {path} must be a JSON object")

    fixture_id = str(raw.get("id") or path.stem)
    connector = str(raw.get("connector") or "").strip()
    if not connector:
        raise ValueError(f"fixture {path} missing 'connector' field")
    limit = int(raw.get("limit", 25))

    seeds_raw = raw.get("activity_records") or []
    if not isinstance(seeds_raw, list):
        raise ValueError(f"fixture {path} 'activity_records' must be a list")
    seeds = tuple(
        ActivityRecordSeed(
            url=str(s["url"]),
            source_browser=str(s.get("source_browser", "safari")),
            source_profile=str(s.get("source_profile", "")),
            title=s.get("title"),
            domain=s.get("domain"),
            entity_type=s.get("entity_type"),
            entity_id=s.get("entity_id"),
            last_seen_at=s.get("last_seen_at"),
        )
        for s in seeds_raw
    )

    expect_raw = raw.get("expect") or {}
    expect = ConnectorFixtureExpectation(
        kind=expect_raw.get("kind"),
        capabilities=expect_raw.get("capabilities"),
        enabled=expect_raw.get("enabled"),
        cli_required=expect_raw.get("cli_required") if "cli_required" in expect_raw else None,
        cli_available=expect_raw.get("cli_available") if "cli_available" in expect_raw else None,
        command_count=expect_raw.get("command_count"),
        annotation_count=expect_raw.get("annotation_count"),
        candidate_count=expect_raw.get("candidate_count"),
        permission_notes_contain=list(expect_raw.get("permission_notes_contain") or []),
        warnings_contain=list(expect_raw.get("warnings_contain") or []),
        truncated=expect_raw.get("truncated"),
    )

    return ConnectorFixture(
        id=fixture_id,
        connector=connector,
        limit=limit,
        activity_records=seeds,
        expect=expect,
        source=path,
    )


def discover_fixtures(directory: Path = FIXTURES_DIR) -> list[ConnectorFixture]:
    """Load every `*.json` fixture from `directory`."""
    if not directory.exists():
        return []
    return sorted(
        (load_fixture(p) for p in directory.glob("*.json")),
        key=lambda f: f.id,
    )


# ─────────────────────── Harness execution ───────────────────────


@dataclass(frozen=True)
class FixtureRunResult:
    """Outcome of running one fixture."""

    fixture_id: str
    payload: Mapping[str, Any]
    annotations_before: int
    annotations_after: int
    candidates_before: int
    candidates_after: int
    failures: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not self.failures

    def diff_report(self) -> str:
        if not self.failures:
            return "(passed)"
        lines = [f"fixture {self.fixture_id} — {len(self.failures)} failure(s):"]
        lines.extend(f"  - {f}" for f in self.failures)
        lines.append("payload (truncated):")
        lines.append(json.dumps(self._summary(), indent=2))
        return "\n".join(lines)

    def _summary(self) -> dict[str, Any]:
        return {
            "kind": self.payload.get("kind"),
            "capabilities": self.payload.get("capabilities"),
            "enabled": self.payload.get("enabled"),
            "cli_required": self.payload.get("cli_required"),
            "cli_available": self.payload.get("cli_available"),
            "command_count": len(self.payload.get("commands") or []),
            "annotation_count": len(self.payload.get("proposed_annotations") or []),
            "candidate_count": len(self.payload.get("proposed_candidates") or []),
            "warnings": self.payload.get("warnings"),
            "permission_notes": self.payload.get("permission_notes"),
            "truncated": self.payload.get("truncated"),
        }


def _seed_records(db: MeetingDatabase, seeds: Iterable[ActivityRecordSeed]) -> None:
    for seed in seeds:
        last_seen = (
            datetime.fromisoformat(seed.last_seen_at.replace("Z", "+00:00"))
            if seed.last_seen_at
            else None
        )
        db.upsert_activity_record(
            source_browser=seed.source_browser,
            source_profile=seed.source_profile,
            url=seed.url,
            title=seed.title,
            domain=seed.domain,
            entity_type=seed.entity_type,
            entity_id=seed.entity_id,
            last_seen_at=last_seen,
        )


def run_fixture(db: MeetingDatabase, fixture: ConnectorFixture) -> FixtureRunResult:
    """Seed the fixture's records, dry-run, assert no mutation, return result."""
    _seed_records(db, fixture.activity_records)

    annotations_before = len(db.list_activity_annotations(limit=5000))
    candidates_before = len(db.list_activity_meeting_candidates(limit=5000))

    result = dry_run(db, fixture.connector, limit=fixture.limit)
    payload = result.to_payload()

    annotations_after = len(db.list_activity_annotations(limit=5000))
    candidates_after = len(db.list_activity_meeting_candidates(limit=5000))

    failures: list[str] = []
    expect = fixture.expect

    if expect.kind is not None and payload.get("kind") != expect.kind:
        failures.append(f"kind expected {expect.kind!r}, got {payload.get('kind')!r}")

    if expect.capabilities is not None and payload.get("capabilities") != expect.capabilities:
        failures.append(
            f"capabilities expected {expect.capabilities!r}, got {payload.get('capabilities')!r}"
        )

    if expect.enabled is not None and payload.get("enabled") != expect.enabled:
        failures.append(f"enabled expected {expect.enabled!r}, got {payload.get('enabled')!r}")

    if expect.cli_required is not None and payload.get("cli_required") != expect.cli_required:
        failures.append(
            f"cli_required expected {expect.cli_required!r}, got {payload.get('cli_required')!r}"
        )

    if expect.cli_available is not None and payload.get("cli_available") != expect.cli_available:
        failures.append(
            f"cli_available expected {expect.cli_available!r}, got {payload.get('cli_available')!r}"
        )

    actual_command_count = len(payload.get("commands") or [])
    if expect.command_count is not None and actual_command_count != expect.command_count:
        failures.append(
            f"command_count expected {expect.command_count}, got {actual_command_count}"
        )

    actual_annotation_count = len(payload.get("proposed_annotations") or [])
    if expect.annotation_count is not None and actual_annotation_count != expect.annotation_count:
        failures.append(
            f"proposed_annotation_count expected {expect.annotation_count}, "
            f"got {actual_annotation_count}"
        )

    actual_candidate_count = len(payload.get("proposed_candidates") or [])
    if expect.candidate_count is not None and actual_candidate_count != expect.candidate_count:
        failures.append(
            f"proposed_candidate_count expected {expect.candidate_count}, "
            f"got {actual_candidate_count}"
        )

    notes = payload.get("permission_notes") or []
    for needle in expect.permission_notes_contain:
        if not any(needle in note for note in notes):
            failures.append(
                f"permission_notes missing substring {needle!r} (got {notes!r})"
            )

    warnings = payload.get("warnings") or []
    for needle in expect.warnings_contain:
        if not any(needle in warning for warning in warnings):
            failures.append(
                f"warnings missing substring {needle!r} (got {warnings!r})"
            )

    if expect.truncated is not None and payload.get("truncated") != expect.truncated:
        failures.append(
            f"truncated expected {expect.truncated!r}, got {payload.get('truncated')!r}"
        )

    if annotations_after != annotations_before:
        failures.append(
            f"DB MUTATION — activity_annotations: "
            f"{annotations_before} → {annotations_after}"
        )
    if candidates_after != candidates_before:
        failures.append(
            f"DB MUTATION — activity_meeting_candidates: "
            f"{candidates_before} → {candidates_after}"
        )

    return FixtureRunResult(
        fixture_id=fixture.id,
        payload=payload,
        annotations_before=annotations_before,
        annotations_after=annotations_after,
        candidates_before=candidates_before,
        candidates_after=candidates_after,
        failures=tuple(failures),
    )
