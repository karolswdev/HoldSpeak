"""Canonical prompt adapter used by runner-owned service migrations."""
from __future__ import annotations

import threading
from typing import Any


class CanonicalPromptAdapter:
    """Dispatch a canonical prompt payload without giving services an engine."""

    connector_id = "inference-provider"

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> dict[str, str]:
        return {"output": str(engine.run_prompt(
            system_prompt=str(payload["system_prompt"]),
            user_prompt=str(payload["user_prompt"]),
            temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"),
        )), "provider": str(getattr(engine, "active_provider", "")),
            # HS-132-09: `active_model` is the ENGINE's report of what it loaded,
            # and every provider this adapter is handed now defines it
            # (`MeetingIntel` did not, so this read was always `''` and each
            # consumer fell back to a hub-side describer that had never seen the
            # engine). A blank report still falls back to the admitted
            # deployment's frozen model downstream — never to a live config read.
            "model": str(getattr(engine, "active_model", "") or getattr(engine, "model", ""))}

    def cancel(self) -> str:
        return "cancelled"
