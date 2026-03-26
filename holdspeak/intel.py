"""Local meeting intelligence extraction using llama-cpp-python.

`MeetingIntel` lazily loads a GGUF model and analyzes transcript text to extract:
- topics
- action items
- summary

The model is prompted to return JSON-only output for reliable parsing.
"""

from __future__ import annotations

import hashlib
import json
import re
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


DEFAULT_INTEL_MODEL_PATH = "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"


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


@dataclass
class IntelResult:
    topics: list[str]
    action_items: list[ActionItem]
    summary: str
    raw_response: str


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


class MeetingIntel:
    """Extract structured meeting intelligence using llama-cpp-python."""

    def __init__(
        self,
        *,
        model_path: str = DEFAULT_INTEL_MODEL_PATH,
        chat_format: Optional[str] = None,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = -1,  # -1 = offload all layers to GPU (Metal on Apple Silicon)
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> None:
        self.model_path = model_path
        self.chat_format = chat_format
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.temperature = temperature
        self.max_tokens = max_tokens

        self._llm: Optional["Llama"] = None

    def _resolved_model_path(self) -> Path:
        return Path(self.model_path).expanduser()

    def _ensure_model_loaded(self) -> None:
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

    def _analyze_once(self, transcript: str) -> IntelResult:
        self._ensure_model_loaded()
        assert self._llm is not None

        messages = _json_only_messages(transcript)
        try:
            response = self._llm.create_chat_completion(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            raw = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            raw_text = str(raw)
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
                )

        return self._analyze_stream(transcript)

    def _analyze_stream(self, transcript: str) -> Iterator[Union[str, IntelResult]]:
        raw_parts: list[str] = []

        try:
            self._ensure_model_loaded()
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
            self._ensure_model_loaded()
            assert self._llm is not None

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

            response = self._llm.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=30,
            )

            title = response["choices"][0]["message"]["content"].strip()
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
            self._ensure_model_loaded()
            assert self._llm is not None

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

            response = self._llm.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=20,
            )

            label = response["choices"][0]["message"]["content"].strip()
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
            self._ensure_model_loaded()
            assert self._llm is not None

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

            response = self._llm.create_chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=20,
            )

            label = response["choices"][0]["message"]["content"].strip()
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
