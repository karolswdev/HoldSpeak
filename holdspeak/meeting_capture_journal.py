"""Crash-recoverable, bounded-loss audio journal for desktop Meetings (HS-92-04)."""

from __future__ import annotations

import json
import os
import threading
from holdspeak.timestamps import utc_now_iso
from pathlib import Path
from typing import Any, Optional

import numpy as np


class MeetingCaptureJournal:
    """Append f32le streams and atomically publish only fsynced byte lengths.

    A torn final append is harmless: recovery trusts the manifest's durable byte
    count, never the physical EOF.  Checkpoints default to five seconds, which is
    also the maximum audio loss after process death.
    """

    def __init__(
        self,
        meeting_id: str,
        *,
        sample_rate: int = 16_000,
        directory: Optional[Path] = None,
        checkpoint_seconds: float = 5.0,
    ) -> None:
        root = directory or (
            Path.home() / ".local" / "share" / "holdspeak" / "meeting-captures"
        )
        self.directory = root / meeting_id
        self.directory.mkdir(parents=True, exist_ok=True)
        self.meeting_id = meeting_id
        self.sample_rate = sample_rate
        self.checkpoint_bytes = max(4, int(sample_rate * checkpoint_seconds) * 4)
        self.manifest_path = self.directory / "capture.json"
        self._lock = threading.Lock()
        self._files: dict[str, Any] = {}
        self._written: dict[str, int] = {}
        self._durable: dict[str, int] = {}
        self._error: Optional[str] = None
        self._status = "recording"
        self._sealed = False
        self._write_manifest()

    @property
    def error(self) -> Optional[str]:
        with self._lock:
            return self._error

    def append(self, source: str, audio: np.ndarray) -> None:
        if audio.size == 0:
            return
        with self._lock:
            if self._sealed or self._error is not None:
                return
            try:
                handle = self._files.get(source)
                if handle is None:
                    handle = open(self.directory / f"{source}.f32le.partial", "ab", buffering=0)
                    self._files[source] = handle
                payload = np.asarray(audio, dtype="<f4").tobytes()
                handle.write(payload)
                self._written[source] = self._written.get(source, 0) + len(payload)
                if self._written[source] - self._durable.get(source, 0) >= self.checkpoint_bytes:
                    self._checkpoint_locked()
            except Exception as exc:
                self._error = f"{type(exc).__name__}: {exc}"

    def checkpoint(self) -> None:
        with self._lock:
            if self._error is not None:
                raise OSError(self._error)
            try:
                self._checkpoint_locked()
            except Exception as exc:
                self._error = f"{type(exc).__name__}: {exc}"
                raise

    def seal(self) -> None:
        """Close accepted audio durably, keeping an unfinished Meeting discoverable."""
        with self._lock:
            if self._sealed:
                if self._error is not None:
                    raise OSError(self._error)
                return
            if not self._files:
                self._reload_manifest_locked()
            self._sealed = True
            failure: Optional[Exception] = None
            try:
                if self._error is not None:
                    raise OSError(self._error)
                self._checkpoint_locked()
            except Exception as exc:
                failure = exc
            for handle in self._files.values():
                try:
                    handle.close()
                except Exception as exc:
                    failure = failure or exc
            self._files.clear()
            if failure is not None:
                self._error = f"{type(failure).__name__}: {failure}"
                self._status = "recoverable"
                self._write_manifest()
                raise failure

    def finalize(self) -> None:
        """Complete the capture marker after the Meeting's final durable commit."""
        self.seal()
        with self._lock:
            previous = self._status
            self._status = "finalized"
            try:
                self._write_manifest()
            except Exception:
                self._status = previous
                raise

    def mark_recoverable(self, error: str) -> None:
        with self._lock:
            if not self._files:
                self._reload_manifest_locked()
            self._error = error
            self._status = "recoverable"
            self._write_manifest()

    def _checkpoint_locked(self) -> None:
        # HS-93-06: a failed checkpoint remains a failed checkpoint when
        # this object observes the child's manifest rather than open handles.
        from .faults import trip as _fault_trip

        _fault_trip("meeting.checkpoint_write", OSError)
        # C10: the capture child owns the open PCM handles. The parent
        # refreshes its durable manifest instead of overwriting the byte map.
        if not self._files:
            self._reload_manifest_locked()
            return
        for source, handle in self._files.items():
            handle.flush()
            os.fsync(handle.fileno())
            self._durable[source] = self._written.get(source, 0)
        self._write_manifest()

    def _write_manifest(self) -> None:
        manifest = {
            "meeting_id": self.meeting_id,
            "sample_rate": self.sample_rate,
            "format": "f32le",
            "status": self._status,
            "durable_bytes": dict(self._durable),
            "error": self._error,
            "updated_at": utc_now_iso(),
            "actions": ["retry", "discard"] if self._status == "recoverable" else [],
        }
        temp = self.manifest_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        with open(temp, "rb") as handle:
            os.fsync(handle.fileno())
        temp.replace(self.manifest_path)

    def _reload_manifest_locked(self) -> None:
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if manifest.get("meeting_id") != self.meeting_id:
            return
        durable = manifest.get("durable_bytes")
        if isinstance(durable, dict):
            self._durable = {
                str(source): int(length)
                for source, length in durable.items()
                if isinstance(length, (int, float))
            }
        self._status = str(manifest.get("status") or self._status)
        error = manifest.get("error")
        self._error = str(error) if error else None

    @classmethod
    def recoverable(cls, directory: Optional[Path] = None) -> list[dict[str, Any]]:
        root = directory or (
            Path.home() / ".local" / "share" / "holdspeak" / "meeting-captures"
        )
        found: list[dict[str, Any]] = []
        for path in root.glob("*/capture.json") if root.exists() else []:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if value.get("status") in {"recording", "recoverable"}:
                found.append(value)
        return sorted(found, key=lambda item: str(item.get("updated_at") or ""), reverse=True)
