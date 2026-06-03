"""The `MeetingIntel` engine (HS-34-04).

`OpenAI`/`Llama` are read via the package (`_intel_pkg`) so the cloud/local
monkeypatches (incl. the egress-invariant test) reach the engine.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional, Union

import holdspeak.intel as _intel_pkg

from ..logging_config import get_logger
from .models import (
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

    @property
    def active_provider(self) -> Optional[str]:
        return self._active_provider

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
            raise MeetingIntelError(f"Intel model not found: {model_path}")

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
        else:
            self._ensure_openai_client_loaded()

    def _ensure_model_loaded(self) -> None:
        """Backward-compatible alias for older tests/callers."""
        self._ensure_runtime_loaded()

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
        base_kwargs: dict[str, object] = {
            "model": self.cloud_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra_body": {"thinking": False},
        }
        if self.cloud_reasoning_effort:
            base_kwargs["reasoning_effort"] = self.cloud_reasoning_effort
        if self.cloud_store:
            base_kwargs["store"] = True

        try:
            try:
                response = self._openai_client.chat.completions.create(**base_kwargs)
            except TypeError as exc:
                # Compatibility fallback for clients/endpoints that use max_completion_tokens.
                if "max_tokens" not in str(exc):
                    raise
                fallback_kwargs = dict(base_kwargs)
                fallback_kwargs.pop("max_tokens", None)
                fallback_kwargs["max_completion_tokens"] = max_tokens
                response = self._openai_client.chat.completions.create(**fallback_kwargs)
        except Exception as exc:
            raise MeetingIntelError(
                _describe_cloud_exception(
                    exc,
                    model=self.cloud_model,
                    base_url=self.cloud_base_url,
                )
            ) from exc

        raw = response.choices[0].message.content if response.choices else ""
        return _extract_openai_message_text(raw)

    def _analyze_once(self, transcript: str) -> IntelResult:
        messages = _json_only_messages(transcript)
        try:
            raw_text = self._chat_completion_text(
                messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except MeetingIntelError:
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
            action_items=_coerce_action_items(data.get("action_items", [])),
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
        """Stream analysis when available.

        Cloud mode currently emits only the final IntelResult.
        """
        raw_parts: list[str] = []

        try:
            self._ensure_model_loaded()
        except Exception as exc:
            log.error(f"Intel analyze(stream=True) failed to start: {exc}", exc_info=True)
            yield IntelResult(
                topics=[],
                action_items=[],
                summary="",
                raw_response=f"ERROR: {exc}",
                error=str(exc),
            )
            return

        if self._active_provider == "cloud":
            try:
                yield self._analyze_once(transcript)
            except Exception as exc:
                yield IntelResult(
                    topics=[],
                    action_items=[],
                    summary="",
                    raw_response=f"ERROR: {exc}",
                    error=str(exc),
                )
            return

        try:
            assert self._llm is not None
            messages = _json_only_messages(transcript)
            stream_iter = self._llm.create_chat_completion(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
        except Exception as exc:
            log.error(f"Intel analyze(stream=True) failed to start: {exc}", exc_info=True)
            yield IntelResult(
                topics=[],
                action_items=[],
                summary="",
                raw_response=f"ERROR: {exc}",
                error=str(exc),
            )
            return

        try:
            for chunk in stream_iter:
                try:
                    choice0 = (chunk.get("choices") or [{}])[0]
                    delta = choice0.get("delta") or {}
                    piece = delta.get("content")
                    if piece is None:
                        piece = choice0.get("text")
                    if not piece:
                        continue
                    text_piece = str(piece)
                except Exception:
                    continue

                raw_parts.append(text_piece)
                yield text_piece
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

        except Exception as exc:
            log.error(f"Title generation failed: {exc}", exc_info=True)
            return None

    def generate_bookmark_label(self, context: str, max_words: int = 5) -> Optional[str]:
        """Generate a concise bookmark label from context.

        Args:
            context: Transcript text around the bookmark (±10 seconds).
            max_words: Maximum words in generated label.

        Returns:
            Generated label string, or None if generation failed.
        """
        if not context.strip():
            return None

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"Generate a concise bookmark label (2-{max_words} words) that captures "
                        "the key topic being discussed. Return ONLY the label text, nothing else. "
                        "No quotes, no punctuation, no explanation. Examples: "
                        "'Budget Discussion', 'Project Timeline', 'Next Steps', 'Key Decision'"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Label this moment:\n\n{context[:500]}",
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
            # Remove "Label:" prefix if present
            if label.lower().startswith("label:"):
                label = label[6:].strip()

            log.info(f"Generated bookmark label: {label}")
            return label if label else None

        except Exception as exc:
            log.error(f"Bookmark label generation failed: {exc}", exc_info=True)
            return None

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

        except Exception as exc:
            log.error(f"Refined bookmark label generation failed: {exc}", exc_info=True)
            return None
