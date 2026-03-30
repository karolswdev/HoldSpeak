"""Meeting intelligence extraction for local and cloud providers.

`MeetingIntel` can run using:
- local GGUF models via llama-cpp-python
- OpenAI chat models in the cloud

The model is prompted to return JSON-only output for reliable parsing.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
from urllib.parse import urlparse
from collections.abc import Iterator
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .logging_config import get_logger

log = get_logger("intel")

try:
    from llama_cpp import Llama

    log.debug("llama_cpp imported successfully")
except Exception as exc:  # pragma: no cover
    Llama = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
    # This dependency is optional; avoid noisy errors during normal voice-typing usage.
    log.debug(f"llama_cpp not available: {exc}")
else:  # pragma: no cover
    _IMPORT_ERROR = None

try:
    from openai import OpenAI
except Exception as exc:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]
    _OPENAI_IMPORT_ERROR = exc
    log.debug(f"openai not available: {exc}")
else:  # pragma: no cover
    _OPENAI_IMPORT_ERROR = None


DEFAULT_INTEL_MODEL_PATH = "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"
DEFAULT_INTEL_PROVIDER = "local"
DEFAULT_INTEL_CLOUD_MODEL = "gpt-5-mini"
DEFAULT_INTEL_CLOUD_API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 20.0
VALID_INTEL_PROVIDERS = frozenset({"local", "cloud", "auto"})


class MeetingIntelError(RuntimeError):
    """Raised when MeetingIntel analysis fails."""


def _generate_action_item_id(task: str, owner: Optional[str] = None) -> str:
    """Generate a unique ID for an action item based on task text."""
    content = f"{task}:{owner or ''}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]


@dataclass
class ActionItem:
    """A captured action item from the meeting."""

    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
    id: str = ""  # Unique ID for tracking
    status: str = "pending"  # pending, done, dismissed
    review_state: str = "pending"  # pending, accepted
    reviewed_at: Optional[str] = None
    source_timestamp: Optional[float] = None  # Link to transcript timestamp
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def __post_init__(self) -> None:
        """Generate ID if not provided."""
        if not self.id:
            self.id = _generate_action_item_id(self.task, self.owner)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def mark_done(self) -> None:
        """Mark this action item as done."""
        self.status = "done"
        self.completed_at = datetime.now().isoformat()

    def dismiss(self) -> None:
        """Dismiss this action item."""
        self.status = "dismissed"
        self.completed_at = datetime.now().isoformat()

    def accept(self) -> None:
        """Mark this action item as reviewed/accepted."""
        self.review_state = "accepted"
        self.reviewed_at = datetime.now().isoformat()


@dataclass
class IntelResult:
    topics: list[str]
    action_items: list[ActionItem]
    summary: str
    raw_response: str
    error: Optional[str] = None


def _normalize_provider(provider: Optional[str]) -> str:
    value = (provider or DEFAULT_INTEL_PROVIDER).strip().lower()
    if value not in VALID_INTEL_PROVIDERS:
        return DEFAULT_INTEL_PROVIDER
    return value


def _resolve_cloud_api_key(api_key_env: Optional[str]) -> Optional[str]:
    env_name = (api_key_env or DEFAULT_INTEL_CLOUD_API_KEY_ENV).strip()
    if not env_name:
        env_name = DEFAULT_INTEL_CLOUD_API_KEY_ENV
    value = os.environ.get(env_name)
    if value:
        return value.strip() or None
    return None


def _validate_base_url(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    value = base_url.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return f"Invalid cloud base URL: {value}"
    return None


def get_local_intel_runtime_status(
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
) -> tuple[bool, Optional[str]]:
    """Return whether local meeting intelligence can run right now."""
    if Llama is None:
        return False, "llama-cpp-python is not available"

    resolved = Path(model_path).expanduser()
    if not resolved.exists():
        return False, f"Intel model not found: {resolved}"

    return True, None


def get_cloud_intel_runtime_status(
    *,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Return whether cloud meeting intelligence can run right now."""
    if OpenAI is None:
        return False, "openai package is not available"

    if not (cloud_model or "").strip():
        return False, "Cloud intel model is not configured"

    base_url_error = _validate_base_url(cloud_base_url)
    if base_url_error is not None:
        return False, base_url_error

    if not _resolve_cloud_api_key(cloud_api_key_env):
        return False, f"Missing API key in ${cloud_api_key_env}"

    return True, None


def resolve_intel_provider(
    provider: str = DEFAULT_INTEL_PROVIDER,
    *,
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Resolve the active provider for this runtime.

    Returns:
        (provider, None) on success where provider is "local" or "cloud".
        (None, reason) when unavailable.
    """
    normalized = _normalize_provider(provider)

    if normalized == "local":
        ok, reason = get_local_intel_runtime_status(model_path)
        return ("local", None) if ok else (None, reason)

    if normalized == "cloud":
        ok, reason = get_cloud_intel_runtime_status(
            cloud_model=cloud_model,
            cloud_api_key_env=cloud_api_key_env,
            cloud_base_url=cloud_base_url,
        )
        return ("cloud", None) if ok else (None, reason)

    # auto = local-first fallback to cloud
    local_ok, local_reason = get_local_intel_runtime_status(model_path)
    if local_ok:
        return "local", None

    cloud_ok, cloud_reason = get_cloud_intel_runtime_status(
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    if cloud_ok:
        return "cloud", None

    return (
        None,
        "Local intel unavailable"
        f" ({local_reason}); cloud intel unavailable ({cloud_reason})",
    )


def get_intel_runtime_status(
    model_path: str = DEFAULT_INTEL_MODEL_PATH,
    *,
    provider: str = DEFAULT_INTEL_PROVIDER,
    cloud_model: str = DEFAULT_INTEL_CLOUD_MODEL,
    cloud_api_key_env: str = DEFAULT_INTEL_CLOUD_API_KEY_ENV,
    cloud_base_url: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Return whether the configured meeting-intel mode can run right now."""
    active, reason = resolve_intel_provider(
        provider,
        model_path=model_path,
        cloud_model=cloud_model,
        cloud_api_key_env=cloud_api_key_env,
        cloud_base_url=cloud_base_url,
    )
    if active is None:
        return False, reason
    return True, None


def _json_only_messages(transcript: str) -> list[dict[str, str]]:
    schema = {
        "topics": ["<short topic>", "..."],
        "action_items": [
            {"task": "<task>", "owner": "Me|Remote|null", "due": "<date or null>"},
        ],
        "summary": "<short summary>",
    }

    return [
        {
            "role": "system",
            "content": (
                "You are a meeting intelligence assistant.\n"
                "Return ONLY a single valid JSON object and nothing else.\n"
                "Do not wrap in markdown or code fences.\n"
                "Do not add explanations.\n"
                "If a field is unknown, use null or an empty list.\n"
            ),
        },
        {
            "role": "user",
            "content": (
                "Analyze this transcript and extract meeting intelligence.\n\n"
                "Output JSON with this exact shape:\n"
                f"{json.dumps(schema, ensure_ascii=False)}\n\n"
                "Transcript:\n"
                f"{transcript}\n"
            ),
        },
    ]


def _extract_json(text: str) -> Optional[dict]:
    s = text.strip()
    if not s:
        return None

    # Remove common wrappers like ```json ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)

    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # Best-effort recovery: find the first JSON object in the text.
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = s[start : end + 1].strip()
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _coerce_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            out.append(str(item).strip())
        return [t for t in out if t]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def _coerce_action_items(value: object) -> list[ActionItem]:
    if not isinstance(value, list):
        return []

    items: list[ActionItem] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        task = str(entry.get("task", "")).strip()
        if not task:
            continue
        owner = entry.get("owner", None)
        due = entry.get("due", None)
        items.append(
            ActionItem(
                task=task,
                owner=(None if owner in (None, "", "null") else str(owner).strip()),
                due=(None if due in (None, "", "null") else str(due).strip()),
            )
        )
    return items


def _extract_openai_message_text(content: object) -> str:
    """Extract text from OpenAI SDK message content variants."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    parts.append(str(text_value))
                    continue
                nested = item.get("content")
                if nested:
                    parts.append(str(nested))
                    continue
                if "type" in item and item.get("type") == "output_text" and item.get("text"):
                    parts.append(str(item["text"]))
                    continue
            else:
                text_attr = getattr(item, "text", None)
                if text_attr:
                    parts.append(str(text_attr))
        return "".join(parts)
    return str(content)


def _extract_status_code(exc: BaseException) -> Optional[int]:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value

    response = getattr(exc, "response", None)
    if response is not None:
        for attr in ("status_code", "status"):
            value = getattr(response, attr, None)
            if isinstance(value, int):
                return value
    return None


def _describe_cloud_exception(exc: BaseException, *, model: str, base_url: Optional[str]) -> str:
    endpoint = (base_url or "https://api.openai.com/v1").strip() or "https://api.openai.com/v1"
    message = str(exc).strip() or exc.__class__.__name__
    message_lower = message.lower()
    exc_name = exc.__class__.__name__.lower()
    status_code = _extract_status_code(exc)

    if status_code in {401, 403} or "unauthorized" in message_lower or "forbidden" in message_lower:
        return f"Cloud auth failed for {endpoint}: {message}"

    if (
        "model" in message_lower
        and ("not found" in message_lower or "does not exist" in message_lower or "unknown" in message_lower)
    ) or (status_code == 404 and "model" in message_lower):
        return f"Cloud model '{model}' not found at {endpoint}: {message}"

    if status_code == 404:
        return f"Cloud endpoint not found at {endpoint}: {message}"

    if status_code == 429 or "rate limit" in message_lower:
        return f"Cloud rate limit hit at {endpoint}: {message}"

    if status_code is not None and status_code >= 500:
        return f"Cloud server error ({status_code}) at {endpoint}: {message}"

    if (
        isinstance(exc, (TimeoutError, socket.timeout))
        or "timeout" in exc_name
        or "timed out" in message_lower
        or "read timeout" in message_lower
    ):
        return f"Cloud request timed out to {endpoint}: {message}"

    if isinstance(exc, ConnectionRefusedError):
        return f"Cloud connection refused by {endpoint}: {message}"

    if isinstance(exc, socket.gaierror):
        return f"Cloud DNS resolution failed for {endpoint}: {message}"

    if (
        "connection" in exc_name
        or "connection" in message_lower
        or "name or service not known" in message_lower
        or "temporary failure in name resolution" in message_lower
        or "failed to establish a new connection" in message_lower
    ):
        return f"Cloud connection failed to {endpoint}: {message}"

    return f"Cloud request failed at {endpoint}: {message}"


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
        max_tokens: int = 800,
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

        self._llm: Optional["Llama"] = None
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

        if OpenAI is None:
            raise MeetingIntelError(
                "openai package is not available. Install dependencies first."
            ) from _OPENAI_IMPORT_ERROR

        api_key = _resolve_cloud_api_key(self.cloud_api_key_env)
        if not api_key:
            raise MeetingIntelError(f"Missing API key in ${self.cloud_api_key_env}")

        kwargs: dict[str, object] = {"api_key": api_key}
        if self.cloud_base_url:
            kwargs["base_url"] = self.cloud_base_url
        kwargs["timeout"] = self.cloud_timeout_seconds

        try:
            self._openai_client = OpenAI(**kwargs)
        except Exception as exc:
            raise MeetingIntelError(f"Failed to initialize OpenAI client: {exc}") from exc

    def _ensure_local_model_loaded(self) -> None:
        if self._llm is not None:
            return

        if Llama is None:
            raise MeetingIntelError(
                "llama-cpp-python is not available. Install dependencies first."
            ) from _IMPORT_ERROR

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
            self._llm = Llama(**kwargs)  # type: ignore[arg-type]
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
