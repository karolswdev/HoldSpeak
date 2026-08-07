"""Unified error hierarchy for HoldSpeak (HS-117-11).

Every domain exception inherits from :class:`HoldSpeakError`, giving callers
a single ``except HoldSpeakError`` catch-all and a machine-readable ``code``
for structured error responses.
"""

from __future__ import annotations


class HoldSpeakError(Exception):
    """Root of the HoldSpeak domain-error hierarchy.

    Subclasses set a ``code`` class attribute (e.g. ``"AUDIO_ERROR"``).
    The optional *code* keyword in ``__init__`` overrides it per-instance.
    """

    code: str = "HOLDSPEAK_ERROR"

    def __init__(self, *args: object, code: str | None = None) -> None:
        super().__init__(*args)
        if code is not None:
            self.code = code


class ConfigError(HoldSpeakError):
    """Configuration validation failures."""

    code: str = "CONFIG_ERROR"


class AudioError(HoldSpeakError):
    """Audio recording / device errors."""

    code: str = "AUDIO_ERROR"


class TranscriptionError(HoldSpeakError):
    """Transcription pipeline errors."""

    code: str = "TRANSCRIPTION_ERROR"


class DatabaseError(HoldSpeakError):
    """Database schema and state errors."""

    code: str = "DATABASE_ERROR"


class PluginError(HoldSpeakError):
    """Plugin and connector discovery errors."""

    code: str = "PLUGIN_ERROR"


class AgentError(HoldSpeakError):
    """Agent capability and adapter errors."""

    code: str = "AGENT_ERROR"


# ── Error-to-response mapping ───────────────────────────────────────


def error_response(e: HoldSpeakError) -> dict:
    """Translate a domain error into a structured JSON-ready dict.

    Used by the web API layer to return ``{"error": "<CODE>", "message": "..."}``
    instead of raw 500s.
    """
    return {"error": e.code, "message": str(e)}
