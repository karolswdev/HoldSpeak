"""Transport-neutral errors raised by HoldSpeak application services."""
from __future__ import annotations

from typing import Any


class ServiceError(Exception):
    """A stable domain failure, independent of its eventual transport."""

    def __init__(
        self, code: str, detail: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.code = code
        self.detail = detail
        self.context = dict(context or {})
        super().__init__(detail)


class NotFound(ServiceError):
    def __init__(self, kind: str, id: str) -> None:
        self.kind = kind
        self.id = id
        super().__init__(
            "not_found", f"Unknown {kind}: {id}", context={"kind": kind, "id": id}
        )


class ValidationError(ServiceError):
    def __init__(
        self,
        detail: str,
        *,
        code: str = "validation_error",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(code, detail, context=context)


class ConflictError(ServiceError):
    def __init__(
        self,
        detail: str,
        *,
        existing_name: str = "",
        code: str = "conflict",
        context: dict[str, Any] | None = None,
    ) -> None:
        self.existing_name = existing_name
        merged_context = dict(context or {})
        if existing_name:
            merged_context.setdefault("existing_name", existing_name)
        super().__init__(code, detail, context=merged_context)
