"""The mesh-edge relay provider (HS-85-02).

Implements the same tiny interface every intel provider speaks —
``run_prompt(...) -> str`` raising ``MeetingIntelError`` — by enqueueing the
run on the hub's relay queue (HS-85-01) and waiting, bounded, for the node's
worker to execute it on ITS OWN provider. The model and the key never move;
the request does.

Honesty rules, pinned by the phase design:
- A node that has not polled within the liveness window refuses IMMEDIATELY,
  naming the node and its last-seen age — never queue-then-timeout.
- Every job carries a deadline; expiry and node-side failures surface the
  queue's own named error verbatim.
"""
from __future__ import annotations

import time as _time
from datetime import datetime
from typing import Any, Callable, Optional

from .models import MeetingIntelError

DEFAULT_LIVENESS_WINDOW_SECONDS = 15
DEFAULT_DEADLINE_SECONDS = 120
DEFAULT_POLL_INTERVAL_SECONDS = 0.5


class MeshRelayIntel:
    """Runs prompts on a mesh node's provider via the hub relay queue."""

    def __init__(
        self,
        *,
        node: str,
        model_hint: str = "",
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
        liveness_window_seconds: int = DEFAULT_LIVENESS_WINDOW_SECONDS,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        relay: Any = None,
        sleep: Callable[[float], None] = _time.sleep,
        now: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.node = str(node or "").strip()
        self.model_hint = str(model_hint or "")
        self.active_provider = "mesh"
        self._deadline_seconds = max(1, int(deadline_seconds))
        self._liveness_window = max(1, int(liveness_window_seconds))
        self._poll_interval = max(0.05, float(poll_interval_seconds))
        self._relay = relay
        self._sleep = sleep
        self._now = now

    def _queue(self) -> Any:
        if self._relay is not None:
            return self._relay
        from ..db import get_database

        return get_database().mesh_relay

    def run_prompt(
        self,
        *,
        system_prompt: str = "",
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self.node:
            raise MeetingIntelError("mesh relay: no node configured")
        queue = self._queue()

        last_seen = queue.worker_last_seen(self.node)
        now = self._now()
        if last_seen is None:
            raise MeetingIntelError(
                f"mesh node '{self.node}' is offline (no worker has ever polled)"
            )
        age = (now - last_seen).total_seconds()
        if age > self._liveness_window:
            raise MeetingIntelError(
                f"mesh node '{self.node}' is offline (last seen {int(age)}s ago)"
            )

        job = queue.enqueue(
            node=self.node,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_hint=self.model_hint,
            deadline_seconds=self._deadline_seconds,
            now=now,
        )
        while True:
            current = queue.get(job.id, now=self._now())
            if current is None:
                raise MeetingIntelError(f"mesh relay job {job.id} vanished")
            if current.status == "completed":
                return str(current.result or "")
            if current.status == "failed":
                raise MeetingIntelError(
                    f"mesh node '{self.node}': {current.error or 'run failed'}"
                )
            self._sleep(self._poll_interval)
