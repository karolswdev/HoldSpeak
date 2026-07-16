"""HS-93-06 — the deterministic capture/intelligence fault plane.

Real-life faults (a transcription crash mid-meeting, a model that is gone at
intelligence time, one routed plugin failing, process death between the last
checkpoint and finalize, a disk that refuses the checkpoint write) must be
reproducible on demand to prove the recovery contract. This module is that
switchboard: production code calls :func:`trip` / :func:`kill_process` /
:func:`faulted_plugin_keys` at exactly one declared injection site per fault
point, and every call is a no-op unless the ``HOLDSPEAK_FAULT`` environment
variable explicitly names the point.

Rules:

- **Off by default.** ``HOLDSPEAK_FAULT`` unset or empty means every hook is
  inert; there is no config knob, CLI flag, or API that can enable a fault.
- **Explicit only.** The env value is a comma-separated list of point names
  from :data:`FAULT_POINTS` (plus the parameterized ``intel.plugin:<id>``
  form). An unknown name raises ``ValueError`` instead of silently doing
  nothing, so a typo cannot fake a passing fault walk.
- **One declared site per point.** ``tests/unit/test_fault_plane.py`` holds a
  census locking each point to the file listed in :data:`FAULT_POINTS`.
"""

from __future__ import annotations

import os
import signal

#: The only switch. Unset/empty = every fault hook is inert.
FAULT_ENV = "HOLDSPEAK_FAULT"

#: Parameterized plugin fault: ``intel.plugin:<plugin_id>`` fails exactly the
#: named routed plugin key inside ``run_meeting_plugin_chain``.
PLUGIN_FAULT_PREFIX = "intel.plugin:"

#: Every declared fault point -> the single module allowed to inject it.
FAULT_POINTS: dict[str, str] = {
    # Transcription raises mid-meeting; the loop must drop the segment,
    # keep the meeting alive, and keep checkpointing.
    "meeting.transcribe": "holdspeak/meeting_session/transcribe_loop.py",
    # The journal's fsync checkpoint fails like a full/refusing disk; the
    # capture must go `recoverable`, never silently lose audio claims.
    "meeting.checkpoint_write": "holdspeak/meeting_capture_journal.py",
    # SIGKILL between the last durable checkpoint and the finalize
    # transaction; restart must recover the SAME meeting identity.
    "meeting.finalize_kill": "holdspeak/meeting_session/session.py",
    # The deferred-intel model construction fails at intelligence time; the
    # job must schedule a bounded retry, never a false Ready.
    "intel.model_unavailable": "holdspeak/intel_queue.py",
    # intel.plugin:<id> — one named routed plugin fails; the meeting must
    # stay `partial` with the completed work retained.
    PLUGIN_FAULT_PREFIX: "holdspeak/meeting_plugins.py",
}


class FaultInjected(RuntimeError):
    """Raised by :func:`trip` when the named fault point is armed."""


def active_faults() -> frozenset[str]:
    """Parse ``HOLDSPEAK_FAULT`` into the armed point set (empty when unset).

    Raises ``ValueError`` on any token that is not a declared fault point —
    failing loud is the guard against a typo silently disarming a fault walk.
    """
    raw = os.environ.get(FAULT_ENV, "").strip()
    if not raw:
        return frozenset()
    points: set[str] = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if token in FAULT_POINTS and token != PLUGIN_FAULT_PREFIX:
            points.add(token)
        elif token.startswith(PLUGIN_FAULT_PREFIX) and len(token) > len(PLUGIN_FAULT_PREFIX):
            points.add(token)
        else:
            known = ", ".join(sorted(FAULT_POINTS))
            raise ValueError(
                f"{FAULT_ENV} names unknown fault point {token!r}; known: {known}"
            )
    return frozenset(points)


def fault_enabled(point: str) -> bool:
    """True only when ``HOLDSPEAK_FAULT`` explicitly names ``point``."""
    return point in active_faults()


def trip(point: str, exc_type: type[BaseException] = FaultInjected) -> None:
    """Raise ``exc_type`` at an armed fault point; no-op otherwise."""
    if fault_enabled(point):
        raise exc_type(f"{FAULT_ENV}={point} injected failure")


def kill_process(point: str) -> None:
    """SIGKILL this process at an armed fault point; no-op otherwise.

    SIGKILL (not ``sys.exit``) on purpose: no ``finally`` blocks, no atexit,
    no flush — the honest shape of a crash or forced termination.
    """
    if fault_enabled(point):
        os.kill(os.getpid(), signal.SIGKILL)


def faulted_plugin_keys() -> frozenset[str]:
    """Plugin ids named via ``intel.plugin:<id>`` entries (empty when unarmed)."""
    return frozenset(
        point[len(PLUGIN_FAULT_PREFIX):]
        for point in active_faults()
        if point.startswith(PLUGIN_FAULT_PREFIX)
    )
