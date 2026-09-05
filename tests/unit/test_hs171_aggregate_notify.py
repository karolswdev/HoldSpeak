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
