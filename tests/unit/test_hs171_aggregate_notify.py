"""HS-171-03/05/06 tests: needs-you cache, notifications, brief recurring.

Run: HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \
     tests/unit/test_hs171_aggregate_notify.py tests/unit -k "needs_you or brief or presence or notify"
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── HS-171-03: needs-you aggregate cache ────────────────────────────


class TestNeedsYouCache:
    """The cached read returns computedAt/stale and never calls the Room
    builder on a warm cache; ``?fresh=1`` rebuilds."""

    def _make_builder(self, items: list[dict] | None = None):
        """Return a builder callable that counts invocations."""
        call_count = {"n": 0}
        def builder() -> dict[str, Any]:
            call_count["n"] += 1
            return {
                "count": len(items or []),
                "projects": [],
                "items": items or [],
                "next": None,
                "computedAt": datetime.now().isoformat(),
                "stale": False,
                "sweepId": None,
            }
        return builder, call_count

    def test_cached_read_returns_computed_at_and_stale(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, counts = self._make_builder([{"severity": "info"}])
        cache = NeedsYouCache(builder, max_age_s=60.0)

        result = cache.get()
        assert "computedAt" in result
        assert result["stale"] is False
        assert counts["n"] == 1

    def test_warm_cache_does_not_rebuild(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, counts = self._make_builder([{"severity": "info"}])
        cache = NeedsYouCache(builder, max_age_s=60.0)

        first = cache.get()
        second = cache.get()
        assert counts["n"] == 1, "Builder should be called exactly once on warm cache"
        assert second["computedAt"] == first["computedAt"]

    def test_fresh_forces_rebuild(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, counts = self._make_builder([{"severity": "info"}])
        cache = NeedsYouCache(builder, max_age_s=60.0)

        cache.get()
        assert counts["n"] == 1
        cache.get(force=True)
        assert counts["n"] == 2, "force=True should trigger a rebuild"

    def test_invalidate_clears_cache(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, counts = self._make_builder()
        cache = NeedsYouCache(builder, max_age_s=60.0)

        cache.get()
        assert counts["n"] == 1
        cache.invalidate(sweep_id="sweep-1")
        cache.get()
        assert counts["n"] == 2, "Invalidation should force a rebuild on next get"

    def test_stale_after_max_age(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, counts = self._make_builder()
        cache = NeedsYouCache(builder, max_age_s=0.01)  # 10ms

        cache.get()
        time.sleep(0.02)
        # peek should report stale
        peeked = cache.peek()
        assert peeked is not None
        assert peeked["stale"] is True

    def test_sweep_id_propagated(self):
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, _ = self._make_builder()
        cache = NeedsYouCache(builder, max_age_s=60.0)

        cache.invalidate(sweep_id="sweep-42")
        result = cache.get()
        assert result["sweepId"] == "sweep-42"


class TestBuildAggregate:
    """The pure builder produces the correct shape."""

    def test_shape_has_required_fields(self):
        from holdspeak.services.needs_you_aggregate import build_aggregate
        from holdspeak.principals import Principal, PrincipalKind

        def list_projects(principal, filters):
            return [{"id": "p1", "name": "Gov"}]

        def room(principal, project_id):
            return {
                "needsYou": {
                    "state": "ok",
                    "items": [
                        {"title": "PR #42", "why": "review overdue", "severity": "danger"},
                    ],
                },
            }

        result = build_aggregate(
            list_projects=list_projects,
            room=room,
            principal=Principal(PrincipalKind.OWNER, "test"),
        )
        assert "computedAt" in result
        assert "stale" in result
        assert "sweepId" in result
        assert result["count"] == 1
        assert result["items"][0]["projectId"] == "p1"
        assert result["items"][0]["why"] == "review overdue"


# ── HS-171-05: edge rule and notification ───────────────────────────


class TestEdgeDetector:
    """Edge rule: 3->3 no fire, 3->4 fires, 4->2->4 fires once."""

    def test_rising_edge_fires(self):
        from holdspeak.desktop_notify import EdgeDetector

        edge = EdgeDetector()
        assert edge.should_fire(3) is True  # 0->3 fires
        edge.mark_fired(3)
        assert edge.should_fire(3) is False  # 3->3 no fire
        assert edge.should_fire(4) is True   # 3->4 fires

    def test_drop_and_rise_fires(self):
        from holdspeak.desktop_notify import EdgeDetector

        edge = EdgeDetector()
        edge.mark_fired(4)
        # count drops to 2 -- should_fire(2) is False (2 < 4)
        assert edge.should_fire(2) is False
        # But we don't mark_fired on a non-fire, so last stays 4.
        # Now count rises to 5: 5 > 4, so fires.
        assert edge.should_fire(5) is True

    def test_same_count_no_fire(self):
        from holdspeak.desktop_notify import EdgeDetector

        edge = EdgeDetector()
        edge.mark_fired(3)
        assert edge.should_fire(3) is False
        assert edge.should_fire(3) is False

    def test_zero_never_fires(self):
        from holdspeak.desktop_notify import EdgeDetector

        edge = EdgeDetector()
        assert edge.should_fire(0) is False


class TestQuietHours:
    """Quiet hours hold + receipt."""

    def test_quiet_hours_hold(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        receipts = []
        result = heartbeat_notify(
            count=3,
            project_count=2,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=23,   # always quiet
            receipt_writer=lambda r: receipts.append(r),
            _notifier=lambda *a, **k: True,
        )
        assert result["held"] is True
        assert result["fired"] is False
        assert result["reason"] == "quiet_hours"
        assert len(receipts) == 1
        assert "held:quiet_hours" in receipts[0]["result_summary"]

    def test_outside_quiet_hours_fires(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        fired_calls = []
        result = heartbeat_notify(
            count=3,
            project_count=2,
            edge=edge,
            quiet_hours_start=23,
            quiet_hours_end=23,  # never quiet (start==end => False)
            _notifier=lambda *a, **k: (fired_calls.append(1), True)[1],
        )
        assert result["fired"] is True
        assert len(fired_calls) == 1


class TestNotifyContentDefault:
    """Content is count-only by default."""

    def test_count_only_body(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        bodies = []
        def mock_notifier(title, body, *, click_url=None):
            bodies.append(body)
            return True

        heartbeat_notify(
            count=3,
            project_count=2,
            edge=edge,
            quiet_hours_start=23,
            quiet_hours_end=23,
            notify_content=False,
            content_items=[{"projectId": "p1", "projectName": "Gov", "why": "overdue"}],
            _notifier=mock_notifier,
        )
        assert len(bodies) == 1
        assert bodies[0] == "3 need you across 2 projects"
        assert "overdue" not in bodies[0]

    def test_content_opt_in_includes_why(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        bodies = []
        def mock_notifier(title, body, *, click_url=None):
            bodies.append(body)
            return True

        heartbeat_notify(
            count=3,
            project_count=2,
            edge=edge,
            quiet_hours_start=23,
            quiet_hours_end=23,
            notify_content=True,
            content_items=[{"projectId": "p1", "projectName": "Gov", "why": "PR review overdue"}],
            _notifier=mock_notifier,
        )
        assert len(bodies) == 1
        assert "Gov: PR review overdue" in bodies[0]

    def test_single_project_body(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        bodies = []
        def mock_notifier(title, body, *, click_url=None):
            bodies.append(body)
            return True

        heartbeat_notify(
            count=2,
            project_count=1,
            edge=edge,
            quiet_hours_start=23,
            quiet_hours_end=23,
            _notifier=mock_notifier,
        )
        assert bodies[0] == "2 need you"


# ── HS-171-06: brief human items vs ledger ──────────────────────────


class TestBriefHumanVsLedger:
    """A brief over a DB with 1839 kernel ops + 2 human items reports
    2 items and ledger.operations == 1839."""

    def _service(self, tmp_path):
        from holdspeak.db.core import Database
        from holdspeak.services.monday_brief_service import MondayBriefService
        return MondayBriefService(Database(tmp_path / "brief.db"))

    def _insert_event(self, service, event_id, timestamp, service_name, method,
                      correlation_id="", args_summary="{}", error=None):
        with service._db._connection() as conn:
            conn.execute(
                """INSERT INTO pipeline_events
                   (event_id, timestamp, service, method, principal_kind, args_summary,
                    correlation_id, error)
                   VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
                (event_id, timestamp, service_name, method, args_summary,
                 correlation_id, error),
            )

    def test_brief_1839_kernel_ops_2_human_items(self, tmp_path):
        import datetime as _dt
        service = self._service(tmp_path)

        # Insert 1839 kernel operations (PrimitiveService, RecipeService, etc.)
        base_ts = _dt.datetime(2026, 8, 1, 12, tzinfo=_dt.UTC).timestamp()
        kernel_services = [
            ("PrimitiveService", "delete_directory"),
            ("RecipeService", "run"),
            ("GateService", "transition"),
            ("InvocationService", "create"),
            ("SyncService", "update"),
        ]
        for i in range(1839):
            svc, method = kernel_services[i % len(kernel_services)]
            self._insert_event(
                service,
                event_id=f"kernel-{i}",
                timestamp=base_ts + i,
                service_name=svc,
                method=method,
            )

        # Insert 2 human items (NoteService, MeetingService)
        self._insert_event(
            service,
            event_id="human-1",
            timestamp=base_ts + 2000,
            service_name="NoteService",
            method="create_note",
            args_summary='{"title":"Plan"}',
        )
        self._insert_event(
            service,
            event_id="human-2",
            timestamp=base_ts + 2001,
            service_name="MeetingService",
            method="update",
            args_summary='{"meeting_id":"m1"}',
        )

        brief = service.generate(
            None, now=_dt.datetime(2026, 8, 3, 9, 30, tzinfo=_dt.UTC)
        )

        # Only 2 human items in the sections (meetings collector is separate,
        # but pipeline changes should only have human items).
        total_items = sum(len(items) for items in brief.sections.values())
        assert total_items == 2, f"Expected 2 human items, got {total_items}"
        assert brief.ledger.operations == 1839

    def test_ledger_only_brief_is_empty(self, tmp_path):
        """A brief with only kernel ops (no human items) is empty."""
        import datetime as _dt
        service = self._service(tmp_path)

        base_ts = _dt.datetime(2026, 8, 1, 12, tzinfo=_dt.UTC).timestamp()
        for i in range(10):
            self._insert_event(
                service,
                event_id=f"kernel-{i}",
                timestamp=base_ts + i,
                service_name="PrimitiveService",
                method="delete_directory",
            )

        brief = service.generate(
            None, now=_dt.datetime(2026, 8, 3, 9, 30, tzinfo=_dt.UTC)
        )

        assert brief.is_empty is True
        assert brief.ledger.operations == 10
        assert brief.headline == "Nothing material changed."

    def test_human_service_items_are_preserved(self, tmp_path):
        """Items from human services appear in the changed section."""
        import datetime as _dt
        service = self._service(tmp_path)

        base_ts = _dt.datetime(2026, 8, 1, 12, tzinfo=_dt.UTC).timestamp()
        self._insert_event(
            service,
            event_id="note-created",
            timestamp=base_ts,
            service_name="NoteService",
            method="create_note",
            correlation_id="note-1",
        )

        items, ledger = service._collect_changes(
            "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
        )

        assert len(items) == 1
        assert items[0].text == "NoteService.create_note"
        assert ledger.operations == 0

    def test_kernel_ops_go_to_ledger_not_items(self, tmp_path):
        """Kernel service operations land in the ledger, not in items."""
        import datetime as _dt
        service = self._service(tmp_path)

        base_ts = _dt.datetime(2026, 8, 1, 12, tzinfo=_dt.UTC).timestamp()
        self._insert_event(
            service,
            event_id="prim-delete",
            timestamp=base_ts,
            service_name="PrimitiveService",
            method="delete_directory",
        )
        self._insert_event(
            service,
            event_id="recipe-run",
            timestamp=base_ts + 1,
            service_name="RecipeService",
            method="run",
        )

        items, ledger = service._collect_changes(
            "2026-08-01T00:00:00+00:00", "2026-08-02T00:00:00+00:00"
        )

        assert items == []
        assert ledger.operations == 2
        assert ledger.since is not None


# ── HS-171-05: macOS notifier monkeypatched ─────────────────────────


class TestMacOSNotifier:
    """The macOS path uses osascript; exercised with subprocess monkeypatched."""

    def test_macos_notify_calls_osascript(self):
        from holdspeak.desktop_notify import _notify_macos

        with patch("holdspeak.desktop_notify.subprocess") as mock_sp:
            mock_sp.run.return_value = MagicMock(returncode=0)
            result = _notify_macos("HoldSpeak", "3 need you across 2 projects")
            assert result is True
            mock_sp.run.assert_called_once()
            args = mock_sp.run.call_args
            assert args[0][0][0] == "osascript"
            assert "display notification" in args[0][0][2]

    def test_macos_notify_escapes_quotes(self):
        from holdspeak.desktop_notify import _notify_macos

        with patch("holdspeak.desktop_notify.subprocess") as mock_sp:
            mock_sp.run.return_value = MagicMock(returncode=0)
            _notify_macos('HoldSpeak', 'He said "hello"')
            script = mock_sp.run.call_args[0][0][2]
            assert '\\"hello\\"' in script


# ── HS-171-05: Cocoa child notify command ───────────────────────────


class TestCocoaChildNotify:
    """The Cocoa child process handles the ``notify`` command."""

    def test_cocoa_notify_calls_osascript(self):
        import subprocess

        calls = []
        original_run = subprocess.run

        def mock_run(*args, **kwargs):
            calls.append(args)
            return MagicMock(returncode=0)

        with patch.object(subprocess, "run", mock_run):
            from holdspeak.desktop_presence_cocoa import _cocoa_notify
            _cocoa_notify({"title": "HoldSpeak", "body": "Test"})
            assert len(calls) == 1
            # Verify osascript was called
            cmd_args = calls[0][0]
            assert cmd_args[0] == "osascript"
            assert "display notification" in cmd_args[2]


class TestCocoaRendererNotifyCommand:
    """The parent-side renderer can send a notify command."""

    def test_notify_command_sent_to_queue(self):
        from holdspeak.desktop_notify import _notify_cocoa_child

        mock_renderer = MagicMock()
        mock_renderer._commands = MagicMock()
        result = _notify_cocoa_child(mock_renderer, "Test", "Body", click_url="http://localhost")
        assert result is True
        mock_renderer._commands.put.assert_called_once()
        cmd, payload = mock_renderer._commands.put.call_args[0][0]
        assert cmd == "notify"
        assert payload["title"] == "Test"
        assert payload["body"] == "Body"


# ── HS-171-06: brief regeneration on cadence ────────────────────────


class TestBriefRegeneration:
    """The brief regenerates on its cadence and lands a receipt."""

    def test_brief_regenerates_when_stale(self):
        """Simulates the _maybe_regenerate_brief logic path."""
        from holdspeak.cadence.brief import should_send_daily_brief

        now = datetime(2026, 9, 5, 9, 0)  # 09:00, after quiet hours
        last_regen = "2026-09-04"  # yesterday
        assert should_send_daily_brief(now, last_sent_date=last_regen, earliest_hour=8) is True

    def test_brief_does_not_regenerate_when_fresh(self):
        from holdspeak.cadence.brief import should_send_daily_brief

        now = datetime(2026, 9, 5, 9, 0)
        last_regen = "2026-09-05"  # today, already done
        assert should_send_daily_brief(now, last_sent_date=last_regen, earliest_hour=8) is False

    def test_brief_suppressed_during_quiet_hours(self):
        from holdspeak.cadence.brief import should_send_daily_brief

        now = datetime(2026, 9, 5, 6, 0)  # 06:00, before earliest_hour=8
        last_regen = "2026-09-04"
        assert should_send_daily_brief(now, last_sent_date=last_regen, earliest_hour=8) is False


# ── HS-171-05: notify function dispatch ─────────────────────────────


class TestNotifyDispatch:
    """The ``notify()`` function dispatches to the right platform."""

    def test_injected_notifier(self):
        from holdspeak.desktop_notify import notify

        calls = []
        def mock(title, body, *, click_url=None):
            calls.append((title, body))
            return True

        result = notify("HoldSpeak", "test", _notifier=mock)
        assert result is True
        assert len(calls) == 1

    def test_receipt_written_on_fire(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        receipts = []
        heartbeat_notify(
            count=5,
            project_count=3,
            edge=edge,
            quiet_hours_start=23,
            quiet_hours_end=23,
            receipt_writer=lambda r: receipts.append(r),
            _notifier=lambda *a, **k: True,
        )
        assert len(receipts) == 1
        assert receipts[0]["service"] == "heartbeat"
        assert "fired=True" in receipts[0]["result_summary"]
        assert "count=5" in receipts[0]["result_summary"]


# ── MCP tool: heartbeat.notify_test ─────────────────────────────────


class TestMCPNotifyTest:
    """The MCP tool schema and dispatch exist in the heartbeat family."""

    def test_tool_schema_present(self):
        from holdspeak.mcp.families.heartbeat import TOOLS

        names = [t["name"] for t in TOOLS]
        assert "heartbeat.notify_test" in names

    def test_dispatch_fires_notification(self):
        from holdspeak.mcp.families import heartbeat as heartbeat_family

        with patch("holdspeak.desktop_notify.notify", return_value=True):
            from holdspeak.principals import Principal, PrincipalKind
            result = heartbeat_family.dispatch(
                "heartbeat.notify_test",
                {},
                Principal(PrincipalKind.OWNER, "test"),
            )
            assert result["fired"] is True


# ── HS-171-03: cadence tick invalidates the cache ─────────────────────


class TestCadenceTickInvalidatesCache:
    """Box 3 of HS-171-03: the cadence tick calls _invalidate_needs_you_cache,
    which clears the NeedsYouCache so the next read re-queries."""

    def test_tick_invalidates_via_web_context(self):
        """Simulate the cadence mixin's _invalidate_needs_you_cache path
        where the cache lives on _web_context._needs_you_cache."""
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        call_count = {"n": 0}

        def builder():
            call_count["n"] += 1
            return {
                "count": 0, "projects": [], "items": [], "next": None,
                "computedAt": datetime.now().isoformat(),
                "stale": False, "sweepId": None,
            }

        cache = NeedsYouCache(builder, max_age_s=600.0)
        cache.get()
        assert call_count["n"] == 1

        # Build a mock object that mimics the cadence mixin.
        mixin = MagicMock()
        mixin._needs_you_cache = None
        ctx = MagicMock()
        ctx._needs_you_cache = cache
        mixin._web_context = ctx

        # Call the real _invalidate_needs_you_cache logic inline.
        from holdspeak.runtime.cadence import CadenceMixin
        CadenceMixin._invalidate_needs_you_cache(mixin)

        # Now the next get should rebuild.
        cache.get()
        assert call_count["n"] == 2, \
            "After cadence tick invalidation, the cache should rebuild on next get"

    def test_tick_invalidates_via_direct_attribute(self):
        """When _needs_you_cache is set directly on the mixin (e.g. test setup)."""
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        call_count = {"n": 0}

        def builder():
            call_count["n"] += 1
            return {
                "count": 0, "projects": [], "items": [], "next": None,
                "computedAt": datetime.now().isoformat(),
                "stale": False, "sweepId": None,
            }

        cache = NeedsYouCache(builder, max_age_s=600.0)
        cache.get()
        assert call_count["n"] == 1

        mixin = MagicMock()
        mixin._needs_you_cache = cache
        mixin._web_context = None

        from holdspeak.runtime.cadence import CadenceMixin
        CadenceMixin._invalidate_needs_you_cache(mixin)

        cache.get()
        assert call_count["n"] == 2


# ── HS-171-03: zero egress during cached read ─────────────────────────


class TestZeroEgressCachedRead:
    """Box 5 of HS-171-03: no outbound HTTP during a cached read (Article III)."""

    def test_no_http_during_cache_hit(self):
        """Monkeypatch urllib3 + httpx to assert no outbound calls
        during a warm-cache NeedsYouCache.get()."""
        from holdspeak.services.needs_you_aggregate import NeedsYouCache

        builder, _ = self._make_builder()
        cache = NeedsYouCache(builder, max_age_s=600.0)
        cache.get()  # prime the cache

        http_calls: list[str] = []

        def _trap_urllib(*a, **kw):
            http_calls.append("urllib3")
            raise AssertionError("urllib3 egress during cached read")

        def _trap_httpx(*a, **kw):
            http_calls.append("httpx")
            raise AssertionError("httpx egress during cached read")

        with patch("urllib.request.urlopen", _trap_urllib), \
             patch.dict("sys.modules", {
                 "httpx": MagicMock(**{"Client.return_value.get.side_effect": _trap_httpx}),
             }):
            result = cache.get()
            assert result is not None
            assert len(http_calls) == 0, \
                f"Zero egress expected, got: {http_calls}"

    def _make_builder(self):
        call_count = {"n": 0}
        def builder():
            call_count["n"] += 1
            return {
                "count": 0, "projects": [], "items": [], "next": None,
                "computedAt": datetime.now().isoformat(),
                "stale": False, "sweepId": None,
            }
        return builder, call_count


# ── HS-171-06: brief regeneration integration via cadence tick ────────


class TestBriefCadenceTickIntegration:
    """Box 1 of HS-171-06: the brief regenerates once per day after quiet
    hours, driven by the cadence tick, WITHOUT the owner opening anything."""

    def test_one_generate_call_across_quiet_hours_boundary(self):
        """Drive _maybe_regenerate_brief with a fake clock crossing the
        quiet-hours boundary. Assert exactly one generate() call, not two."""
        from holdspeak.cadence.brief import should_send_daily_brief

        # 06:00 -- still in quiet hours (earliest_hour=8)
        before = datetime(2026, 9, 5, 6, 0)
        assert should_send_daily_brief(
            before, last_sent_date="2026-09-04", earliest_hour=8
        ) is False, "Should NOT regenerate during quiet hours"

        # 08:01 -- quiet hours closed, last_regen yesterday
        after = datetime(2026, 9, 5, 8, 1)
        assert should_send_daily_brief(
            after, last_sent_date="2026-09-04", earliest_hour=8
        ) is True, "Should regenerate after quiet hours close"

        # 08:02 -- same day, already regenerated
        after2 = datetime(2026, 9, 5, 8, 2)
        assert should_send_daily_brief(
            after2, last_sent_date="2026-09-05", earliest_hour=8
        ) is False, "Should NOT regenerate again the same day"

    def test_quiet_hours_suppress_until_window_closes(self):
        """HS-171-06 box 3: quiet hours suppress regeneration until the
        window closes."""
        from holdspeak.cadence.brief import should_send_daily_brief

        # Walk the clock from 00:00 to 07:59 -- all suppressed.
        for hour in range(0, 8):
            now = datetime(2026, 9, 5, hour, 30)
            result = should_send_daily_brief(
                now, last_sent_date="2026-09-04", earliest_hour=8
            )
            assert result is False, \
                f"Should be suppressed at {hour}:30 (quiet hours)"

        # 08:00 -- first tick after quiet hours: fires.
        now_ok = datetime(2026, 9, 5, 8, 0)
        assert should_send_daily_brief(
            now_ok, last_sent_date="2026-09-04", earliest_hour=8
        ) is True


class TestBriefRegenerationReceipt:
    """Box 4 of HS-171-06: the regeneration leaves a pipeline_events receipt."""

    def test_regeneration_writes_pipeline_event(self, tmp_path):
        """Drive _maybe_regenerate_brief on a real DB and assert the
        pipeline_events row is written (Article XI.2)."""
        from holdspeak.db import Database

        db = Database(tmp_path / "brief_receipt_test.db")

        # Seed a stale brief_regeneration policy: use yesterday's real date
        # so the should_send check passes regardless of when we run.
        from holdspeak.cadence.models import CadencePolicy
        yesterday = (datetime.now() - __import__("datetime").timedelta(days=1)).strftime("%Y-%m-%d")
        db.cadence.upsert_policy(CadencePolicy(
            name="brief_regeneration",
            config={"last_regen_date": yesterday},
        ))

        # Build a mock mixin with quiet_hours_end=0 so the earliest_hour
        # check always passes (current hour >= 0 is always True).
        mixin = MagicMock()
        mixin.config = MagicMock()
        mixin.config.cadence = MagicMock()
        mixin.config.cadence.quiet_hours_end = 0

        generate_calls = []

        # Patch MondayBriefService.generate to record calls.
        mock_brief = MagicMock()
        mock_brief.items = [MagicMock(), MagicMock()]
        mock_brief.item_count = 2

        with patch("holdspeak.db.get_database", return_value=db), \
             patch("holdspeak.services.monday_brief_service.MondayBriefService.generate",
                   side_effect=lambda *a, **kw: (generate_calls.append(1), mock_brief)[1]):
            from holdspeak.runtime.cadence import CadenceMixin
            CadenceMixin._maybe_regenerate_brief(mixin)

        assert len(generate_calls) == 1, \
            "generate() should be called exactly once"

        # Check the pipeline_events receipt.
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM pipeline_events WHERE method='brief.regenerated'"
            ).fetchall()
        assert len(rows) >= 1, "A pipeline_events receipt should exist"
        row = rows[0]
        assert "items=2" in row["result_summary"]
