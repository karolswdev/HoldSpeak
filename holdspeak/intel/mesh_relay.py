"""The mesh-edge relay provider (HS-85-02).

Implements the same tiny interface every intel provider speaks —
``run_prompt(...) -> str`` raising ``MeetingIntelError`` — by enqueueing the
run on the hub's relay queue (HS-85-01) and waiting, bounded, for the node's
worker to execute it on ITS OWN provider. The model and the key never move;
the request does.

Honesty rules, pinned by the phase design:
- A destination whose pairing is absent, unreadable, or revoked, and one whose
  exact ``(node_id, credential_generation)`` has not polled within the liveness
  window, refuses IMMEDIATELY by a fixed name — never queue-then-timeout, and
  never on a name-only timestamp that another generation's poll could satisfy
  (HS-131-16 repair R2.5).
- Every job carries a deadline; expiry and node-side failures surface the
  queue's own named error verbatim.
"""
from __future__ import annotations

import time as _time
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..mesh_authority.refusals import (
    NODE_CUSTODY_UNREADABLE,
    NODE_OFFLINE,
    NODE_UNPAIRED,
)
from .models import MeetingIntelError

_log = get_logger("intel.mesh_relay")

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
        token_store: Any = None,
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
        self._token_store = token_store
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

        now = self._now()
        if self._deployment_revision is None or not isinstance(self._warrant, dict):
            raise MeetingIntelError("mesh relay: mesh_envelope_missing")
        revision = self._deployment_revision.to_dict()
        if not str(revision.get("id") or ""):
            raise MeetingIntelError("mesh relay: mesh_envelope_missing")
        self._assert_envelope_is_this_childs(revision)

        from ..constitutional_context import constitutional_system_message
        constitutional = constitutional_system_message()
        full_system = (constitutional + "\n\n" + system_prompt).strip() if constitutional else system_prompt
        envelope: dict[str, Any] = {
            "deployment_revision": revision, "warrant": self._warrant
        }
        # HS-131-16: the attempt ordinal the hub will SIGN comes only from the
        # runner-issued dispatch context bound to this engine — never from a
        # relay caller field and never from the request body. Without one there
        # is no ordinal to bind, so the hub can sign no offer for this row and it
        # honestly expires at its deadline instead of dispatching unbound.
        ordinal = self._context_attempt_ordinal()
        if ordinal:
            envelope["attempt_ordinal"] = ordinal
        # HS-131-16 (repair R2.5): the pairing read, the exact
        # ``(node_id, generation)`` liveness check, and the enqueue happen under
        # ONE held custody lock. Reading the pairing, then checking liveness,
        # then queueing lets a rotate or re-pair land in the middle and address
        # the row to a credential nothing is polling under. There is no name-only
        # fallback below it: an unpaired, unreadable, revoked, or non-live
        # destination refuses IMMEDIATELY, by a fixed name, and queues nothing.
        store = self._store()
        with self._custody_lock(store):
            node_id, generation = self._destination_binding(store)
            if not queue.node_live(node_id, generation, self._liveness_window, now=now):
                raise MeetingIntelError(f"mesh relay: {NODE_OFFLINE}")
            job = queue.enqueue(
                node=self.node,
                system_prompt=full_system,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model_hint=self.model_hint,
                envelope=envelope,
                deadline_seconds=self._deadline_seconds,
                destination_node_id=node_id,
                destination_generation=generation,
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

    def _context_attempt_ordinal(self) -> int:
        """The bound child's attempt ordinal, or ``0`` when none is bound."""
        from ..kernel.dispatch_context import dispatch_context_of

        context = dispatch_context_of(self)
        ordinal = int(getattr(context, "attempt_ordinal", 0) or 0) if context else 0
        return ordinal if ordinal >= 1 else 0

    def _store(self) -> Any:
        """This hub's node pairing custody."""
        if self._token_store is not None:
            return self._token_store
        from ..delivery.node_link import NodeTokenStore

        return NodeTokenStore()

    @staticmethod
    def _custody_lock(store: Any) -> Any:
        """Hold pairing custody, when there is custody to hold."""
        lock = getattr(store, "custody_lock", None)
        return lock() if callable(lock) else nullcontext()

    def _destination_binding(self, store: Any) -> tuple[str, int]:
        """This node's STABLE id and live credential generation, or a refusal.

        Binding by identity rather than by name is Sol Amendment 3: a rotate,
        revoke, or re-pair moves the generation, so queued work addressed to the
        previous credential can never be claimed by its replacement.

        Repair R2.5: there is no unbound pair any more. ``("", 0)`` was a
        destination no claim could ever match, so queueing under it was work
        that could only expire — and, worse, it dropped the caller onto a
        name-only timestamp that any generation's poll could satisfy. Absent,
        unreadable, and revoked custody each refuse here by a fixed name.
        """
        try:
            pairing = store.pairing(self.node)
        except Exception:  # custody is refused BY NAME, never guessed at
            _log.warning("mesh node %r pairing custody is unreadable", self.node)
            raise MeetingIntelError(
                f"mesh relay: {NODE_CUSTODY_UNREADABLE}"
            ) from None
        if pairing is None or not pairing.node_id:
            _log.warning(
                "mesh node %r is not paired; its relay work cannot be claimed",
                self.node,
            )
            raise MeetingIntelError(f"mesh relay: {NODE_UNPAIRED}")
        generation = int(pairing.generation or 0)
        if generation < 1:
            raise MeetingIntelError(f"mesh relay: {NODE_UNPAIRED}")
        return str(pairing.node_id), generation

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
