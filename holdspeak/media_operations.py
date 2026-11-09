"""Screen recordings and the hub's voice on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``calls_operations.py`` is. Each row states one verb of
``RecordingsService`` (``holdspeak/recordings/service.py``, the process's one
``RECORDINGS``) or ``TtsService`` (``holdspeak/services/tts_service.py``) once.
``web/routes/recordings.py`` and ``web/routes/tts.py`` produce the routes;
``mcp/families/declared.py`` produces the tools. Every ``/api/recordings`` and
``/api/tts`` route is the OWNER's at the edge (``principals.required_right``).

Kept hand-written, and why: a recording's chunk (``POST .../chunks``: the
body is raw video bytes), its video and poster (file answers with byte
ranges), the shared link ``/r/{id}/{token}/{name}`` (no hub token; the share
token is the key) and ``POST /api/tts`` (a streaming WAV answer).

No tool, and why:

- ``recordings.start`` / ``recordings.stop``: the capture runs in his browser;
  an agent neither starts nor ends a screen capture.
- ``recordings.share``: a link anyone who holds it can open; his press.
- ``recordings.open_folder``: opens Finder on his desk.
- ``tts.download``: fetches the voice weights from the catalogue host
  (egress, his press).

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ServiceError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver); the service takes none"
_REFUSALS = _CONTRACT_REFUSALS + (
    "ServiceError: a named reason with its HTTP status (not_found, busy, not_recording, not_ready, "
    "tts_not_installed, tts_no_preset, ...)",
)
_ID = {"type": "string", "minLength": 1}


def _refusing(fn: Callable[[], Any]) -> Any:
    """A ``RecordingRefused`` as the contract's ``ServiceError`` (its code, status and body kept)."""
    from holdspeak.recordings.store import RecordingRefused

    try:
        return fn()
    except RecordingRefused as exc:
        raise ServiceError(exc.code, exc.detail, context={
            "status": exc.status, "body": {"error": exc.detail, "reason": exc.code}}) from exc


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call,
        description: str, *, write: bool = False, tool: bool = True, status: int = 200,
        authority: str = "work", owner_press: bool = False, blocking_io: bool = False,
        properties: Optional[Mapping[str, Any]] = None, kind: str = "recording") -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids, "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_ANY,
        effect="write" if write else "read", result=f"the {service} answer", refusals=_REFUSALS,
        # The recordings service sends its own recording_state frame; the
        # registry adds the one desk_changed frame (kind recording).
        completion=f"synchronous; a write is one desk_changed frame (kind {kind}) on the hub bus"
        if write else "synchronous",
        exposure=(f"http:{http[0]} {http[1]}",) + ((f"mcp:{name}",) if tool else ()),
        service=service, method=method, call=call, http=http, http_status=status, handler=handler,
        tool_schema=schema if tool else None, authority=authority, owner_press=owner_press,
        blocking_io=blocking_io,
        # A read is evidence (MCP and HTTP only: thread_modes._MCP_ONLY); a write a proposal.
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _rec(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
         **kwargs: Any) -> OperationDescriptor:
    return _op(name, "recordings_service", method, http, handler,
               lambda s, p, a: _refusing(lambda: call(s, p, a)), description, **kwargs)


def _start(s: Any, p: Any, a: dict[str, Any]) -> Any:
    return s.start(width=int(a.get("width") or 0), height=int(a.get("height") or 0), voice=bool(a.get("voice")),
                   project_id=str(a.get("project_id") or ""), view=str(a.get("view") or ""))


_R = "/api/recordings"
_ONE = _R + "/{recording_id}"
MEDIA_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _rec("recordings.list", "payload", ("GET", _R), "api_recordings", lambda s, p, a: s.payload(),
         "List the screen recordings with their state and links, the disk usage, the keep days and the encoder."),
    _rec("recordings.start", "start", ("POST", _R), "api_recording_start", _start,
         "Start a screen recording (the browser captures and sends the chunks).", write=True, tool=False,
         status=201),
    _rec("recordings.open_folder", "open_folder", ("POST", _R + "/folder/open"), "api_recordings_open_folder",
         lambda s, p, a: s.open_folder(), "Open the recordings folder in Finder.", write=True, tool=False,
         blocking_io=True),
    _rec("recordings.get", "get", ("GET", _ONE), "api_recording_get",
         lambda s, p, a: s.get(str(a.get("recording_id") or "")), "Read one screen recording."),
    _rec("recordings.stop", "stop", ("POST", _ONE + "/stop"), "api_recording_stop",
         lambda s, p, a: s.stop(str(a.get("recording_id") or "")),
         "End a screen capture; the encode starts.", write=True, tool=False),
    _rec("recordings.retry", "retry", ("POST", _ONE + "/retry"), "api_recording_retry",
         lambda s, p, a: s.retry(str(a.get("recording_id") or "")),
         "Encode a failed screen recording again.", write=True),
    _rec("recordings.share", "share", ("POST", _ONE + "/share"), "api_recording_share",
         lambda s, p, a: s.share(str(a.get("recording_id") or "")),
         "Make a new share link for a screen recording.", write=True, tool=False),
    _rec("recordings.unshare", "unshare", ("POST", _ONE + "/unshare"), "api_recording_unshare",
         lambda s, p, a: s.unshare(str(a.get("recording_id") or "")),
         "Stop sharing a screen recording: its link stops working.", write=True),
    _rec("recordings.park", "park", ("POST", _ONE + "/park"), "api_recording_park",
         lambda s, p, a: s.park(str(a.get("recording_id") or "")),
         "Park a screen recording (it moves to recordings/_parked/; nothing is deleted).", write=True),
    _op("tts.status", "tts_service", "status", ("GET", "/api/tts/status"), "tts_status",
        lambda s, p, a: s.status(), "Read the hub's voice: whether the Line extra is installed and the voice "
        "model is downloaded, the engine and the voice.", kind="tts"),
    _op("tts.download", "tts_service", "download", ("POST", "/api/tts/download"), "tts_download",
        lambda s, p, a: s.download(), "Download the voice model weights from the catalogue host.", write=True,
        tool=False, status=202, authority="egress", owner_press=True, blocking_io=True, kind="tts"),
)


class _LiveRecordingsService:
    """The bound target: the process's one RecordingsService (``recordings.service.RECORDINGS``), read at each call."""

    def __getattr__(self, name: str) -> Any:
        from holdspeak.recordings import service as recordings

        return getattr(recordings.RECORDINGS, name)


LIVE_RECORDINGS_SERVICE = _LiveRecordingsService()

__all__ = ["LIVE_RECORDINGS_SERVICE", "MEDIA_OPERATIONS"]
