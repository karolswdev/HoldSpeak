"""Settings screen."""

from dataclasses import replace
from urllib.parse import urlparse

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Select, TabbedContent, TabPane

from ...audio_devices import get_input_devices
from ...config import Config, get_available_keys


class SettingsScreen(ModalScreen[None]):
    """Modal settings screen (voice typing + meeting + intel + export)."""

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
            yield Label(
                "Tabs: General, Meeting Audio, Intelligence, Speakers, Export.",
                id="settings_hint",
            )

            with TabbedContent(id="settings_tabs"):
                with TabPane("General", id="settings_tab_general"):
                    with Vertical(classes="settings_form_section"):
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

                with TabPane("Meeting Audio", id="settings_tab_meeting"):
                    with Vertical(classes="settings_form_section"):
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
                        yield Label("Mic speaker label", classes="settings_label")
                        yield Input(
                            value=self._config.meeting.mic_label,
                            placeholder="Me",
                            id="mic_label_input",
                        )
                        yield Label("Remote speaker label", classes="settings_label")
                        yield Input(
                            value=self._config.meeting.remote_label,
                            placeholder="Remote",
                            id="remote_label_input",
                        )

                with TabPane("Intelligence", id="settings_tab_intel"):
                    with Vertical(classes="settings_form_section"):
                        yield Checkbox(
                            "Enable meeting intelligence",
                            id="intel_enabled",
                            value=self._config.meeting.intel_enabled,
                        )
                        yield Label("Intel provider mode", classes="settings_label")
                        yield Select(
                            options=[
                                ("Local only", "local"),
                                ("Cloud only", "cloud"),
                                ("Auto (local-first, cloud fallback)", "auto"),
                            ],
                            id="intel_provider_select",
                            value=self._config.meeting.intel_provider,
                        )
                        yield Label("Cloud model", classes="settings_label")
                        yield Input(
                            value=self._config.meeting.intel_cloud_model,
                            placeholder="gpt-5-mini",
                            id="intel_cloud_model_input",
                        )
                        yield Label("Cloud API key env var", classes="settings_label")
                        yield Input(
                            value=self._config.meeting.intel_cloud_api_key_env,
                            placeholder="OPENAI_API_KEY",
                            id="intel_cloud_api_key_env_input",
                        )
                        yield Label("Cloud API base URL (optional)", classes="settings_label")
                        yield Input(
                            value=self._config.meeting.intel_cloud_base_url or "",
                            placeholder="https://api.openai.com/v1",
                            id="intel_cloud_base_url_input",
                        )
                        yield Checkbox(
                            "Enable deferred intelligence queue",
                            id="intel_deferred_enabled",
                            value=self._config.meeting.intel_deferred_enabled,
                        )
                        yield Label("Queue poll interval (seconds)", classes="settings_label")
                        yield Input(
                            value=str(self._config.meeting.intel_queue_poll_seconds),
                            placeholder="120",
                            id="intel_queue_poll_input",
                        )
                        yield Checkbox(
                            "Enable meeting web dashboard",
                            id="web_enabled",
                            value=self._config.meeting.web_enabled,
                        )
                        yield Checkbox(
                            "Auto-open dashboard when meeting starts",
                            id="web_auto_open",
                            value=self._config.meeting.web_auto_open,
                        )

                with TabPane("Speakers", id="settings_tab_speakers"):
                    with Vertical(classes="settings_form_section"):
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
                        yield Checkbox(
                            "Recognize speakers across meetings",
                            id="cross_meeting_recognition",
                            value=self._config.meeting.cross_meeting_recognition,
                        )
                        yield Label("Speaker match threshold (0.0-1.0)", classes="settings_label")
                        yield Input(
                            value=str(self._config.meeting.similarity_threshold),
                            placeholder="0.75",
                            id="similarity_threshold_input",
                        )

                with TabPane("Export", id="settings_tab_export"):
                    with Vertical(classes="settings_form_section"):
                        yield Checkbox(
                            "Auto-export meeting transcript on stop",
                            id="auto_export",
                            value=self._config.meeting.auto_export,
                        )
                        yield Label("Export format", classes="settings_label")
                        yield Select(
                            options=[(f, f) for f in ["txt", "markdown", "json", "srt"]],
                            id="export_format_select",
                            value=self._config.meeting.export_format,
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
            mic_label = self.query_one("#mic_label_input", Input).value.strip()
            remote_label = self.query_one("#remote_label_input", Input).value.strip()
            intel_enabled = self.query_one("#intel_enabled", Checkbox).value
            intel_provider = self.query_one("#intel_provider_select", Select).value
            cloud_model = self.query_one("#intel_cloud_model_input", Input).value.strip()
            cloud_api_key_env = self.query_one("#intel_cloud_api_key_env_input", Input).value.strip()
            cloud_base_url = self.query_one("#intel_cloud_base_url_input", Input).value.strip()
            intel_deferred_enabled = self.query_one("#intel_deferred_enabled", Checkbox).value
            queue_poll_raw = self.query_one("#intel_queue_poll_input", Input).value.strip()
            web_enabled = self.query_one("#web_enabled", Checkbox).value
            web_auto_open = self.query_one("#web_auto_open", Checkbox).value
            diarization_enabled = self.query_one("#diarization_enabled", Checkbox).value
            diarize_mic = self.query_one("#diarize_mic", Checkbox).value
            cross_meeting_recognition = self.query_one("#cross_meeting_recognition", Checkbox).value
            similarity_raw = self.query_one("#similarity_threshold_input", Input).value.strip()
            auto_export = self.query_one("#auto_export", Checkbox).value
            export_format = self.query_one("#export_format_select", Select).value

            if hotkey_key is None or model_name is None or export_format is None or intel_provider is None:
                self.app.bell()
                return
            if str(intel_provider) not in {"local", "cloud", "auto"}:
                self.app.notify("Intel provider must be local, cloud, or auto", severity="error", timeout=2.5)
                self.app.bell()
                return
            if cloud_base_url:
                parsed = urlparse(cloud_base_url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    self.app.notify("Cloud base URL must start with http:// or https://", severity="error", timeout=2.5)
                    self.app.bell()
                    return

            if queue_poll_raw:
                try:
                    queue_poll = int(queue_poll_raw)
                except ValueError:
                    self.app.notify("Queue poll interval must be an integer", severity="error", timeout=2.5)
                    self.app.bell()
                    return
                if queue_poll < 5:
                    self.app.notify("Queue poll interval must be at least 5 seconds", severity="error", timeout=2.5)
                    self.app.bell()
                    return
            else:
                queue_poll = self._config.meeting.intel_queue_poll_seconds

            if similarity_raw:
                try:
                    similarity_threshold = float(similarity_raw)
                except ValueError:
                    self.app.notify("Speaker threshold must be a number", severity="error", timeout=2.5)
                    self.app.bell()
                    return
                if similarity_threshold < 0.0 or similarity_threshold > 1.0:
                    self.app.notify("Speaker threshold must be between 0.0 and 1.0", severity="error", timeout=2.5)
                    self.app.bell()
                    return
            else:
                similarity_threshold = self._config.meeting.similarity_threshold

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
            updated.meeting.mic_label = mic_label or "Me"
            updated.meeting.remote_label = remote_label or "Remote"
            updated.meeting.intel_enabled = intel_enabled
            updated.meeting.intel_provider = str(intel_provider)
            updated.meeting.intel_cloud_model = cloud_model or "gpt-5-mini"
            updated.meeting.intel_cloud_api_key_env = cloud_api_key_env or "OPENAI_API_KEY"
            updated.meeting.intel_cloud_base_url = cloud_base_url or None
            updated.meeting.intel_deferred_enabled = intel_deferred_enabled
            updated.meeting.intel_queue_poll_seconds = queue_poll
            updated.meeting.web_enabled = web_enabled
            updated.meeting.web_auto_open = web_auto_open
            updated.meeting.diarization_enabled = diarization_enabled
            updated.meeting.diarize_mic = diarize_mic
            updated.meeting.cross_meeting_recognition = cross_meeting_recognition
            updated.meeting.similarity_threshold = similarity_threshold
            updated.meeting.auto_export = auto_export
            updated.meeting.export_format = str(export_format)
            updated.save()

            self.post_message(self.Applied(updated))
            self.app.pop_screen()
