"""Settings screen."""

from dataclasses import replace

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label, Select

from ...audio_devices import get_input_devices
from ...config import Config, get_available_keys


class SettingsScreen(ModalScreen[None]):
    """Modal settings screen (hotkey + model + device selection)."""

    BINDINGS = [("escape", "cancel", "Close")]

    class Applied(Message):
        def __init__(self, config: Config) -> None:
            super().__init__()
            self.config = config

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def _get_mic_options(self) -> list[tuple[str, str]]:
        """Get microphone device options."""
        options = [("System Default", "")]
        for device in get_input_devices():
            options.append((device.name, device.name))
        return options

    def _get_system_audio_options(self) -> list[tuple[str, str]]:
        """Get system audio device options (input devices that can capture system audio)."""
        options = [("None (mic only)", "")]
        for device in get_input_devices():
            # Show all input devices - BlackHole and similar will be here
            label = f"{device.name} [VIRTUAL]" if device.is_virtual else device.name
            options.append((label, device.name))
        return options

    def _get_valid_value(self, saved_value: str | None, options: list[tuple[str, str]]) -> str:
        """Return saved value if it exists in options, otherwise return default."""
        if not saved_value:
            return ""
        option_values = [v for _, v in options]
        return saved_value if saved_value in option_values else ""

    def compose(self) -> ComposeResult:
        mic_options = self._get_mic_options()
        system_options = self._get_system_audio_options()

        with Container(id="settings_dialog"):
            yield Label("Settings", id="settings_title")

            # Allow the form to scroll on small terminals.
            with VerticalScroll(id="settings_scroll"):
                with Vertical(id="settings_form"):
                    yield Label("Hotkey", classes="settings_label")
                    yield Select(
                        options=[(f"{display}  ({key})", key) for key, display in get_available_keys()],
                        id="hotkey_select",
                        value=self._config.hotkey.key,
                    )

                    yield Label("Model", classes="settings_label")
                    yield Select(
                        options=[(m, m) for m in ["tiny", "base", "small", "medium", "large"]],
                        id="model_select",
                        value=self._config.model.name,
                    )

                    yield Label("─── Meeting Mode ───", classes="settings_label settings_separator")

                    yield Label("Microphone", classes="settings_label")
                    yield Select(
                        options=mic_options,
                        id="mic_select",
                        value=self._get_valid_value(self._config.meeting.mic_device, mic_options),
                    )

                    yield Label("System Audio (for remote participants)", classes="settings_label")
                    yield Select(
                        options=system_options,
                        id="system_audio_select",
                        value=self._get_valid_value(self._config.meeting.system_audio_device, system_options),
                    )

                    yield Label("─── Speaker Diarization ───", classes="settings_label settings_separator")

                    yield Checkbox(
                        "Identify speakers in system audio",
                        id="diarization_enabled",
                        value=self._config.meeting.diarization_enabled,
                    )
                    yield Checkbox(
                        "Identify speakers in mic (on-site meetings)",
                        id="diarize_mic",
                        value=self._config.meeting.diarize_mic,
                    )

            with Horizontal(id="settings_actions"):
                yield Button("Cancel", id="settings_cancel")
                yield Button("Save", variant="primary", id="settings_save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings_cancel":
            self.app.pop_screen()
            return

        if event.button.id == "settings_save":
            hotkey_key = self.query_one("#hotkey_select", Select).value
            model_name = self.query_one("#model_select", Select).value
            mic_device = self.query_one("#mic_select", Select).value
            system_audio = self.query_one("#system_audio_select", Select).value
            diarization_enabled = self.query_one("#diarization_enabled", Checkbox).value
            diarize_mic = self.query_one("#diarize_mic", Checkbox).value

            if hotkey_key is None or model_name is None:
                self.app.bell()
                return

            available = dict(get_available_keys())
            display = available.get(hotkey_key, str(hotkey_key))

            updated = Config(
                hotkey=replace(self._config.hotkey),
                model=replace(self._config.model),
                ui=replace(self._config.ui),
                meeting=replace(self._config.meeting),
            )
            updated.hotkey.key = str(hotkey_key)
            updated.hotkey.display = display
            updated.model.name = str(model_name)
            # Store None for empty string (system default)
            updated.meeting.mic_device = str(mic_device) if mic_device else None
            updated.meeting.system_audio_device = str(system_audio) if system_audio else None
            updated.meeting.diarization_enabled = diarization_enabled
            updated.meeting.diarize_mic = diarize_mic
            updated.save()

            self.post_message(self.Applied(updated))
            self.app.pop_screen()
