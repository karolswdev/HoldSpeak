"""Intel models + constants (HS-34-04)."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from holdspeak.timestamps import utc_now_iso
from typing import Optional


#: The local starter model's place on this device: the file "Set up local AI"
#: (and a Models-library download of the same signed preset) writes. Owner
#: ruling 2026-10-05: a default names a file the product itself provides,
#: never one nobody has (fence: tests/unit/test_local_ai_setup.py).
DEFAULT_INTEL_MODEL_PATH = (
    "~/.local/share/holdspeak/models/artifacts/"
    "artifact_8eeea91e273c731f889a47405d49651dc4dcb90bc98b9a08af8135d1af44a4a8/"
    "Qwen3.5-4B-Q4_K_M.gguf"
)


DEFAULT_INTEL_PROVIDER = "local"


DEFAULT_INTEL_CLOUD_MODEL = "gpt-5-mini"


DEFAULT_INTEL_CLOUD_API_KEY_ENV = "OPENAI_API_KEY"


DEFAULT_INTEL_CLOUD_TIMEOUT_SECONDS = 180.0


# The ONE default-endpoint chokepoint (HS-112-01): every surface that needs
# "where does a bare cloud call go" derives it from here.
DEFAULT_CLOUD_BASE_URL = "https://api.openai.com/v1"


DEFAULT_CLOUD_HOST = "api.openai.com"


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
    created_at: str = field(default_factory=lambda: utc_now_iso())
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
        self.completed_at = utc_now_iso()

    def dismiss(self) -> None:
        """Dismiss this action item."""
        self.status = "dismissed"
        self.completed_at = utc_now_iso()

    def accept(self) -> None:
        """Mark this action item as reviewed/accepted."""
        self.review_state = "accepted"
        self.reviewed_at = utc_now_iso()


@dataclass
class IntelResult:
    topics: list[str]
    action_items: list[ActionItem]
    summary: str
    raw_response: str
    error: Optional[str] = None


SELF_HOSTED_CLOUD_API_KEY_PLACEHOLDER = "sk-no-key-required"
