"""Unit tests for GitHub CLI activity enrichment."""

from __future__ import annotations

import json
import subprocess

import pytest

from holdspeak.activity_github import preview_github_cli_enrichment, run_github_cli_enrichment
from holdspeak.db import MeetingDatabase, reset_database


@pytest.fixture
def test_db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_preview_github_cli_enrichment_plans_read_only_commands(test_db):
    pr = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/42",
        title="PR 42",
        domain="github.com",
        entity_type="github_pull_request",
        entity_id="openai/codex#42",
    )
    test_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.com/",
        title="Example",
        domain="example.com",
        entity_type="domain",
        entity_id="example.com",
    )

    preview = preview_github_cli_enrichment(
        test_db.list_activity_records(limit=10),
        gh_path="/usr/local/bin/gh",
    )

    assert preview["available"] is True
    assert preview["command_path"] == "/usr/local/bin/gh"
    assert preview["count"] == 1
    command = preview["commands"][0]
    assert command["activity_record_id"] == pr.id
    assert command["annotation_type"] == "github_pr"
    assert command["command"][:4] == ["/usr/local/bin/gh", "pr", "view", "42"]
    assert "--repo" in command["command"]
    assert "openai/codex" in command["command"]
    assert command["command"][1] in {"pr", "issue"}
    assert "edit" not in command["command"]


def test_run_github_cli_enrichment_writes_annotations(test_db):
    record = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/issues/99",
        title="Issue 99",
        domain="github.com",
        entity_type="github_issue",
        entity_id="openai/codex#99",
    )
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        assert kwargs["timeout"] == 2.0
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "number": 99,
                    "title": "Triage activity ledger",
                    "state": "OPEN",
                    "url": "https://github.com/openai/codex/issues/99",
                }
            ),
            stderr="",
        )

    results = run_github_cli_enrichment(
        test_db,
        [record],
        gh_path="/usr/local/bin/gh",
        timeout_seconds=2.0,
        max_bytes=4096,
        run_command=fake_run,
    )

    assert len(results) == 1
    assert results[0].error is None
    assert calls[0][:4] == ["/usr/local/bin/gh", "issue", "view", "99"]
    annotations = test_db.list_activity_annotations(
        activity_record_id=record.id,
        source_connector_id="gh",
        annotation_type="github_issue",
    )
    assert len(annotations) == 1
    assert annotations[0].title == "Triage activity ledger"
    assert annotations[0].value["entity_id"] == "openai/codex#99"
    assert annotations[0].value["gh"]["state"] == "OPEN"


def test_run_github_cli_enrichment_caps_output(test_db):
    record = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/42",
        title="PR 42",
        domain="github.com",
        entity_type="github_pull_request",
        entity_id="openai/codex#42",
    )

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="x" * 200, stderr="")

    results = run_github_cli_enrichment(
        test_db,
        [record],
        gh_path="/usr/local/bin/gh",
        max_bytes=64,
        run_command=fake_run,
    )

    assert results[0].error == "gh output exceeded max_bytes"
    assert test_db.list_activity_annotations(source_connector_id="gh") == []
