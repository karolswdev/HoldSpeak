"""Mesh-relay backend for the DIR-01 dictation router (HS-85-02, owner call).

DIR already runs on OpenAI-compatible endpoints where constrained decoding is
advisory (ask for JSON, validate, retry) — so the same posture rides the mesh
relay: prompts go to the node's worker (HS-85-01), the node's own provider
answers, and the reply is parsed + validated against the identical structured
schema. The message construction and validation helpers are REUSED from the
endpoint backend so the two advisory legs cannot drift.

Latency is governed by the pipeline's existing honesty: the per-utterance
budget skips passes that would breach it, and the DIR-R-003 cold-start cap
disables the LLM stage for the session when the first classify is too slow —
a far edge degrades honestly, exactly like a slow endpoint.
"""

from __future__ import annotations

from typing import Any

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
from holdspeak.plugins.dictation.runtime_openai_compatible import (
    _parse_json_object,
    _schema_hint,
    _validate_output,
)

log = get_logger("dictation.runtime.mesh_relay")


class MeshRelayRuntime:
    """`LLMRuntime` over the hub's mesh relay queue."""

    backend = "mesh_relay"

    def __init__(
        self,
        *,
        node: str,
        model_hint: str = "",
        intel: Any | None = None,
    ) -> None:
        self.node = str(node or "").strip()
        self.model_hint = str(model_hint or "")
        self._intel = intel

    def load(self) -> None:
        if self._intel is not None:
            return
        from holdspeak.intel.mesh_relay import MeshRelayIntel

        self._intel = MeshRelayIntel(node=self.node, model_hint=self.model_hint)

    def info(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "node": self.node,
            "model": self.model_hint,
            "loaded": self._intel is not None,
        }

    def classify(
        self,
        prompt: str,
        schema: StructuredOutputSchema,
        *,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        self.load()
        text = self._run(
            system_prompt=(
                "Return exactly one JSON object and no prose. "
                "The object must contain matched, block_id, confidence, and extras."
            ),
            user_prompt=f"{prompt}\n\nAllowed output schema:\n{_schema_hint(schema)}",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        data = _parse_json_object(text)
        return _validate_output(data, schema)

    def rewrite(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.15,
    ) -> str:
        """Generate unconstrained rewritten text for the project rewriter stage."""
        self.load()
        return self._run(
            system_prompt=(
                "You rewrite dictation for direct insertion. "
                "Return only the rewritten text, with no explanation."
            ),
            user_prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _run(self, *, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
        from holdspeak.intel.models import MeetingIntelError

        try:
            return self._intel.run_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except MeetingIntelError as exc:
            # the pipeline's error contract is RuntimeError; the relay's named
            # reasons (offline node, deadline, node-side failure) ride verbatim
            log.error("mesh-relay dictation run failed: %s", exc)
            raise RuntimeError(str(exc)) from exc
