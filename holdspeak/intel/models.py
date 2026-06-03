"""Intel models + constants (HS-34-04)."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional


DEFAULT_INTEL_MODEL_PATH = "~/Models/gguf/Qwen3.5-9B-Instruct-Q6_K.gguf"


DEFAULT_INTEL_PROVIDER = "local"


DEFAULT_INTEL_CLOUD_MODEL = "gpt-5-mini"


DEFAULT_INTEL_CLOUD_API_KEY_ENV = "OPENAI_API_KEY"


DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 180.0


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


SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER = "sk-no-key-required"
