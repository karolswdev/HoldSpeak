"""The `MeetingIntel` engine (HS-34-04).

`OpenAI`/`Llama` are read via the package (`_intel_pkg`) so the cloud/local
monkeypatches (incl. the egress-invariant test) reach the engine.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Callable, Optional, Union
from urllib.parse import urlsplit

import holdspeak.intel as _intel_pkg

from ..kernel.external_egress import run_external_egress
from ..kernel.provider_signals import ProviderCompatibilityRetry
from ..logging_config import get_logger
from .endpoint_health import default_health as _endpoint_health
from .models import (
    DEFAULT_CLOUD_BASE_URL,
    DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    DEFAULT_INTEL_CLOUD_MODEL,
    DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS,
    DEFAULT_INTEL_MODEL_PATH,
    DEFAULT_INTEL_PROVIDER,
    IntelResult,
    MeetingIntelError,
)
from .parsing import (
    _coerce_action_items,
    _coerce_str_list,
    _describe_cloud_exception,
    _extract_json,
    _extract_openai_message_text,
    _json_only_messages,
)
from .providers import (
    _effective_cloud_api_key,
    _normalize_provider,
    resolve_intel_provider,
)

log = get_logger("intel")

#: Endpoint keys (`_cloud_endpoint_key()`) that answered `max_tokens` with a
#: TypeError and therefore speak `max_completion_tokens` (HS-131-10).
#:
#: This is the same shape as `_endpoint_health`: a process-local memory of what
#: an endpoint just told us about itself. It exists so the compatibility retry
#: needs exactly ONE physical request per attempt — the first attempt learns the
#: dialect and refuses by name, the SECOND admitted child speaks it immediately —
#: instead of the old hidden second `.create` under one receipt.
_COMPAT_MAX_COMPLETION_TOKENS: set[str] = set()


def endpoint_speaks_max_completion_tokens(endpoint_key: str) -> bool:
    """Whether this endpoint has already rejected ``max_tokens`` in this process."""
    return str(endpoint_key) in _COMPAT_MAX_COMPLETION_TOKENS


def forget_endpoint_dialects() -> None:
    """Drop every learned dialect (tests; a new process starts empty anyway)."""
    _COMPAT_MAX_COMPLETION_TOKENS.clear()


def _token_budget_kwargs(endpoint_key: str, max_tokens: int) -> dict[str, object]:
    """The token-budget parameter THIS endpoint accepts, as its own one entry."""
    if endpoint_speaks_max_completion_tokens(endpoint_key):
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


def _compat_signal(exc: BaseException) -> BaseException:
    """The typed signal an admitted caller turns into a second child."""
    return ProviderCompatibilityRetry("max_completion_tokens", str(exc))


def _compatibility_retry(endpoint_key: str, exc: BaseException) -> bool:
    """True when the ONE named dialect fallback applies to this failure.

    Records what the endpoint said, so the next admitted child gets it right on
    its first request. Anything else is an honest provider failure.
    """
    if not isinstance(exc, TypeError) or "max_tokens" not in str(exc):
        return False
    if endpoint_speaks_max_completion_tokens(endpoint_key):
        return False  # already speaking the dialect: this is a real failure
    _COMPAT_MAX_COMPLETION_TOKENS.add(str(endpoint_key))
    return True


class MeetingIntel:
    """Extract structured meeting intelligence via local or cloud provider."""

    def __init__(
        self,
        *,
        provider: str = DEFAULT_INTEL_PROVIDER,
        model_path: str = DEFAULT_INTEL_MODEL_PATH,
        cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
        cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
        cloud_base_url: Optional[str] = None,
        cloud_reasoning_effort: Optional[str] = None,
        cloud_store: bool = False,
        cloud_timeout_seconds: float = DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS,
        chat_format: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = -1,  # -1 = offload all layers to GPU (Metal on Apple Silicon)
        temperature: float = 0.2,
        max_tokens: int = 3000,
    ) -> None:
        self.provider = _normalize_provider(provider)
        self.model_path = model_path
        self.cloud_model = cloud_model
        self.cloud_api_key_env = cloud_api_key_env
        self.cloud_base_url = cloud_base_url
        self.cloud_reasoning_effort = cloud_reasoning_effort
        self.cloud_store = cloud_store
        self.cloud_timeout_seconds = max(1.0, float(cloud_timeout_seconds))
        self.chat_format = chat_format
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._llm: Optional[Any] = None
        self._openai_client = None
        self._active_provider: Optional[str] = None
        self._active_model: str = ""

    @property
    def active_provider(self) -> Optional[str]:
        return self._active_provider

    @property
    def active_model(self) -> str:
        """The model this engine ACTUALLY loaded — blank until it has (HS-132-09).

        The canonical prompt adapter reads this to stamp the executed model onto
        every receipt. ``MeetingIntel`` used to define neither ``active_model``
        nor ``model``, so the adapter's report was ALWAYS ``''`` and every
        consumer fell back to a describer that had never seen this engine: an
        Ask on ``this_machine`` (pinned local) printed the hub's cloud model id.

        It is a plain read of what ``_ensure_runtime_loaded`` recorded when the
        provider actually loaded — never a lazy load of its own, so naming it
        cannot execute anything.
        """
        return self._active_model

    def _resolved_model_path(self) -> Path:
        return Path(self.model_path).expanduser()

    def _ensure_openai_client_loaded(self) -> None:
        if self._openai_client is not None:
            return

        if _intel_pkg.OpenAI is None:
            raise MeetingIntelError(
                "openai package is not available. Install dependencies first."
            ) from _intel_pkg._OPENAI_IMPORT_ERROR

        api_key = _effective_cloud_api_key(self.cloud_api_key_env, self.cloud_base_url)
        if not api_key:
            raise MeetingIntelError(f"Missing API key in ${self.cloud_api_key_env}")

        kwargs: dict[str, object] = {"api_key": api_key}
        if self.cloud_base_url:
            kwargs["base_url"] = self.cloud_base_url
        kwargs["timeout"] = self.cloud_timeout_seconds

        try:
            self._openai_client = _intel_pkg.OpenAI(**kwargs)
        except Exception as exc:
            raise MeetingIntelError(f"Failed to initialize OpenAI client: {exc}") from exc

    def _ensure_local_model_loaded(self) -> None:
        if self._llm is not None:
            return

        if _intel_pkg.Llama is None:
            raise MeetingIntelError(
                "llama-cpp-python is not available. Install dependencies first."
            ) from _intel_pkg._IMPORT_ERROR

        model_path = self._resolved_model_path()
        if not model_path.exists():
            raise MeetingIntelError(
                "No language model on this hub. Pick one in Settings under"
                " Intelligence."
            )

        kwargs: dict[str, object] = {
            "model_path": str(model_path),
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,  # -1 = all layers on GPU
        }
        if self.chat_format:
            kwargs["chat_format"] = self.chat_format
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads

        log.info(f"Loading intel model: {model_path}")
        try:
            self._llm = _intel_pkg.Llama(**kwargs)  # type: ignore[arg-type]
        except Exception as exc:
            log.error(f"Failed to load intel model: {exc}", exc_info=True)
            raise MeetingIntelError(f"Failed to load intel model: {exc}") from exc

    def _ensure_runtime_loaded(self) -> None:
        if self._active_provider is None:
            provider, reason = resolve_intel_provider(
                self.provider,
                model_path=self.model_path,
                cloud_model=self.cloud_model,
                cloud_api_key_env=self.cloud_api_key_env,
                cloud_base_url=self.cloud_base_url,
            )
            if provider is None:
                raise MeetingIntelError(reason or "No compatible intel provider available")
            self._active_provider = provider

        if self._active_provider == "local":
            self._ensure_local_model_loaded()
            # Recorded AFTER the load succeeds, from the path that was loaded:
            # the receipt's executed-model is a report, not an intention.
            self._active_model = self._resolved_model_path().stem
        else:
            self._ensure_openai_client_loaded()
            self._active_model = str(self.cloud_model or "")

    def _ensure_model_loaded(self) -> None:
        """Backward-compatible alias for older tests/callers."""
        self._ensure_runtime_loaded()

    def _cloud_endpoint_key(self) -> str:
        """HS-103-04: the breaker's identity for this engine's cloud
        endpoint — the base URL when self-hosted, else the model name (the
        default OpenAI endpoint is one shared identity)."""
        return f"cloud:{self.cloud_base_url or self.cloud_model}"

    def _remote_completion(self, sender: Callable[..., Any], values: dict[str, object]) -> Any:
        """Dispatch one remote model invocation under its egress warrant."""
        endpoint = urlsplit(self.cloud_base_url or DEFAULT_CLOUD_BASE_URL)
        destination = (endpoint.hostname or "invalid-model-endpoint").lower()
        if endpoint.port:
            destination += f":{endpoint.port}"
        return run_external_egress(
            connector_id="meeting-intel-openai-compatible",
            destination=destination,
            data_classes=("model_input",),
            payload_material=values,
            sender=sender,
            kwargs=values,
            allowed_destinations=(destination,),
        )

    def _chat_completion_text(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        self._ensure_model_loaded()

        if self._active_provider == "local":
            assert self._llm is not None
            response = self._llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            raw = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return str(raw)

        assert self._openai_client is not None
        # HS-103-04: fail fast, honestly, without attempting the network call
        # at all, when this endpoint has just failed several times in a row.
        endpoint_key = self._cloud_endpoint_key()
        ok, refusal = _endpoint_health.check(endpoint_key)
        if not ok:
            raise MeetingIntelError(refusal or "endpoint unreachable")

        base_kwargs: dict[str, object] = {
            "model": self.cloud_model,
            "messages": messages,
            "temperature": temperature,
            "extra_body": {"thinking": False},
            **_token_budget_kwargs(endpoint_key, max_tokens),
        }
        if self.cloud_reasoning_effort:
            base_kwargs["reasoning_effort"] = self.cloud_reasoning_effort
        if self.cloud_store:
            base_kwargs["store"] = True

        started = time.monotonic()
        try:
            # HS-131-10 (Sol Amendment 3): ONE physical request per admitted child.
            # The `max_completion_tokens` fallback used to fire a second `.create`
            # right here, inside the same child and under the same receipt. It is
            # now a NAMED signal the runner turns into a second admitted child.
            response = self._remote_completion(self._openai_client.chat.completions.create, base_kwargs)
        except Exception as exc:
            if _compatibility_retry(endpoint_key, exc):
                raise _compat_signal(exc) from exc
            _endpoint_health.record_failure(endpoint_key)
            raise MeetingIntelError(
                _describe_cloud_exception(
                    exc,
                    model=self.cloud_model,
                    base_url=self.cloud_base_url,
                )
            ) from exc
        _endpoint_health.record_success(
            endpoint_key, latency_ms=(time.monotonic() - started) * 1000
        )

        raw = response.choices[0].message.content if response.choices else ""
        return _extract_openai_message_text(raw)

    def _chat_completion_stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        """Stream text deltas from the active provider (local GGUF OR cloud).

        The streaming twin of `_chat_completion_text`. The cloud branch forwards
        the OpenAI-compatible endpoint's SSE deltas (`.43`/llama.cpp, Ollama,
        vLLM, a real API), so endpoint intel streams token-by-token like the
        local model — which is what lights the generation theater's "thinking"
        pulse and the Queue HUD heartbeat for endpoint users.
        """
        self._ensure_model_loaded()

        if self._active_provider == "local":
            assert self._llm is not None
            stream_iter = self._llm.create_chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            for chunk in stream_iter:
                try:
                    choice0 = (chunk.get("choices") or [{}])[0]
                    delta = choice0.get("delta") or {}
                    piece = delta.get("content")
                    if piece is None:
                        piece = choice0.get("text")
                except Exception:
                    continue
                if piece:
                    yield str(piece)
            return

        assert self._openai_client is not None
        endpoint_key = self._cloud_endpoint_key()
        base_kwargs: dict[str, object] = {
            "model": self.cloud_model,
            "messages": messages,
            "temperature": temperature,
            "extra_body": {"thinking": False},
            "stream": True,
            **_token_budget_kwargs(endpoint_key, max_tokens),
        }
        if self.cloud_reasoning_effort:
            base_kwargs["reasoning_effort"] = self.cloud_reasoning_effort
        if self.cloud_store:
            base_kwargs["store"] = True

        try:
            # The streaming twin of the non-streaming leg: ONE physical stream
            # open per admitted child; the dialect fallback is the runner's second
            # child, never a hidden second open under this one's receipt.
            stream_iter = self._remote_completion(self._openai_client.chat.completions.create, base_kwargs)
        except Exception as exc:
            if _compatibility_retry(endpoint_key, exc):
                raise _compat_signal(exc) from exc
            raise MeetingIntelError(
                _describe_cloud_exception(
                    exc,
                    model=self.cloud_model,
                    base_url=self.cloud_base_url,
                )
            ) from exc

        for chunk in stream_iter:
            try:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                piece = getattr(delta, "content", None) if delta is not None else None
            except Exception:
                continue
            if piece:
                yield str(piece)

    def run_prompt(
        self,
        *,
        system_prompt: str = "",
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Run a freeform chat completion and return the raw text.

        The generic seam the Primitive Framework uses to RUN a saved Agent persona
        on the hub: a persona's `system_prompt` + rendered `user_template` go in,
        the model's text comes out, through the same local/cloud provider plumbing
        the meeting intel engine already uses (so a persona honours the user's
        configured endpoint). No JSON coercion — personas produce free text.
        """
        from ..constitutional_context import constitutional_system_message
        constitutional = constitutional_system_message()
        messages: list[dict[str, str]] = []
        if constitutional:
            messages.append({"role": "system", "content": constitutional})
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        try:
            return self._chat_completion_text(
                messages,
                temperature=self.temperature if temperature is None else temperature,
                max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            )
        except (MeetingIntelError, ProviderCompatibilityRetry):
            # The dialect signal is the runner's to act on: swallowing it here
            # would put a second physical request back under one receipt.
            raise
        except Exception as exc:
            log.error(f"Persona run failed: {exc}", exc_info=True)
            raise MeetingIntelError(f"Persona run failed: {exc}") from exc

    def _analyze_once(self, transcript: str) -> IntelResult:
        messages = _json_only_messages(transcript)
        try:
            raw_text = self._chat_completion_text(
                messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except (MeetingIntelError, ProviderCompatibilityRetry):
            raise
        except Exception as exc:
            log.error(f"Intel inference failed: {exc}", exc_info=True)
            raise MeetingIntelError(f"Intel inference failed: {exc}") from exc

        data = _extract_json(raw_text)
        if data is None:
            log.warning("Failed to parse JSON intel response")
            return IntelResult(
                topics=[],
                action_items=[],
                summary="",
                raw_response=raw_text,
            )

        return IntelResult(
            topics=_coerce_str_list(data.get("topics", [])),
            action_items=_coerce_action_items(
                data.get("action_items", data.get("actionItems", data.get("actions", [])))
            ),
            summary=str(data.get("summary", "")).strip(),
            raw_response=raw_text,
        )

    def analyze(
        self, transcript: str, *, stream: bool = False
    ) -> Union[IntelResult, Iterator[Union[str, IntelResult]]]:
        """Analyze transcript and return structured intelligence.

        Args:
            transcript: Full transcript text to analyze.
            stream: If True, returns a generator yielding streamed text chunks
                followed by a final `IntelResult` as the last yielded item.

        Returns:
            IntelResult when stream=False.
            When stream=True: an iterator of streamed chunks, ending with the
            final IntelResult.
        """

        if not stream:
            try:
                return self._analyze_once(transcript)
            except ProviderCompatibilityRetry:
                raise
            except Exception as exc:
                log.error(f"Intel analyze failed: {exc}", exc_info=True)
                return IntelResult(
                    topics=[],
                    action_items=[],
                    summary="",
                    raw_response=f"ERROR: {exc}",
                    error=str(exc),
                )

        return self._analyze_stream(transcript)

    def _analyze_stream(self, transcript: str) -> Iterator[Union[str, IntelResult]]:
        """Stream analysis token-by-token, then a final parsed IntelResult.

        Both providers stream now: the local GGUF and the cloud/endpoint path
        (the latter forwards the endpoint's SSE deltas via
        `_chat_completion_stream`). So the live meeting intel broadcasts
        `intel_token` for endpoint users too — lighting the generation theater's
        "thinking" pulse and the Queue HUD heartbeat, not only for local models.
        """
        raw_parts: list[str] = []
        messages = _json_only_messages(transcript)

        try:
            for piece in self._chat_completion_stream(
                messages, temperature=self.temperature, max_tokens=self.max_tokens
            ):
                raw_parts.append(piece)
                yield piece
        except ProviderCompatibilityRetry:
            raise
        except Exception as exc:
            log.error(f"Intel streaming failed: {exc}", exc_info=True)
            yield IntelResult(
                topics=[],
                action_items=[],
                summary="",
                raw_response=f"ERROR: {exc}",
                error=str(exc),
            )
            return

        raw_text = "".join(raw_parts)
        data = _extract_json(raw_text)
        if data is None:
            log.warning("Failed to parse JSON intel response (streaming)")
            yield IntelResult(
                topics=[],
                action_items=[],
                summary="",
                raw_response=raw_text,
            )
            return

        yield IntelResult(
            topics=_coerce_str_list(data.get("topics", [])),
            action_items=_coerce_action_items(data.get("action_items", [])),
            summary=str(data.get("summary", "")).strip(),
            raw_response=raw_text,
        )

    def generate_title(self, transcript: str, max_words: int = 8) -> Optional[str]:
        """Generate a concise meeting title from transcript.

        Args:
            transcript: Full transcript text.
            max_words: Maximum words in generated title.

        Returns:
            Generated title string, or None if generation failed.
        """
        if not transcript.strip():
            return None

        try:
            # Truncate transcript for faster processing
            truncated = transcript[:3000] if len(transcript) > 3000 else transcript

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Generate a concise meeting title (3-{max_words} words). "
                        "Return ONLY the title text, nothing else. "
                        "No quotes, no punctuation at the end, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Generate a title for this meeting transcript:\n\n{truncated}",
                },
            ]

            title = self._chat_completion_text(
                messages,
                temperature=0.3,
                max_tokens=30,
            ).strip()

            # Clean up common LLM artifacts
            title = title.strip('"\'')
            title = title.rstrip('.')
            # Remove "Title:" prefix if present
            if title.lower().startswith("title:"):
                title = title[6:].strip()

            log.info(f"Generated meeting title: {title}")
            return title if title else None

        except ProviderCompatibilityRetry:
            raise
        except Exception as exc:
            log.error(f"Title generation failed: {exc}", exc_info=True)
            return None

    # HS-131-17: the context-only `generate_bookmark_label(context)` leaf is
    # DELETED. Its only caller was the session's direct background thread, which
    # now goes through the admitted `bookmark-label` child;
    # `generate_bookmark_label_with_context` below is the ONE bookmark-label leaf
    # both the live and the deferred admitted children dispatch. The retired name
    # stays in the one-path census vocabulary, so typing it again fails the fence.

    def generate_bookmark_label_with_context(
        self,
        local_context: str,
        meeting_summary: str = "",
        max_words: int = 5,
    ) -> Optional[str]:
        """Generate a refined bookmark label using meeting context.

        This is called during final analysis to improve bookmark labels with
        the full meeting summary providing grounding context.

        Args:
            local_context: Transcript text around the bookmark (±10 seconds).
            meeting_summary: High-level summary of the entire meeting for grounding.
            max_words: Maximum words in generated label.

        Returns:
            Generated label string, or None if generation failed.
        """
        if not local_context.strip():
            return None

        try:
            # Build context with meeting summary for grounding
            grounding = ""
            if meeting_summary:
                grounding = f"Meeting context: {meeting_summary[:300]}\n\n"

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Generate a concise bookmark label (2-{max_words} words) that captures "
                        "the specific topic at this moment in the meeting. "
                        "Use the meeting context for grounding but focus on the specific moment. "
                        "Return ONLY the label text, nothing else. "
                        "No quotes, no punctuation, no explanation. Examples: "
                        "'Budget Approval', 'Q3 Timeline', 'Action Items Review', 'Risk Discussion'"
                    ),
                },
                {
                    "role": "user",
                    "content": f"{grounding}Bookmarked moment:\n{local_context[:500]}",
                },
            ]

            label = self._chat_completion_text(
                messages,
                temperature=0.3,
                max_tokens=20,
            ).strip()
            # Clean up common LLM artifacts
            label = label.strip('"\'')
            label = label.rstrip('.')
            if label.lower().startswith("label:"):
                label = label[6:].strip()

            log.info(f"Generated refined bookmark label: {label}")
            return label if label else None

        except ProviderCompatibilityRetry:
            raise
        except Exception as exc:
            log.error(f"Refined bookmark label generation failed: {exc}", exc_info=True)
            return None
