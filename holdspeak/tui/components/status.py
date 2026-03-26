"""Status widget component."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label, Static


class StatusWidget(Horizontal):
    """Shows the current HoldSpeak state with a colored indicator."""

    state: reactive[str] = reactive("idle")
    _blink_on: reactive[bool] = reactive(True)

    def compose(self) -> ComposeResult:
        yield Static("◉", id="status_indicator")
        yield Label("IDLE", id="status_label")

    def on_mount(self) -> None:
        self._apply_state(self.state)
        self.set_interval(0.5, self._tick)

    def watch_state(self, state: str) -> None:
        self._apply_state(state)

    def watch__blink_on(self, _value: bool) -> None:
        self._apply_indicator()

    def _apply_state(self, state: str) -> None:
        state = (state or "").strip().lower()
        if state not in {"idle", "recording", "transcribing", "loading", "error"}:
            state = "idle"

        self.remove_class("idle", "recording", "transcribing", "loading", "error")
        self.add_class(state)

        label = self.query_one("#status_label", Label)
        display = {
            "loading": "LOADING MODEL...",
            "error": "ERROR",
        }.get(state, state.upper())
        label.update(display)
        self._apply_indicator()

    def _tick(self) -> None:
        # Blink only when actively doing something.
        if self.state in {"recording", "transcribing"}:
            self._blink_on = not self._blink_on
        else:
            self._blink_on = True

    def _apply_indicator(self) -> None:
        indicator = self.query_one("#status_indicator", Static)
        if self.state in {"recording", "transcribing"} and not self._blink_on:
            indicator.update(" ")
        else:
            indicator.update("◉")

    def set_state(self, state: str) -> None:
        self.state = state
