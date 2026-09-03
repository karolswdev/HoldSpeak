"""HS-159-01: Legacy Watch compatibility pins.

These characterization tests freeze the ReactionService's Watch paths
BEFORE the WatchSpec@1 graduation.  They must be GREEN before and after
the schema change, proving that the graduation is additive-only and
does not alter legacy behavior.

Pins:
- PIN-01: create_watch result shape (keys, types, defaults).
- PIN-02: list_watches returns created watches with parsed JSON.
- PIN-03: set_watch_enabled toggles and persists.
- PIN-04: preview_watch queries the fetcher, returns baseline/entity_count/changes.
- PIN-05: refresh_watch baseline cycle (first refresh = baseline, second = diff).
- PIN-06: refresh_due_watches respects cadence and isolates failures.
- PIN-07: diff_snapshots produces semantic transitions for gh and jira.
- PIN-08: Reactions routing (matching_reactions, event pattern matching).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.reaction_service import (
    DEFAULT_WATCH_REFRESH_MINUTES,
    ReactionService,
    diff_snapshots,
    normalize_snapshot,
)


OWNER = Principal(PrincipalKind.OWNER, "legacy-test-owner")


# ── PIN-01: create_watch result shape ────────────────────────────────────

class TestCreateWatchShape:
    """Freeze the shape of create_watch's return dict."""

    def test_gh_watch_has_expected_keys(self, tmp_path) -> None:
        db = Database(tmp_path / "pin01.db")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            name="My PRs", query={"repository": "acme/app"},
            watch_id="watch-pin01",
        )
        expected_keys = {
            "id", "connector_id", "query_kind", "name",
            "query", "snapshot", "enabled",
            "last_success_at", "last_error",
            "created_at", "updated_at",
        }
        assert set(watch.keys()) >= expected_keys

    def test_gh_watch_values(self, tmp_path) -> None:
        db = Database(tmp_path / "pin01b.db")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            name="My PRs", query={"repository": "acme/app"},
            watch_id="watch-pin01b",
        )
        assert watch["id"] == "watch-pin01b"
        assert watch["connector_id"] == "gh"
        assert watch["query_kind"] == "pull_requests"
        assert watch["name"] == "My PRs"
        assert watch["query"] == {"repository": "acme/app"}
        assert watch["enabled"] is True
        assert watch["snapshot"] == {}
        assert watch["last_error"] is None

    def test_github_alias_normalizes_to_gh(self, tmp_path) -> None:
        db = Database(tmp_path / "pin01c.db")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="github", query_kind="pull_requests",
            watch_id="watch-alias",
        )
        assert watch["connector_id"] == "gh"

    def test_jira_watch_creates(self, tmp_path) -> None:
        db = Database(tmp_path / "pin01d.db")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="jira", query_kind="issues",
            name="Jira", query={"jql": "assignee=me"},
            watch_id="watch-jira",
        )
        assert watch["connector_id"] == "jira"
        assert watch["query_kind"] == "issues"

    def test_unsupported_query_kind_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "pin01e.db")
        svc = ReactionService(db)
        with pytest.raises(ValidationError):
            svc.create_watch(OWNER, connector_id="gh", query_kind="commits")


# ── PIN-02: list_watches ─────────────────────────────────────────────────

class TestListWatches:
    def test_list_returns_all_created_watches(self, tmp_path) -> None:
        db = Database(tmp_path / "pin02.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-a",
        )
        svc.create_watch(
            OWNER, connector_id="jira", query_kind="issues",
            watch_id="watch-b",
        )
        watches = svc.list_watches(OWNER)
        ids = [w["id"] for w in watches]
        assert "watch-a" in ids
        assert "watch-b" in ids

    def test_list_parses_json_fields(self, tmp_path) -> None:
        db = Database(tmp_path / "pin02b.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            query={"repository": "acme/tool"}, watch_id="watch-json",
        )
        watches = svc.list_watches(OWNER)
        w = [x for x in watches if x["id"] == "watch-json"][0]
        assert isinstance(w["query"], dict)
        assert w["query"]["repository"] == "acme/tool"
        assert isinstance(w["snapshot"], dict)


# ── PIN-03: set_watch_enabled ────────────────────────────────────────────

class TestSetWatchEnabled:
    def test_disable_and_reenable(self, tmp_path) -> None:
        db = Database(tmp_path / "pin03.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-toggle",
        )
        result = svc.set_watch_enabled(OWNER, "watch-toggle", False)
        assert result["enabled"] is False
        result = svc.set_watch_enabled(OWNER, "watch-toggle", True)
        assert result["enabled"] is True

    def test_set_enabled_on_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "pin03b.db")
        svc = ReactionService(db)
        with pytest.raises(NotFound):
            svc.set_watch_enabled(OWNER, "no-such-watch", True)


# ── PIN-04: preview_watch ────────────────────────────────────────────────

class TestPreviewWatch:
    def test_preview_calls_fetcher_and_returns_shape(self, tmp_path) -> None:
        db = Database(tmp_path / "pin04.db")
        calls = []

        def fetcher(principal, **kwargs):
            calls.append(kwargs)
            return [{"number": 5, "state": "open", "title": "Five"}]

        svc = ReactionService(db, snapshot_fetcher=fetcher)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            query={"repository": "acme/lib"}, watch_id="watch-preview",
        )
        preview = svc.preview_watch(OWNER, "watch-preview")
        assert preview["watch_id"] == "watch-preview"
        assert preview["baseline"] is True  # no snapshot yet
        assert preview["entity_count"] == 1
        assert preview["changes"] == []
        assert preview["would_project"] == 0
        assert len(calls) == 1
        assert calls[0]["query"]["repository"] == "acme/lib"

    def test_preview_does_not_advance_baseline(self, tmp_path) -> None:
        db = Database(tmp_path / "pin04b.db")

        def fetcher(principal, **kwargs):
            return [{"number": 1, "state": "open", "title": "One"}]

        svc = ReactionService(db, snapshot_fetcher=fetcher)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-noadvance",
        )
        svc.preview_watch(OWNER, "watch-noadvance")
        watch = db.automations.get_watch("watch-noadvance")
        assert watch["snapshot"] == {}  # not advanced

    def test_preview_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "pin04c.db")
        svc = ReactionService(db)
        with pytest.raises(NotFound):
            svc.preview_watch(OWNER, "no-such-watch")


# ── PIN-05: refresh_watch baseline cycle ─────────────────────────────────

class TestRefreshWatchCycle:
    def test_first_refresh_is_baseline_second_diffs(self, tmp_path) -> None:
        db = Database(tmp_path / "pin05.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-cycle",
        )
        # First refresh: baseline.
        r1 = asyncio.run(svc.refresh_watch(OWNER, "watch-cycle", [
            {"number": 10, "state": "open", "title": "Ten"},
        ]))
        assert r1["baseline"] is True
        assert r1["events"] == []

        # Second refresh with changes: emits events.
        r2 = asyncio.run(svc.refresh_watch(OWNER, "watch-cycle", [
            {"number": 10, "state": "merged", "title": "Ten"},
        ]))
        assert r2["baseline"] is False
        assert len(r2["events"]) > 0
        types = {e["event_type"] for e in r2["events"]}
        assert "github.pr.merged" in types

    def test_refresh_disabled_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "pin05b.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-disabled", enabled=False,
        )
        with pytest.raises(ValidationError, match="Watch is disabled"):
            asyncio.run(svc.refresh_watch(OWNER, "watch-disabled", []))

    def test_refresh_records_error_on_failure(self, tmp_path) -> None:
        db = Database(tmp_path / "pin05c.db")

        def bad_fetcher(principal, **kwargs):
            raise RuntimeError("network down")

        svc = ReactionService(db, snapshot_fetcher=bad_fetcher)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-err",
        )
        with pytest.raises(RuntimeError, match="network down"):
            asyncio.run(svc.refresh_watch(OWNER, "watch-err"))

        watch = db.automations.get_watch("watch-err")
        assert watch["last_error"] == "network down"

    def test_repeated_identical_refresh_is_quiet(self, tmp_path) -> None:
        db = Database(tmp_path / "pin05d.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-quiet",
        )
        entities = [{"number": 7, "state": "open", "title": "Seven"}]
        asyncio.run(svc.refresh_watch(OWNER, "watch-quiet", entities))
        r = asyncio.run(svc.refresh_watch(OWNER, "watch-quiet", entities))
        assert r["events"] == []


# ── PIN-06: refresh_due_watches ──────────────────────────────────────────

class TestRefreshDueWatches:
    def test_due_watches_respect_cadence(self, tmp_path) -> None:
        db = Database(tmp_path / "pin06.db")

        def fetcher(principal, **kwargs):
            return [{"number": 1, "state": "open", "title": "PR"}]

        svc = ReactionService(db, snapshot_fetcher=fetcher)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-due",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        now = datetime.now(timezone.utc)
        # Push updated_at back so watch is due.
        old = (now - timedelta(minutes=20)).isoformat(timespec="seconds")
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at=? WHERE id='watch-due'",
                (old,),
            )
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER, now=now))
        assert len(outcomes) == 1
        assert outcomes[0]["watch_id"] == "watch-due"
        assert outcomes[0]["status"] == "refreshed"

        # Not due again within cadence.
        outcomes2 = asyncio.run(
            svc.refresh_due_watches(OWNER, now=now + timedelta(minutes=10))
        )
        assert outcomes2 == []

    def test_disabled_watches_skipped(self, tmp_path) -> None:
        db = Database(tmp_path / "pin06b.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-off", enabled=False,
        )
        now = datetime.now(timezone.utc)
        old = (now - timedelta(minutes=999)).isoformat(timespec="seconds")
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at=? WHERE id='watch-off'",
                (old,),
            )
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER, now=now))
        assert outcomes == []

    def test_default_cadence_is_35_minutes(self, tmp_path) -> None:
        assert DEFAULT_WATCH_REFRESH_MINUTES == 35

    def test_failure_isolation(self, tmp_path) -> None:
        db = Database(tmp_path / "pin06c.db")

        def flaky_fetcher(principal, **kwargs):
            if kwargs["connector_id"] == "jira":
                raise RuntimeError("jira offline")
            return [{"number": 1, "state": "open", "title": "PR"}]

        svc = ReactionService(db, snapshot_fetcher=flaky_fetcher)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-ok",
        )
        svc.create_watch(
            OWNER, connector_id="jira", query_kind="issues",
            watch_id="watch-fail",
        )
        now = datetime.now(timezone.utc)
        old = (now - timedelta(minutes=36)).isoformat(timespec="seconds")
        with db._connection() as conn:
            conn.execute("UPDATE connector_watches SET updated_at=?", (old,))

        outcomes = asyncio.run(svc.refresh_due_watches(OWNER, now=now))
        statuses = {o["watch_id"]: o["status"] for o in outcomes}
        assert statuses["watch-ok"] == "refreshed"
        assert statuses["watch-fail"] == "failed"


# ── PIN-07: diff_snapshots ───────────────────────────────────────────────

class TestDiffSnapshots:
    def test_gh_state_change(self) -> None:
        before = {"entities": {"17": {"id": "17", "state": "open", "title": "X"}}}
        after = {"entities": {"17": {"id": "17", "state": "merged", "title": "X"}}}
        events = diff_snapshots("gh", before, after)
        types = {e["event_type"] for e in events}
        assert "github.pr.merged" in types

    def test_gh_review_requested(self) -> None:
        before = {"entities": {"1": {"id": "1", "state": "open", "review_requests": []}}}
        after = {"entities": {"1": {"id": "1", "state": "open", "review_requests": ["alice"]}}}
        events = diff_snapshots("gh", before, after)
        assert any(e["event_type"] == "github.pr.review_requested" for e in events)

    def test_gh_new_entity_discovery(self) -> None:
        before = {"entities": {}}
        after = {"entities": {"2": {"id": "2", "state": "open", "title": "New"}}}
        events = diff_snapshots("gh", before, after)
        assert events[0]["event_type"] == "github.pr.opened"

    def test_jira_status_change(self) -> None:
        before = {"entities": {"X-1": {"id": "X-1", "status": "todo"}}}
        after = {"entities": {"X-1": {"id": "X-1", "status": "done"}}}
        events = diff_snapshots("jira", before, after)
        assert any(e["event_type"] == "jira.issue.status_changed" for e in events)

    def test_jira_resolution(self) -> None:
        before = {"entities": {"X-2": {"id": "X-2", "resolution": ""}}}
        after = {"entities": {"X-2": {"id": "X-2", "resolution": "fixed"}}}
        events = diff_snapshots("jira", before, after)
        assert any(e["event_type"] == "jira.issue.resolved" for e in events)

    def test_missing_rows_not_deletions(self) -> None:
        before = {"entities": {"3": {"id": "3", "state": "open"}}}
        after = {"entities": {}}
        events = diff_snapshots("gh", before, after)
        assert events == []


# ── PIN-08: Reactions routing ────────────────────────────────────────────

class TestReactionsRouting:
    def test_matching_reactions_exact_pattern(self, tmp_path) -> None:
        db = Database(tmp_path / "pin08.db")
        db.workbenches.upsert(workbench_id="wb-1", name="WB")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-r",
        )
        svc.create_reaction(
            OWNER, event_pattern="github.pr.merged",
            workbench_id="wb-1", watch_id=watch["id"],
            reaction_id="reaction-exact", enabled=True,
        )
        matches = db.automations.matching_reactions("watch-r", "github.pr.merged")
        assert len(matches) == 1
        assert matches[0]["id"] == "reaction-exact"

        # Non-matching event type.
        no_match = db.automations.matching_reactions("watch-r", "github.pr.opened")
        assert len(no_match) == 0

    def test_matching_reactions_wildcard_pattern(self, tmp_path) -> None:
        db = Database(tmp_path / "pin08b.db")
        db.workbenches.upsert(workbench_id="wb-2", name="WB2")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-wild",
        )
        svc.create_reaction(
            OWNER, event_pattern="github.pr.*",
            workbench_id="wb-2", watch_id=watch["id"],
            reaction_id="reaction-wild", enabled=True,
        )
        matches = db.automations.matching_reactions("watch-wild", "github.pr.merged")
        assert len(matches) == 1

    def test_disabled_reaction_not_matched(self, tmp_path) -> None:
        db = Database(tmp_path / "pin08c.db")
        db.workbenches.upsert(workbench_id="wb-3", name="WB3")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-dis",
        )
        svc.create_reaction(
            OWNER, event_pattern="github.pr.*",
            workbench_id="wb-3", watch_id=watch["id"],
            reaction_id="reaction-disabled", enabled=False,
        )
        matches = db.automations.matching_reactions("watch-dis", "github.pr.merged")
        assert len(matches) == 0

    def test_global_reaction_matches_any_watch(self, tmp_path) -> None:
        db = Database(tmp_path / "pin08d.db")
        db.workbenches.upsert(workbench_id="wb-4", name="WB4")
        svc = ReactionService(db)
        # Reaction with no watch_id (global).
        svc.create_reaction(
            OWNER, event_pattern="decision.committed",
            workbench_id="wb-4", reaction_id="reaction-global", enabled=True,
        )
        matches = db.automations.matching_reactions(None, "decision.committed")
        assert len(matches) == 1
        matches2 = db.automations.matching_reactions("some-watch", "decision.committed")
        assert len(matches2) == 1

    def test_owner_principal_required(self, tmp_path) -> None:
        db = Database(tmp_path / "pin08e.db")
        svc = ReactionService(db)
        agent = Principal(PrincipalKind.AGENT, "agent-x")
        with pytest.raises(ServiceError, match="Reactions run as OWNER"):
            svc.create_watch(agent, connector_id="gh", query_kind="pull_requests")


# ── HS-166-03 rider-b: graduated watches skipped by legacy scheduler ──


class TestRiderBGraduatedGuard:
    """refresh_due_watches skips rows whose state is graduated."""

    def test_graduated_watch_not_refreshed_by_legacy(self, tmp_path) -> None:
        """A watch with state='active' is NOT refreshed by the legacy pump."""
        import asyncio
        db = Database(tmp_path / "rider-b.db")
        svc = ReactionService(db)
        watch = svc.create_watch(
            OWNER, connector_id="jira", query_kind="issues",
            name="Graduated Jira", query={"jql": "project=KAN"},
            watch_id="watch-graduated",
        )
        # Graduate it
        db.automations.update_watch_spec(
            "watch-graduated",
            state="active",
            schema_version="WatchSpec@1",
        )
        # Force updated_at far in the past so cadence is met
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at='2020-01-01T00:00:00' WHERE id=?",
                ("watch-graduated",),
            )

        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        # The graduated watch should be skipped -- not in outcomes
        watch_ids = [o["watch_id"] for o in outcomes]
        assert "watch-graduated" not in watch_ids

    def test_legacy_watch_still_refreshed(self, tmp_path) -> None:
        """A watch with state='' (legacy) IS refreshed by the legacy pump."""
        import asyncio
        db = Database(tmp_path / "rider-b-legacy.db")
        svc = ReactionService(db)
        svc.create_watch(
            OWNER, connector_id="jira", query_kind="issues",
            name="Legacy Jira", query={"jql": "project=KAN"},
            watch_id="watch-legacy",
        )
        # Force updated_at far in the past
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at='2020-01-01T00:00:00' WHERE id=?",
                ("watch-legacy",),
            )

        # This will fail because we don't have a real adapter,
        # but the point is the watch is NOT skipped.
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        watch_ids = [o["watch_id"] for o in outcomes]
        assert "watch-legacy" in watch_ids
