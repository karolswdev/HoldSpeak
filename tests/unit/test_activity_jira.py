"""Unit tests for Jira CLI activity enrichment."""

from __future__ import annotations

import json
import subprocess

import pytest

from holdspeak.activity_jira import preview_jira_cli_enrichment, run_jira_cli_enrichment
from holdspeak.db import MeetingDatabase, reset_database


@pytest.fixture
def test_db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def test_preview_jira_cli_enrichment_plans_read_only_commands(test_db):
    ticket = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 activity mapping",
        domain="example.atlassian.net",
        entity_type="jira_ticket",
        entity_id="HS-123",
    )
    test_db.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/openai/codex/pull/42",
        title="PR 42",
        domain="github.com",
        entity_type="github_pull_request",
        entity_id="openai/codex#42",
    )

    preview = preview_jira_cli_enrichment(
        test_db.list_activity_records(limit=10),
        jira_path="/usr/local/bin/jira",
    )

    assert preview["available"] is True
    assert preview["command_path"] == "/usr/local/bin/jira"
    assert preview["count"] == 1
    command = preview["commands"][0]
    assert command["activity_record_id"] == ticket.id
    assert command["annotation_type"] == "jira_ticket"
    assert command["command"] == ["/usr/local/bin/jira", "issue", "view", "HS-123", "--plain"]
    assert "edit" not in command["command"]


def test_run_jira_cli_enrichment_writes_json_annotations(test_db):
    record = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 activity mapping",
        domain="example.atlassian.net",
        entity_type="jira_ticket",
        entity_id="HS-123",
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
                    "key": "HS-123",
                    "summary": "Ship Jira enrichment",
                    "status": "In Progress",
                    "assignee": "Karol",
                }
            ),
            stderr="",
        )

    results = run_jira_cli_enrichment(
        test_db,
        [record],
        jira_path="/usr/local/bin/jira",
        timeout_seconds=2.0,
        max_bytes=4096,
        run_command=fake_run,
    )

    assert len(results) == 1
    assert results[0].error is None
    assert calls[0] == ["/usr/local/bin/jira", "issue", "view", "HS-123", "--plain"]
    annotations = test_db.list_activity_annotations(
        activity_record_id=record.id,
        source_connector_id="jira",
        annotation_type="jira_ticket",
    )
    assert len(annotations) == 1
    assert annotations[0].title == "Ship Jira enrichment"
    assert annotations[0].value["entity_id"] == "HS-123"
    assert annotations[0].value["jira"]["status"] == "In Progress"


def test_run_jira_cli_enrichment_accepts_capped_raw_output(test_db):
    record = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-124",
        title="HS-124 activity mapping",
        domain="example.atlassian.net",
        entity_type="jira_ticket",
        entity_id="HS-124",
    )

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="HS-124 Done\nStatus: Done", stderr="")

    results = run_jira_cli_enrichment(
        test_db,
        [record],
        jira_path="/usr/local/bin/jira",
        max_bytes=4096,
        run_command=fake_run,
    )

    assert results[0].error is None
    annotations = test_db.list_activity_annotations(source_connector_id="jira")
    assert annotations[0].title == "HS-124"
    assert annotations[0].value["jira"]["raw"] == "HS-124 Done\nStatus: Done"


def test_run_jira_cli_enrichment_caps_output(test_db):
    record = test_db.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-125",
        title="HS-125 activity mapping",
        domain="example.atlassian.net",
        entity_type="jira_ticket",
        entity_id="HS-125",
    )

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="x" * 200, stderr="")

    results = run_jira_cli_enrichment(
        test_db,
        [record],
        jira_path="/usr/local/bin/jira",
        max_bytes=64,
        run_command=fake_run,
    )

    assert results[0].error == "jira output exceeded max_bytes"
    assert test_db.list_activity_annotations(source_connector_id="jira") == []
