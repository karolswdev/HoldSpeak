from __future__ import annotations

import asyncio
import contextvars
import functools
import inspect
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar("_correlation_id")


def current_correlation_id() -> str:
    """Correlation shared by an observed service call and its domain events."""
    return str(_correlation_id.get(""))


# HS-174: context var for origin tagging on remote MCP calls.
_origin: contextvars.ContextVar[str] = contextvars.ContextVar("_origin", default="local")
_caller: contextvars.ContextVar[str] = contextvars.ContextVar("_caller", default="")
_caller_identity: contextvars.ContextVar[str] = contextvars.ContextVar("_caller_identity", default="")


@dataclass(frozen=True)
class PipelineEvent:
    event_id: str
    timestamp: float
    service: str
    method: str
    principal_kind: str
    principal_identity: str
    args_summary: str
    result_summary: str
    error: str | None
    error_code: str | None
    duration_ms: float
    correlation_id: str
    is_async: bool
    # HS-174: origin of the call.
    origin: str = "local"
    caller: str = ""
    caller_identity: str = ""


@runtime_checkable
class PipelineObserver(Protocol):
    def on_event(self, event: PipelineEvent) -> None: ...


class NullObserver:
    def on_event(self, event: PipelineEvent) -> None:
        pass


def _truncate(value: Any, limit: int = 2048) -> str:
    try:
        summary = json.dumps(value, default=str, separators=(",", ":"))
    except Exception:
        try:
            summary = repr(value)
        except Exception:
            summary = "<unserializable>"

    if len(summary) > limit:
        return summary[: limit - 1] + "…"
    return summary


def _summarize_args(fn: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    try:
        signature = inspect.signature(fn)
        bound = signature.bind_partial(*args, **kwargs)
        summary = {
            name: value
            for name, value in bound.arguments.items()
            if name != "self" and "Principal" not in str(signature.parameters[name].annotation)
        }
        return _truncate(summary)
    except Exception:
        return "<args-unavailable>"


def observed(fn: Any) -> Any:
    is_async = asyncio.iscoroutinefunction(fn)

    def _principal(args: tuple[Any, ...]) -> tuple[str, str]:
        if not args:
            return "unknown", ""
        principal = args[0]
        try:
            return principal.kind.value, principal.identity
        except AttributeError:
            return "unknown", ""

    def _emit(
        self: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        correlation_id: str,
        t0: float,
        result_summary: str,
        error: str | None,
        error_code: str | None,
    ) -> None:
        principal_kind, principal_identity = _principal(args)
        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=t0,
            service=type(self).__name__,
            method=fn.__name__,
            principal_kind=principal_kind,
            principal_identity=principal_identity,
            args_summary=_summarize_args(fn, (self, *args), kwargs),
            result_summary=result_summary,
            error=error,
            error_code=error_code,
            duration_ms=(time.time() - t0) * 1000,
            correlation_id=correlation_id,
            is_async=is_async,
            origin=_origin.get("local"),
            caller=_caller.get(""),
            caller_identity=_caller_identity.get(""),
        )
        observer = getattr(self, "_observer", None) or NullObserver()
        try:
            observer.on_event(event)
        except Exception:
            logging.getLogger(__name__).warning("Pipeline observer failed", exc_info=True)

    if is_async:

        @functools.wraps(fn)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            correlation_id = _correlation_id.get(None)
            token = None
            if correlation_id is None:
                correlation_id = str(uuid.uuid4())
                token = _correlation_id.set(correlation_id)

            t0 = time.time()
            result_summary = ""
            error: str | None = None
            error_code: str | None = None
            try:
                result = await fn(self, *args, **kwargs)
                result_summary = _truncate(result)
                return result
            except BaseException as exc:
                error = repr(exc)
                error_code = exc.code if hasattr(exc, "code") else None
                raise
            finally:
                _emit(self, args, kwargs, correlation_id, t0, result_summary, error, error_code)
                if token is not None:
                    _correlation_id.reset(token)

        return async_wrapper

    @functools.wraps(fn)
    def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        correlation_id = _correlation_id.get(None)
        token = None
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
            token = _correlation_id.set(correlation_id)

        t0 = time.time()
        result_summary = ""
        error: str | None = None
        error_code: str | None = None
        try:
            result = fn(self, *args, **kwargs)
            result_summary = _truncate(result)
            return result
        except BaseException as exc:
            error = repr(exc)
            error_code = exc.code if hasattr(exc, "code") else None
            raise
        finally:
            _emit(self, args, kwargs, correlation_id, t0, result_summary, error, error_code)
            if token is not None:
                _correlation_id.reset(token)

    return sync_wrapper


def observe_service(cls: type[Any]) -> type[Any]:
    for name, attribute in list(vars(cls).items()):
        if isinstance(attribute, (staticmethod, classmethod)):
            continue
        if callable(attribute) and not name.startswith("_"):
            setattr(cls, name, observed(attribute))
    return cls
