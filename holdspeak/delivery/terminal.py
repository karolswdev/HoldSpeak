"""Immutable terminal targets and the shared output stream (HS-94-06).

PLATFORM-CONTRACT §7: a terminal is subscribed by an IMMUTABLE
node-issued target (``target_id`` + ``target_generation``), never by a
mutable client pane selector. The node keeps ONE capture per pane and
fans it out to every subscriber as an initial snapshot plus sequenced,
ANSI-preserving deltas held in a bounded replay ring. A subscriber that
falls behind the ring gets ``resync_required`` and a fresh snapshot —
never fabricated output. Absences are typed: ``target_gone``,
``generation_mismatch``, ``stream_unavailable`` (``unauthorized`` is
the transport layer's refusal, upstream of this module).

The generation is the recycled-pane lesson made structural: when the
mutable address a target was issued from resolves to a DIFFERENT
canonical ``%N`` than the one pinned at issue time, the registry bumps
the generation. Every command or subscription still carrying the old
generation refuses; nothing is ever sent to a pane's successor.

Terminal output is ephemeral — nothing in this module writes pane
content to any database (§7.2: never written to the hub DB by default).
"""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from collections import deque
from typing import Any, Optional

from ..coder_steering import (
    Clock,
    Runner,
    _default_runner,
    content_hash,
    resolve_pane_identity,
)

# ── ring / backpressure numbers ──────────────────────────────────────
# One capture window mirrors the peek contract (200 lines); the replay
# ring bounds both entry count and total bytes so a slow client can
# never grow node memory — it falls off the ring and resyncs.
CAPTURE_LINES = 200
SNAPSHOT_MAX_BYTES = 64_000  # the peek ceiling, tail-kept
RING_MAX_DELTAS = 256
RING_MAX_BYTES = 256 * 1024
MIN_POLL_INTERVAL_SECONDS = 0.2  # N subscribers share one tmux capture

PANE_REF_PREFIX = "pane:"


def _new_target_id() -> str:
    return "term_" + uuid.uuid4().hex[:16]


def _new_generation() -> str:
    return "gen_" + uuid.uuid4().hex[:12]


def normalize_pane_ref(ref: Any) -> str:
    """Accept the compat forms a client already holds: ``pane:%N``,
    a bare ``%N``, or a mutable ``session:window.pane`` address."""
    text = str(ref or "").strip()
    if text.startswith(PANE_REF_PREFIX):
        return text[len(PANE_REF_PREFIX) :].strip()
    return text


class TerminalTargetRegistry:
    """Opaque ``target_id`` → canonical tmux ``%N``, with a generation
    that moves when the underlying pane identity changes.

    ``issue`` pins what the mutable ref resolves to NOW; ``verify``
    re-proves it at use time. A ref that resolves to a different pane
    than the pinned one bumps the generation (the new pane is reachable
    only by deliberately re-issuing/refreshing the target), and the old
    generation refuses forever.
    """

    def __init__(self, *, runner: Optional[Runner] = None) -> None:
        self._runner = runner
        self._lock = threading.Lock()
        self._by_id: dict[str, dict[str, Any]] = {}
        self._by_ref: dict[str, str] = {}

    def issue(self, ref: Any) -> dict[str, Any]:
        """Issue (or refresh) the immutable target for a pane ref.

        Statuses: ``issued`` (with ``target_id``/``target_generation``/
        ``pane_id``), or the identity failure verbatim (``pane_gone`` /
        ``tmux_absent`` / ``error``) — an unprovable pane gets no target.
        """
        pane_ref = normalize_pane_ref(ref)
        if not pane_ref:
            return {"status": "pane_gone", "detail": "a pane ref is required"}
        identity = resolve_pane_identity(pane_ref, runner=self._runner)
        if identity["status"] != "ok":
            return dict(identity)
        pane_id = identity["pane_id"]
        with self._lock:
            target_id = self._by_ref.get(pane_ref)
            record = self._by_id.get(target_id) if target_id else None
            if record is None:
                record = {
                    "target_id": _new_target_id(),
                    "target_generation": _new_generation(),
                    "pane_ref": pane_ref,
                    "pane_id": pane_id,
                }
                self._by_id[record["target_id"]] = record
                self._by_ref[pane_ref] = record["target_id"]
            elif record["pane_id"] != pane_id:
                # The ref now names a DIFFERENT pane: same target handle,
                # new generation — old-generation holders refuse.
                record["pane_id"] = pane_id
                record["target_generation"] = _new_generation()
            return {
                "status": "issued",
                "target_id": record["target_id"],
                "target_generation": record["target_generation"],
                "pane_id": record["pane_id"],
            }

    def verify(self, target_id: Any, target_generation: Any) -> dict[str, Any]:
        """Prove a (target, generation) pair against tmux NOW.

        Statuses: ``ok`` (with the verified ``pane_id``), ``target_gone``,
        ``generation_mismatch`` (with ``current_generation``), and the
        transient ``tmux_absent`` / ``error`` verbatim.
        """
        with self._lock:
            record = self._by_id.get(str(target_id or ""))
        if record is None:
            return {"status": "target_gone", "detail": "unknown target_id"}
        identity = resolve_pane_identity(record["pane_ref"], runner=self._runner)
        if identity["status"] == "pane_gone":
            return {"status": "target_gone", "detail": identity.get("detail")}
        if identity["status"] != "ok":
            return dict(identity)  # transient: tmux_absent / error
        with self._lock:
            if identity["pane_id"] != record["pane_id"]:
                # Recycled: the address survived, the pane did not.
                record["pane_id"] = identity["pane_id"]
                record["target_generation"] = _new_generation()
            if str(target_generation or "") != record["target_generation"]:
                return {
                    "status": "generation_mismatch",
                    "current_generation": record["target_generation"],
                    "detail": "the pane behind this target changed identity",
                }
            return {
                "status": "ok",
                "target_id": record["target_id"],
                "target_generation": record["target_generation"],
                "pane_id": record["pane_id"],
            }

    def view(self, target_id: Any) -> Optional[dict[str, Any]]:
        with self._lock:
            record = self._by_id.get(str(target_id or ""))
            return dict(record) if record else None


# ── the shared capture ───────────────────────────────────────────────


def _delta_between(old: str, new: str) -> tuple[str, str]:
    """The honest delta from one real capture to the next.

    ``append`` when the new window extends the old (typing, fresh
    output) or scrolls past it (line overlap); ``screen`` (a full
    redraw payload) otherwise. Every byte comes from a real capture —
    nothing is synthesized.
    """
    if new.startswith(old):
        return new[len(old) :], "append"
    old_lines = old.split("\n")
    new_lines = new.split("\n")
    for k in range(min(len(old_lines), len(new_lines)), 0, -1):
        if old_lines[-k:] == new_lines[:k]:
            rest = "\n".join(new_lines[k:])
            if rest:
                return "\n" + rest, "append"
            break
    return new, "screen"


class TerminalCapture:
    """ONE node-side capture of one pane: a sequenced snapshot plus a
    bounded replay ring of ANSI-preserving deltas. All subscribers read
    from this object; none of them can stall it (reads never block the
    capture, and a reader past the ring floor resyncs)."""

    def __init__(
        self,
        pane_id: str,
        *,
        runner: Optional[Runner] = None,
        clock: Clock = time.monotonic,
        lines: int = CAPTURE_LINES,
        snapshot_max_bytes: int = SNAPSHOT_MAX_BYTES,
        ring_max_deltas: int = RING_MAX_DELTAS,
        ring_max_bytes: int = RING_MAX_BYTES,
        min_poll_interval: float = MIN_POLL_INTERVAL_SECONDS,
    ) -> None:
        self.pane_id = str(pane_id)
        self._runner = runner
        self._clock = clock
        self._lines = int(lines)
        self._snapshot_max_bytes = int(snapshot_max_bytes)
        self._ring_max_deltas = int(ring_max_deltas)
        self._ring_max_bytes = int(ring_max_bytes)
        self._min_poll_interval = float(min_poll_interval)
        self._lock = threading.Lock()
        self.sequence = 0
        self._text: Optional[str] = None
        self._hash: Optional[str] = None
        self._ring: deque[dict[str, Any]] = deque()
        self._ring_bytes = 0
        self._last_poll: Optional[float] = None
        self.capture_calls = 0  # test/metric seam: real tmux invocations

    # capture ----------------------------------------------------------

    def _capture_raw(self) -> dict[str, Any]:
        run = self._runner or _default_runner
        try:
            completed = run(
                [
                    "tmux",
                    "capture-pane",
                    "-p",
                    "-e",  # ANSI preserved: the stream is byte-honest
                    "-t",
                    self.pane_id,
                    "-S",
                    f"-{self._lines}",
                ]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"status": "error", "detail": str(exc)}
        if completed.returncode != 0:
            detail = (completed.stderr or "").strip() or "tmux refused"
            return {"status": "pane_gone", "detail": detail}
        text = (completed.stdout or "").rstrip("\n")
        encoded = text.encode("utf-8", "replace")
        if len(encoded) > self._snapshot_max_bytes:
            text = encoded[-self._snapshot_max_bytes :].decode("utf-8", "replace")
            cut = text.find("\n")
            if cut != -1:
                text = text[cut + 1 :]
        return {"status": "ok", "text": text}

    def poll(self, *, force: bool = False) -> dict[str, Any]:
        """Advance the capture if the throttle window has passed.

        Returns ``{"status": "ok"}`` (ring is current), or the capture
        failure verbatim. The throttle is what makes N subscribers cost
        one tmux call per interval.
        """
        with self._lock:
            now = self._clock()
            if (
                not force
                and self._text is not None
                and self._last_poll is not None
                and now - self._last_poll < self._min_poll_interval
            ):
                return {"status": "ok", "polled": False}
            self._last_poll = now
            captured = self._capture_raw()
            self.capture_calls += 1
            if captured["status"] != "ok":
                return captured
            text = captured["text"]
            digest = content_hash(text)
            if self._text is None:
                self.sequence = 1
                self._text, self._hash = text, digest
                return {"status": "ok", "polled": True}
            if digest == self._hash:
                return {"status": "ok", "polled": True}
            data, kind = _delta_between(self._text, text)
            self.sequence += 1
            entry = {
                "sequence": self.sequence,
                "data": data,
                "kind": kind,
                "bytes": len(data.encode("utf-8", "replace")),
            }
            self._ring.append(entry)
            self._ring_bytes += entry["bytes"]
            while self._ring and (
                len(self._ring) > self._ring_max_deltas
                or self._ring_bytes > self._ring_max_bytes
            ):
                dropped = self._ring.popleft()
                self._ring_bytes -= dropped["bytes"]
            self._text, self._hash = text, digest
            return {"status": "ok", "polled": True}

    # fan-out reads ------------------------------------------------------

    def _snapshot_envelope(self) -> dict[str, Any]:
        return {
            "status": "snapshot",
            "sequence": self.sequence,
            "content": self._text or "",
            "hash": self._hash or content_hash(""),
            "ansi": True,
            "lines": (self._text or "").count("\n") + 1 if self._text else 0,
        }

    def read(
        self,
        resume_sequence: Optional[int] = None,
        *,
        last_hash: Optional[str] = None,
    ) -> dict[str, Any]:
        """One subscriber's view: snapshot / deltas / not_modified /
        resync_required. Replay comes only from the ring — a reader the
        ring left behind resyncs with a REAL fresh snapshot."""
        with self._lock:
            if self._text is None:
                return {"status": "stream_unavailable", "detail": "no capture yet"}
            if resume_sequence is None:
                if last_hash and last_hash == self._hash:
                    # §7.1 hash-gated snapshot fallback.
                    return {"status": "not_modified", "sequence": self.sequence}
                return self._snapshot_envelope()
            try:
                resume = int(resume_sequence)
            except (TypeError, ValueError):
                out = self._snapshot_envelope()
                out["status"] = "resync_required"
                out["reason"] = "resume_sequence_invalid"
                return out
            if resume == self.sequence:
                return {"status": "not_modified", "sequence": self.sequence}
            floor = self._ring[0]["sequence"] if self._ring else self.sequence + 1
            if resume > self.sequence or resume + 1 < floor:
                out = self._snapshot_envelope()
                out["status"] = "resync_required"
                return out
            deltas = [
                {"sequence": e["sequence"], "data": e["data"], "kind": e["kind"]}
                for e in self._ring
                if e["sequence"] > resume
            ]
            return {
                "status": "deltas",
                "sequence": self.sequence,
                "deltas": deltas,
            }

    def ring_metrics(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._ring),
                "bytes": self._ring_bytes,
                "floor_sequence": self._ring[0]["sequence"] if self._ring else None,
                "sequence": self.sequence,
                "capture_calls": self.capture_calls,
            }


class TerminalStreamService:
    """Hub/node-side fan-out: verify the immutable target, then serve
    every subscriber from the ONE capture that pane owns."""

    def __init__(
        self,
        targets: TerminalTargetRegistry,
        *,
        runner: Optional[Runner] = None,
        clock: Clock = time.monotonic,
        lines: int = CAPTURE_LINES,
        ring_max_deltas: int = RING_MAX_DELTAS,
        ring_max_bytes: int = RING_MAX_BYTES,
        min_poll_interval: float = MIN_POLL_INTERVAL_SECONDS,
    ) -> None:
        self.targets = targets
        self._runner = runner
        self._clock = clock
        self._lines = lines
        self._ring_max_deltas = ring_max_deltas
        self._ring_max_bytes = ring_max_bytes
        self._min_poll_interval = min_poll_interval
        self._lock = threading.Lock()
        self._captures: dict[str, TerminalCapture] = {}

    def _capture_for(self, pane_id: str) -> TerminalCapture:
        with self._lock:
            capture = self._captures.get(pane_id)
            if capture is None:
                capture = TerminalCapture(
                    pane_id,
                    runner=self._runner,
                    clock=self._clock,
                    lines=self._lines,
                    ring_max_deltas=self._ring_max_deltas,
                    ring_max_bytes=self._ring_max_bytes,
                    min_poll_interval=self._min_poll_interval,
                )
                self._captures[pane_id] = capture
            return capture

    def read(
        self,
        target_id: Any,
        target_generation: Any,
        *,
        resume_sequence: Optional[int] = None,
        last_hash: Optional[str] = None,
    ) -> dict[str, Any]:
        """One subscription poll. Typed absences pass through per §7.1;
        transient tmux failures surface as ``stream_unavailable`` —
        never fabricated continuity."""
        verified = self.targets.verify(target_id, target_generation)
        if verified["status"] in ("tmux_absent", "error"):
            return {
                "status": "stream_unavailable",
                "detail": verified.get("detail") or verified["status"],
            }
        if verified["status"] != "ok":
            return verified  # target_gone / generation_mismatch, typed
        pane_id = verified["pane_id"]
        capture = self._capture_for(pane_id)
        polled = capture.poll()
        if polled["status"] == "pane_gone":
            with self._lock:
                self._captures.pop(pane_id, None)
            return {"status": "target_gone", "detail": polled.get("detail")}
        if polled["status"] == "error":
            return {"status": "stream_unavailable", "detail": polled.get("detail")}
        out = capture.read(resume_sequence, last_hash=last_hash)
        out["target_id"] = verified["target_id"]
        out["target_generation"] = verified["target_generation"]
        return out

    def capture_metrics(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            captures = dict(self._captures)
        return {pane: cap.ring_metrics() for pane, cap in captures.items()}


__all__ = [
    "CAPTURE_LINES",
    "MIN_POLL_INTERVAL_SECONDS",
    "RING_MAX_BYTES",
    "RING_MAX_DELTAS",
    "SNAPSHOT_MAX_BYTES",
    "TerminalCapture",
    "TerminalStreamService",
    "TerminalTargetRegistry",
    "normalize_pane_ref",
]
