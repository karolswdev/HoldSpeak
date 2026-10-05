"""Identity-only context for Desk-origin focused workrooms (HS-93-02).

The envelope deliberately carries references and orientation, never authored
speech, prompts, transcripts, or draft bodies. Clients may add unknown metadata
in later versions; known content-bearing fields remain a hard refusal.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Optional

from .db.relationships import qualified_ref


WORKROOM_CONTEXT_VERSION = 1
_ACTION_RE = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_CONTENT_FIELDS = frozenset({
    "body", "content", "draft", "input", "prompt", "text", "transcript",
    "utterance",
})


def _optional_ref(value: object) -> Optional[str]:
    if value is None:
        return None
    return qualified_ref(value)


@dataclass(frozen=True)
class WorkroomContext:
    """Versioned route orientation shared by the hub, Web, and native clients."""

    version: int
    origin: str
    action: str
    return_to: str
    subject_ref: Optional[str] = None
    draft_ref: Optional[str] = None
    run_ref: Optional[str] = None
    return_ref: Optional[str] = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "WorkroomContext":
        if not isinstance(value, Mapping):
            raise ValueError("workroom context must be an object")
        if _CONTENT_FIELDS.intersection(str(key).lower() for key in value):
            raise ValueError("workroom context cannot contain authored content")

        raw_version = value.get("version", WORKROOM_CONTEXT_VERSION)
        if isinstance(raw_version, bool):
            raise ValueError("workroom context version must be an integer")
        try:
            version = int(raw_version)
        except (TypeError, ValueError) as exc:
            raise ValueError("workroom context version must be an integer") from exc
        if version < 1 or version > 999:
            raise ValueError("unsupported workroom context version")

        origin = str(value.get("origin") or "").strip()
        if origin != "desk":
            raise ValueError("workroom origin must be desk")
        return_to = str(value.get("return_to") or "").strip()
        if return_to != "desk":
            raise ValueError("workroom return destination must be desk")
        action = str(value.get("action") or "").strip()
        if not _ACTION_RE.fullmatch(action):
            raise ValueError("workroom action must be a bounded action identifier")

        return cls(
            version=version,
            origin=origin,
            action=action,
            return_to=return_to,
            subject_ref=_optional_ref(value.get("subject_ref")),
            draft_ref=_optional_ref(value.get("draft_ref")),
            run_ref=_optional_ref(value.get("run_ref")),
            return_ref=_optional_ref(value.get("return_ref")),
        )

    @classmethod
    def desk(
        cls,
        *,
        action: str,
        subject_ref: Optional[str] = None,
        draft_ref: Optional[str] = None,
        run_ref: Optional[str] = None,
        return_ref: Optional[str] = None,
    ) -> "WorkroomContext":
        return cls.from_mapping({
            "version": WORKROOM_CONTEXT_VERSION,
            "origin": "desk",
            "subject_ref": subject_ref,
            "action": action,
            "draft_ref": draft_ref,
            "run_ref": run_ref,
            "return_to": "desk",
            "return_ref": return_ref or subject_ref,
        })

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "version": self.version,
            "origin": self.origin,
            "action": self.action,
            "return_to": self.return_to,
        }
        for key in ("subject_ref", "draft_ref", "run_ref", "return_ref"):
            item = getattr(self, key)
            if item is not None:
                value[key] = item
        return value
