"""Polling adapter for HoldSpeak's `/api/companion/status` endpoint."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from bridge.companion_state import (
    CompanionSignals,
    CompanionState,
    LcdPlan,
    build_lcd_plan,
)
from bridge.settings import Settings

AGENT_QUESTION_LCD_MAX_CHARS = 96
AGENT_QUESTION_LCD_WINDOW_CHARS = 76
COMPANION_HTTP_TIMEOUT_S = 3.0


class CompanionStatusPoller:
    """Poll HoldSpeak companion status and paint agent attention.

    The existing WebSocket status path still owns bottom activity and transcript
    flashes. This poller only takes over the middle zone while a fresh agent
    question is waiting, and clears only the agent text it previously painted.
    """

    def __init__(
        self,
        settings: Settings,
        log: Any,
        *,
        on_middle_update: Callable[[str], Awaitable[None]],
    ) -> None:
        self.settings = settings
        self.log = log.bind(component="companion_status")
        self.on_middle_update = on_middle_update
        self._url = (
            f"http://{settings.holdspeak_host}:{settings.holdspeak_port}"
            "/api/companion/status"
        )
        self._last_agent_middle: str | None = None
        self._last_agent_key: str | None = None
        self._agent_question_page = 0
        self._force_repaint = False
        self._last_plan: LcdPlan | None = None
        self._middle_hold_until = 0.0

    def force_repaint(self) -> None:
        """Ask the next successful poll to repaint active agent state."""

        self._force_repaint = True

    def hold_middle_for(self, ttl_ms: int) -> None:
        """Defer companion middle paints while an external flash is visible."""

        if ttl_ms <= 0:
            return
        deadline = time.monotonic() + (ttl_ms / 1000.0)
        self._middle_hold_until = max(self._middle_hold_until, deadline)
        self._force_repaint = True

    async def run(self) -> None:
        interval = max(0.5, float(self.settings.companion_poll_interval_s))
        while True:
            await self.poll_once()
            await asyncio.sleep(interval)

    async def poll_once(self) -> LcdPlan | None:
        try:
            payload = await fetch_companion_status(self._url)
        except Exception as exc:
            self.log.debug(
                "companion.status.fetch_error",
                error=type(exc).__name__,
                error_msg=str(exc)[:200],
            )
            return None

        agent_key = _agent_display_key(payload)
        if agent_key != self._last_agent_key:
            self._last_agent_key = agent_key
            self._agent_question_page = 0

        signals = companion_signals_from_status(
            payload,
            question_page=self._agent_question_page,
        )
        plan = build_lcd_plan(signals)
        self._last_plan = plan
        target = _agent_middle_text(plan)
        middle_held = time.monotonic() < self._middle_hold_until

        if target is None:
            if middle_held:
                return plan
            if self._last_agent_middle is not None:
                await self.on_middle_update("")
                self._last_agent_middle = None
            self._last_agent_key = None
            self._agent_question_page = 0
            self._force_repaint = False
            return plan

        if middle_held:
            self._agent_question_page += 1
            return plan

        if self._force_repaint or target != self._last_agent_middle:
            await self.on_middle_update(target)
            self._last_agent_middle = target
        self._agent_question_page += 1
        self._force_repaint = False
        return plan

    def is_agent_waiting(self) -> bool:
        """Return true when the latest companion snapshot is replyable."""

        return bool(
            self._last_plan
            and self._last_plan.primary_state == CompanionState.AGENT_WAITING
        )


async def fetch_companion_status(url: str) -> dict[str, Any]:
    """Fetch and decode one companion status payload."""

    return await asyncio.to_thread(_fetch_companion_status_sync, url)


def companion_signals_from_status(
    payload: dict[str, Any],
    *,
    now: datetime | None = None,
    question_page: int = 0,
) -> CompanionSignals:
    """Adapt HoldSpeak's companion status JSON into bridge state signals."""

    now = now or datetime.now(timezone.utc)
    runtime = _dict(payload.get("runtime"))
    agent = _dict(payload.get("agent"))
    session = _dict(agent.get("session"))
    identity = _dict(agent.get("identity"))
    awaiting = bool(agent.get("awaiting_response"))
    question = _compact(str(session.get("last_assistant_text") or ""))
    agent_label = _agent_identity_label(session, identity=identity)
    agent_age_s = _agent_age_seconds(session, now=now)
    voice_state = str(runtime.get("voice_state") or "").strip().lower()

    return CompanionSignals(
        connected=True,
        meeting_recording=bool(runtime.get("meeting_active")),
        agent_waiting=awaiting and bool(question),
        agent_label=agent_label,
        agent_question=_window_question(question, page=question_page),
        agent_age_s=agent_age_s,
        reply_capture=voice_state in {"listening", "recording", "capturing"},
        transcribing=voice_state in {"transcribing", "rewriting", "inserting"},
        error_text=str(agent.get("error") or ""),
    )


def _agent_middle_text(plan: LcdPlan) -> str | None:
    if plan.primary_state not in {
        CompanionState.AGENT_WAITING,
        CompanionState.REPLY_CAPTURE,
        CompanionState.STALE_CLEARED,
    }:
        return None
    if not plan.middle.text:
        return None
    return plan.middle.text


def _fetch_companion_status_sync(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=COMPANION_HTTP_TIMEOUT_S) as response:
            raw = response.read(256 * 1024)
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("companion status payload must be an object")
    return payload


def _agent_age_seconds(session: dict[str, Any], *, now: datetime) -> float | None:
    for key in ("last_assistant_text_at", "updated_at"):
        stamp = _parse_datetime(session.get(key))
        if stamp is None:
            continue
        return max(0.0, (now - stamp).total_seconds())
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _agent_label(agent: str) -> str:
    normalized = agent.strip().lower()
    if normalized == "codex":
        return "Codex"
    if normalized == "claude":
        return "Claude"
    return "Agent"


def _agent_identity_label(
    session: dict[str, Any],
    *,
    identity: dict[str, Any] | None = None,
) -> str:
    if identity:
        compact_label = _compact(str(identity.get("compact_label") or ""))
        if compact_label:
            return compact_label
    parts = [_agent_label(str(session.get("agent") or ""))]
    project = _short_project_label(session)
    if project:
        parts.append(project)
    tmux = _tmux_label(session)
    if tmux:
        parts.append(tmux)
    return " | ".join(parts)


def _short_project_label(session: dict[str, Any]) -> str:
    project = _compact(str(session.get("project_name") or ""))
    if project:
        return _shorten_label(project, 18)
    for key in ("repo_root", "cwd"):
        raw = _compact(str(session.get(key) or ""))
        if not raw:
            continue
        tail = raw.rstrip("/").rsplit("/", 1)[-1]
        if tail:
            return _shorten_label(tail, 18)
    return ""


def _tmux_label(session: dict[str, Any]) -> str:
    tmux_session = _compact(str(session.get("tmux_session") or ""))
    tmux_window = _compact(str(session.get("tmux_window") or ""))
    tmux_pane_index = _compact(str(session.get("tmux_pane_index") or ""))
    if tmux_session and tmux_window and tmux_pane_index:
        return _shorten_label(f"{tmux_session}:{tmux_window}.{tmux_pane_index}", 18)
    pane = _compact(str(session.get("tmux_pane") or ""))
    return _shorten_label(pane, 18) if pane else ""


def _shorten_label(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    return f"{text[: max_chars - 1]}>"


def _window_question(
    text: str,
    *,
    page: int = 0,
    max_chars: int = AGENT_QUESTION_LCD_WINDOW_CHARS,
) -> str:
    text = _compact(text)
    if not text:
        return ""
    windows = _question_windows(text, max_chars=max_chars)
    if len(windows) <= 1:
        return windows[0]
    index = max(0, page) % len(windows)
    marker = "more >" if index < len(windows) - 1 else "end"
    return f"[{index + 1}/{len(windows)}] {windows[index]}\n{marker}"


def _question_windows(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    windows: list[str] = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            if current:
                windows.append(current)
                current = ""
            windows.extend(
                word[start : start + max_chars]
                for start in range(0, len(word), max_chars)
            )
            continue
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            windows.append(current)
            current = word
    if current:
        windows.append(current)
    return windows or [text[:max_chars]]


def _agent_display_key(payload: dict[str, Any]) -> str | None:
    agent = _dict(payload.get("agent"))
    if not bool(agent.get("awaiting_response")):
        return None
    session = _dict(agent.get("session"))
    text = _compact(str(session.get("last_assistant_text") or ""))
    if not text:
        return None
    session_id = _compact(str(session.get("session_id") or ""))
    stamp = _compact(str(session.get("last_assistant_text_at") or session.get("updated_at") or ""))
    return "|".join((session_id, stamp, text))


def _compact(text: str) -> str:
    return " ".join(text.split())


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return text[:max_chars]
    return f"{text[: max_chars - 3]}..."


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


__all__ = [
    "AGENT_QUESTION_LCD_MAX_CHARS",
    "COMPANION_HTTP_TIMEOUT_S",
    "CompanionStatusPoller",
    "companion_signals_from_status",
    "fetch_companion_status",
]
