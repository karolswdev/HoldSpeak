"""Trusted startup wiring and request-principal context for the broker."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Mapping, Sequence

from ..principals import UNAUTHENTICATED
from .broker import Broker
from .journal import JournalStore
from .model import OperationSpec
from .tool_call import ToolCallCodec

_principal = ContextVar("kernel_principal", default=UNAUTHENTICATED)
_broker: Broker | None = None
_database_id: int | None = None


def _mode() -> str:
    from ..config import Config

    return str(Config.load().control_mode)


def _build(database: Any, *, clock: Any = None) -> Broker:
    store = JournalStore(database._connection, **({"clock": clock} if clock else {}))
    codec = ToolCallCodec(database.gate, _mode)
    specs = (OperationSpec(codec.name, codec.version, codec, "agent.submit", "propose"),)
    return Broker(store, specs, **({"clock": clock} if clock else {}))


def _service() -> Broker:
    global _broker, _database_id
    from ..db import get_database

    database = get_database()
    if _broker is None or _database_id != id(database):
        _broker = _build(database)
        _database_id = id(database)
    return _broker


def _configure(database: Any, *, clock: Any = None) -> Broker:
    """Test/startup seam; deliberately private, never an operation registration API."""
    global _broker, _database_id
    _broker = _build(database, clock=clock)
    _database_id = id(database)
    return _broker


@contextmanager
def _as_principal(principal: Any):
    token = _principal.set(principal)
    try:
        yield
    finally:
        _principal.reset(token)


def read(refs: Sequence[str], view: str = "state", consistency: str = "committed") -> dict[str, Any]:
    return _service().read(refs, view, consistency, _principal.get())


def submit(request: Mapping[str, Any]) -> dict[str, Any]:
    return _service().submit(request, _principal.get())


def decide(operation_id: str, decision: str, expected_revision: int) -> dict[str, Any]:
    return _service().decide(operation_id, decision, expected_revision, _principal.get())


def events(after_cursor: int = 0, filter: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return _service().events(after_cursor, filter or {}, _principal.get())


def claim() -> dict[str, Any]:
    return _service().claim(_principal.get())


def receipt(operation_id: str, outcome: str, result_ref: str = "") -> dict[str, Any]:
    return _service().receipt(operation_id, outcome, result_ref, _principal.get())


def reconcile(operation_id: str) -> dict[str, Any]:
    return _service().reconcile(operation_id, _principal.get())
