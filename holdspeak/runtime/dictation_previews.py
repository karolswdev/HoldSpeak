"""The dictation preview one-shots (HS-131-09B carve).

The P60 preview grammar: ONE armed preview at a time, its token minted
server-side, consumed or burned exactly once. The runtime types only its own
stored text — client text is never accepted here.

Carved out of ``dictation_capture`` verbatim to keep each runtime module to one
concern (the 600-line module budget). ``DictationCaptureMixin`` inherits it, so
every caller keeps the exact same methods on the runtime.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..logging_config import get_logger

log = get_logger("web_runtime")


class DictationPreviewMixin:
    def _arm_dictation_preview(self, text: str) -> None:
        """Arm ONE one-shot preview instead of typing (HS-75-01).

        The token is minted server-side; `/api/dictation/preview/type`
        consumes it (the runtime types only its own stored text) and
        `/api/dictation/preview/discard` burns it. One active preview at a
        time, the P60 rule.
        """
        import uuid as uuid_mod

        token = uuid_mod.uuid4().hex
        self.dictation_previews.clear()
        self.dictation_previews[token] = {
            "text": text,
            "created_at": datetime.now().isoformat(),
        }
        if self.server is not None:
            try:
                self.server.broadcast(
                    "dictation_preview", {"token": token, "text": text}
                )
            except Exception:
                pass
        self._set_runtime_activity(
            "complete",
            source="dictation",
            label="Preview ready",
            detail=text[:120],
            last_event="dictation_preview",
            last_error="",
        )

    def consume_dictation_preview(self, token: str) -> Optional[str]:
        """One-shot: return the stored preview text and burn the token."""
        entry = self.dictation_previews.pop(str(token or ""), None)
        return None if entry is None else str(entry.get("text", ""))

    def type_dictation_preview(self, token: str) -> Optional[str]:
        """Consume a preview and deliver it through the normal typing path."""
        text = self.consume_dictation_preview(token)
        if text is None:
            return None
        if self.typer is not None:
            self._set_runtime_activity(
                "typing",
                source="dictation",
                detail="Typing dictated text.",
                last_event="dictation_typing",
                last_error="",
            )
            from ..desktop_typing import type_text_from_owner_gesture

            type_text_from_owner_gesture(
                text,
                typer=self.typer,
                gesture="preview_type",
                preview_ref=f"dictation-preview:{token}",
                submit=False,
            )
        self._set_runtime_activity(
            "complete",
            source="dictation",
            label="Typed",
            detail="Dictated text was inserted.",
            last_event="dictation_typed",
            last_error="",
        )
        self._mark_first_dictation()
        return text

    def discard_dictation_preview(self, token: str) -> bool:
        """Burn a preview without typing (HS-75-01)."""
        text = self.consume_dictation_preview(token)
        if text is None:
            return False
        self._set_runtime_activity(
            "complete",
            source="dictation",
            label="Discarded",
            detail="",
            last_event="dictation_preview_discarded",
            last_error="",
        )
        return True


__all__ = ["DictationPreviewMixin"]
