"""The suggested-source service: the transcript scanner and the suggestion rows.

Moved from tests/unit/test_hs172_people_sources.py (HS-172-06; fast diet, by service).
Real plain DB on the real schema in tmp_path; never the owner's database.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.services.suggested_source_service import SuggestedSourceService


@pytest.fixture
def plain_db(tmp_path: Path) -> Any:
    """The real plain DB on the real schema."""
    from holdspeak.db.core import Database

    return Database(tmp_path / "plain.sqlite3")


# ==============================================================================
# HS-172-06: The suggested source
# ==============================================================================


class TestSuggestedSourceScanner:
    """Transcript scanner finds repos and Jira keys."""

    def test_finds_github_repo(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We discussed karolswdev/holdspeak and the roadmap.",
            "proj-1", "m-1",
        )
        assert any(r["provider"] == "github" and r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_finds_jira_key(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "The issue KAN-7 was discussed at length.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
        )
        assert any(r["provider"] == "jira" and r["reference"] == "KAN-7" for r in results)

    def test_filters_unconnected_jira_prefix(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "The issue XYZ-99 came up.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
        )
        assert not any(r["provider"] == "jira" for r in results)

    def test_excludes_existing_sources(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We discussed karolswdev/holdspeak again.",
            "proj-1", "m-1",
            existing_source_refs={"karolswdev/holdspeak"},
        )
        assert not any(r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_no_mentions_empty(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "Nothing interesting here, just talking.",
            "proj-1", "m-1",
        )
        assert results == []

    def test_dedup_within_transcript(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "karolswdev/holdspeak and again karolswdev/holdspeak",
            "proj-1", "m-1",
        )
        refs = [r["reference"] for r in results]
        assert refs.count("karolswdev/holdspeak") == 1

    def test_github_dedup_case_insensitive(self, plain_db: Any) -> None:
        """GitHub owner/repo dedup is case-insensitive (lower-cased)."""
        sug = SuggestedSourceService(plain_db)
        results = sug.scan_transcript(
            "We use KarolSwDev/HoldSpeak for everything.",
            "proj-1", "m-1",
            existing_source_refs={"karolswdev/holdspeak"},
        )
        assert not any(r["reference"].lower() == "karolswdev/holdspeak" for r in results)

    def test_jira_dedup_case_insensitive(self, plain_db: Any) -> None:
        """Jira key dedup is case-insensitive (upper-cased)."""
        sug = SuggestedSourceService(plain_db)
        # Jira keys in transcript are always uppercase (regex [A-Z]+),
        # but existing refs might be stored differently.
        results = sug.scan_transcript(
            "Issue KAN-7 was discussed.",
            "proj-1", "m-1",
            connected_jira_keys={"KAN"},
            existing_source_refs={"kan-7"},  # lower-cased existing ref
        )
        assert not any(r["reference"].upper() == "KAN-7" for r in results)

    def test_dismissed_github_case_insensitive_suppresses(self, plain_db: Any) -> None:
        """A dismissed GitHub ref suppresses future scans case-insensitively."""
        sug = SuggestedSourceService(plain_db)
        # Create and dismiss a suggestion with different casing.
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "KarolSwDev/HoldSpeak"},
        ])
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan with the same repo in different casing.
        results = sug.scan_transcript(
            "Let me check karolswdev/holdspeak again.",
            "proj-1", "m-2",
        )
        assert not any(r["reference"].lower() == "karolswdev/holdspeak" for r in results)

    def test_dismissed_jira_case_insensitive_suppresses(self, plain_db: Any) -> None:
        """A dismissed Jira ref suppresses future scans case-insensitively."""
        sug = SuggestedSourceService(plain_db)
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "jira", "reference": "kan-7"},
        ])
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan with uppercase (as regex produces).
        results = sug.scan_transcript(
            "Issue KAN-7 again.",
            "proj-1", "m-2",
            connected_jira_keys={"KAN"},
        )
        assert not any(r["reference"].upper() == "KAN-7" for r in results)


class TestSuggestedSourceCRUD:
    """Accept, dismiss, and persistence."""

    def test_create_and_list(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        assert len(created) == 1
        listed = sug.list_suggestions("proj-1", status="pending")
        assert len(listed) == 1
        assert listed[0]["reference"] == "karolswdev/holdspeak"

    def test_accept_marks_accepted(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        accepted = sug.accept_suggestion(created[0]["id"])
        assert accepted["status"] == "accepted"
        # No longer in pending list.
        pending = sug.list_suggestions("proj-1", status="pending")
        assert len(pending) == 0

    def test_dismiss_marks_dismissed(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "jira", "reference": "KAN-7"},
        ])
        dismissed = sug.dismiss_suggestion(created[0]["id"])
        assert dismissed["status"] == "dismissed"

    def test_dismissed_suppresses_future_scans(self, plain_db: Any) -> None:
        sug = SuggestedSourceService(plain_db)
        sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "karolswdev/holdspeak"},
        ])
        # Dismiss it.
        listed = sug.list_suggestions("proj-1", status="pending")
        sug.dismiss_suggestion(listed[0]["id"])
        # Scan again -- the dismissed reference should not appear.
        results = sug.scan_transcript(
            "karolswdev/holdspeak mentioned again.",
            "proj-1", "m-2",
        )
        assert not any(r["reference"] == "karolswdev/holdspeak" for r in results)

    def test_accept_is_idempotent(self, plain_db: Any) -> None:
        """Accepting the same suggestion twice does not crash."""
        sug = SuggestedSourceService(plain_db)
        created = sug.create_suggestions("proj-1", "m-1", [
            {"provider": "github", "reference": "test/repo"},
        ])
        sug.accept_suggestion(created[0]["id"])
        # Second accept is safe.
        result = sug.accept_suggestion(created[0]["id"])
        assert result["status"] == "accepted"
