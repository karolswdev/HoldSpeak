"""One removal refusal at GitHub process boundaries, including injected runners.

Only the owner's explicit check can release a durable removal. The narrow
status/logout exceptions are scoped to exact argv, never request arguments.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Any

from holdspeak.principals import PrincipalKind
from .errors import ServiceError

class GitHubAccessRefused(ServiceError):
    def __init__(self):
        super().__init__("github_sign_in_required", "Sign in again", context={"status": 409})


ACCESS_LOCK = RLock()
_ALLOWED: ContextVar[tuple[str, ...] | None] = ContextVar("github_owner_argv", default=None)


def database(db: Any = None) -> Any:
    if db is not None:
        return db
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or
    return db_or(get_database)


def require_access(argv: Any, db: Any = None) -> None:
    if not argv or Path(str(argv[0])).name != "gh":
        return
    if _ALLOWED.get() == tuple(str(word) for word in argv):
        return
    from holdspeak.db.github_access import removal
    target = database(db)
    marker = removal(target)
    with target._connection() as conn:
        row = conn.execute("SELECT state,external_connection_ref FROM watch_provider_connections WHERE id='wpc_github'").fetchone()
    # Rows left by the previous Remove implementation are also held until Check.
    if marker or (row and row["state"] == "owner_action_required" and not row["external_connection_ref"]):
        raise GitHubAccessRefused()


def guarded(runner: Any, db: Any = None) -> Any:
    @wraps(runner)
    def run(argv: Any, *args: Any, **kwargs: Any) -> Any:
        if argv and Path(str(argv[0])).name == "gh":
            with ACCESS_LOCK:
                require_access(argv, db)
                return runner(argv, *args, **kwargs)
        return runner(argv, *args, **kwargs)
    return run


@contextmanager
def owner_command(principal: Any, argv: Any):
    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        raise ServiceError("owner_required", "Owner access is required", context={"status": 403})
    token = _ALLOWED.set(tuple(str(word) for word in argv))
    try:
        yield
    finally:
        _ALLOWED.reset(token)
