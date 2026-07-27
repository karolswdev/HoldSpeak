"""Small typed values shared by the operation broker."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional


FINAL_STATES = frozenset({"succeeded", "failed", "refused", "indeterminate"})
FORBIDDEN_CONTENT_KEYS = frozenset(
    {"audio", "audio_frame", "audio_frames", "pcm", "token", "tokens", "token_stream"}
)
_REF = re.compile(r"^[a-z][a-z0-9_.-]*:[A-Za-z0-9_.:/-]{1,160}$")


class KernelRefused(ValueError):
    """A named broker refusal which never includes domain content."""

    def __init__(self, reason: str, message: Optional[str] = None, *, operation_id: str = ""):
        super().__init__(message or reason)
        self.reason = reason
        self.operation_id = operation_id


@dataclass(frozen=True)
class OperationRequest:
    request_schema: int
    request_id: str
    idempotency_key: str
    name: str
    version: int
    target_ref: str
    placement: str
    arguments: Mapping[str, Any]
    subject_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Admission:
    target_ref: str
    placement: str
    payload_hash: str
    refs: tuple[str, ...]
    head: str
    ttl_seconds: float
    native_id: str


@dataclass(frozen=True)
class OperationSpec:
    name: str
    version: int
    codec: Any
    required_capability: str
    interruption: str


def valid_ref(value: str) -> bool:
    return not value or _REF.fullmatch(value) is not None


def forbidden_content(value: Any) -> bool:
    """Reject bulk/stream content recursively before it can reach the journal."""
    if isinstance(value, Mapping):
        return bool(FORBIDDEN_CONTENT_KEYS.intersection(map(str, value))) or any(
            forbidden_content(item) for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(forbidden_content(item) for item in value)
    return False
