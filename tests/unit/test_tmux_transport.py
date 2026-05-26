"""Tests for tmux reply delivery."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.tmux_transport as tmux_transport
from holdspeak.tmux_transport import TmuxTransportError, send_text_to_pane


def test_send_text_to_pane_sends_literal_text_then_enter(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")

    def fake_run(cmd, **_kwargs):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(tmux_transport.subprocess, "run", fake_run)

    delivery = send_text_to_pane(pane="%42", text="hello there", submit=True)

    assert delivery.pane == "%42"
    assert delivery.submitted is True
    assert calls == [
        ["tmux", "send-keys", "-t", "%42", "-l", "hello there"],
        ["tmux", "send-keys", "-t", "%42", "Enter"],
    ]


def test_send_text_to_pane_can_insert_without_submit(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(
        tmux_transport.subprocess,
        "run",
        lambda cmd, **_kwargs: calls.append(list(cmd))
        or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    delivery = send_text_to_pane(pane="%42", text="hello there", submit=False)

    assert delivery.submitted is False
    assert calls == [["tmux", "send-keys", "-t", "%42", "-l", "hello there"]]


def test_send_text_to_pane_requires_tmux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: None)

    with pytest.raises(TmuxTransportError, match="tmux executable"):
        send_text_to_pane(pane="%42", text="hello")
