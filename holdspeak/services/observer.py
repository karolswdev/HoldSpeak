from __future__ import annotations

import asyncio
import contextvars
import functools
import inspect
import json
import logging
import re
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from holdspeak.line.secrets import SETTINGS_FIELDS as _LINE_SECRET_FIELDS
from holdspeak.redaction import REDACTED, redact_bounded, redact_error

#: The most of an exception's text one pipeline event keeps (redacted first).
FAILURE_LIMIT = 4096


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


#: A dict key that names a credential: its value is withheld whole.
_CREDENTIAL_KEY = re.compile(r"(?i)[A-Za-z0-9_-]*(?:token|password|passwd|secret|api[_-]?key|apikey|credential|authorization)")


#: The summary is the text the WHOLE value gives (Codex on #1936: a summary
#: read from the head of a large result was not the old text; past the 1 MB
#: guard it stored source text the guard left out). The cost was redaction:
#: each string leaf, then the whole encoding (70 % of a Needs-you build).
#: Both are pure functions of their exact text, so their answers are kept:
#: the same text always gives the same summary, byte for byte. Bounds: the
#: count of entries and the length of a text kept (a longer text is redacted
#: each time, as before).
_LEAF_SHORT = 1024
_LEAF_LONG = 64 * 1024
_ENCODED_KEPT = 256 * 1024


@functools.lru_cache(maxsize=8192)
def _redact_short(text: str) -> str:
    return redact_bounded(text)


@functools.lru_cache(maxsize=32)
def _redact_long(text: str) -> str:
    return redact_bounded(text)


@functools.lru_cache(maxsize=4096)
def _is_credential_key(key: str) -> bool:
    return _CREDENTIAL_KEY.fullmatch(key) is not None


def _redact_leaf(value: str) -> str:
    # Only an exact ``str`` is kept: a subclass can give another ``str()``.
    if type(value) is str:
        if len(value) <= _LEAF_SHORT:
            return _redact_short(value)
        if len(value) <= _LEAF_LONG:
            return _redact_long(value)
    return redact_bounded(value)


def _redact_tree(value: Any) -> Any:
    """Every string leaf redacted, and every value under a credential key
    withheld, BEFORE the JSON encoding (PHILO-17 redact, Astra r2: an
    encoded string escapes its quotes, which hides a quoted label)."""
    if isinstance(value, str):
        return _redact_leaf(value)
    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            if (isinstance(key, str)
                    and (_is_credential_key(key) if type(key) is str else _CREDENTIAL_KEY.fullmatch(key))
                    and isinstance(item, (str, int, float)) and not isinstance(item, bool)
                    and str(item).strip() and not str(item).isdigit()):
                out[key] = REDACTED
            else:
                out[key] = _redact_tree(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_redact_tree(item) for item in value]
    return value


def _redact_cut(summary: str, limit: int) -> str:
    # PHILO-17 redact: agents read pipeline events (MCP ``pipeline://events``),
    # so no credential a provider echoed is recorded. Redact the WHOLE text
    # first (up to the 1 MB guard of ``redact_bounded``), then cut.
    summary = redact_bounded(summary)
    if len(summary) > limit:
        return summary[: limit - 1] + "…"
    return summary


#: The kept whole-text answers: an observed call summarizes its arguments
#: and its result, so one Needs-you build reads about 80 texts. Bounded by
#: their characters, oldest out first.
_KEPT_CHARS = 4 * 1024 * 1024
_kept: OrderedDict[tuple[str, int], str] = OrderedDict()
_kept_size = 0
_kept_lock = threading.Lock()


def _redact_cut_kept(summary: str, limit: int) -> str:
    global _kept_size
    key = (summary, limit)
    with _kept_lock:
        answer = _kept.get(key)
        if answer is not None:
            _kept.move_to_end(key)
            return answer
    answer = _redact_cut(summary, limit)
    with _kept_lock:
        if key not in _kept:
            _kept[key] = answer
            _kept_size += len(summary)
            while _kept_size > _KEPT_CHARS:
                (old, _), _ = _kept.popitem(last=False)
                _kept_size -= len(old)
    return answer


def _truncate(value: Any, limit: int = 2048) -> str:
    try:
        value = _redact_tree(value)
    except Exception:
        pass
    try:
        summary = json.dumps(value, default=str, separators=(",", ":"))
    except Exception:
        try:
            summary = repr(value)
        except Exception:
            summary = "<unserializable>"
    if type(summary) is str and len(summary) <= _ENCODED_KEPT:
        return _redact_cut_kept(summary, limit)
    return _redact_cut(summary, limit)


#: What the observer never records (PHILO-15 20, Astra r1 on #1011): a
#: pipeline event is readable by agents (MCP ``pipeline://events``), so the
#: whole text of a held tool call, kept for the owner's Raw read only, is
#: withheld from every record. Fields: by name, at any depth of the
#: arguments and the result. Results: whole, by ``(service, method)``.
#: Refused settings patches still reach the observer. Withhold their credential
#: fields using the custody map as well as the Line's legacy paths.
UNRECORDED_FIELDS = frozenset({"args_full", "token", "api_key", "webhook_url", "slack_webhook_url"}
                             | {path[-1] for path in _LINE_SECRET_FIELDS.values()})


@functools.lru_cache(maxsize=1)
def _unrecorded_fields() -> frozenset[str]:
    # Late import: CredentialService itself uses this observer.
    from holdspeak.services.credential_service import SECRET_PATHS
    return UNRECORDED_FIELDS | {path[-1] for path in SECRET_PATHS.values()}


UNRECORDED_RESULTS = frozenset({
    ("GateService", "full_call"), ("GateService", "issue_agent"),
    ("DictationService", "readiness"), ("DictationService", "open_mic"),
    ("DictationService", "transcribe_audio"), ("DictationService", "preview_intent_route"),
    ("DictationService", "wake_type"), ("DictationService", "preview_type"),
    ("DictationService", "test_voice_command"),
    # A peek answers the terminal's screen: the owner's read only.
    ("CoderService", "relay"),
})
#: Arguments withheld by ``(service, method)``: a credential replacement is
#: recorded (which secret, by whom), never its value (Codex on #2127, finding 3).
UNRECORDED_ARGS = {("CredentialService", "replace"): frozenset({"value", "metadata_or_patch"}),
                   ("TelegramReach", "save_token"): frozenset({"value"}),
                   ("CredentialService", "rotate"): frozenset({"rotation_input"}),
    ("DictationService", "transcribe_audio"): frozenset({"raw"}),
    ("DictationService", "readiness"): frozenset({"project_root"}),
    ("DictationService", "preview_intent_route"): frozenset({"args"}),
    ("DictationService", "wake_type"): frozenset({"payload"}),
    ("DictationService", "preview_type"): frozenset({"payload"}),
    ("DictationService", "preview_discard"): frozenset({"payload"}),
    ("DictationService", "test_voice_command"): frozenset({"payload"}),
    # The owner's steering text and keys can be a credential typed into a
    # terminal (Codex on #2149, F1): the verb is recorded, never the body.
    ("CoderService", "relay"): frozenset({"args"}),
}
WITHHELD = "<withheld>"


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: (WITHHELD if k in _unrecorded_fields() else _scrub(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    return value


def _summarize_result(service: str, method: str, result: Any) -> str:
    if (service, method) in UNRECORDED_RESULTS:
        return _truncate(WITHHELD)
    return _truncate(_scrub(result))


def _summarize_args(fn: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    try:
        signature = inspect.signature(fn)
        bound = signature.bind_partial(*args, **kwargs)
        withheld = UNRECORDED_ARGS.get((type(args[0]).__name__, fn.__name__), frozenset()) if args else frozenset()
        summary = {
            name: (WITHHELD if name in withheld else value)
            for name, value in bound.arguments.items()
            if name != "self" and "Principal" not in str(signature.parameters[name].annotation)
        }
        return _truncate(_scrub(summary))
    except Exception:
        return "<args-unavailable>"


def _failure(exc: BaseException) -> tuple[str | None, str | None, str]:
    """``(error, error_code, result_summary)`` for an exception.

    An exception that carries ``observed_outcome`` is an owner setting that
    refused the call (PHILO-15 01: summaries OFF), not a fault: it is recorded
    as that outcome with no error, so nothing reads it as breakage.
    """
    code = exc.code if hasattr(exc, "code") else None
    outcome = getattr(exc, "observed_outcome", None)
    if outcome:
        return None, None, _truncate({"outcome": str(outcome), "code": code})
    return redact_error(repr(exc), FAILURE_LIMIT), code, ""


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
                result_summary = _summarize_result(type(self).__name__, fn.__name__, result)
                return result
            except BaseException as exc:
                error, error_code, result_summary = _failure(exc)
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
            result_summary = _summarize_result(type(self).__name__, fn.__name__, result)
            return result
        except BaseException as exc:
            error, error_code, result_summary = _failure(exc)
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
        # A ``*_in_transaction`` method runs inside its CALLER's write
        # transaction. Its event would be written on another connection while
        # that transaction holds the write lock: the insert waited out the
        # 5 s busy timeout and was then dropped (an Accept of a risk proposal
        # took 5 s). The caller's own call is the record.
        if name.endswith("_in_transaction"):
            continue
        if callable(attribute) and not name.startswith("_"):
            setattr(cls, name, observed(attribute))
    return cls
