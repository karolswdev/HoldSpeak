"""Private, opt-in storage for local Desk UI feedback.

The browser owns the selection and capture.  This module only validates the
captured media and words, then publishes one complete, owner-readable bundle.  It has
no database, queue, model, or external delivery dependency.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import io
import json
import os
import re
import shutil
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any, Mapping

from .. import runtime_identity
from ..timestamps import utc_now_iso
from .errors import ServiceError

UI_FEEDBACK_ENV = "HOLDSPEAK_UI_FEEDBACK"
_ID_RE = re.compile(r"^[0-9a-f]{32}$")

REPORT_FILE = "report.json"
AUDIO_FILE = "audio.wav"
WINDOW_FILE = "window.png"
README_FILE = "README.md"
TRANSCRIPT_FILE = "transcript.txt"
FEEDBACK_FILES = (REPORT_FILE, AUDIO_FILE, WINDOW_FILE, README_FILE)

# A normal browser screenshot is small and a short recording is well below
# these limits.  The limits keep an accidental paste from filling the desk.
MAX_CONTEXT_BYTES = 256 * 1024
MAX_AUDIO_BYTES = 16 * 1024 * 1024
MAX_PNG_BYTES = 16 * 1024 * 1024
MAX_CAPTURED_AT_LENGTH = 128


class UIFeedbackError(ValueError):
    """A client payload cannot be accepted."""


class UIFeedbackConflict(UIFeedbackError):
    """The id has already been used for a different request."""


def enabled() -> bool:
    """Read the opt-in switch at request time."""
    return os.environ.get(UI_FEEDBACK_ENV, "").strip() == "1"


def feedback_root(home: Path | None = None) -> Path:
    """The fixed owner-local feedback directory."""
    base = Path.home() if home is None else Path(home)
    return base / ".local" / "share" / "holdspeak" / "feedback"


def _error(message: str) -> UIFeedbackError:
    return UIFeedbackError(message)


def _decode_attachment(value: Any, name: str, maximum: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise _error(f"{name} must be raw base64 text.")
    # Reject a huge encoded value before handing it to the decoder.
    encoded_limit = 4 * ((maximum + 2) // 3) + 4
    if len(value) > encoded_limit:
        raise _error(f"{name} is too large.")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _error(f"{name} is not valid base64.") from exc
    if not decoded or len(decoded) > maximum:
        raise _error(f"{name} is empty or too large.")
    return decoded


def _validate_wav(raw: bytes) -> None:
    try:
        with wave.open(io.BytesIO(raw), "rb") as source:
            if (
                source.getnchannels() != 1
                or source.getframerate() != 16_000
                or source.getsampwidth() != 2
                or source.getcomptype() != "NONE"
            ):
                raise _error("audio_base64 must be a 16 kHz mono PCM WAV.")
            if source.getnframes() <= 0:
                raise _error("audio_base64 must contain audio frames.")
            # Reading forces wave to parse the complete data chunk before the
            # bytes are published.  A truncated data chunk must not pass as a
            # readable recording.
            frames = source.readframes(source.getnframes())
            expected = source.getnframes() * source.getnchannels() * source.getsampwidth()
            if len(frames) != expected:
                raise _error("audio_base64 is a truncated WAV file.")
    except UIFeedbackError:
        raise
    except (EOFError, OSError, wave.Error) as exc:
        raise _error("audio_base64 is not a readable WAV file.") from exc


def _validate_png(raw: bytes) -> None:
    """Validate the bounded PNG envelope without inflating image data."""
    signature = b"\x89PNG\r\n\x1a\n"
    if len(raw) < len(signature) or raw[: len(signature)] != signature:
        raise _error("screenshot_base64 must be a PNG image.")

    # A browser PNG starts with IHDR.  Keep this check deliberately shallow:
    # the server does not inflate client image data, which could expand to an
    # unbounded allocation.  The browser-produced wire fixture proves the
    # complete image separately.
    if len(raw) < len(signature) + 25 + 12:
        raise _error("screenshot_base64 is not a complete PNG.")
    header_length = struct.unpack(">I", raw[8:12])[0]
    if header_length != 13 or raw[12:16] != b"IHDR":
        raise _error("screenshot_base64 is not a valid PNG.")
    width, height = struct.unpack(">II", raw[16:24])
    if width == 0 or height == 0 or width > 16_384 or height > 16_384:
        raise _error("screenshot_base64 is not a valid PNG.")
    if b"IDAT" not in raw[33:-12]:
        raise _error("screenshot_base64 is not a valid PNG.")
    # The final chunk must be an empty IEND.  This catches truncated and
    # concatenated input while keeping validation bounded to the file size.
    if raw[-12:-8] != b"\x00\x00\x00\x00" or raw[-8:-4] != b"IEND":
        raise _error("screenshot_base64 is not a complete PNG.")


def _context_json(context: Any) -> str:
    if not isinstance(context, dict):
        raise _error("context must be a JSON object.")
    try:
        encoded = json.dumps(
            context,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise _error("context must contain JSON values.") from exc
    if len(encoded.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise _error("context is too large.")
    return encoded


def _validate_captured_at(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_CAPTURED_AT_LENGTH:
        raise _error("captured_at must be an ISO date and time.")
    candidate = value.strip()
    try:
        from datetime import datetime

        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _error("captured_at must be an ISO date and time.") from exc
    return candidate


def _runtime_identity() -> dict[str, str]:
    """Return only compact, non-sensitive loaded build facts."""
    try:
        identity = runtime_identity.current_runtime_identity()
        return {
            "backend_version": str(identity.backend_version),
            "backend_revision": str(identity.backend_revision),
            "frontend_build": str(identity.frontend_build),
        }
    except Exception:
        # Feedback must remain useful when a partially started test/runtime has
        # no identity yet.  Do not make identity probing a save prerequisite.
        return {"backend_version": "unknown", "backend_revision": "unknown", "frontend_build": "unknown"}


def _canonical_digest(
    *, id: str, captured_at: str, context_json: str, audio: bytes, screenshot: bytes, words: str = ""
) -> str:
    request = {
        "id": id,
        "captured_at": captured_at,
        "context": json.loads(context_json),
        "audio_base64": base64.b64encode(audio).decode("ascii"),
        "screenshot_base64": base64.b64encode(screenshot).decode("ascii"),
    }
    if words:
        request["words"] = words
    canonical = json.dumps(
        request, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _parse_payload(payload: Mapping[str, Any]) -> tuple[str, str, str, bytes, bytes, str, str]:
    if not isinstance(payload, Mapping):
        raise _error("A JSON object is required.")
    identifier = payload.get("id")
    if not isinstance(identifier, str) or not _ID_RE.fullmatch(identifier):
        raise _error("id must be 32 lowercase hexadecimal characters.")
    captured_at = _validate_captured_at(payload.get("captured_at"))
    context_json = _context_json(payload.get("context"))
    words = payload.get("words", "")
    if not isinstance(words, str) or len(words) > 32_000:
        raise _error("words must be text of at most 32000 characters.")
    words = words.strip()
    audio_value = payload.get("audio_base64")
    audio = _decode_attachment(audio_value, "audio_base64", MAX_AUDIO_BYTES) if audio_value is not None else b""
    if not audio and not words:
        raise _error("Words or a recording are required.")
    screenshot = _decode_attachment(
        payload.get("screenshot_base64"), "screenshot_base64", MAX_PNG_BYTES
    )
    if audio:
        _validate_wav(audio)
    _validate_png(screenshot)
    digest = _canonical_digest(
        id=identifier,
        captured_at=captured_at,
        context_json=context_json,
        audio=audio,
        screenshot=screenshot,
        words=words,
    )
    return identifier, captured_at, context_json, audio, screenshot, digest, words


def _durable_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, mode)
    try:
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)
    os.chmod(path, mode)


def _sync_directory(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _receipt(directory: Path) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "success": True,
        "id": directory.name,
        "directory": str(directory.absolute()),
        "files": list(FEEDBACK_FILES),
    }
    try:
        report = json.loads((directory / REPORT_FILE).read_text(encoding="utf-8"))
        receipt["files"] = report.get("files", list(FEEDBACK_FILES))
        transcript = report.get("transcript", {})
        if isinstance(transcript, dict):
            status = str(transcript.get("status") or "pending")
            receipt["transcript_status"] = status
            if status == "complete":
                receipt["transcript"] = (directory / TRANSCRIPT_FILE).read_text(encoding="utf-8")
                receipt["egress_boundary"] = str(transcript.get("egress_boundary") or "")
            elif status == "failed":
                receipt["transcript_error"] = str(transcript.get("reason") or "transcription_failed")
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        receipt["transcript_status"] = "pending"
    return receipt


def _complete_existing(directory: Path, digest: str) -> dict[str, Any] | None:
    if not directory.exists() and not directory.is_symlink():
        return None
    if directory.is_symlink() or not directory.is_dir():
        raise UIFeedbackConflict("This feedback id is already in use.")
    try:
        if (directory / REPORT_FILE).is_symlink():
            raise UIFeedbackConflict("This feedback id has an incomplete report.")
        report = json.loads((directory / REPORT_FILE).read_text(encoding="utf-8"))
        paths = [directory / name for name in _bundle_files(report)]
        if any(path.is_symlink() or not path.is_file() for path in paths):
            raise UIFeedbackConflict("This feedback id has an incomplete report.")
        stored_digest = _canonical_digest(
            id=str(report["id"]),
            captured_at=str(report["captured_at"]),
            context_json=json.dumps(
                report["context"], ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
            ),
            audio=(directory / AUDIO_FILE).read_bytes() if report.get("has_audio", True) else b"",
            screenshot=(directory / WINDOW_FILE).read_bytes(),
            words=report.get("words", ""),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise UIFeedbackConflict("This feedback id has an unreadable report.")
    if stored_digest != digest:
        raise UIFeedbackConflict("This feedback id is already in use.")
    return _receipt(directory)


def save_feedback(payload: Mapping[str, Any], *, home: Path | None = None) -> dict[str, Any]:
    """Validate and atomically publish one local feedback bundle."""
    identifier, captured_at, context_json, audio, screenshot, digest, words = _parse_payload(payload)
    root = feedback_root(home)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    directory = root / identifier

    existing = _complete_existing(directory, digest)
    if existing is not None:
        return existing

    temporary = Path(tempfile.mkdtemp(prefix=f".{identifier}.", dir=str(root)))
    os.chmod(temporary, 0o700)
    try:
        if audio:
            _durable_write(temporary / AUDIO_FILE, audio)
        _durable_write(temporary / WINDOW_FILE, screenshot)
        report = {
            "id": identifier,
            "captured_at": captured_at,
            "context": json.loads(context_json),
            "runtime_identity": _runtime_identity(),
            "saved_at": utc_now_iso(),
            "has_audio": bool(audio),
            "words": words,
            "files": [name for name in FEEDBACK_FILES if audio or name != AUDIO_FILE],
            "transcript": {"status": "pending" if audio else "complete", "file": TRANSCRIPT_FILE},
        }
        if not audio:
            report["transcript"]["egress_boundary"] = "same_device"
            report["files"].append(TRANSCRIPT_FILE)
            _durable_write(temporary / TRANSCRIPT_FILE, words.encode("utf-8"))
        report_bytes = json.dumps(
            report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2
        ).encode("utf-8") + b"\n"
        _durable_write(temporary / REPORT_FILE, report_bytes)
        readme = (
            "# HoldSpeak local UI feedback\n\n"
            "Purpose: keep one typed or spoken report about a selected Desk element for local developer review.\n\n"
            "Files:\n"
            "- `report.json` — captured context and loaded build identity.\n"
            "- `audio.wav` — the original 16 kHz mono PCM recording, when recorded.\n"
            "- `window.png` — the captured Desk window.\n"
            "- `README.md` — this file.\n"
            "- `transcript.txt` — typed words, or the speech engine transcript when available.\n"
        ).encode("utf-8")
        _durable_write(temporary / README_FILE, readme)
        _sync_directory(temporary)
        try:
            os.rename(temporary, directory)
        except FileExistsError:
            # Another same-id request won the publication race.  Its complete
            # report is authoritative; an unlike request receives 409.
            existing = _complete_existing(directory, digest)
            if existing is None:
                raise UIFeedbackConflict("This feedback id is already in use.")
            return existing
        temporary = Path()
        _sync_directory(root)
        return _receipt(directory)
    finally:
        if temporary != Path() and temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


WALKS_DIR = "walks"


def walks_root(home: Path | None = None) -> Path:
    """The Walk's folder, inside the feedback folder: a walk's script, its
    answers and its window shots land where feedback bundles land."""
    return feedback_root(home) / WALKS_DIR


class WalkShotBudgetError(UIFeedbackError):
    """The walk's folder has no room left for this image."""


def save_walk_shot(directory: Path, name: str, screenshot_base64: Any, *, room: int | None = None) -> str:
    """Validate one walk window PNG with the feedback limits and write it as
    ``<name>.png`` (``name`` is a plain file stem). A later image of the same
    name replaces the earlier one: one image per question. ``room`` is the
    byte budget left in the walk's folder; a larger image is refused with
    ``WalkShotBudgetError`` and nothing is written. Returns the file name."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,96}", str(name or "")):
        raise _error("The shot name is not valid.")
    screenshot = _decode_attachment(screenshot_base64, "window_png", MAX_PNG_BYTES)
    _validate_png(screenshot)
    if room is not None and len(screenshot) > room:
        raise WalkShotBudgetError("This walk has no room for more images. The answer is kept without the image.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    filename = f"{name}.png"
    _atomic_replace(directory / filename, screenshot)
    return filename


def _bundle_files(report: Mapping[str, Any]) -> list[str]:
    return [name for name in FEEDBACK_FILES if report.get("has_audio", True) or name != AUDIO_FILE]


def _feedback_directory(identifier: str, home: Path | None = None) -> Path:
    if not isinstance(identifier, str) or not _ID_RE.fullmatch(identifier):
        raise UIFeedbackError("id must be 32 lowercase hexadecimal characters.")
    directory = feedback_root(home) / identifier
    if directory.is_symlink() or not directory.is_dir():
        raise UIFeedbackError("This feedback report was not found.")
    try:
        if (directory / REPORT_FILE).is_symlink():
            raise UIFeedbackError("This feedback report is incomplete.")
        report = json.loads((directory / REPORT_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UIFeedbackError("This feedback report is incomplete.") from exc
    if any((directory / name).is_symlink() or not (directory / name).is_file() for name in _bundle_files(report)):
        raise UIFeedbackError("This feedback report is incomplete.")
    return directory


def feedback_audio(identifier: str, *, home: Path | None = None) -> bytes:
    """Read the already-published WAV for a transcript retry."""
    directory = _feedback_directory(identifier, home)
    try:
        return (directory / AUDIO_FILE).read_bytes()
    except OSError as exc:
        raise UIFeedbackError("The saved feedback recording could not be read.") from exc


def feedback_transcript(identifier: str, *, home: Path | None = None) -> dict[str, Any]:
    """Return the current transcript state without invoking speech."""
    return _receipt(_feedback_directory(identifier, home))


def _atomic_replace(path: Path, data: bytes) -> None:
    temporary = Path()
    try:
        fd, raw_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        temporary = Path(raw_path)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        temporary = Path()
        _sync_directory(path.parent)
    finally:
        if temporary != Path() and temporary.exists():
            temporary.unlink(missing_ok=True)


def _set_transcript(
    identifier: str,
    *,
    status: str,
    text: str = "",
    egress_boundary: str = "",
    reason: str = "",
    home: Path | None = None,
) -> dict[str, Any]:
    if status not in {"complete", "failed"}:
        raise UIFeedbackError("Invalid transcript status.")
    directory = _feedback_directory(identifier, home)
    report_path = directory / REPORT_FILE
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise UIFeedbackError("This feedback report has an unreadable report.") from exc
    transcript = {"status": status, "file": TRANSCRIPT_FILE}
    if status == "complete":
        if not isinstance(text, str) or not text.strip():
            raise UIFeedbackError("A completed transcript must contain text.")
        if not str(egress_boundary).strip():
            raise UIFeedbackError("A completed transcript needs an egress boundary.")
        transcript["egress_boundary"] = str(egress_boundary)
        report["files"] = [*_bundle_files(report), TRANSCRIPT_FILE]
        transcript_bytes = text.encode("utf-8")
    else:
        transcript["reason"] = str(reason or "transcription_failed")
        report["files"] = _bundle_files(report)
        transcript_bytes = None
    report["transcript"] = transcript
    report_bytes = json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if transcript_bytes is not None:
        _atomic_replace(directory / TRANSCRIPT_FILE, transcript_bytes)
    _atomic_replace(report_path, report_bytes)
    return _receipt(directory)


def save_transcript(
    identifier: str,
    text: str,
    egress_boundary: str,
    *,
    home: Path | None = None,
) -> dict[str, Any]:
    """Attach one admitted speech result to an existing feedback bundle."""
    current = feedback_transcript(identifier, home=home)
    if current.get("transcript_status") == "complete":
        return current
    return _set_transcript(
        identifier,
        status="complete",
        text=text,
        egress_boundary=egress_boundary,
        home=home,
    )


def fail_transcript(identifier: str, reason: str, *, home: Path | None = None) -> dict[str, Any]:
    """Persist a named speech failure while retaining the original bundle."""
    current = feedback_transcript(identifier, home=home)
    if current.get("transcript_status") == "complete":
        return current
    return _set_transcript(identifier, status="failed", reason=reason, home=home)


__all__ = [
    "FEEDBACK_FILES",
    "README_FILE",
    "TRANSCRIPT_FILE",
    "AUDIO_FILE",
    "REPORT_FILE",
    "WINDOW_FILE",
    "UIFeedbackConflict",
    "UIFeedbackError",
    "enabled",
    "feedback_root",
    "feedback_audio",
    "feedback_transcript",
    "save_transcript",
    "fail_transcript",
    "save_feedback",
]


class FeedbackRefused(UIFeedbackError, ServiceError):
    """A named service refusal, with the same status and words on both transports."""

    def __init__(self, detail: str, status: int, *, code: str = "ui_feedback_not_found") -> None:
        ServiceError.__init__(self, code, detail, context={"status": status})
        self.status = status


class FeedbackService:
    """The Desk's UI feedback verbs, once (2026-11-09, ops/connections): the
    routes are produced from ``holdspeak/feedback_operations.py``. Owner only:
    each write is a file in his feedback folder. ``source`` is the hub's
    context, read at each call for ``on_transcribe_admitted`` (the hub's
    admitted speech route)."""

    def __init__(self, source: Any = None) -> None:
        self._source = source

    def status(self, principal: Any) -> dict[str, Any]:
        from ..principals import PrincipalKind

        result: dict[str, Any] = {"enabled": enabled()}
        # The flag remains an authenticated read. Engine choices are owner
        # configuration: only its existing owner read may supply this field.
        if not result["enabled"] or getattr(principal, "kind", None) != PrincipalKind.OWNER:
            return result
        assignments = getattr(self._source, "inference_assignment_service", None)
        resolved = assignments.resolve_effective(principal, capability_id="speech.transcribe") if assignments else {}
        entries = (resolved.get("assignment") or {}).get("entries") or []
        result["transcription_egress"] = [
            {"label": entry["label"], "boundary": entry["boundary"]}
            for entry in entries if entry.get("boundary") not in {"local", "same_device"}
        ]
        return result

    @staticmethod
    def _require_enabled() -> None:
        if not enabled():
            raise FeedbackRefused("UI feedback is disabled.", 404, code="ui_feedback_disabled")

    def save(self, principal: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and publish one feedback bundle (the window shot, the recording, the context)."""
        self._require_enabled()
        try:
            return save_feedback(payload)
        except UIFeedbackConflict as exc:
            raise FeedbackRefused(str(exc), 409, code="ui_feedback_conflict") from exc
        except UIFeedbackError as exc:
            raise FeedbackRefused(str(exc), 400, code="ui_feedback_invalid") from exc

    def transcribe(self, principal: Any, identifier: str) -> dict[str, Any]:
        """Transcribe one saved recording, verbatim, on the configured speech route; a failure is kept on the bundle."""
        self._require_enabled()
        try:
            current = feedback_transcript(identifier)
        except UIFeedbackError as exc:
            raise FeedbackRefused(str(exc), 404) from exc
        if current.get("transcript_status") == "complete":
            return current
        try:
            import numpy as np

            with wave.open(io.BytesIO(feedback_audio(identifier)), "rb") as source:
                frames = source.readframes(source.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        except (OSError, EOFError, ValueError, wave.Error):
            return fail_transcript(identifier, "audio_unreadable")
        transcribe = getattr(self._source, "on_transcribe_admitted", None)
        if transcribe is None:
            return fail_transcript(identifier, "transcription_unavailable")
        from ..speech_session import SpeechSessionRefused

        admitted = None
        outcome = "failed"
        try:
            admitted = transcribe(audio, principal=principal, mic_handle="", verbatim=True)
            text = str(admitted.text)
            if not text.strip():
                return fail_transcript(identifier, "no_speech")
            result = save_transcript(identifier, text, str(admitted.provider.egress_boundary))
            outcome = "succeeded"
            return result
        except SpeechSessionRefused as exc:
            return fail_transcript(identifier, exc.reason)
        except Exception as exc:  # pragma: no cover - provider/runtime specific
            return fail_transcript(identifier, str(getattr(exc, "reason", "") or "transcription_failed"))
        finally:
            if admitted is not None:
                admitted.close(outcome)
