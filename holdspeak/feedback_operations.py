"""The Desk's UI feedback verbs on the one declared contract (2026-11-09, ops/connections).

Carved beside ``holdspeak/operations.py`` (which imports it into ``DESCRIPTORS``);
``services/ui_feedback.FeedbackService`` serves every row (the module of
functions the route called before). The save and the transcription are owner
only: each writes a file in his feedback folder; they are the Desk's presses,
HTTP only. The switch's read has a tool.
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (the HTTP auth middleware); owner only"
_NO_ARGS = {"type": "object", "properties": {}, "additionalProperties": False}

FEEDBACK_OPERATIONS: tuple[OperationDescriptor, ...] = (
    OperationDescriptor(
        name="ui_feedback.status", version=1, description="Read whether Desk UI feedback is on (HOLDSPEAK_UI_FEEDBACK=1).",
        args_schema={"type": "object"}, principal=_ANY, effect="read", result="{enabled}",
        refusals=_CONTRACT_REFUSALS, completion="synchronous", exposure=("http:GET /api/ui-feedback/status",
                                                                         "mcp:ui_feedback.status"),
        service="feedback_service", method="status", call=lambda s, p, a: s.status(p),
        http=("GET", "/api/ui-feedback/status"), handler="api_ui_feedback_status", tool_schema=_NO_ARGS,
        thread="evidence_read",
    ),
    OperationDescriptor(
        name="ui_feedback.save", version=1,
        description="Save one Desk feedback bundle (the window shot, the recording, the context) in his feedback folder.",
        args_schema={"type": "object"}, principal=_OWNER, effect="write",
        result="{success, id, directory, files, transcript_status}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "ui_feedback_disabled", "ui_feedback_invalid",
                                       "ui_feedback_conflict"),
        completion="synchronous; the bundle is complete on disk or absent",
        exposure=("http:POST /api/ui-feedback",), service="feedback_service", method="save", owner_only=True,
        blocking_io=True, call=lambda s, p, a: s.save(p, dict(a)), http=("POST", "/api/ui-feedback"),
        handler="api_ui_feedback",
    ),
    OperationDescriptor(
        name="ui_feedback.transcribe", version=1,
        description="Transcribe one saved feedback recording, verbatim, on the configured speech route.",
        args_schema={"type": "object", "properties": {"identifier": {"type": "string"}}, "required": ["identifier"]},
        principal=_OWNER, effect="write", result="the bundle's transcript: {transcript_status, transcript?, "
                                                 "transcript_error?, egress_boundary?}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "ui_feedback_disabled", "ui_feedback_not_found"),
        completion="synchronous; a failure is kept on the bundle and a second press tries again",
        exposure=("http:POST /api/ui-feedback/{identifier}/transcribe",), service="feedback_service",
        method="transcribe", owner_only=True, blocking_io=True,
        call=lambda s, p, a: s.transcribe(p, str(a.get("identifier") or "")),
        http=("POST", "/api/ui-feedback/{identifier}/transcribe"), handler="api_ui_feedback_transcribe",
    ),
)


__all__ = ["FEEDBACK_OPERATIONS"]
