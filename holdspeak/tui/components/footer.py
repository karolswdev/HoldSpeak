"""Footer and hotkey hint components."""

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Label, Static


class HotkeyHintWidget(Label):
    """Displays the current hotkey hint."""

    hotkey_display: reactive[str] = reactive("⌥R")
    global_hotkey_enabled: reactive[bool] = reactive(True)
    focused_hold_to_talk_key: reactive[str] = reactive("v")

    def __init__(self, hotkey_display: str, *, id: str | None = None) -> None:
        super().__init__("", id=id)
        self.hotkey_display = hotkey_display

    def watch_hotkey_display(self, display: str) -> None:
        self._refresh_hint()

    def watch_global_hotkey_enabled(self, enabled: bool) -> None:
        self._refresh_hint()

    def watch_focused_hold_to_talk_key(self, key: str) -> None:
        self._refresh_hint()

    def _refresh_hint(self) -> None:
        if self.global_hotkey_enabled:
            self.update(f"{self.hotkey_display} to speak")
        else:
            self.update(f"Hold {self.focused_hold_to_talk_key} (focused) to speak")

    def set_hotkey_display(self, display: str) -> None:
        self.hotkey_display = display

    def set_global_hotkey_enabled(self, enabled: bool) -> None:
        self.global_hotkey_enabled = enabled

    def set_focused_hold_to_talk_key(self, key: str) -> None:
        self.focused_hold_to_talk_key = key


class FooterHintsWidget(Static):
    """Footer with keybinding hints - context-aware based on active tab."""

    hotkey_display: reactive[str] = reactive("⌥R")
    meeting_active: reactive[bool] = reactive(False)
    active_tab: reactive[str] = reactive("voice_typing")
    global_hotkey_enabled: reactive[bool] = reactive(True)
    focused_hold_to_talk_key: reactive[str] = reactive("v")

    def __init__(self, hotkey_display: str, *, id: str | None = None) -> None:
        super().__init__("", id=id)
        self.hotkey_display = hotkey_display

    def watch_hotkey_display(self, display: str) -> None:
        self.refresh()

    def watch_meeting_active(self, active: bool) -> None:
        self.refresh()

    def watch_active_tab(self, tab_id: str) -> None:
        self.refresh()

    def watch_global_hotkey_enabled(self, enabled: bool) -> None:
        self.refresh()

    def watch_focused_hold_to_talk_key(self, key: str) -> None:
        self.refresh()

    def set_hotkey_display(self, display: str) -> None:
        self.hotkey_display = display

    def set_meeting_active(self, active: bool) -> None:
        self.meeting_active = active

    def set_active_tab(self, tab_id: str) -> None:
        self.active_tab = tab_id

    def set_global_hotkey_enabled(self, enabled: bool) -> None:
        self.global_hotkey_enabled = enabled

    def set_focused_hold_to_talk_key(self, key: str) -> None:
        self.focused_hold_to_talk_key = key

    def render(self) -> Text:
        parts = ["Tab Switch"]

        if self.active_tab == "voice_typing":
            if self.global_hotkey_enabled:
                parts.append(f"{self.hotkey_display} Record")
            else:
                parts.append(f"Hold {self.focused_hold_to_talk_key} Record (focused)")

            if self.meeting_active:
                parts.extend([
                    "m Stop",
                    "b Bookmark",
                    "e Edit",
                    "t Transcript",
                ])
            else:
                parts.extend([
                    "m Meeting",
                ])

            parts.extend(["c Copy", "d Diagnostics", "s Settings", "q Quit"])

        elif self.active_tab == "meetings":
            parts.extend([
                "/ Search",
                "r Refresh",
            ])
            if self.meeting_active:
                parts.append("m Stop")
            else:
                parts.append("m Start")
            parts.extend(["d Diagnostics", "s Settings", "q Quit"])

        return Text("  │  ".join(parts))
