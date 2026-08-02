"""Warrant-only proxy for desktop text injection."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class DesktopEffectWarrantRequired(RuntimeError):
    """Raw desktop input is unavailable without a claimed kernel warrant."""


class TextTyper:
    """Ordinary-runtime proxy; it owns no keyboard or clipboard primitive."""

    def __init__(self, use_clipboard: bool = True) -> None:
        self.use_clipboard = bool(use_clipboard)

    def type_text(
        self,
        text: str,
        *,
        target_profile: str | None = None,
        submit: bool = False,
        warrant: Mapping[str, Any] | None = None,
        request: Mapping[str, Any] | None = None,
        operation_id: str = "",
        executor: Any = None,
    ) -> dict[str, Any]:
        """Execute only through the privileged child's warrant protocol."""
        del text, target_profile, submit
        if (
            not isinstance(warrant, Mapping)
            or not isinstance(request, Mapping)
            or not operation_id
            or executor is None
        ):
            raise DesktopEffectWarrantRequired(
                "desktop_effect_warrant_required"
            )
        return dict(
            executor.execute(
                operation_id=operation_id,
                warrant=warrant,
                request=request,
                use_clipboard=self.use_clipboard,
            )
        )


__all__ = ["DesktopEffectWarrantRequired", "TextTyper"]
