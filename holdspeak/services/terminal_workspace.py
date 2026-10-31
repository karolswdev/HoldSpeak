"""Terminal inventory over the existing tmux and agent-session boundaries.

The inventory is deliberately a projection, not a second session registry:
tmux is the live producer, the hook registry supplies optional agent state, and
``TerminalTargetRegistry`` supplies the immutable command/read target. The
stable session id is a hash of the target fingerprint, so a pane process or
tmux server restart cannot silently restore the old window onto a successor.
"""

from __future__ import annotations

import hashlib
from typing import Any, Callable, Iterable, Mapping, Optional

from .. import coder_steering
from ..coder_steering import Runner
from ..delivery.terminal import TerminalTargetRegistry


PaneLoader = Callable[[], Mapping[str, Any]]
SessionLoader = Callable[[], Iterable[Any]]


def _hook_state(session: Any) -> str:
    """Use the agent registry's age decay when a real session has a stamp.

    Small injected fixtures often omit ``updated_at``; those retain their
    explicit lifecycle for compatibility. Real ``AgentSession`` records use
    the existing idle/dead policy so an old record cannot claim a recycled
    pane forever.
    """
    lifecycle = str(getattr(session, "lifecycle", "") or "").strip().lower()
    if not getattr(session, "updated_at", None):
        return lifecycle or "live"
    try:
        from ..agent_context import effective_state

        return str(effective_state(session) or lifecycle or "live")
    except Exception:
        return lifecycle or "live"


def _stable_id(fingerprint: str, pane_id: str) -> str:
    """Return an opaque, URL/window-id-safe inventory identity."""
    seed = fingerprint or f"legacy:{pane_id}"
    digest = hashlib.sha256(seed.encode("utf-8", "replace")).hexdigest()
    return f"terminal_{digest[:32]}"


def _hook_pane(session: Any) -> Optional[str]:
    pane = getattr(session, "tmux_pane", None)
    if pane:
        return str(pane)
    name = getattr(session, "tmux_session", None)
    window = getattr(session, "tmux_window", None)
    index = getattr(session, "tmux_pane_index", None)
    if name and window is not None and index is not None:
        return f"{name}:{window}.{index}"
    return None


def _matches_hook(pane: Mapping[str, Any], session: Any) -> bool:
    def present(value: Any) -> bool:
        return value is not None and str(value) != ""

    pane_id = str(pane.get("pane_id") or "")
    hook_pane = _hook_pane(session)
    hook_session = getattr(session, "tmux_session", None)
    hook_window = getattr(session, "tmux_window", None)
    hook_index = getattr(session, "tmux_pane_index", None)
    pane_session = pane.get("session")
    pane_window = pane.get("window")
    pane_index = pane.get("pane_index")
    supplied_coordinates = any(
        present(value)
        for value in (hook_session, hook_window, hook_index)
    )
    coordinates_match = (
        (not present(hook_session) or (present(pane_session) and str(hook_session) == str(pane_session)))
        and (not present(hook_window) or (present(pane_window) and str(hook_window) == str(pane_window)))
        and (not present(hook_index) or (present(pane_index) and str(hook_index) == str(pane_index)))
    )
    complete_coordinates = all(
        present(value)
        for value in (hook_session, hook_window, hook_index, pane_session, pane_window, pane_index)
    )
    if hook_pane:
        # An exact pane id is useful, but any available positional metadata
        # must agree with it. This rejects a stale hook payload after `%N`
        # reuse without requiring a new hook-schema process fingerprint.
        if hook_pane == pane_id:
            return not supplied_coordinates or coordinates_match
        if hook_pane == f"{pane_session}:{pane_window}.{pane_index}":
            return coordinates_match and complete_coordinates
        return False
    return coordinates_match and complete_coordinates


def _best_hook(pane: Mapping[str, Any], hooks: Iterable[Any]) -> Optional[Any]:
    matches = [
        candidate
        for candidate in hooks
        if _hook_state(candidate) != "ended"
        and _matches_hook(pane, candidate)
    ]
    if not matches:
        return None
    # The registry is normally newest-first, but make that an explicit
    # invariant so a stale historical record cannot win by list order.
    return max(matches, key=lambda item: str(getattr(item, "updated_at", "") or ""))


class TerminalWorkspaceService:
    """Build the native Terminals inventory from live local producers."""

    def __init__(
        self,
        targets: TerminalTargetRegistry,
        *,
        local_node_id: str = "local",
        runner: Optional[Runner] = None,
        pane_loader: Optional[PaneLoader] = None,
        session_loader: Optional[SessionLoader] = None,
        context: Any = None,
    ) -> None:
        self.targets = targets
        self.local_node_id = str(local_node_id or "local")
        self.runner = runner
        self._pane_loader = pane_loader or (
            lambda: coder_steering.list_panes(runner=self.runner)
        )
        self._session_loader = session_loader or self._default_sessions
        self._context = context

    @staticmethod
    def _default_sessions() -> list[Any]:
        try:
            from ..agent_context import list_agent_sessions

            return list_agent_sessions()
        except Exception:
            # Hook correlation is optional. A failing registry must not hide
            # live shells from the owner.
            return []

    def discover(self) -> dict[str, Any]:
        """Return the exact ``/sessions`` projection used by the Desk."""
        try:
            listed = dict(self._pane_loader() or {})
        except Exception as exc:
            return {"status": "error", "detail": str(exc), "sessions": []}
        status = str(listed.get("status") or "ok")
        if status != "ok":
            return {
                "status": status,
                **({"detail": listed["detail"]} if listed.get("detail") else {}),
                "sessions": [],
            }

        try:
            hooks = list(self._session_loader() or [])
        except Exception:
            hooks = []

        # The connected context is one composed read for this inventory.  A
        # failed context read is represented on each row; it never hides a
        # live pane from the owner.
        context_snapshot = None
        if self._context is not None:
            try:
                context_snapshot = self._context.snapshot()
            except Exception:
                context_snapshot = None

        rows: list[dict[str, Any]] = []
        for raw_pane in listed.get("panes") or []:
            if not isinstance(raw_pane, Mapping):
                continue
            pane = dict(raw_pane)
            pane_id = str(pane.get("pane_id") or "")
            if not pane_id.startswith("%"):
                continue
            issued = self.targets.issue(f"pane:{pane_id}")
            if issued.get("status") != "issued":
                continue
            hook = _best_hook(pane, hooks)
            if hook is None:
                key = f"pane:{pane_id}"
                agent = "pane"
                state = "live"
                session_name = str(pane.get("session") or pane_id)
                slot = f"{pane.get('window')}.{pane.get('pane_index')}"
                label = f"{session_name}:{slot}" if pane.get("pane_index") is not None else session_name
            else:
                agent_name = str(getattr(hook, "agent", "") or "agent")
                session_id = str(getattr(hook, "session_id", "") or pane_id)
                key = f"{agent_name}:{session_id}"
                agent = agent_name
                state = _hook_state(hook)
                project = str(getattr(hook, "project_name", "") or "")
                session_name = str(pane.get("session") or session_id)
                slot = f"{pane.get('window')}.{pane.get('pane_index')}"
                session_label = f"{session_name}:{slot}" if pane.get("pane_index") is not None else session_name
                label = " · ".join(
                    part for part in (agent_name, project, session_label) if part
                )
            # The target registry resolved this identity immediately before
            # issuing the handle. Prefer it over the inventory snapshot, which
            # may have raced a pane respawn.
            fingerprint = str(
                issued.get("fingerprint") or pane.get("fingerprint") or ""
            )
            row = {
                "id": _stable_id(fingerprint, pane_id),
                "label": label,
                "session": str(pane.get("session") or ""),
                "key": key,
                "agent": agent,
                "command": str(pane.get("command") or ""),
                "current_path": str(
                    pane.get("current_path")
                    or getattr(hook, "tmux_pane_current_path", None)
                    or getattr(hook, "cwd", None)
                    or ""
                ),
                "state": state,
                "target": {
                    "node_id": self.local_node_id,
                    "target_id": issued["target_id"],
                    "target_generation": issued["target_generation"],
                },
                "pane_id": issued["pane_id"],
            }
            if self._context is not None:
                try:
                    row["context"] = self._context.for_terminal(
                        snapshot=context_snapshot,
                        issued=issued,
                        current_path=row["current_path"],
                        verify=self.targets.verify,
                    )
                except Exception:
                    # Context is additive.  A broken ledger, registry or DB
                    # read must never make a terminal disappear.
                    row["context"] = {
                        "status": "unavailable",
                        "project": None,
                        "source": None,
                        "worktree": None,
                        "launch": None,
                        "program": None,
                        "mcp": None,
                    }
            rows.append(row)
        return {"status": "ok", "sessions": rows}


__all__ = ["TerminalWorkspaceService"]
