"""OpenAI-compatible backend for the DIR-01 dictation router.

This backend targets local or remote servers that expose the OpenAI
``/v1/chat/completions`` contract: LM Studio, Ollama's OpenAI bridge, vLLM,
llama.cpp server, LiteLLM, or OpenAI itself. Unlike the MLX and llama-cpp
backends, constrained decoding is advisory: the runtime asks for JSON output
and validates the parsed object against the same structured schema.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

from holdspeak.logging_config import get_logger
from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
from holdspeak.plugins.dictation.runtime import RuntimeUnavailableError

log = get_logger("dictation.runtime.openai_compatible")


class OpenAICompatibleRuntime:
    """`LLMRuntime` over an OpenAI-compatible chat-completions endpoint."""

    backend = "openai_compatible"

    def __init__(
        self,
        *,
        model: str,
        base_url: str = "http://127.0.0.1:8000/v1",
        api_key_env: str = "OPENAI_API_KEY",
        timeout_seconds: float = 8.0,
        warm_on_start: bool = False,
        client_factory: Any | None = None,
    ) -> None:
        self.model = str(model or "").strip()
        self.base_url = str(base_url or "").strip()
        self.api_key_env = str(api_key_env or "").strip()
        self.timeout_seconds = max(1.0, float(timeout_seconds))
        self._client_factory = client_factory
        self._client: Any | None = None

        if warm_on_start:
            self.load()

    def load(self) -> None:
        if self._client is not None:
            return
        if not self.model:
            raise RuntimeUnavailableError("OpenAI-compatible dictation model is not configured")
        _validate_base_url(self.base_url)

        factory = self._client_factory
        if factory is None:
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except Exception as exc:  # pragma: no cover - install-dependent
                raise RuntimeUnavailableError(
                    "openai package is not installed. "
                    "Install with: uv pip install holdspeak[dictation-openai]"
                ) from exc
            factory = OpenAI

        api_key = os.environ.get(self.api_key_env, "").strip() if self.api_key_env else ""
        kwargs: dict[str, Any] = {
            "api_key": api_key or "not-needed",
            "base_url": self.base_url,
            "timeout": self.timeout_seconds,
        }
        try:
            self._client = factory(**kwargs)
        except Exception as exc:  # pragma: no cover - env-dependent
            raise RuntimeUnavailableError(
                f"Failed to initialize OpenAI-compatible client at {self.base_url}: {exc}"
            ) from exc

    def info(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "timeout_seconds": self.timeout_seconds,
            "loaded": self._client is not None,
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
        assert self._client is not None
        schema_hint = _schema_hint(schema)
        messages = [
            {
                "role": "system",
                "content": (
                    "Return exactly one JSON object and no prose. "
                    "The object must contain matched, block_id, confidence, and extras."
                ),
            },
            {
                "role": "user",
                "content": f"{prompt}\n\nAllowed output schema:\n{schema_hint}",
            },
        ]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                extra_body={"thinking": False},
            )
        except Exception as exc:
            if not _response_format_unsupported(exc):
                log.error("OpenAI-compatible dictation classify failed: %s", exc, exc_info=True)
                raise RuntimeError(f"OpenAI-compatible classify failed: {exc}") from exc
            # Some OpenAI-compatible servers reject response_format as a
            # bad-request error rather than a Python TypeError.
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_body={"thinking": False},
                )
            except Exception as retry_exc:
                log.error(
                    "OpenAI-compatible dictation classify retry failed: %s",
                    retry_exc,
                    exc_info=True,
                )
                raise RuntimeError(
                    f"OpenAI-compatible classify failed: {retry_exc}"
                ) from retry_exc

        text = _extract_message_text(response)
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
        assert self._client is not None
        messages = [
            {
                "role": "system",
                "content": (
                    "You rewrite dictation for direct insertion. "
                    "Return only the rewritten text, with no explanation."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"thinking": False},
            )
        except Exception as exc:
            log.error("OpenAI-compatible dictation rewrite failed: %s", exc, exc_info=True)
            raise RuntimeError(f"OpenAI-compatible rewrite failed: {exc}") from exc
        return _extract_message_text(response)


def _validate_base_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeUnavailableError(
            "OpenAI-compatible base URL must start with http:// or https:// and include a host"
        )


def _response_format_unsupported(exc: Exception) -> bool:
    if isinstance(exc, TypeError):
        return True
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    return "badrequest" in name and "response_format" in message


def _schema_hint(schema: StructuredOutputSchema) -> str:
    # The hint shows the EXPECTED OUTPUT OBJECT itself: `extras` is a flat object
    # whose allowed keys depend on the chosen block_id (listed in the reference
    # table). The previous hint's only example of extras was the nested
    # `extras_per_block` table, and a faithful model mirrored that nesting back
    # (`extras: {"<block_id>": {...}}`) and was rejected — the shape the
    # validator's unwrap now also tolerates.
    return json.dumps(
        {
            "matched": "boolean",
            "block_id": list(schema.block_ids),
            "confidence": "number between 0 and 1",
            "extras": (
                "a FLAT object; only keys allowed for the chosen block_id "
                "(see extras_allowed_per_block), or {}"
            ),
            "extras_allowed_per_block": {
                block_id: {key: list(values) for key, values in extras.items()}
                for block_id, extras in schema.extras_per_block.items()
            },
        },
        separators=(",", ":"),
    )


def _extract_message_text(response: Any) -> str:
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif hasattr(item, "text"):
                    parts.append(str(item.text))
            return "".join(parts)
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message") or {}
            if isinstance(message, dict):
                return str(message.get("content", ""))
    return str(response)


def _parse_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise RuntimeError(f"OpenAI-compatible runtime returned non-object JSON: {text!r}")
    return data


def _validate_output(data: dict[str, Any], schema: StructuredOutputSchema) -> dict[str, Any]:
    if not isinstance(data.get("matched"), bool):
        raise RuntimeError("matched must be a boolean")
    block_id = data.get("block_id")
    # An honest no-match: an unconstrained model says `matched: false` with a
    # null block_id where the grammar-constrained runtimes are forced to name a
    # block anyway. The router's own normalizer (`intent_router._to_intent_tag`)
    # already accepts exactly this; rejecting it here turned honesty into a
    # classify failure. Normalize to the no-match shape and skip block checks.
    if data["matched"] is False and block_id is None:
        return {"matched": False, "block_id": None, "confidence": 0.0, "extras": {}}
    if block_id not in schema.block_ids:
        raise RuntimeError(f"block_id {block_id!r} is not in allowed set {schema.block_ids!r}")
    confidence = data.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        raise RuntimeError(f"confidence must be a number in [0, 1], got {confidence!r}")
    extras = data.get("extras")
    if not isinstance(extras, dict):
        raise RuntimeError("extras must be an object")
    # Tolerate the nested reading: a model that mirrors the per-block reference
    # table returns `extras: {"<chosen block_id>": {...}}`. Unwrap exactly that
    # shape (one key, equal to block_id, dict value) before validating flat.
    if len(extras) == 1 and str(block_id) in extras and isinstance(extras[str(block_id)], dict):
        extras = extras[str(block_id)]
        data = dict(data)
        data["extras"] = extras
    allowed_extras = schema.extras_per_block.get(str(block_id), {})
    for key, value in extras.items():
        allowed_values = allowed_extras.get(str(key))
        if allowed_values is None:
            raise RuntimeError(f"extra key {key!r} is not allowed for block {block_id!r}")
        if str(value) not in allowed_values:
            raise RuntimeError(
                f"extra {key!r} value {value!r} is not in allowed set {allowed_values!r}"
            )
    return data
