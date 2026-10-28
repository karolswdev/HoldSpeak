"""The recordings on disk: one folder per recording, ``meta.json`` is its row.

``~/.local/share/holdspeak/recordings/<id>/``:

* ``in.webm``   the chunks as the browser sent them, appended in order;
* ``out.mp4``   the encode (H.264, AAC, faststart), when ffmpeg is present;
* ``poster.jpg`` one frame at 2 s;
* ``meta.json`` the row (state, times, sizes, share token, note ref).

No table: the folder is the record, and parking moves it whole
(``recordings/_parked/<id>/``). Nothing here is ever deleted.
"""
from __future__ import annotations

import json
import os
import secrets
import shutil
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

#: A recording with no chunk for this long is closed by the hub.
STALE_SECONDS = 120.0
#: A recording older than this many days is parked.
KEEP_DAYS = 30
#: One chunk is 5 s at 2.5 Mbit/s (about 1.6 MB); refuse anything absurd.
MAX_CHUNK_BYTES = 64 * 1024 * 1024

STATES = ("recording", "encoding", "ready", "failed")
PARKED_DIR = "_parked"


class RecordingRefused(Exception):
    """A write the recording's state does not allow (HTTP 409 / 404)."""

    def __init__(self, code: str, detail: str, status: int = 409) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status = status


def recordings_root() -> Path:
    """The fixed owner-local recordings folder (read at call time: HOME isolation)."""
    return Path.home() / ".local" / "share" / "holdspeak" / "recordings"


def utc_stamp(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def title_for(started_ts: float) -> str:
    """``Recording · Tue 28 Oct 17:40`` in the hub's local zone."""
    local = datetime.fromtimestamp(float(started_ts), tz=timezone.utc).astimezone()
    return f"Recording · {local:%a} {local.day} {local:%b %H:%M}"


def slug_for(started_ts: float) -> str:
    """``recording-2026-10-28-1740``: the file name of the shared link."""
    local = datetime.fromtimestamp(float(started_ts), tz=timezone.utc).astimezone()
    return f"recording-{local:%Y-%m-%d-%H%M}"


@dataclass
class Recording:
    id: str
    started_ts: float
    title: str
    state: str = "recording"
    ended_ts: Optional[float] = None
    last_chunk_ts: Optional[float] = None
    bytes_in: int = 0
    bytes_out: int = 0
    chunks: int = 0
    width: int = 0
    height: int = 0
    duration_s: float = 0.0
    voice: bool = False
    project_id: str = ""
    share_token: str = ""
    note_ref: str = ""
    progress: int = 0
    error: str = ""
    #: ``mp4`` (ffmpeg encoded it) or ``webm`` (no ffmpeg: the input is the video).
    encoder: str = ""
    #: The view that captures (``started`` by it); a second view sees "another view".
    view: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Recording":
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

    def video_name(self) -> str:
        return f"{slug_for(self.started_ts)}.{'mp4' if self.encoder == 'mp4' else 'webm'}"

    def wire(self, *, links: Optional[dict[str, Optional[str]]] = None) -> dict[str, Any]:
        row = asdict(self)
        row.pop("extra", None)
        row["started_at"] = utc_stamp(self.started_ts)
        row["ended_at"] = utc_stamp(self.ended_ts)
        row["shared"] = bool(self.share_token)
        row.pop("share_token", None)
        row["video_name"] = self.video_name() if self.state == "ready" else None
        share = self.share_path()
        bases = links or {}
        row["links"] = {
            "tailnet": f"{bases['tailnet']}{share}" if share and bases.get("tailnet") else None,
            "local": f"{bases['local']}{share}" if share and bases.get("local") else None,
        }
        return row

    def share_path(self) -> Optional[str]:
        if self.state != "ready" or not self.share_token:
            return None
        return f"/r/{self.id}/{self.share_token}/{self.video_name()}"


class RecordingStore:
    """The recordings folder: create, append, stop, park, share; one lock."""

    def __init__(self, root: Optional[Callable[[], Path]] = None) -> None:
        self._root = root or recordings_root
        self._lock = threading.RLock()

    # ── paths ───────────────────────────────────────────────────────────

    def root(self) -> Path:
        return self._root()

    def folder(self, recording_id: str) -> Path:
        if not recording_id or "/" in recording_id or recording_id.startswith((".", "_")):
            raise RecordingRefused("not_found", "No such recording.", 404)
        return self.root() / recording_id

    def input_path(self, recording_id: str) -> Path:
        return self.folder(recording_id) / "in.webm"

    def output_path(self, recording_id: str) -> Path:
        return self.folder(recording_id) / "out.mp4"

    def poster_path(self, recording_id: str) -> Path:
        return self.folder(recording_id) / "poster.jpg"

    def video_path(self, rec: Recording) -> Path:
        return self.output_path(rec.id) if rec.encoder == "mp4" else self.input_path(rec.id)

    # ── rows ────────────────────────────────────────────────────────────

    def _write(self, rec: Recording) -> None:
        folder = self.folder(rec.id)
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / "meta.json.tmp"
        tmp.write_text(json.dumps(asdict(rec), indent=2), encoding="utf-8")
        os.replace(tmp, folder / "meta.json")

    def save(self, rec: Recording) -> Recording:
        with self._lock:
            self._write(rec)
        return rec

    def get(self, recording_id: str) -> Optional[Recording]:
        try:
            meta = self.folder(recording_id) / "meta.json"
        except RecordingRefused:
            return None
        try:
            return Recording.from_json(json.loads(meta.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            return None

    def require(self, recording_id: str) -> Recording:
        rec = self.get(recording_id)
        if rec is None:
            raise RecordingRefused("not_found", "No such recording.", 404)
        return rec

    def list(self) -> list[Recording]:
        root = self.root()
        if not root.is_dir():
            return []
        rows = []
        for child in root.iterdir():
            if not child.is_dir() or child.name.startswith(("_", ".")):
                continue
            rec = self.get(child.name)
            if rec is not None:
                rows.append(rec)
        return sorted(rows, key=lambda r: r.started_ts, reverse=True)

    # ── the state machine ───────────────────────────────────────────────

    def create(self, *, width: int = 0, height: int = 0, voice: bool = False,
               project_id: str = "", view: str = "", now: Optional[float] = None) -> Recording:
        started = time.time() if now is None else float(now)
        rec = Recording(
            id=f"r{uuid.uuid4().hex[:10]}",
            started_ts=started,
            title=title_for(started),
            last_chunk_ts=started,
            width=max(0, int(width or 0)),
            height=max(0, int(height or 0)),
            voice=bool(voice),
            project_id=str(project_id or ""),
            view=str(view or "")[:64],
            share_token=secrets.token_urlsafe(18),
        )
        with self._lock:
            self._write(rec)
            self.input_path(rec.id).touch()
        return rec

    def append_chunk(self, recording_id: str, data: bytes, *, now: Optional[float] = None) -> Recording:
        if len(data) > MAX_CHUNK_BYTES:
            raise RecordingRefused("too_large", "The chunk is too large.", 413)
        with self._lock:
            rec = self.require(recording_id)
            if rec.state != "recording":
                raise RecordingRefused("not_recording", "This recording has stopped.")
            if data:
                with self.input_path(rec.id).open("ab") as sink:
                    sink.write(data)
            rec.bytes_in += len(data)
            rec.chunks += 1
            rec.last_chunk_ts = time.time() if now is None else float(now)
            rec.duration_s = max(0.0, rec.last_chunk_ts - rec.started_ts)
            self._write(rec)
            return rec

    def stop(self, recording_id: str, *, now: Optional[float] = None) -> tuple[Recording, bool]:
        """End the capture. Returns ``(row, changed)``; a second stop changes nothing."""
        with self._lock:
            rec = self.require(recording_id)
            if rec.state != "recording":
                return rec, False
            ended = time.time() if now is None else float(now)
            rec.ended_ts = ended
            rec.duration_s = max(0.0, ended - rec.started_ts)
            if rec.bytes_in <= 0:
                rec.state = "failed"
                rec.error = "Nothing was recorded."
            else:
                rec.state = "encoding"
                rec.progress = 0
            self._write(rec)
            return rec, True

    def stale(self, *, now: Optional[float] = None, after: float = STALE_SECONDS) -> list[str]:
        """The ids of recordings that got no chunk for ``after`` seconds."""
        clock = time.time() if now is None else float(now)
        return [
            rec.id for rec in self.list()
            if rec.state == "recording" and clock - float(rec.last_chunk_ts or rec.started_ts) >= after
        ]

    def update(self, recording_id: str, **changes: Any) -> Recording:
        with self._lock:
            rec = self.require(recording_id)
            for key, value in changes.items():
                setattr(rec, key, value)
            self._write(rec)
            return rec

    # ── share, park, keep ───────────────────────────────────────────────

    def share(self, recording_id: str) -> Recording:
        return self.update(recording_id, share_token=secrets.token_urlsafe(18))

    def unshare(self, recording_id: str) -> Recording:
        return self.update(recording_id, share_token="")

    def by_share(self, recording_id: str, token: str) -> Optional[Recording]:
        """The shared recording when the token matches; a parked one never does."""
        rec = self.get(recording_id)
        if rec is None or rec.state != "ready" or not rec.share_token or not token:
            return None
        if not secrets.compare_digest(rec.share_token, str(token)):
            return None
        return rec

    def park(self, recording_id: str) -> Recording:
        with self._lock:
            rec = self.require(recording_id)
            if rec.state in {"recording", "encoding"}:
                raise RecordingRefused("busy", "Stop the recording first.")
            parked = self.root() / PARKED_DIR
            parked.mkdir(parents=True, exist_ok=True)
            target = parked / rec.id
            if target.exists():
                target = parked / f"{rec.id}-{int(time.time())}"
            shutil.move(str(self.folder(rec.id)), str(target))
            return rec

    def sweep(self, *, now: Optional[float] = None, keep_days: int = KEEP_DAYS) -> list[str]:
        """Park every finished recording older than ``keep_days``. Never deletes."""
        clock = time.time() if now is None else float(now)
        horizon = clock - keep_days * 86400
        parked: list[str] = []
        for rec in self.list():
            if rec.state in {"recording", "encoding"} or rec.started_ts >= horizon:
                continue
            try:
                self.park(rec.id)
                parked.append(rec.id)
            except (OSError, RecordingRefused):
                continue
        return parked

    def usage(self) -> int:
        """Bytes under the recordings folder, parked ones included."""
        root = self.root()
        if not root.is_dir():
            return 0
        total = 0
        for path in root.rglob("*"):
            try:
                if path.is_file():
                    total += path.stat().st_size
            except OSError:
                continue
        return total


__all__ = [
    "KEEP_DAYS",
    "MAX_CHUNK_BYTES",
    "PARKED_DIR",
    "Recording",
    "RecordingRefused",
    "RecordingStore",
    "STALE_SECONDS",
    "recordings_root",
    "slug_for",
    "title_for",
    "utc_stamp",
]
