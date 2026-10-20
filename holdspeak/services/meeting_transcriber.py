"""Shared transcriber construction for HTTP and MCP meeting intake."""
from __future__ import annotations

from typing import Any

from holdspeak.config import Config


def default_transcriber_factory(config: Config):
    """Build a transcriber from the admitted live configuration."""
    from holdspeak.transcribe import Transcriber

    return Transcriber(
        model_name=config.model.name,
        backend=getattr(config.model, "backend", None),
        language=getattr(config.model, "language", "auto"),
    )


def frozen_transcriber_factory(construct: dict[str, Any]):
    """Build from the frozen speech admission, never rereading Config."""
    from holdspeak.transcribe import Transcriber

    return Transcriber(
        model_name=construct["model_name"],
        backend=construct["backend"],
        language=construct.get("language") or "auto",
    )
