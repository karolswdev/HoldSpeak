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
from typing import Any, Callable, Iterable, Mapping

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


class ItemSetEdge:
    """HS-200-15 (AC4): fire on a changed ITEM SET, never on a changed count.

    The audit found the count edge can miss a new item when the total
    stays unchanged (one item resolved, another arrived: 3 -> 3, silent).
    This detector remembers WHICH items have been notified -- the stable
    ``_item_id`` -> ``{"project": <project id>, "class": <rank class>}``
    -- and fires when any current item is new, or when a known item has
    ESCALATED (any class -> ``due_today`` or ``overdue``, or ``due_today``
    -> ``overdue``; counsel P1-4).

    The explicit transitions (D2(b) "Notifications"):

    * **changed item, same count** -- a new id is present: fire.
    * **escalation, same id** -- the class rose into due today / overdue:
      fire, and say ``N escalated``.
    * **quiet hours** -- the caller holds and does NOT mark, so the new
      ids stay new and are delivered ONCE on the first sweep after the
      window; a sweep inside the window never marks them delivered.
    * **mute** -- muted items are not offered to ``should_fire``; their
      ids are not pruned while the item still exists (``present``
      includes muted ids), so un-muting re-notifies only what arrived
      while the Room was muted, never what was already notified.
    * **restart** -- the caller persists ``notified`` and seeds a fresh
      detector from it, so a restart re-notifies nothing.
    * **recovery** -- ``prune`` keeps an absent id whose Project is
      KNOWN but not fully observed (a source ``cant_check`` / stale /
      failed), so the source coming back re-notifies nothing; it drops
      an absent id whose Project was fully observed, whose Project no
      longer exists (archived / deleted), or which has no Project and
      is simply gone (a resolved Door card) -- counsel P1-3.  An empty
      set over a failed source is never an all-clear (the caller reports
      ``held_coverage_incomplete``).
    """

    ESCALATED = ("due_today", "overdue")

    def __init__(self, *, notified: Mapping[str, Any] | Iterable[str] | None = None) -> None:
        self._notified: dict[str, dict[str, str]] = {}
        if isinstance(notified, Mapping):
            for key, value in notified.items():
                self._notified[str(key)] = _entry(value)
        elif notified:
            for key in notified:
                self._notified[str(key)] = _entry("")

    @staticmethod
    def _rank(cls: str) -> int:
        return {"overdue": 2, "due_today": 1}.get(cls, 0)

    def new_ids(self, current: Mapping[str, Any]) -> list[str]:
        """The current ids not yet notified, sorted (deterministic)."""
        return sorted(str(k) for k in current if str(k) not in self._notified)

    def escalated_ids(self, current: Mapping[str, Any]) -> list[str]:
        """Known ids whose class rose into due today / overdue since they
        were notified, sorted."""
        out: list[str] = []
        for key, value in current.items():
            known = self._notified.get(str(key))
            if known is None:
                continue
            if self._rank(_entry(value)["class"]) > self._rank(known["class"]):
                out.append(str(key))
        return sorted(out)

    def should_fire(self, current: Mapping[str, Any]) -> bool:
        return bool(self.new_ids(current) or self.escalated_ids(current))

    def mark_fired(self, current: Mapping[str, Any]) -> None:
        for key, value in current.items():
            self._notified[str(key)] = _entry(value)

    def prune(
        self,
        present: Iterable[str],
        observed_projects: Iterable[str] | None = None,
        known_projects: Iterable[str] | None = None,
    ) -> None:
        """Forget ids that are gone -- unless their Project is known but
        was not fully observed.  ``observed_projects=None`` means every
        Project was observed (no coverage on the wire); ``known_projects``
        defaults to the observed set."""
        keep = {str(k) for k in present}
        observed = None if observed_projects is None else {str(p) for p in observed_projects}
        known = observed if known_projects is None else {str(p) for p in known_projects}
        for key in list(self._notified):
            if key in keep:
                continue
            project = self._notified[key]["project"]
            if observed is None or not project:
                del self._notified[key]
            elif project in observed or project not in (known or set()):
                del self._notified[key]

    @property
    def notified(self) -> dict[str, dict[str, str]]:
        return {k: dict(v) for k, v in self._notified.items()}


def _entry(value: Any) -> dict[str, str]:
    """One notified-set entry: ``{"project", "class"}`` from a mapping, a
    bare project id (the older persisted shape), or nothing."""
    if isinstance(value, Mapping):
        return {
            "project": str(value.get("project") or value.get("projectId") or ""),
            "class": str(value.get("class") or value.get("rankClass") or ""),
        }
    return {"project": str(value or ""), "class": ""}


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
    edge: EdgeDetector | ItemSetEdge,
    item_ids: Mapping[str, str] | None = None,
    quiet_hours_start: int = 22,
    quiet_hours_end: int = 8,
    content_items: list[dict[str, Any]] | None = None,
    notify_content: bool = False,
    click_url: str | None = None,
    receipt_writer: Callable[[dict[str, Any]], None] | None = None,
    mesh_event_writer: Callable[[dict[str, Any]], None] | None = None,
    _notifier: Callable[..., bool] | None = None,
    now: Any | None = None,
) -> dict[str, Any]:
    """Evaluate the edge rule, quiet hours, and fire if appropriate.

    Returns a receipt dict (always), with ``fired``, ``held``,
    ``reason``, and the count.

    HS-200-15 (AC4): with an ``ItemSetEdge`` and ``item_ids`` (the
    current unmuted ids -> Project), the edge is the ITEM SET -- a new
    id fires even when the count is unchanged, and ``newItems`` says how
    many were new.  A count-based ``EdgeDetector`` is still honoured for
    callers that have no ids.  A held notification never marks the ids
    delivered, so quiet hours hold and then deliver once.

    HS-174-09: when ``mesh_event_writer`` is provided and a notification
    fires, publish a ``desk.notification`` event on the mesh bus with
    ``{count, projects, origin}`` for a future LAN companion (Phase 179).
    The caller gates this on the mesh-on setting.
    """
    from datetime import datetime

    # The instant is the CALLER's (the heartbeat's injectable local clock);
    # the wall clock is only for callers that pass none.
    now = now or datetime.now()
    set_based = isinstance(edge, ItemSetEdge) and item_ids is not None
    new_ids = edge.new_ids(item_ids) if set_based else []  # type: ignore[union-attr]
    escalated = edge.escalated_ids(item_ids) if set_based else []  # type: ignore[union-attr]
    result: dict[str, Any] = {
        "count": count,
        "projectCount": project_count,
        "fired": False,
        "held": False,
        "reason": "",
        "newItems": len(new_ids),
        "escalatedItems": len(escalated),
        "timestamp": now.isoformat(),
    }

    # Edge check first.
    if set_based:
        if not new_ids and not escalated:
            result["reason"] = "no_edge"
            return result
    elif not edge.should_fire(count):
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
    # HS-200-15: a notification whose total did not move says what moved.
    if set_based:
        moved: list[str] = []
        if 0 < len(new_ids) < count:
            moved.append(f"{len(new_ids)} new")
        if escalated:
            moved.append(f"{len(escalated)} escalated")
        if moved:
            body = f"{body} · " + " · ".join(moved)

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
        if set_based:
            edge.mark_fired(item_ids)  # type: ignore[union-attr]
        else:
            edge.mark_fired(count)  # type: ignore[union-attr]
    result["fired"] = fired
    result["reason"] = "fired" if fired else "dispatch_failed"

    if receipt_writer:
        receipt_writer({
            "service": "heartbeat",
            "method": "notify",
            "result_summary": f"fired={fired} count={count} projects={project_count}",
        })

    # HS-174-09: publish desk.notification on the mesh bus for a future
    # LAN companion (Phase 179).  Hub side only -- no new listener, no
    # new egress.  The caller gates this on the mesh-on setting.
    if fired and mesh_event_writer is not None:
        try:
            mesh_event_writer({
                "kind": "desk.notification",
                "count": count,
                "projects": project_count,
                "origin": "heartbeat",
            })
        except Exception as exc:
            log.warning("mesh desk.notification event failed: %s", exc)

    return result


__all__ = [
    "notify",
    "heartbeat_notify",
    "EdgeDetector",
    "ItemSetEdge",
]
