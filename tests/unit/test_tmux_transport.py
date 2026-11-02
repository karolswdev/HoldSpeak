"""Tests for tmux reply delivery."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.tmux_transport as tmux_transport
from holdspeak.tmux_transport import (
    TmuxTransportError,
    send_keys_to_pane,
    send_text_to_pane,
)


def _capture(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(
        tmux_transport.subprocess,
        "run",
        lambda cmd, **_kwargs: calls.append(list(cmd))
        or SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    return calls


def test_send_keys_named_key_is_a_bare_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    # C-c interrupts: a named key, NOT -l (that would type the letters).
    calls = _capture(monkeypatch)
    delivery = send_keys_to_pane(pane="%7", keys=[("named", "C-c")])
    assert delivery.pane == "%7"
    assert calls == [["tmux", "send-keys", "-t", "%7", "C-c"]]


def test_send_keys_renders_a_tui_drive_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture(monkeypatch)
    send_keys_to_pane(pane="%7", keys=[("named", "Down"), ("named", "Down"), ("named", "Enter")])
    assert calls == [
        ["tmux", "send-keys", "-t", "%7", "Down"],
        ["tmux", "send-keys", "-t", "%7", "Down"],
        ["tmux", "send-keys", "-t", "%7", "Enter"],
    ]


def test_send_keys_literal_run_uses_dash_l(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture(monkeypatch)
    send_keys_to_pane(pane="%7", keys=[("literal", "/search"), ("named", "Enter")])
    assert calls == [
        ["tmux", "send-keys", "-t", "%7", "-l", "/search"],
        ["tmux", "send-keys", "-t", "%7", "Enter"],
    ]


def test_send_keys_requires_tmux_and_a_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    with pytest.raises(TmuxTransportError, match="key sequence is required"):
        send_keys_to_pane(pane="%7", keys=[])
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: None)
    with pytest.raises(TmuxTransportError, match="tmux executable"):
        send_keys_to_pane(pane="%7", keys=[("named", "C-c")])


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
        # the submit is the NAMED C-m: a literal CR was typed into Claude
        # Code's composer as a character (2026-11-02, pane %56)
        ["tmux", "send-keys", "-t", "%42", "C-m"],
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


def test_the_split_enter_takes_the_usual_pause_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ruling 2026-11-02: a bound answer is its text, a second read of the
    wait, then the Enter. The Enter takes the same pause a plain send takes,
    so the only change from before #1775 is the second read."""
    events: list = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(tmux_transport.subprocess, "run",
                        lambda cmd, **_kwargs: events.append(("run", list(cmd)))
                        or SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(tmux_transport.time, "sleep", lambda seconds: events.append(("sleep", seconds)))

    send_text_to_pane(pane="%42", text="1", submit=False)
    delivery = send_text_to_pane(pane="%42", text="", submit=True)

    assert delivery.submitted is True
    assert events == [
        ("run", ["tmux", "send-keys", "-t", "%42", "-l", "1"]),
        ("sleep", tmux_transport.SUBMIT_PAUSE_SECONDS),
        ("run", ["tmux", "send-keys", "-t", "%42", "C-m"]),
    ]


@pytest.mark.parametrize("text", ["fix it", "line one\nline two", "x" * 201, "a\r\nb", ""])
def test_every_submit_is_the_named_c_m_and_no_text_carries_a_cr(monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    """The fix proof of 2026-11-02: the plain path, the paste path and the
    split path's lone Enter all submit with the named C-m; nothing typed or
    pasted carries a carriage return."""
    calls: list = []
    monkeypatch.setattr(tmux_transport.shutil, "which", lambda _name: "/usr/bin/tmux")
    monkeypatch.setattr(tmux_transport.subprocess, "run",
                        lambda cmd, **kwargs: calls.append((list(cmd), kwargs.get("input")))
                        or SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(tmux_transport.time, "sleep", lambda _s: None)
    send_text_to_pane(pane="%9", text=text, submit=True)
    assert calls[-1][0] == ["tmux", "send-keys", "-t", "%9", "C-m"]
    for cmd, stdin in calls:
        assert all("\r" not in part for part in cmd), cmd
        assert "\r" not in str(stdin or ""), stdin
