"""The announce scope: one write sends ONE ``desk_changed`` frame.

Carved out of ``holdspeak/runtime/composition.py`` (no behaviour change). The
composition root holds the services; this module holds the changes of the
write in progress. ``RuntimeServices.emit_desk_changed`` adds to the scope;
the roots (``holdspeak/web/announce.py`` for an HTTP request,
``OperationRegistry.invoke`` outside one) open it.
"""

from __future__ import annotations

import contextlib
import contextvars
from typing import Callable, Iterator, Optional


def _origin() -> str:
    try:
        from holdspeak.services.observer import _caller_identity

        return _caller_identity.get("") or "hub"
    except Exception:  # pragma: no cover - the bus must not break a write
        return "hub"


class _AnnounceScope:
    """The changes of one write, held until the write ends."""

    __slots__ = ("changes", "emitters", "closed")

    def __init__(self) -> None:
        self.changes: list = []
        self.emitters: list = []
        self.closed = False


#: The current write (an HTTP request, or one ``OperationRegistry.invoke``
#: outside a request). An object, not a flag: the request handler runs in a
#: child task or a worker thread that COPIES the context, and a shared object
#: is the one thing both sides see. ``closed`` covers a task that outlives its
#: request: its later changes go out at once, never into a dead list.
_announced: contextvars.ContextVar[Optional[_AnnounceScope]] = contextvars.ContextVar(
    "desk_changed_announced", default=None
)


@contextlib.contextmanager
def announce_scope() -> Iterator[Callable[[str, str, str], None]]:
    """One write at a root (an HTTP request, one ``OperationRegistry.invoke``).

    Service announcements inside the scope are held. Yields
    ``announce(kind, id, op)``, the root's own name for the write: it counts
    only when no service announced since this scope (or this nested scope)
    opened. When the outermost scope ends, ONE ``desk_changed`` frame goes
    out with every change. A scope inside a scope (an ``invoke`` inside a
    request) adds to the outer one and sends nothing itself.
    """
    outer = _announced.get()
    nested = outer is not None and not outer.closed
    scope = outer if nested else _AnnounceScope()
    token = None if nested else _announced.set(scope)
    before = len(scope.changes)

    def announce(kind: str, obj_id: str, op: str) -> None:
        if len(scope.changes) == before and not scope.closed:
            scope.changes.append((kind, obj_id, op, _origin()))

    try:
        yield announce
    finally:
        if not nested:
            scope.closed = True
            _announced.reset(token)
            if scope.changes:
                from holdspeak.runtime import composition

                sender = (
                    next((e for e in scope.emitters if e.broadcast is not None), None)
                    or composition._installed
                )
                if sender is not None:
                    sender._send_desk_changed(scope.changes)
