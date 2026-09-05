"""Cross-platform desktop notification dispatcher (HS-171-05).

``notify(title, body, *, click_url) -> bool``

macOS: posts via ``osascript -e 'display notification …'`` because
``UserNotifications`` (the UNUserNotificationCenter pyobjc bridge) is
NOT available in the venv -- verified by
``python -c "import UserNotifications"`` which raises ModuleNotFoundError.
The osascript fallback is the ONLY mechanism.

Linux: delegates to the existing ``_LibnotifyNotifier`` seam in
``desktop_presence_freedesktop.py``.

Both paths honour quiet hours and fire only on the EDGE of the needs-you
count (count rises above the last notified count).  Every notification
writes a pipeline_events receipt (``heartbeat.notify``).
"""
from __future__ import annotations

import logging
import platform
import subprocess
import time
from typing import Any, Callable

from .cadence.scheduler import in_quiet_hours

log = logging.getLogger(__name__)


# ── Edge detector ────────────────────────────────────────────────────


class EdgeDetector:
    """Fire only when the count rises above the last notified level.

    Tracks ``last_notified_count`` in memory.  A persisted seed can be
    passed via ``initial_count`` so a restart does not re-notify the
    same count (the heartbeat settings row stores the last-notified
    count across process lifetimes).
    """

    def __init__(self, *, initial_count: int = 0) -> None:
        self._last: int = initial_count

    def should_fire(self, count: int) -> bool:
        """True when count > last_notified_count (a rising edge)."""
        if count > self._last:
            return True
        return False

    def mark_fired(self, count: int) -> None:
        self._last = count

    @property
    def last_notified_count(self) -> int:
        return self._last


# ── macOS notifier (osascript fallback) ──────────────────────────────


def _notify_macos(title: str, body: str, *, click_url: str | None = None) -> bool:
    """Post a macOS notification via osascript.

    UNUserNotificationCenter is NOT available in the venv (the PyObjC
    ``UserNotifications`` framework bridge is not installed).  The
    ``osascript`` path is the fallback named in the design.
    """
    # Escape double-quotes in the body/title for AppleScript string safety.
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    script = f'display notification "{safe_body}" with title "{safe_title}"'
    try:
        subprocess.run(
            ["osascript", "-e", script],
            timeout=5,
            capture_output=True,
            check=False,
        )
        return True
    except Exception as exc:
        log.warning("osascript notification failed: %s", exc)
        return False


# ── Linux notifier (libnotify seam) ──────────────────────────────────


def _notify_linux(title: str, body: str, *, click_url: str | None = None) -> bool:
    """Post a Linux notification via the existing libnotify seam."""
    try:
        from .desktop_presence_freedesktop import _LibnotifyNotifier

        notifier = _LibnotifyNotifier()
        notifier.notify({
            "summary": title,
            "body": body,
            "icon": "dialog-information",
            "urgency": 1,
            "transient": True,
        })
        return True
    except Exception as exc:
        log.warning("libnotify notification failed: %s", exc)
        return False


# ── Cocoa child IPC (extend the existing command queue) ──────────────


def _notify_cocoa_child(
    renderer: Any,
    title: str,
    body: str,
    *,
    click_url: str | None = None,
) -> bool:
    """Send a ``notify`` command over the Cocoa child's IPC queue.

    The child process (desktop_presence_cocoa.py) is extended to handle
    a ``notify`` command that posts via osascript from inside the AppKit
    runloop.
    """
    if renderer is None:
        return False
    try:
        commands = getattr(renderer, "_commands", None)
        if commands is None:
            return False
        commands.put(("notify", {"title": title, "body": body, "click_url": click_url}))
        return True
    except Exception as exc:
        log.warning("Cocoa child notify command failed: %s", exc)
        return False


# ── The public API ───────────────────────────────────────────────────


_PLATFORM = platform.system()


def notify(
    title: str,
    body: str,
    *,
    click_url: str | None = None,
    _notifier: Callable[..., bool] | None = None,
) -> bool:
    """Post a desktop notification.  Returns True on success.

    The ``_notifier`` parameter is for testing (inject a mock).
    """
    if _notifier is not None:
        return _notifier(title, body, click_url=click_url)
    if _PLATFORM == "Darwin":
        return _notify_macos(title, body, click_url=click_url)
    if _PLATFORM == "Linux":
        return _notify_linux(title, body, click_url=click_url)
    log.info("Desktop notifications not supported on %s", _PLATFORM)
    return False


def heartbeat_notify(
    count: int,
    project_count: int,
    *,
    edge: EdgeDetector,
    quiet_hours_start: int = 22,
    quiet_hours_end: int = 8,
    content_items: list[dict[str, Any]] | None = None,
    notify_content: bool = False,
    click_url: str | None = None,
    receipt_writer: Callable[[dict[str, Any]], None] | None = None,
    _notifier: Callable[..., bool] | None = None,
) -> dict[str, Any]:
    """Evaluate the edge rule, quiet hours, and fire if appropriate.

    Returns a receipt dict (always), with ``fired``, ``held``,
    ``reason``, and the count.
    """
    from datetime import datetime

    now = datetime.now()
    result: dict[str, Any] = {
        "count": count,
        "projectCount": project_count,
        "fired": False,
        "held": False,
        "reason": "",
        "timestamp": now.isoformat(),
    }

    # Edge check first.
    if not edge.should_fire(count):
        result["reason"] = "no_edge"
        return result

    # Quiet hours check.
    if in_quiet_hours(now, quiet_hours_start, quiet_hours_end):
        result["held"] = True
        result["reason"] = "quiet_hours"
        if receipt_writer:
            receipt_writer({
                "service": "heartbeat",
                "method": "notify",
                "result_summary": f"held:quiet_hours count={count}",
            })
        return result

    # Build body.
    if project_count > 1:
        body = f"{count} need you across {project_count} projects"
    else:
        body = f"{count} need you"

    if notify_content and content_items:
        # First WHY per project, max 3 lines.
        seen_projects: set[str] = set()
        lines: list[str] = []
        for item in content_items:
            pid = item.get("projectId", "")
            if pid in seen_projects:
                continue
            seen_projects.add(pid)
            pname = item.get("projectName", "")
            why = item.get("why", "")
            if pname and why:
                lines.append(f"{pname}: {why}")
            if len(lines) >= 3:
                break
        if lines:
            body = body + " -- " + "; ".join(lines)

    fired = notify("HoldSpeak", body, click_url=click_url, _notifier=_notifier)
    if fired:
        edge.mark_fired(count)
    result["fired"] = fired
    result["reason"] = "fired" if fired else "dispatch_failed"

    if receipt_writer:
        receipt_writer({
            "service": "heartbeat",
            "method": "notify",
            "result_summary": f"fired={fired} count={count} projects={project_count}",
        })

    return result


__all__ = [
    "notify",
    "heartbeat_notify",
    "EdgeDetector",
]
