"""Bridge configuration loaded from env vars + an optional `bridge.env` file.

Pydantic-settings handles env-var → field mapping; `_normalise` adds
post-load fixes (case-normalising the log level, defaulting the device
label, rejecting empty PSK loud).
"""

from __future__ import annotations

import sys

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bridge configuration loaded from env + an optional `bridge.env` file.

    `bridge.env` lives next to the bridge package and is gitignored.
    Env vars override file values. The PSK uses Pydantic's `SecretStr`
    so it redacts in `repr()` / log lines that capture the model — call
    `settings.holdspeak_psk.get_secret_value()` to read the plaintext
    when sending it on the wire.
    """

    model_config = SettingsConfigDict(
        env_file="bridge.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # tolerate other env vars in the environment
    )

    # ESPHome API endpoint (the AIPI-Lite device).
    aipi_host: str = Field(default="aipi.local", alias="ESPHOME_HOST")
    aipi_port: int = Field(default=6053, alias="ESPHOME_PORT")
    aipi_password: str | None = Field(default=None, alias="ESPHOME_PASSWORD")

    # HoldSpeak host. PSK + port are required.
    holdspeak_host: str = Field(default="127.0.0.1")
    holdspeak_port: int
    holdspeak_psk: SecretStr

    # Identity sent in the WS handshake.
    device_id: str = "aipi-1"
    device_label: str | None = None

    # UDP port the bridge listens on for the device's voice_assistant
    # audio stream. The bridge advertises this back to the device in
    # handle_va_start; the device opens a UDP socket to it and pushes
    # int16-LE PCM. ESPHome's voice_assistant is UDP-first (returning
    # None from handle_va_start logs "Server could not be started"
    # and audio never flows).
    udp_audio_port: int = 50000

    # Optional debug tee for incoming device mic audio. When set, the bridge
    # starts this shell command and writes raw 16 kHz mono signed-16-bit PCM
    # chunks to its stdin. Example:
    #   AUDIO_MONITOR_CMD='aplay -q -f S16_LE -r 16000 -c 1 -t raw -'
    audio_monitor_cmd: str | None = None

    # Poll cadence for HoldSpeak's `/api/companion/status`. The poller owns
    # agent-attention paint in the LCD middle zone; 2 s is fast enough for a
    # physical companion without creating noisy local HTTP traffic.
    companion_poll_interval_s: float = 2.0

    log_level: str = "INFO"

    @model_validator(mode="after")
    def _normalise(self) -> Settings:
        # Default device_label to device_id when blank (keeps the
        # handshake's `label` non-empty without making it required).
        if not self.device_label:
            object.__setattr__(self, "device_label", self.device_id)
        # Normalise log level to upper-case so configure_logging() lookup
        # works regardless of how the user wrote it.
        object.__setattr__(self, "log_level", self.log_level.upper())
        # SecretStr("") is truthy at the Pydantic-required level, so
        # without this check an empty HOLDSPEAK_PSK silently passes
        # config validation and only fails downstream on the Hello
        # frame's `psk: non-empty` validator. Reject loud, here.
        if not self.holdspeak_psk.get_secret_value():
            raise ValueError(
                "holdspeak_psk: must not be empty (run "
                "`holdspeak device-psk show` and put it in HOLDSPEAK_PSK)"
            )
        return self


def load_settings() -> Settings:
    """Build Settings from env + `bridge.env`; exit 1 with a clear error on
    missing/invalid required fields.
    """
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        sys.stderr.write("ERROR: bridge configuration invalid:\n")
        for err in exc.errors():
            loc = ".".join(str(x) for x in err["loc"]) or "<root>"
            sys.stderr.write(f"  {loc}: {err['msg']}\n")
        sys.stderr.write(
            "\nSee bridge.env.example for the full schema.\n"
            "Required env vars: HOLDSPEAK_PORT, HOLDSPEAK_PSK.\n"
        )
        sys.exit(1)
