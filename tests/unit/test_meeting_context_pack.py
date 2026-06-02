"""HS-13-07 — meeting-context pipeline pack tests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from holdspeak.connector_packs import meeting_context
from holdspeak.connector_runtime import PipelineRunner
from holdspeak.db import (
    ActivityAnnotation,
    ActivityMeetingCandidate,
    MeetingDatabase,
    reset_database,
)


@pytest.fixture
def db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _ann(**overrides) -> ActivityAnnotation:
    """Build an `ActivityAnnotation` for the synthesizer test
    without touching the DB. The synthesizer is a pure function
    over duck-typed objects with `.title` and `.value`."""
    base = {
        "id": "ann-test",
        "activity_record_id": 1,
        "source_connector_id": "gh",
        "annotation_type": "github_pr",
        "title": "",
        "value": {},
        "confidence": 1.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    base.update(overrides)
    return ActivityAnnotation(**base)


def _candidate(**overrides) -> ActivityMeetingCandidate:
    base = {
        "id": "cand-test",
        "source_connector_id": "calendar_activity",
        "source_activity_record_id": 1,
        "dedupe_key": "",
        "title": "",
        "starts_at": None,
        "ends_at": None,
        "meeting_url": None,
        "started_meeting_id": None,
        "confidence": 0.5,
        "status": "candidate",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    base.update(overrides)
    return ActivityMeetingCandidate(**base)


# ──────────────────────── Manifest shape ──────────────────────────


def test_manifest_is_pipeline_with_three_upstreams():
    manifest = meeting_context.MANIFEST
    assert manifest.kind == "pipeline"
    upstream_ids = sorted(c.pack_id for c in manifest.consumes)
    assert upstream_ids == ["calendar_activity", "gh", "jira"]
    # Downstream of `consumes`, the validator already enforced
    # that read:* permissions match. Spot-check that the pack
    # actually carries them.
    perms = set(manifest.permissions)
    for needed in (
        "read:activity_annotations",
        "read:activity_meeting_candidates",
        "write:activity_annotations",
    ):
        assert needed in perms


# ──────────────────────── Synthesizer ──────────────────────────────


def test_synthesizer_renders_grouped_markdown():
    markdown = meeting_context.synthesize_briefing(
        project_name="HoldSpeak",
        gh_annotations=[
            _ann(
                title="Wire new runtime",
                value={"entity_id": "anthropic/holdspeak#42", "gh": {"state": "OPEN"}},
            ),
        ],
        jira_annotations=[
            _ann(
                title="Land HS-13-07",
                value={"issue_key": "HS-101"},
                source_connector_id="jira",
                annotation_type="jira_ticket",
            ),
        ],
        calendar_candidates=[
            _candidate(
                title="Architecture sync",
                starts_at=datetime(2026, 5, 3, 10, 0),
            ),
        ],
    )
    assert "# HoldSpeak — meeting context" in markdown
    assert "## GitHub" in markdown
    assert "anthropic/holdspeak#42 — Wire new runtime (OPEN)" in markdown
    assert "## Jira" in markdown
    assert "HS-101 — Land HS-13-07" in markdown
    assert "## Upcoming calendar" in markdown
    assert "2026-05-03 10:00 — Architecture sync" in markdown


def test_synthesizer_handles_empty_inputs():
    markdown = meeting_context.synthesize_briefing(
        project_name="HoldSpeak",
        gh_annotations=[],
        jira_annotations=[],
        calendar_candidates=[],
    )
    assert "# HoldSpeak — meeting context" in markdown
    assert "No new activity since the last meeting." in markdown


def test_synthesizer_is_deterministic():
    """Same inputs in different order produce the same output —
    the synthesizer sorts each section so downstream diffs
    only fire when content actually changes."""
    a = meeting_context.synthesize_briefing(
        project_name="HoldSpeak",
        gh_annotations=[
            _ann(title="A", value={"entity_id": "o/r#1"}),
            _ann(title="B", value={"entity_id": "o/r#2"}),
        ],
        jira_annotations=[],
        calendar_candidates=[],
    )
    b = meeting_context.synthesize_briefing(
        project_name="HoldSpeak",
        gh_annotations=[
            _ann(title="B", value={"entity_id": "o/r#2"}),
            _ann(title="A", value={"entity_id": "o/r#1"}),
        ],
        jira_annotations=[],
        calendar_candidates=[],
    )
    assert a == b


# ──────────────────────── End-to-end run ──────────────────────────


def _seed_project(db: MeetingDatabase, project_id: str, name: str) -> None:
    db.projects.create_project(
        project_id=project_id,
        name=name,
        keywords=[name.lower()],
    )


def _seed_records_and_upstreams(db: MeetingDatabase, project_id: str) -> int:
    record = db.activity.upsert_activity_record(
        source_browser="safari",
        url=f"https://github.com/anthropic/{project_id}/pull/7",
        title=f"PR 7 in {project_id}",
        domain="github.com",
        last_seen_at=datetime.now(),
        entity_type="github_pull_request",
        entity_id=f"anthropic/{project_id}#7",
    )
    db.activity.assign_activity_record_project(record.id, project_id)
    db.activity.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_pr",
        title="Wire new runtime",
        value={"entity_id": f"anthropic/{project_id}#7", "gh": {"state": "OPEN"}},
    )
    db.activity.create_activity_annotation(
        activity_record_id=record.id,
        source_connector_id="jira",
        annotation_type="jira_ticket",
        title="Plan briefing",
        value={"issue_key": "HS-200"},
    )
    db.activity.create_activity_meeting_candidate(
        source_connector_id="calendar_activity",
        source_activity_record_id=record.id,
        title="Architecture sync",
        starts_at=datetime(2026, 5, 3, 10, 0),
    )
    return record.id


def test_run_writes_one_briefing_per_active_project(db):
    _seed_project(db, "holdspeak", "HoldSpeak")
    _seed_records_and_upstreams(db, "holdspeak")

    meeting_context.run(db)

    annotations = db.activity.list_activity_annotations(
        source_connector_id="meeting_context"
    )
    assert len(annotations) == 1
    payload = annotations[0].value
    assert payload["project_id"] == "holdspeak"
    assert payload["project_name"] == "HoldSpeak"
    assert payload["gh_count"] == 1
    assert payload["jira_count"] == 1
    assert payload["calendar_count"] == 1
    markdown = payload["markdown"]
    assert "## GitHub" in markdown
    assert "## Jira" in markdown
    assert "## Upcoming calendar" in markdown


def test_run_with_empty_upstream_still_writes_briefing(db):
    _seed_project(db, "holdspeak", "HoldSpeak")
    # Project exists but no records / annotations / candidates.
    meeting_context.run(db)

    annotations = db.activity.list_activity_annotations(
        source_connector_id="meeting_context"
    )
    assert len(annotations) == 1
    assert "No new activity since the last meeting." in annotations[0].value["markdown"]


def test_re_running_with_no_upstream_changes_does_not_duplicate(db):
    """HS-13-07 + HS-13-09: re-running the pipeline against
    an unchanged upstream produces no new annotation. The
    pack content-hashes the synthesized markdown against the
    most-recent briefing per project; identical output means
    no row appended."""
    _seed_project(db, "holdspeak", "HoldSpeak")
    _seed_records_and_upstreams(db, "holdspeak")

    meeting_context.run(db)
    meeting_context.run(db)
    rows = db.activity.list_activity_annotations(source_connector_id="meeting_context")
    assert len(rows) == 1
    assert rows[0].value["project_id"] == "holdspeak"


def test_re_running_with_changed_upstream_appends_new_snapshot(db):
    """HS-13-09: when upstream output changes between runs the
    pipeline appends a new annotation so /history's project
    briefing timeline can walk the cross-meeting narrative."""
    _seed_project(db, "holdspeak", "HoldSpeak")
    record_id = _seed_records_and_upstreams(db, "holdspeak")

    meeting_context.run(db)

    # Upstream changes: a new gh annotation lands on the same
    # record, which the synthesizer will pick up next run.
    db.activity.create_activity_annotation(
        activity_record_id=record_id,
        source_connector_id="gh",
        annotation_type="github_pr",
        title="Second wave",
        value={"entity_id": "anthropic/holdspeak#8", "gh": {"state": "OPEN"}},
    )

    meeting_context.run(db)

    rows = db.activity.list_activity_annotations(source_connector_id="meeting_context")
    assert len(rows) == 2
    # Newest first per the listing's ORDER BY.
    assert "Second wave" in rows[0].value["markdown"]


def test_run_records_a_connector_run_row(db):
    _seed_project(db, "holdspeak", "HoldSpeak")
    meeting_context.run(db)
    runs = db.activity.list_connector_runs(connector_id="meeting_context")
    assert len(runs) == 1
    assert runs[0].succeeded is True
    assert runs[0].annotation_count == 1


# ──────────────────────── PipelineRunner ──────────────────────────


def test_pipeline_runner_dispatches_meeting_context_with_fresh_upstreams(db):
    """When gh + jira + calendar all have fresh successful
    runs, the runner skips them and runs only the pipeline.
    HS-13-05's connector_runs is the freshness signal."""
    _seed_project(db, "holdspeak", "HoldSpeak")
    _seed_records_and_upstreams(db, "holdspeak")

    now = datetime(2026, 5, 2, 12, 0, 0)
    for upstream in ("gh", "jira", "calendar_activity"):
        db.activity.record_connector_run(
            connector_id=upstream,
            started_at=now - timedelta(seconds=30),
            finished_at=now - timedelta(seconds=20),
            succeeded=True,
        )

    runner = PipelineRunner(db, now=lambda: now)
    result = runner.run("meeting_context")

    assert result.succeeded is True
    statuses = {s.pack_id: s.status for s in result.steps}
    assert statuses["gh"] == "skipped_fresh"
    assert statuses["jira"] == "skipped_fresh"
    assert statuses["calendar_activity"] == "skipped_fresh"
    assert statuses["meeting_context"] == "ran"

    # The pipeline produced its annotation.
    annotations = db.activity.list_activity_annotations(
        source_connector_id="meeting_context"
    )
    assert len(annotations) == 1


def test_pipeline_run_history_carries_pipeline_row(db):
    """HS-13-05 + HS-13-07: a successful pipeline run records
    one connector_runs row for the pipeline pack itself
    (upstream rows are owned by the upstreams)."""
    _seed_project(db, "holdspeak", "HoldSpeak")
    _seed_records_and_upstreams(db, "holdspeak")

    now = datetime(2026, 5, 2, 12, 0, 0)
    for upstream in ("gh", "jira", "calendar_activity"):
        db.activity.record_connector_run(
            connector_id=upstream,
            started_at=now - timedelta(seconds=30),
            finished_at=now - timedelta(seconds=20),
            succeeded=True,
        )

    runner = PipelineRunner(db, now=lambda: now)
    runner.run("meeting_context")

    pipe_runs = db.activity.list_connector_runs(connector_id="meeting_context")
    assert len(pipe_runs) == 1
    assert pipe_runs[0].succeeded is True
