"""Canonical prompt adapter used by runner-owned service migrations."""
from __future__ import annotations

import threading
from collections.abc import Iterator
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


class StreamingPromptAdapter:
    """Streaming dispatch adapter for thread turns (HS-151-03).

    Calls ``engine.run_prompt_stream(messages=..., temperature=..., max_tokens=...)``
    and yields ``Delta`` objects, checking the cancellation Event between chunks.
    The non-streaming ``dispatch`` falls back to ``run_prompt_messages`` so the
    Protocol is satisfied for callers that use ``invoke`` instead of
    ``invoke_stream``.

    An optional ``external_cancel`` event (from the thread service's abort
    path) is checked alongside the runner's own cancellation event so that
    ``POST /abort`` stops the engine within one delta gap (~100 ms).
    """

    connector_id = "inference-provider"

    def __init__(self, *, external_cancel: threading.Event | None = None):
        self._external_cancel = external_cancel

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> dict[str, str]:
        if hasattr(engine, "run_prompt_messages"):
            output = str(engine.run_prompt_messages(
                messages=payload["messages"],
                temperature=payload.get("temperature"),
                max_tokens=payload.get("max_tokens"),
            ))
        else:
            # Fallback: concatenate messages into a single prompt for run_prompt.
            msgs = payload.get("messages", [])
            system = next((m["content"] for m in msgs if m.get("role") == "system"), "")
            user = "\n".join(m["content"] for m in msgs if m.get("role") == "user")
            output = str(engine.run_prompt(
                system_prompt=system,
                user_prompt=user,
                temperature=payload.get("temperature"),
                max_tokens=payload.get("max_tokens"),
            ))
        return {
            "output": output,
            "provider": str(getattr(engine, "active_provider", "")),
            "model": str(getattr(engine, "active_model", "") or getattr(engine, "model", "")),
        }

    def cancel(self) -> str:
        return "cancelled"

    def _is_cancelled(self, cancellation: threading.Event) -> bool:
        """Check both the runner's cancellation and the external abort event."""
        if cancellation.is_set():
            return True
        if self._external_cancel is not None and self._external_cancel.is_set():
            # Propagate the external cancel into the runner's event so the
            # runner's own cancel bookkeeping (lease, receipt) fires too.
            cancellation.set()
            return True
        return False

    def dispatch_stream(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> Iterator:
        """Yield ``Delta`` objects from the engine's streaming completion.

        Falls back to the non-streaming ``run_prompt`` / ``run_prompt_messages``
        path when the engine lacks ``run_prompt_stream``, yielding one text
        Delta with the complete output followed by a done Delta (HS-151-04:
        graceful degradation for engines injected via ``_engine_factory``).

        When *tools*/*tool_choice* are present in the payload they are
        forwarded to the engine; the sealed ``dispatch`` return shape
        stays ``{output, provider, model}`` -- tool_calls travel on the
        Delta stream only (same rule as usage).
        """
        from .inference_stream import Delta

        if not hasattr(engine, "run_prompt_stream"):
            # Graceful degradation: non-streaming fallback.
            result = self.dispatch(engine, payload, cancellation)
            if self._is_cancelled(cancellation):
                return
            yield Delta(kind="text", text=str(result.get("output", "")))
            yield Delta(kind="done")
            return

        stream_kwargs: dict[str, Any] = {
            "messages": payload["messages"],
            "temperature": payload.get("temperature"),
            "max_tokens": payload.get("max_tokens"),
        }
        if payload.get("tools") is not None:
            stream_kwargs["tools"] = payload["tools"]
        if payload.get("tool_choice") is not None:
            stream_kwargs["tool_choice"] = payload["tool_choice"]

        for delta in engine.run_prompt_stream(**stream_kwargs):
            if self._is_cancelled(cancellation):
                return
            yield delta
