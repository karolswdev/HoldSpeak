"""Vision prompt adapter for multi-part content payloads (HS-146-07).

Builds the OpenAI-style multi-part content array (text + data-URL image)
that both llama.cpp and the OpenAI client accept natively.  The canonical
prompt adapter dispatches text-only payloads; this adapter extends the
contract to vision payloads carrying ``image_base64`` + ``image_media_type``.
"""
from __future__ import annotations

import base64
import threading
from typing import Any


class VisionPromptAdapter:
    """Dispatch a vision prompt payload (text + image) through the engine."""

    connector_id = "inference-provider"

    def dispatch(
        self, engine: Any, payload: dict[str, Any], cancellation: threading.Event
    ) -> dict[str, str]:
        image_base64 = payload.get("image_base64", "")
        image_media_type = payload.get("image_media_type", "image/png")

        user_content: list[dict[str, Any]] = [
            {"type": "text", "text": str(payload["user_prompt"])},
        ]
        if image_base64:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_media_type};base64,{image_base64}",
                    },
                }
            )

        messages: list[dict[str, Any]] = []
        system_prompt = str(payload.get("system_prompt", ""))
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        output = engine.run_prompt_messages(messages=messages)
        return {
            "output": str(output),
            "provider": str(getattr(engine, "active_provider", "")),
            "model": str(
                getattr(engine, "active_model", "")
                or getattr(engine, "model", "")
            ),
        }

    def cancel(self) -> str:
        return "cancelled"
