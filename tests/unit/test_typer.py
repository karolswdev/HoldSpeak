"""Privileged desktop driver craft plus the ordinary warrant-only proxy."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.privileged_effects.desktop_driver as driver_module
from holdspeak.privileged_effects.desktop_driver import RawDesktopDriver
from holdspeak.typer import DesktopEffectWarrantRequired, TextTyper


class _Keyboard:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    def press(self, key: object) -> None:
        self.events.append(("press", key))

    def release(self, key: object) -> None:
        self.events.append(("release", key))

    def type(self, char: str) -> None:
        self.events.append(("type", char))


@pytest.fixture
def keyboard(monkeypatch: pytest.MonkeyPatch) -> _Keyboard:
    keyboard = _Keyboard()
    monkeypatch.setattr(driver_module, "Controller", lambda: keyboard)
    monkeypatch.setattr(
        driver_module,
        "Key",
        SimpleNamespace(cmd="cmd", ctrl="ctrl", shift="shift", enter="enter"),
    )
    monkeypatch.setattr(driver_module.pyperclip, "paste", lambda: "old")
    monkeypatch.setattr(driver_module.pyperclip, "copy", lambda _text: None)
    monkeypatch.setattr(driver_module.time, "sleep", lambda _seconds: None)
    return keyboard


def test_linux_generic_target_uses_ctrl_v(
    keyboard: _Keyboard, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver_module.sys, "platform", "linux")

    RawDesktopDriver().type_text("hello", target_profile="browser")

    assert keyboard.events[:4] == [
        ("press", "ctrl"),
        ("press", "v"),
        ("release", "v"),
        ("release", "ctrl"),
    ]


@pytest.mark.parametrize("profile", ["claude_code", "codex_cli", "terminal_shell"])
def test_linux_terminal_targets_use_ctrl_shift_v(
    profile: str, keyboard: _Keyboard, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver_module.sys, "platform", "linux")

    RawDesktopDriver().type_text("hello", target_profile=profile)

    assert keyboard.events[:6] == [
        ("press", "ctrl"),
        ("press", "shift"),
        ("press", "v"),
        ("release", "v"),
        ("release", "shift"),
        ("release", "ctrl"),
    ]


def test_macos_uses_cmd_v_even_for_terminal_target(
    keyboard: _Keyboard, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver_module.sys, "platform", "darwin")

    RawDesktopDriver().type_text("hello", target_profile="claude_code")

    assert keyboard.events[:4] == [
        ("press", "cmd"),
        ("press", "v"),
        ("release", "v"),
        ("release", "cmd"),
    ]


def test_submit_presses_enter_after_insert(
    keyboard: _Keyboard, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(driver_module.sys, "platform", "linux")

    RawDesktopDriver().type_text(
        "hello", target_profile="claude_code", submit=True
    )

    assert keyboard.events == [
        ("press", "ctrl"),
        ("press", "shift"),
        ("press", "v"),
        ("release", "v"),
        ("release", "shift"),
        ("release", "ctrl"),
        ("press", "enter"),
        ("release", "enter"),
    ]


def test_ordinary_proxy_refuses_without_a_claimed_warrant() -> None:
    with pytest.raises(
        DesktopEffectWarrantRequired, match="desktop_effect_warrant_required"
    ):
        TextTyper().type_text("must not land")
