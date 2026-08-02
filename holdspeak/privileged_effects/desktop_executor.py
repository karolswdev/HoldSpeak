"""Warrant-only IPC server for raw desktop input.

The ordinary runtime holds one end of an anonymous pipe. The child independently
checks the broker HMAC, payload binding, expiry, placement, focus generation,
and one-use rule before importing the raw driver.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import multiprocessing
import re
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

from ..desktop_focus import focused_signature
from ..operation_policy import POLICY_VERSION

_WARRANT_FIELDS = frozenset(
    {
        "warrant_id",
        "operation_id",
        "envelope_sha256",
        "target_ref",
        "placement",
        "policy_version",
        "issued_at",
        "expires_at",
        "execution_expires_at",
        "uses",
        "signature",
    }
)
_REQUEST_FIELDS = frozenset(
    {
        "request_schema",
        "request_id",
        "idempotency_key",
        "operation",
        "subject_refs",
        "target",
        "arguments",
        "placement",
    }
)
_ARGUMENT_FIELDS = frozenset(
    {
        "text",
        "submit",
        "expected_generation",
        "native_id",
        "gesture",
        "target_profile",
        "preview_ref",
        "macro_ref",
        "requested_target",
        "delivery_method",
    }
)
_REQUIRED_ARGUMENT_FIELDS = frozenset(
    {
        "text",
        "submit",
        "expected_generation",
        "native_id",
        "gesture",
        "requested_target",
        "delivery_method",
    }
)
_FOCUS_GENERATION = re.compile(r"^focus-[0-9]+-([0-9a-f]{20})$")


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), separators=(",", ":"), sort_keys=True)


def _refused(reason: str) -> dict[str, Any]:
    return {"state": "refused", "outcome": reason}


def execute_authorized(
    message: Any,
    *,
    secret: str,
    used_warrants: set[str],
    clock: Callable[[], float] = time.time,
    focus_reader: Callable[[], str] = focused_signature,
    driver_factory: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Validate one IPC message and, only then, cross the raw boundary."""
    if not isinstance(message, Mapping) or set(message) != {
        "operation_id",
        "warrant",
        "request",
        "use_clipboard",
    }:
        return _refused("desktop_executor_message_invalid")
    warrant = message.get("warrant")
    request = message.get("request")
    if (
        not isinstance(warrant, Mapping)
        or set(warrant) != _WARRANT_FIELDS
        or not isinstance(request, Mapping)
        or set(request) != _REQUEST_FIELDS
        or not isinstance(message.get("use_clipboard"), bool)
    ):
        return _refused("desktop_executor_warrant_invalid")
    unsigned = {key: value for key, value in warrant.items() if key != "signature"}
    expected_signature = hmac.new(
        secret.encode(), _canonical(unsigned).encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(str(warrant.get("signature") or ""), expected_signature):
        return _refused("desktop_executor_warrant_signature_invalid")
    warrant_id = str(warrant.get("warrant_id") or "")
    if (
        not warrant_id.startswith("war_")
        or warrant_id in used_warrants
        or not isinstance(warrant.get("uses"), int)
        or isinstance(warrant.get("uses"), bool)
        or warrant.get("uses") != 1
    ):
        return _refused("desktop_executor_warrant_spent")
    if warrant.get("policy_version") != POLICY_VERSION:
        return _refused("desktop_executor_policy_version_mismatch")
    if str(message.get("operation_id") or "") != str(warrant.get("operation_id") or ""):
        return _refused("desktop_executor_operation_mismatch")
    try:
        issued_at = float(warrant.get("issued_at") or 0)
        expires_at = min(
            float(warrant.get("expires_at") or 0),
            float(warrant.get("execution_expires_at") or 0),
        )
    except (TypeError, ValueError):
        return _refused("desktop_executor_warrant_expired")
    now = clock()
    if (
        issued_at <= 0
        or issued_at > now
        or expires_at <= now
        or expires_at <= issued_at
    ):
        return _refused("desktop_executor_warrant_expired")

    operation = request.get("operation")
    target = request.get("target")
    arguments = request.get("arguments")
    placement = str(request.get("placement") or "")
    if (
        not isinstance(operation, Mapping)
        or set(operation) != {"name", "version"}
        or operation.get("name") != "desktop.type_text"
        or not isinstance(operation.get("version"), int)
        or isinstance(operation.get("version"), bool)
        or operation.get("version") != 1
        or not isinstance(target, Mapping)
        or set(target) != {"ref"}
        or not isinstance(arguments, Mapping)
        or not _REQUIRED_ARGUMENT_FIELDS.issubset(arguments)
        or not set(arguments).issubset(_ARGUMENT_FIELDS)
        or request.get("request_schema") != 1
        or not isinstance(request.get("subject_refs"), list)
        or placement != "node:local-desktop"
    ):
        return _refused("desktop_executor_request_invalid")
    target_ref = str(target.get("ref") or "")
    generation = str(arguments.get("expected_generation") or "")
    match = _FOCUS_GENERATION.fullmatch(generation)
    if (
        match is None
        or target_ref != f"desktop-input:{generation}"
        or target_ref != str(warrant.get("target_ref") or "")
        or placement != str(warrant.get("placement") or "")
    ):
        return _refused("desktop_executor_target_mismatch")
    material = {
        "name": "desktop.type_text",
        "version": 1,
        "target_ref": target_ref,
        "placement": placement,
        "arguments": dict(arguments),
    }
    payload_hash = "sha256:" + hashlib.sha256(_canonical(material).encode()).hexdigest()
    if not hmac.compare_digest(payload_hash, str(warrant.get("envelope_sha256") or "")):
        return _refused("desktop_executor_payload_mismatch")

    # One attempt consumes the warrant, including a focus or driver refusal.
    used_warrants.add(warrant_id)
    current_focus = focus_reader()
    current_hash = hashlib.sha256(current_focus.encode()).hexdigest()[:20]
    if not current_focus:
        return _refused("desktop_focus_unresolved")
    if not hmac.compare_digest(match.group(1), current_hash):
        return _refused("desktop_focus_generation_changed")

    text = arguments.get("text")
    submit = arguments.get("submit")
    if not isinstance(text, str) or not text.strip() or not isinstance(submit, bool):
        return _refused("desktop_executor_request_invalid")
    try:
        if driver_factory is None:
            from .desktop_driver import RawDesktopDriver

            driver_factory = RawDesktopDriver
        driver = driver_factory(use_clipboard=bool(message.get("use_clipboard", True)))
        driver.type_text(
            text,
            target_profile=(
                str(arguments.get("target_profile"))
                if arguments.get("target_profile")
                else None
            ),
            submit=submit,
        )
    except Exception:
        return {"state": "failed", "outcome": "desktop_effect_driver_failed"}
    return {"state": "succeeded", "outcome": "succeeded"}


def _serve(connection: Any, secret: str) -> None:
    used_warrants: set[str] = set()
    try:
        while True:
            message = connection.recv()
            if message == {"control": "close"}:
                return
            connection.send(
                execute_authorized(
                    message,
                    secret=secret,
                    used_warrants=used_warrants,
                )
            )
    except (EOFError, OSError):
        return
    finally:
        connection.close()


class DesktopEffectExecutor:
    """Parent-side handle to the anonymous privileged child."""

    def __init__(
        self,
        secret: str,
        *,
        timeout_seconds: float = 5.0,
        context: Any = None,
    ) -> None:
        self._secret: str | None = str(secret)
        self._timeout = max(0.1, float(timeout_seconds))
        self._context = context or multiprocessing.get_context("spawn")
        self._connection: Any = None
        self._process: Any = None
        self._lock = threading.Lock()
        self._broken = False

    def _start(self) -> bool:
        if self._broken:
            return False
        if self._process is not None:
            return bool(self._process.is_alive())
        if self._secret is None:
            return False
        parent, child = self._context.Pipe(duplex=True)
        process = self._context.Process(
            target=_serve,
            args=(child, self._secret),
            name="holdspeak-desktop-effect-executor",
            daemon=True,
        )
        process.start()
        child.close()
        self._connection = parent
        self._process = process
        # The ordinary process keeps only the protected endpoint after spawn.
        self._secret = None
        return True

    def execute(
        self,
        *,
        operation_id: str,
        warrant: Mapping[str, Any],
        request: Mapping[str, Any],
        use_clipboard: bool = True,
    ) -> dict[str, Any]:
        with self._lock:
            if not self._start() or self._connection is None:
                return {
                    "state": "failed",
                    "outcome": "desktop_effect_executor_unavailable",
                }
            message = {
                "operation_id": str(operation_id),
                "warrant": dict(warrant),
                "request": dict(request),
                "use_clipboard": bool(use_clipboard),
            }
            try:
                self._connection.send(message)
                if not self._connection.poll(self._timeout):
                    self._broken = True
                    return {
                        "state": "indeterminate",
                        "outcome": "desktop_effect_executor_timeout",
                    }
                response = self._connection.recv()
            except (EOFError, OSError, BrokenPipeError):
                self._broken = True
                return {
                    "state": "indeterminate",
                    "outcome": "desktop_effect_executor_lost",
                }
            if not isinstance(response, Mapping):
                self._broken = True
                return {
                    "state": "indeterminate",
                    "outcome": "desktop_effect_executor_response_invalid",
                }
            return dict(response)

    def close(self) -> None:
        with self._lock:
            if self._connection is not None and not self._broken:
                try:
                    self._connection.send({"control": "close"})
                except (OSError, BrokenPipeError):
                    pass
            if self._connection is not None:
                self._connection.close()
            if self._process is not None:
                self._process.join(timeout=1.0)
                if self._process.is_alive():
                    self._process.terminate()
                    self._process.join(timeout=1.0)
            self._connection = None
            self._process = None


__all__ = ["DesktopEffectExecutor", "execute_authorized"]
