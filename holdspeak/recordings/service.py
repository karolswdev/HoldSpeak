"""The hub's recordings: start, chunks, stop, the encoder queue, the Note, the frame.

One service behind the REST routes (``web/routes/recordings.py``). The encoder
runs in one daemon thread, one recording at a time, never on the loop. A
``recording_state`` frame names each change.

``HOLDSPEAK_RECORDINGS=off`` (rig hubs): no ffmpeg run (a stopped recording is
kept as its webm), no Tailscale read and no keep sweep. The routes still answer.
"""
from __future__ import annotations

import os
import queue
import threading
import time
from typing import Any, Callable, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from . import encoder as _encoder
from . import tailnet as _tailnet
from .store import KEEP_DAYS, STALE_SECONDS, Recording, RecordingRefused, RecordingStore

log = get_logger("recordings.service")

OWNER = Principal(PrincipalKind.OWNER, "owner-recordings")
FRAME = "recording_state"
#: The stale watcher looks this often.
WATCH_SECONDS = 30.0


def recordings_on() -> bool:
    """``HOLDSPEAK_RECORDINGS=off``: no ffmpeg, no Tailscale read, no sweep."""
    return os.environ.get("HOLDSPEAK_RECORDINGS", "on").strip().lower() not in {"off", "0", "false", "no"}


def _minutes(seconds: float) -> str:
    whole = max(0, int(round(seconds)))
    if whole < 60:
        return f"{whole} s"
    return f"{max(1, round(whole / 60))} min"


class RecordingsService:
    def __init__(self, store: Optional[RecordingStore] = None) -> None:
        self.store = store or RecordingStore()
        self._broadcast: Callable[[str, Any], None] = lambda *_: None
        self._dispatch: Optional[Callable[..., Any]] = None
        self._bases: dict[str, Optional[str]] = {"local": None, "tailnet": None}
        self._jobs: "queue.Queue[str]" = queue.Queue()
        self._worker: Optional[threading.Thread] = None
        self._watcher: Optional[threading.Thread] = None
        self._halt = threading.Event()
        self._lock = threading.Lock()

    # ── wiring ──────────────────────────────────────────────────────────

    def configure(
        self,
        *,
        broadcast: Optional[Callable[[str, Any], None]] = None,
        dispatch: Optional[Callable[..., Any]] = None,
        store: Optional[RecordingStore] = None,
    ) -> None:
        if broadcast is not None:
            self._broadcast = broadcast
        if dispatch is not None:
            self._dispatch = dispatch
        if store is not None:
            self.store = store

    def remember_bases(self, *, port: Optional[int]) -> dict[str, Optional[str]]:
        """The two link bases for this hub: 127.0.0.1 and (Serve on) the tailnet."""
        if port:
            self._bases["local"] = f"http://127.0.0.1:{int(port)}"
            self._bases["tailnet"] = _tailnet.tailnet_base(int(port)) if recordings_on() else None
        return dict(self._bases)

    def bases(self) -> dict[str, Optional[str]]:
        return dict(self._bases)

    def wire(self, rec: Recording) -> dict[str, Any]:
        return rec.wire(links=self._bases)

    def _emit(self, reason: str, rec: Recording) -> None:
        try:
            self._broadcast("recording_state", {"reason": reason, "recording": self.wire(rec)})
        except Exception as exc:  # pragma: no cover - a dropped frame is not a failure
            log.debug(f"recording frame dropped: {exc}")

    # ── reads ───────────────────────────────────────────────────────────

    def payload(self) -> dict[str, Any]:
        rows = self.store.list()
        return {
            "recordings": [self.wire(rec) for rec in rows],
            "usage": {"bytes": self.store.usage(), "keep_days": KEEP_DAYS},
            "links": self.bases(),
            "encoder": "ffmpeg" if (recordings_on() and _encoder.ffmpeg_path()) else "none",
            "folder": str(self.store.root()),
        }

    def get(self, recording_id: str) -> dict[str, Any]:
        return self.wire(self.store.require(recording_id))

    # ── the capture ─────────────────────────────────────────────────────

    def start(self, *, width: int = 0, height: int = 0, voice: bool = False,
              project_id: str = "", view: str = "") -> dict[str, Any]:
        live = [rec for rec in self.store.list() if rec.state == "recording"]
        if live:
            raise RecordingRefused("busy", "A recording is already running.")
        rec = self.store.create(width=width, height=height, voice=voice, project_id=project_id, view=view)
        self.ensure_watching()
        self._emit("started", rec)
        return self.wire(rec)

    def chunk(self, recording_id: str, data: bytes) -> dict[str, Any]:
        rec = self.store.append_chunk(recording_id, data)
        # One frame a chunk (each 5 s): the other views' lamps keep their clock.
        self._emit("chunk", rec)
        return {"id": rec.id, "bytes_in": rec.bytes_in, "chunks": rec.chunks, "state": rec.state}

    def stop(self, recording_id: str) -> dict[str, Any]:
        rec, changed = self.store.stop(recording_id)
        if changed:
            self._emit("stopped" if rec.state == "encoding" else "failed", rec)
            if rec.state == "encoding":
                self._queue(rec.id)
        return self.wire(rec)

    def close_stale(self, *, now: Optional[float] = None) -> list[str]:
        closed = []
        for recording_id in self.store.stale(now=now, after=STALE_SECONDS):
            try:
                self.stop(recording_id)
                closed.append(recording_id)
            except RecordingRefused:
                continue
        return closed

    # ── the encoder ─────────────────────────────────────────────────────

    def retry(self, recording_id: str) -> dict[str, Any]:
        rec = self.store.require(recording_id)
        if rec.state != "failed" or rec.bytes_in <= 0:
            raise RecordingRefused("not_failed", "Only a failed recording with video can be encoded again.")
        rec = self.store.update(rec.id, state="encoding", progress=0, error="")
        self._emit("encoding", rec)
        self._queue(rec.id)
        return self.wire(rec)

    def _queue(self, recording_id: str) -> None:
        self._jobs.put(recording_id)
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = threading.Thread(target=self._work, name="recordings-encoder", daemon=True)
                self._worker.start()

    def _work(self) -> None:
        while not self._halt.is_set():
            try:
                recording_id = self._jobs.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                self.encode_now(recording_id)
            except Exception as exc:  # pragma: no cover - the row says failed below
                log.error(f"recording {recording_id} encode crashed: {exc}")
                try:
                    rec = self.store.update(recording_id, state="failed", error="The encode stopped.")
                    self._emit("failed", rec)
                except RecordingRefused:
                    pass

    def encode_now(self, recording_id: str) -> dict[str, Any]:
        """Encode one recording in this thread (the worker's body; tests call it)."""
        rec = self.store.require(recording_id)
        if rec.state != "encoding":
            return self.wire(rec)
        ffmpeg = _encoder.ffmpeg_path() if recordings_on() else None
        source = self.store.input_path(rec.id)
        if ffmpeg is None:
            rec = self.store.update(
                rec.id, state="ready", encoder="webm", progress=100,
                bytes_out=source.stat().st_size if source.exists() else 0,
            )
            self._ready(rec)
            return self.wire(rec)
        last_emit = [-10]

        def progress(pct: int) -> None:
            if pct - last_emit[0] < 5 and pct < 100:
                return
            last_emit[0] = pct
            current = self.store.update(rec.id, progress=pct)
            self._emit("progress", current)

        ok, error = _encoder.encode(
            ffmpeg, source, self.store.output_path(rec.id),
            total_s=rec.duration_s or 1.0, on_progress=progress,
        )
        if not ok:
            rec = self.store.update(rec.id, state="failed", error=error or "The encode failed.")
            self._emit("failed", rec)
            return self.wire(rec)
        out = self.store.output_path(rec.id)
        _encoder.poster(ffmpeg, out, self.store.poster_path(rec.id), duration_s=rec.duration_s)
        rec = self.store.update(rec.id, state="ready", encoder="mp4", progress=100, bytes_out=out.stat().st_size)
        self._ready(rec)
        return self.wire(rec)

    def _ready(self, rec: Recording) -> None:
        try:
            note_ref = self._write_note(rec)
        except Exception as exc:
            log.info(f"recording note not written for {rec.id}: {exc}")
            note_ref = ""
        if note_ref:
            rec = self.store.update(rec.id, note_ref=note_ref)
        self._emit("ready", rec)

    # ── the note ────────────────────────────────────────────────────────

    def note_markdown(self, rec: Recording) -> tuple[str, str]:
        title = f"{rec.title} · {_minutes(rec.duration_s)}"
        wire = self.wire(rec)
        links = wire["links"]
        body = [f"# {title}", ""]
        if links.get("tailnet"):
            body += [f"[Watch on your phone]({links['tailnet']})", ""]
        if links.get("local"):
            body += [f"[Watch on this Mac]({links['local']})", ""]
        if rec.encoder == "webm":
            body += ["Kept as webm. Install ffmpeg (`brew install ffmpeg`) for an iPhone video.", ""]
        return title, "\n".join(body).rstrip() + "\n"

    def _write_note(self, rec: Recording) -> str:
        dispatch = self._dispatch
        if dispatch is None:
            from ..mcp.tools import dispatch as mcp_dispatch

            dispatch = mcp_dispatch
        title, body = self.note_markdown(rec)
        created = dispatch("desk.create", {"kind": "notes", "data": {
            "title": title, "body_markdown": body, "tags": ["recording"],
        }}, OWNER)
        from ..calls.service import _note_id

        note_id = _note_id(created)
        if not note_id:
            return ""
        note_ref = f"note:{note_id}"
        if rec.project_id:
            try:
                dispatch("project.resource.add", {"project_id": rec.project_id, "resource_ref": note_ref}, OWNER)
            except Exception as exc:
                log.info(f"recording note not filed to project {rec.project_id}: {exc}")
        return note_ref

    # ── share and park ──────────────────────────────────────────────────

    def share(self, recording_id: str) -> dict[str, Any]:
        rec = self.store.share(recording_id)
        self._emit("shared", rec)
        return self.wire(rec)

    def unshare(self, recording_id: str) -> dict[str, Any]:
        rec = self.store.unshare(recording_id)
        self._emit("shared", rec)
        return self.wire(rec)

    def park(self, recording_id: str) -> dict[str, Any]:
        rec = self.store.park(recording_id)
        self._emit("parked", rec)
        return {"id": rec.id, "parked": True}

    # ── the lifespan ────────────────────────────────────────────────────

    def startup(self) -> None:
        """Park old recordings, finish encodes a restart cut, watch for stale ones."""
        if not recordings_on():
            return
        try:
            self.store.sweep()
        except Exception as exc:
            log.info(f"recordings keep sweep failed: {exc}")
        for rec in self.store.list():
            if rec.state == "encoding":
                self._queue(rec.id)
        self.ensure_watching()

    def ensure_watching(self) -> None:
        if not recordings_on():
            return
        with self._lock:
            if self._watcher is not None and self._watcher.is_alive():
                return
            self._halt.clear()
            self._watcher = threading.Thread(target=self._watch, name="recordings-stale", daemon=True)
            self._watcher.start()

    def _watch(self) -> None:
        while not self._halt.wait(WATCH_SECONDS):
            try:
                self.close_stale()
            except Exception as exc:  # pragma: no cover
                log.debug(f"recordings stale watch: {exc}")

    def shutdown(self) -> None:
        self._halt.set()


#: The hub's one recordings service.
RECORDINGS = RecordingsService()

__all__ = ["FRAME", "OWNER", "RECORDINGS", "RecordingsService", "recordings_on"]
