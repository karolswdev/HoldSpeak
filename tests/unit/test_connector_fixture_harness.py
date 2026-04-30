"""HS-11-02 — fixture-driven dry-run harness tests.

Each JSON file under `tests/fixtures/connectors/` becomes one
parametrized test case. The harness asserts:

  - The dry-run payload's shape matches the fixture's `expect`
    block (kind / capabilities / counts / permission notes /
    warnings / truncated flag).
  - No row was added to `activity_annotations` or
    `activity_meeting_candidates` during the run.

Adding a new fixture file is the only step needed to lock down a
new connector pack's preview behaviour.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.connector_fixtures import (
    FIXTURES_DIR,
    discover_fixtures,
    load_fixture,
    run_fixture,
)
from holdspeak.db import MeetingDatabase, reset_database

FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.json"))


@pytest.fixture
def test_db(tmp_path):
    reset_database()
    database = MeetingDatabase(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.mark.parametrize("fixture_path", FIXTURE_FILES, ids=lambda p: p.stem)
def test_fixture_dry_run_matches_expectation(test_db, fixture_path: Path):
    fixture = load_fixture(fixture_path)
    result = run_fixture(test_db, fixture)
    assert result.passed, result.diff_report()
    assert result.annotations_after == result.annotations_before
    assert result.candidates_after == result.candidates_before


def test_discover_fixtures_finds_every_committed_fixture():
    """Sanity: `discover_fixtures()` returns all fixture files
    in stable id order. Adding a new fixture under the
    fixtures dir is the only step needed to extend coverage."""
    found = discover_fixtures()
    assert {f.id for f in found} >= {
        "calendar-empty-ledger",
        "calendar-happy-path",
        "gh-empty-ledger",
        "gh-happy-path",
        "jira-empty-ledger",
        "jira-happy-path",
    }
    # Stable order — fixtures are sorted by id, so any consumer
    # iterating them gets a deterministic walk.
    ids = [f.id for f in found]
    assert ids == sorted(ids)


def test_fixture_failure_reports_readable_diff(test_db, tmp_path):
    """If a fixture's expectation drifts from reality, the
    failure report names every drifted field with both the
    expected and actual value, plus a summary of the actual
    payload. Operators should be able to fix a broken fixture
    from the report alone, no debugger needed."""
    bad_fixture_path = tmp_path / "bad-expectations.json"
    bad_fixture_path.write_text(
        '{"id":"bad","connector":"gh","limit":5,'
        '"activity_records":[{"url":"https://github.com/o/r/pull/1",'
        '"entity_type":"github_pull_request","entity_id":"o/r#1"}],'
        '"expect":{"kind":"oauth_cloud","command_count":99,'
        '"capabilities":["records"]}}'
    )
    fixture = load_fixture(bad_fixture_path)
    result = run_fixture(test_db, fixture)
    assert not result.passed
    report = result.diff_report()
    assert "kind expected 'oauth_cloud'" in report
    assert "command_count expected 99" in report
    assert "capabilities expected ['records']" in report
    # The summary block in the report enumerates the actual
    # values so the operator can copy them back into the fixture
    # if intentional.
    assert "kind" in report
    assert "cli_enrichment" in report
