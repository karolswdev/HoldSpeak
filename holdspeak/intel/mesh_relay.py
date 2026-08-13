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
        deployment_revision: Any = None,
        warrant: Optional[dict[str, Any]] = None,
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
        self._deployment_revision = deployment_revision
        self._warrant = warrant
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

        if self._deployment_revision is None or not isinstance(self._warrant, dict):
            raise MeetingIntelError("mesh relay: mesh_envelope_missing")
        revision = self._deployment_revision.to_dict()
        if not str(revision.get("id") or ""):
            raise MeetingIntelError("mesh relay: mesh_envelope_missing")
        self._assert_envelope_is_this_childs(revision)

        from ..constitutional_context import constitutional_system_message
        constitutional = constitutional_system_message()
        full_system = (constitutional + "\n\n" + system_prompt).strip() if constitutional else system_prompt
        job = queue.enqueue(
            node=self.node,
            system_prompt=full_system,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            model_hint=self.model_hint,
            envelope={"deployment_revision": revision, "warrant": self._warrant},
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

    def _assert_envelope_is_this_childs(self, revision: dict[str, Any]) -> None:
        """The envelope must belong to the child that is dispatching RIGHT NOW.

        HS-131-10 round 2. The revision and the warrant are CONSTRUCTOR state, so
        a relay engine that outlived one admitted child carried that child's
        warrant into the next one's request — the mesh node would then have been
        handed an envelope whose authority belonged to a different operation while
        the receipt named this one.

        The runner refuses to rebind a foreign context onto an engine, which stops
        the reuse itself; this is the same fact checked at the last possible
        moment, from the relay's own side, and it names the mismatch rather than
        relaying under a stale basis. No context bound (a mesh receiver replaying
        an already-verified envelope) leaves the existing posture untouched.
        """
        from ..kernel.dispatch_context import dispatch_context_of

        context = dispatch_context_of(self)
        if context is None:
            return
        warrant = self._warrant if isinstance(self._warrant, dict) else {}
        if context.warrant_basis != str(warrant.get("signature") or ""):
            raise MeetingIntelError("mesh relay: mesh_envelope_stale_warrant")
        if context.revision_id != str(revision.get("id") or ""):
            raise MeetingIntelError("mesh relay: mesh_envelope_stale_revision")

    def _chat_completion_text(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """The engine's de-facto SECOND seam: the built-in meeting plugins and
        the segment probe call the chat surface directly (the `messages`
        keyword shape, `plugins/segment_probe.py`). Without this adapter every
        LLM plugin fails softly on a mesh engine while the chain still reports
        executed=True — the HS-85-05 walk find. The relay wire stays
        `run_prompt`; messages fold onto it."""
        system = "\n\n".join(
            str(m.get("content") or "") for m in messages if m.get("role") == "system"
        ).strip()
        user = "\n\n".join(
            str(m.get("content") or "") for m in messages if m.get("role") != "system"
        ).strip()
        return self.run_prompt(
            system_prompt=system,
            user_prompt=user,
            temperature=temperature,
            max_tokens=max_tokens,
        )
