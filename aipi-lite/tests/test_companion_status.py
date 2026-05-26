"""Tests for `/api/companion/status` bridge polling adapter."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import structlog

from bridge.companion_state import CompanionState
from bridge.companion_status import (
    CompanionStatusPoller,
    companion_signals_from_status,
)
from bridge.settings import Settings


def _settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        holdspeak_host="127.0.0.1",
        holdspeak_port=12345,
        holdspeak_psk="test-psk",
        device_id="aipi-test",
        device_label="Test",
        log_level="ERROR",
        companion_poll_interval_s=1,
    )


def _payload(*, timestamp: str | None = None, **overrides):
    now = timestamp or datetime.now(timezone.utc).isoformat()
    payload = {
        "status": "ok",
        "agent": {
            "awaiting_response": True,
            "session": {
                "agent": "codex",
                "last_assistant_text": "Should I run the hardware dogfood now?",
                "last_assistant_text_at": now,
                "updated_at": now,
            },
            "max_age_seconds": 120,
            "error": None,
        },
        "runtime": {
            "meeting_active": False,
            "voice_state": None,
        },
    }
    payload.update(overrides)
    return payload


def test_companion_signals_adapt_fresh_agent_question():
    signals = companion_signals_from_status(
        _payload(timestamp="2026-05-25T02:00:00+00:00"),
        now=datetime(2026, 5, 25, 2, 1, 0, tzinfo=timezone.utc),
    )

    assert signals.agent_waiting is True
    assert signals.agent_label == "Codex"
    assert signals.agent_question == "Should I run the hardware dogfood now?"
    assert signals.agent_age_s == 60


def test_companion_signals_include_project_and_tmux_identity():
    payload = _payload(
        agent={
            "awaiting_response": True,
            "session": {
                "agent": "claude",
                "project_name": "HoldSpeak",
                "tmux_session": "work",
                "tmux_window": "2",
                "tmux_pane_index": "1",
                "last_assistant_text": "Proceed?",
                "updated_at": "2026-05-25T02:00:00Z",
            },
        }
    )

    signals = companion_signals_from_status(payload)

    assert signals.agent_label == "Claude | HoldSpeak | work:2.1"


def test_companion_signals_prefer_server_identity_payload():
    payload = _payload(
        agent={
            "awaiting_response": True,
            "identity": {
                "compact_label": "Codex | HoldSpeak | no tmux",
                "target_confidence": "medium",
            },
            "session": {
                "agent": "codex",
                "project_name": "FallbackProject",
                "tmux_session": "fallback",
                "tmux_window": "9",
                "tmux_pane_index": "4",
                "last_assistant_text": "Proceed?",
                "updated_at": "2026-05-25T02:00:00Z",
            },
        }
    )

    signals = companion_signals_from_status(payload)

    assert signals.agent_label == "Codex | HoldSpeak | no tmux"


def test_companion_signals_window_long_question_without_ambiguous_ellipsis():
    text = (
        "Should I update the bridge companion display so long Codex questions "
        "rotate through readable windows instead of hiding the useful ending?"
    )
    stamp = datetime.now(timezone.utc).isoformat()
    payload = _payload(
        agent={
            "awaiting_response": True,
            "session": {
                "agent": "codex",
                "last_assistant_text": text,
                "updated_at": "2026-05-25T02:00:00Z",
            },
        }
    )

    first = companion_signals_from_status(payload, question_page=0)
    second = companion_signals_from_status(payload, question_page=1)

    assert first.agent_question.startswith("[1/")
    assert "..." not in first.agent_question
    assert "more >" in first.agent_question
    assert second.agent_question.startswith("[2/")
    assert "useful ending" in second.agent_question


def test_companion_signals_mark_old_agent_as_stale_input():
    signals = companion_signals_from_status(
        _payload(timestamp="2026-05-25T02:00:00+00:00"),
        now=datetime(2026, 5, 25, 2, 3, 1, tzinfo=timezone.utc),
    )

    assert signals.agent_waiting is True
    assert signals.agent_age_s == 181


def test_companion_signals_ignore_agent_without_question_text():
    payload = _payload(
        agent={
            "awaiting_response": True,
            "session": {
                "agent": "codex",
                "last_assistant_text": "",
                "updated_at": "2026-05-25T02:00:00Z",
            },
        }
    )

    signals = companion_signals_from_status(payload)

    assert signals.agent_waiting is False


@pytest.mark.asyncio
async def test_poller_paints_agent_question_once(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )

    async def fake_fetch(_url: str):
        return _payload()

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    first = await poller.poll_once()
    second = await poller.poll_once()

    assert first is not None
    assert first.primary_state == CompanionState.AGENT_WAITING
    assert second is not None
    assert paints == ["Codex waiting\nShould I run the hardware dogfood now?"]


@pytest.mark.asyncio
async def test_poller_advances_long_question_windows(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )
    text = (
        "Should I update the bridge companion display so long Codex questions "
        "rotate through readable windows instead of hiding the useful ending?"
    )
    stamp = datetime.now(timezone.utc).isoformat()

    async def fake_fetch(_url: str):
        return _payload(
            agent={
                "awaiting_response": True,
                "session": {
                    "agent": "codex",
                    "last_assistant_text": text,
                    "updated_at": stamp,
                },
            }
        )

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    await poller.poll_once()
    await poller.poll_once()

    assert len(paints) == 2
    assert paints[0].startswith("Codex waiting\n[1/")
    assert paints[1].startswith("Codex waiting\n[2/")
    assert "..." not in "".join(paints)


@pytest.mark.asyncio
async def test_poller_clears_only_agent_text_it_previously_painted(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )
    payloads = [
        _payload(),
        _payload(agent={"awaiting_response": False, "session": None, "error": None}),
        _payload(agent={"awaiting_response": False, "session": None, "error": None}),
    ]

    async def fake_fetch(_url: str):
        return payloads.pop(0)

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    await poller.poll_once()
    await poller.poll_once()
    await poller.poll_once()

    assert paints == [
        "Codex waiting\nShould I run the hardware dogfood now?",
        "",
    ]


@pytest.mark.asyncio
async def test_poller_paints_reply_capture_instead_of_clearing_question(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )
    payloads = [
        _payload(),
        _payload(runtime={"meeting_active": False, "voice_state": "recording"}),
    ]

    async def fake_fetch(_url: str):
        return payloads.pop(0)

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    first = await poller.poll_once()
    second = await poller.poll_once()

    assert first is not None
    assert first.primary_state == CompanionState.AGENT_WAITING
    assert second is not None
    assert second.primary_state == CompanionState.REPLY_CAPTURE
    assert paints == [
        "Codex waiting\nShould I run the hardware dogfood now?",
        "Replying to Codex",
    ]


@pytest.mark.asyncio
async def test_poller_holds_agent_repaint_during_external_flash(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )
    payloads = [
        _payload(),
        _payload(runtime={"meeting_active": False, "voice_state": "recording"}),
        _payload(),
        _payload(),
    ]

    async def fake_fetch(_url: str):
        return payloads.pop(0)

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    await poller.poll_once()
    await poller.poll_once()
    poller.hold_middle_for(60_000)
    await poller.poll_once()
    poller._middle_hold_until = 0
    await poller.poll_once()

    assert paints == [
        "Codex waiting\nShould I run the hardware dogfood now?",
        "Replying to Codex",
        "Codex waiting\nShould I run the hardware dogfood now?",
    ]


@pytest.mark.asyncio
async def test_poller_force_repaint_repaints_same_agent(monkeypatch):
    paints: list[str] = []
    poller = CompanionStatusPoller(
        _settings(),
        structlog.get_logger(),
        on_middle_update=lambda text: _append_async(paints, text),
    )

    async def fake_fetch(_url: str):
        return _payload()

    monkeypatch.setattr("bridge.companion_status.fetch_companion_status", fake_fetch)

    await poller.poll_once()
    poller.force_repaint()
    await poller.poll_once()

    assert paints == [
        "Codex waiting\nShould I run the hardware dogfood now?",
        "Codex waiting\nShould I run the hardware dogfood now?",
    ]


async def _append_async(items: list[str], text: str) -> None:
    items.append(text)
