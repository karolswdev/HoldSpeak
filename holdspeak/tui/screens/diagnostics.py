"""Diagnostics screen for environment and feature availability."""

from __future__ import annotations

import os
import sys

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class DiagnosticsScreen(ModalScreen[None]):
    """Show platform/environment details and capability flags."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="diagnostics_dialog"):
            yield Label("HoldSpeak Diagnostics", id="diagnostics_title")
            with VerticalScroll(id="diagnostics_body"):
                yield Static("", id="diagnostics_content", markup=True)
            with Horizontal(id="diagnostics_actions"):
                yield Button("Refresh", id="diagnostics_refresh")
                yield Button("Close", id="diagnostics_close")

    def on_mount(self) -> None:
        self._refresh()

    def action_close(self) -> None:
        self.app.pop_screen()

    def action_refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        state = getattr(self.app, "ui_state", None)

        xdg_session_type = os.environ.get("XDG_SESSION_TYPE", "(unset)")
        wayland_display = os.environ.get("WAYLAND_DISPLAY", "(unset)")
        x_display = os.environ.get("DISPLAY", "(unset)")

        global_hotkey_enabled = getattr(state, "global_hotkey_enabled", False)
        global_hotkey_reason = getattr(state, "global_hotkey_disabled_reason", "")
        hotkey_display = getattr(state, "hotkey_display", "")

        injection_enabled = getattr(state, "text_injection_enabled", False)
        injection_reason = getattr(state, "text_injection_disabled_reason", "")

        focused_key = getattr(state, "focused_hold_to_talk_key", "v")
        cfg = getattr(self.app, "config", None)
        mic_device = getattr(getattr(cfg, "meeting", None), "mic_device", None)
        system_device = getattr(getattr(cfg, "meeting", None), "system_audio_device", None)

        try:
            size = self.app.size
            size_str = f"{size.width}x{size.height}"
        except Exception:
            size_str = "(unknown)"

        lines = [
            "[bold]Session[/]",
            f"- XDG_SESSION_TYPE: [cyan]{xdg_session_type}[/]",
            f"- WAYLAND_DISPLAY: [cyan]{wayland_display}[/]",
            f"- DISPLAY: [cyan]{x_display}[/]",
            f"- Terminal size: [cyan]{size_str}[/]",
            "",
            "[bold]Features[/]",
            (
                f"- Global hotkey: [green]ENABLED[/] ({hotkey_display})"
                if global_hotkey_enabled
                else f"- Global hotkey: [red]DISABLED[/] ({global_hotkey_reason or 'unavailable'})"
            ),
            f"- Focused hold-to-talk: [green]ENABLED[/] (hold [cyan]{focused_key}[/])",
            (
                "- Text injection: [green]ENABLED[/]"
                if injection_enabled
                else f"- Text injection: [red]DISABLED[/] ({injection_reason or 'unavailable'})"
            ),
            "",
            "[bold]Audio (config)[/]",
            f"- Mic device: [cyan]{mic_device or 'default'}[/]",
            f"- System audio: [cyan]{system_device or 'auto'}[/]",
            "",
            "[bold]Runtime[/]",
            f"- Platform: [cyan]{sys.platform}[/]",
            f"- Python: [cyan]{sys.version.split()[0]}[/]",
        ]

        self.query_one("#diagnostics_content", Static).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "diagnostics_close":
            self.app.pop_screen()
        elif event.button.id == "diagnostics_refresh":
            self._refresh()
