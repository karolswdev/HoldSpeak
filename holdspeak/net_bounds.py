"""Bounds for the calls that leave the hub (lane HUB TIMEOUTS, 2026-10-27).

Live finding on the owner's desk, away from his LAN: the LAN engine did not
answer, and the whole desk read "Loading" for good. Two causes:

* A read route probed the engine ON the event loop (``GET
  /api/concierge/detect``, ``GET /api/front-door/recommendation``): while the
  probe waited for its timeout, the hub answered nothing else.
* A model call had one scalar timeout (180 s for a meeting summary), so the TCP
  connect to a host that never answers waited for the OS default (about 75 s
  on macOS) before it failed.

Two tools fix both, one place each:

* :func:`engine_timeout` gives an engine client a CONNECT bound of
  :data:`CONNECT_SECONDS` and keeps the call's own budget for the read.
* :data:`endpoint_checks` keeps the last answer of each endpoint check. A read
  checks again, but an endpoint that does not answer costs it half a second:
  it gets the last answer (with its time) and the check goes on behind it.
"""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

#: No outbound connect waits longer than this for a host to answer.
CONNECT_SECONDS = 3.0
#: A readiness check never takes longer than this.
PROBE_SECONDS = 5.0
#: A read waits this long for a check of an endpoint that answered before;
#: past it, the read uses the last answer and the check goes on behind it.
GRACE_SECONDS = 0.5


def engine_timeout(total: float) -> Any:
    """An httpx timeout: connect within :data:`CONNECT_SECONDS`, the rest gets ``total``."""
    import httpx

    seconds = max(0.1, float(total))
    return httpx.Timeout(seconds, connect=min(CONNECT_SECONDS, seconds))


class LastCheck:
    """The last answer of each check, by key, with the time it was made.

    Every ``read`` checks (a check already running for the key is joined,
    never doubled). An endpoint that answers, answers within the grace and
    the read gets the live answer. One that does not answer costs the read
    the grace only: it gets the LAST answer with its time, and the check goes
    on behind it. With no answer yet (or ``fresh``) the read waits for the
    check, which its own timeout bounds.
    """

    def __init__(self, grace: float = GRACE_SECONDS) -> None:
        self._grace = grace
        self._lock = threading.Lock()
        self._seen: dict[str, tuple[str, Any]] = {}
        self._busy: dict[str, threading.Event] = {}

    def reset(self) -> None:
        with self._lock:
            self._seen.clear()
            self._busy.clear()

    def read(self, key: str, check: Callable[[], Any], *, fresh: bool = False) -> tuple[Any, str]:
        """``(answer, checked_at ISO)`` for ``key``; ``answer`` None: the check failed."""
        with self._lock:
            known = key in self._seen
            busy = self._busy.get(key)
            if busy is None:
                busy = self._busy[key] = threading.Event()
                threading.Thread(
                    target=self._check, args=(key, check, busy),
                    name=f"endpoint-check:{key}", daemon=True,
                ).start()
        busy.wait(self._grace if known and not fresh else PROBE_SECONDS * 2)
        with self._lock:
            seen = self._seen.get(key)
        return (seen[1], seen[0]) if seen is not None else (None, _now_iso())

    def read_many(
        self, checks: Mapping[str, Callable[[], Any]], *, fresh: bool = False,
    ) -> dict[str, tuple[Any, str]]:
        """``read`` for several keys, side by side."""
        if len(checks) <= 1:
            return {key: self.read(key, check, fresh=fresh) for key, check in checks.items()}
        with ThreadPoolExecutor(max_workers=min(8, len(checks))) as pool:
            futures = {key: pool.submit(self.read, key, check, fresh=fresh) for key, check in checks.items()}
            return {key: future.result() for key, future in futures.items()}

    def _check(self, key: str, check: Callable[[], Any], busy: threading.Event) -> None:
        try:
            answer = check()
        except Exception:
            answer = None
        with self._lock:
            self._seen[key] = (_now_iso(), answer)
            self._busy.pop(key, None)
        busy.set()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


#: The endpoint checks of the desk's reads (detection, the front door).
endpoint_checks = LastCheck()
