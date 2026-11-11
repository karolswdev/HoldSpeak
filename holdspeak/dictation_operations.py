"""Dictation, intent controls and browser speech jobs on one declared contract.

The registry produces HTTP routes and MCP tools. Owner microphone/preview jobs
and the companion send are HTTP-only: the adapters hold request cancellation,
audio and fresh-session callbacks. DictationService owns the work; it never
receives a Request or a client-supplied principal. The delivery ledger legs are
internal parts of the remote HTTP job, declared without separate endpoints.
Readiness includes local host context and is owner-only on both transports.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver) and passed to the service unchanged"
_OWNER = "the owner only: the hub token (HTTP edge right OWNER; MCP auth resolver), passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required", "intent_profile_unavailable", "intent_preview_unavailable",
    "ServiceError: a named reason with its HTTP status (journal_unavailable, corrections_unavailable, not_found, "
    "project_not_found, invalid_scope, invalid_kind, invalid_blocks, conflict, kb_exists, floor_held, ...)",
    "ValidationError",
)
_ID = {"type": "string", "minLength": 1}
_INT = {"type": "integer"}
_ROOT = {"project_root": {"type": "string", "description": "A project directory. Empty: the project of the hub's cwd."}}
_SCOPE = {"scope": {"enum": ["global", "project"], "description": "Default global."}, **_ROOT}
_TEACH = {
    "kind": {"type": "string", "description": "intent, target or text."},
    "value": {"type": "string", "description": "intent/target: the block id or target profile id; text: what was said."},
    "heard": {"type": "string", "description": "text: what the microphone heard."},
    "said": {"type": "string", "description": "text: what the owner said."},
}


def _int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be an integer") from exc


def _flag(value: Any, default: bool = True) -> bool:
    """A query flag (``?capture_messages=false``) or a JSON boolean."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"} if isinstance(value, str) else bool(value)


def _op(name: str, method: str, http: Optional[tuple[str, str]], handler: Optional[str], call: Call,
        description: str, *, write: bool = False, tool: bool = True, owner_only: bool = False,
        callback_http: Optional[str] = None, held: tuple[str, ...] = (), authority: str = "work", owner_press: bool = False,
        blocking_io: bool = False, completion: Optional[str] = None, status: int = 200, quiet: bool = False, strict: bool = False, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = ()) -> OperationDescriptor:
    """One verb; its tool (when it has one) requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in (http[1] if http else "").split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids + list(required), "additionalProperties": False}
    exposure = ((f"http:{http[0]} {http[1]}",) if http else ((f"http:{callback_http}",) if callback_http else ())) + ((f"mcp:{name}",) if tool else ())
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema=schema if strict else {"type": "object"},
        principal=_OWNER if owner_only else _ANY, effect="write" if write else "read",
        result="the DictationService answer", refusals=_REFUSALS,
        completion=completion or ("synchronous; a write is one desk_changed frame on the hub bus (kind dictation)"
        if write and not quiet else "synchronous"),
        exposure=exposure, service="dictation_service", method=method, owner_only=owner_only, call=call,
        http=http, http_status=status, handler=handler, tool_schema=schema if tool else None,
        held=held, authority=authority, owner_press=owner_press, blocking_io=blocking_io,
        # The floor is noise (web/announce.QUIET_ROUTES): the registry adds no frame.
        announces_changes=quiet,
        # A read is evidence (MCP and HTTP only: thread_modes._MCP_ONLY); a write a proposal.
        thread=("effect_proposal" if write else "evidence_read") if tool else None,
    )


def _list(s: Any, p: Any, a: dict[str, Any]) -> Any:
    cursor = a.get("cursor", a.get("before"))
    return s.list_journal(p, limit=_int(a.get("limit", 200), "limit"),
                          cursor=None if cursor in (None, "") else _int(cursor, "cursor"), source=a.get("source"))


def _teach_args(a: dict[str, Any]) -> dict[str, Any]:
    return {key: a.get(key) for key in ("kind", "value", "heard", "said")}


_D = "/api/dictation"
_J = _D + "/journal"
DICTATION_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("dictation.readiness", "readiness", ("GET", _D + "/readiness"), "api_dictation_readiness",
        lambda s, p, a: s.readiness(p, a.get("project_root")),
        "Read dictation setup, local paths, the active target and hotkey status. Owner-only host context.",
        owner_only=True, blocking_io=True, properties=_ROOT),
    _op("intents.controls", "intent_controls", None, None,
        lambda s, p, a: s.intent_controls(p),
        "Read intent routing controls and the last owner preview. Owner-only.", owner_only=True),
    _op("intents.profile", "set_intent_profile", None, None,
        lambda s, p, a: s.set_intent_profile(p, a["profile"]),
        "Set the owner's intent routing profile.", write=True, owner_only=True, strict=True,
        blocking_io=True, authority="config", owner_press=True,
        properties={"profile": {"type": "string"}}, required=("profile",)),
    _op("intents.preview", "preview_intent_route", None, None,
        lambda s, p, a: s.preview_intent_route(p, **a),
        "Preview an owner intent route, run its plugin chain and retain its preview history.",
        strict=True, write=True, owner_only=True, blocking_io=True, authority="egress", owner_press=True,
        properties={"profile": {"type": ["string", "null"]}, "threshold": {"type": ["number", "null"]},
                    "intent_scores": {"type": ["object", "null"], "additionalProperties": {"type": "number"}},
                    **{key: {"type": ["array", "null"], "items": {"type": "string"}}
                       for key in ("override_intents", "previous_intents", "tags")},
                    "transcript": {"type": ["string", "null"]}}),
    _op("dictation.wake.type", "wake_type", ("POST", "/api/dictation/wake/type"), "api_wake_type",
        lambda s, p, a: s.wake_type(p, a),
        "HTTP-only: type one stored wake preview by the owner press; no agent capture or press.",
        write=True, tool=False, owner_only=True, quiet=True),
    _op("dictation.mic.open", "open_mic", ("POST", "/api/dictation/mic/open"), "api_mic_open",
        lambda s, p, a: s.open_mic(p),
        "HTTP-only: open one owner microphone interval for browser capture; no agent capture or press.",
        write=True, tool=False, owner_only=True, quiet=True),
    _op("dictation.mic.close", "close_mic", ("POST", "/api/dictation/mic/close"), "api_mic_close",
        lambda s, p, a: s.close_mic(p),
        "HTTP-only: close the owner browser microphone interval; no agent capture or press.",
        write=True, tool=False, owner_only=True, quiet=True),
    _op("dictation.transcribe", "transcribe_audio", ("POST", "/api/dictation/transcribe"), "api_transcribe",
        lambda s, p, a: s.transcribe_audio(p, a["raw"], pipeline=_flag(a.get("pipeline"), False), mic_handle=str(a.get("mic_handle") or "")),
        "HTTP-only: accept raw WAV audio from browser capture and return its transcript; no agent capture or press.",
        write=True, tool=False, owner_only=True, held=("raw",), quiet=True,
        completion="asynchronous; the response carries the transcript and speech session outcome"),
    _op("dictation.preview.type", "preview_type", ("POST", "/api/dictation/preview/type"), "api_preview_type",
        lambda s, p, a: s.preview_type(p, a),
        "HTTP-only: type one stored preview by the owner press; no agent capture or press.",
        write=True, tool=False, owner_only=True, quiet=True),
    _op("dictation.preview.discard", "preview_discard", ("POST", "/api/dictation/preview/discard"), "api_preview_discard",
        lambda s, p, a: s.preview_discard(p, a),
        "HTTP-only: discard one owner preview token; no agent capture or press.",
        write=True, tool=False, owner_only=True, quiet=True),
    _op("dictation.command.test", "test_voice_command", ("POST", "/api/commands/test"), "api_test_voice_command",
        lambda s, p, a: s.test_voice_command(p, a),
        "HTTP-only: test an owner voice command on the host; no agent capture or press.",
        write=True, tool=False, owner_only=True, authority="egress", owner_press=True, quiet=False),
    _op("dictation.delivery.claim", "claim_delivery", None, None,
        lambda s, p, a: s.claim_delivery(p, a["delivery_id"], request_hash=a["request_hash"]),
        "HTTP-only internal leg of remote delivery: claim its durable id; never an agent callback or a new route.",
        write=True, tool=False, owner_only=True, quiet=True, callback_http="POST /api/dictation/remote"),
    _op("dictation.delivery.complete", "complete_delivery", None, None,
        lambda s, p, a: s.complete_delivery(p, a["delivery_id"], response_status=a["response_status"],
                                          response=a["response"]),
        "HTTP-only internal leg of remote delivery: retain its terminal response; no agent settlement or new route.",
        write=True, tool=False, owner_only=True, quiet=True, callback_http="POST /api/dictation/remote"),
    _op("dictation.delivery.fail", "fail_delivery", None, None,
        lambda s, p, a: s.fail_delivery(p, a["delivery_id"], response_status=a["response_status"],
                                      response=a["response"], error=a["error"]),
        "HTTP-only internal leg of remote delivery: retain its failure; no agent settlement or new route.",
        write=True, tool=False, owner_only=True, quiet=True, callback_http="POST /api/dictation/remote"),
    _op("dictation.rehearse", "rehearse", ("POST", _D + "/dry-run"), "api_dictation_dry_run",
        lambda s, p, a: s.rehearse(p, **a),
        "HTTP-only: rehearse browser text with its disconnect watcher and a fresh owner speech session.",
        write=True, tool=False, owner_only=True, quiet=True, strict=True,
        completion="asynchronous; the HTTP response carries the result and speech session outcome",
        properties={"payload": {"type": "object"}}, required=("payload",),
        held=("project_doc_suggestions", "dismissed_signatures", "run_entry")),
    _op("dictation.remote", "remote_delivery", ("POST", _D + "/remote"), "api_dictation_remote",
        lambda s, p, a: s.remote_delivery(p, **a),
        "HTTP-only: deliver text from the owner desk or companion; a stable delivery id owns the committed send.",
        write=True, tool=False, owner_only=True, quiet=True, strict=True,
        completion="asynchronous; the HTTP response carries the result and speech session outcome",
        properties={"payload": {"type": "object"}}, required=("payload",),
        held=("project_doc_suggestions", "dismissed_signatures", "open_entry")),
    _op("dictation.journal.replay", "replay_journal", ("POST", _J + "/{entry_id}/replay"),
        "api_dictation_journal_replay", lambda s, p, a: s.replay_journal(p, **a),
        "HTTP-only: preview an owner journal entry with its disconnect watcher; keep the stored entry unchanged.",
        write=False, tool=False, owner_only=True, quiet=True, strict=True,
        completion="asynchronous; the HTTP response carries the result and speech session outcome", properties={"entry_id": _INT},
        held=("project_doc_suggestions", "dismissed_signatures", "run_entry")),
    _op("dictation.blocks.from_template", "create_template_block", ("POST", _D + "/blocks/from-template"),
        "api_dictation_blocks_create_from_template", lambda s, p, a: s.create_template_block(p, **a),
        "HTTP-only: create an owner template block and optionally preview it with the browser disconnect watcher.",
        write=True, tool=False, owner_only=True, quiet=False, strict=True,
        completion="asynchronous; the HTTP response carries the result and speech session outcome", status=201,
        properties={"payload": {"type": "object"}, "scope": {"type": "string"},
                    "project_root": {"type": ["string", "null"]}}, required=("payload",),
        held=("project_doc_suggestions", "run_entry")),
    # ── the journal ──
    _op("dictation.list", "list_journal", ("GET", _J), "api_dictation_journal_list", _list,
        "Read the retained dictation journal, optionally paged and filtered by source.",
        properties={"limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum entries to return."},
                    "cursor": {"type": "integer", "description": "Return entries older than this journal entry id."},
                    "source": {"type": "string", "enum": ["dictation", "dry_run", "browser", "hotkey"],
                               "description": "Optional dictation source filter."}}),
    _op("dictation.get", "get_entry", None, None,
        lambda s, p, a: s.get_entry(p, _int(a.get("entry_id"), "entry_id")),
        "Get one retained dictation journal entry by its numeric id.",
        properties={"entry_id": {"type": "integer", "description": "Numeric dictation journal entry id."}},
        required=("entry_id",)),
    _op("dictation.journal.update", "update_entry", ("PUT", _J + "/{entry_id}"), "api_dictation_journal_update",
        lambda s, p, a: s.update_entry(p, _int(a.get("entry_id"), "entry_id"), a.get("transcript")),
        "Change the transcript of one journal entry. An empty transcript refuses.", write=True,
        properties={"entry_id": _INT, "transcript": _ID}, required=("transcript",)),
    _op("dictation.journal.delete", "delete_entry", ("DELETE", _J + "/{entry_id}"), "api_dictation_journal_delete",
        lambda s, p, a: s.delete_entry(p, _int(a.get("entry_id"), "entry_id")),
        "Delete one journal entry.", write=True, owner_only=True, properties={"entry_id": _INT}),
    _op("dictation.journal.clear", "clear_journal", ("DELETE", _J), "api_dictation_journal_clear",
        lambda s, p, a: s.clear_journal(p), "Delete every journal entry.", write=True, owner_only=True),
    _op("dictation.journal.correct", "correct_entry", ("POST", _J + "/{entry_id}/correct"),
        "api_dictation_journal_correct",
        lambda s, p, a: s.correct_entry(p, _int(a.get("entry_id"), "entry_id"), **_teach_args(a)),
        "Correct one journal entry and teach the correction: intent or target with a value, or text with what "
        "was said. A refused teach names its reason and changes nothing.", write=True,
        properties={"entry_id": _INT, **_TEACH}, required=("kind",)),
    # ── the corrections ──
    _op("dictation.corrections.list", "list_corrections", ("GET", _D + "/corrections"),
        "api_dictation_corrections_list", lambda s, p, a: s.list_corrections(p),
        "List the taught corrections with the times each one fired."),
    _op("dictation.learning_digest", "learning_digest", ("GET", _D + "/learning-digest"),
        "api_dictation_learning_digest", lambda s, p, a: s.learning_digest(p, str(a.get("window") or "week")),
        "Read what HoldSpeak learned in a window: corrections made, dictations corrected, the reach of each.",
        properties={"window": {"type": "string", "description": "Default week."}}),
    _op("dictation.corrections.add", "teach", ("POST", _D + "/corrections"), "api_dictation_corrections_record",
        lambda s, p, a: s.teach(p, text=a.get("text"), **_teach_args(a)),
        "Teach one correction with no journal entry: intent or target with text and value, or text with heard "
        "and said.", write=True, properties={"text": {"type": "string"}, **_TEACH}, required=("kind",)),
    _op("dictation.corrections.remove", "remove_correction", ("DELETE", _D + "/corrections/{correction_id}"),
        "api_dictation_corrections_delete",
        lambda s, p, a: s.remove_correction(p, _int(a.get("correction_id"), "correction_id")),
        "Forget one taught correction.", write=True, owner_only=True, properties={"correction_id": _INT}),
    # ── the audio floor (the browser's open mic) ──
    _op("dictation.floor.claim", "claim_floor", ("POST", _D + "/floor/claim"), "api_audio_floor_claim",
        lambda s, p, a: s.claim_floor(p, a.get("lease_seconds")),
        "HTTP-only: the browser claims its microphone lease; an agent has no capture process.",
        write=True, tool=False, quiet=True, owner_only=True),
    _op("dictation.floor.release", "release_floor", ("POST", _D + "/floor/release"), "api_audio_floor_release",
        lambda s, p, a: s.release_floor(p), "HTTP-only: the browser releases its microphone lease; an agent has no capture process.", write=True,
        tool=False, quiet=True, owner_only=True),
    # ── the project ──
    _op("dictation.project_context", "project_context", ("GET", _D + "/project-context"),
        "api_dictation_project_context", lambda s, p, a: s.project_context(p, a.get("project_root")),
        "Validate and describe the dictation project root and its blocks and KB paths.", properties=_ROOT),
    _op("dictation.agent_hooks", "agent_hooks", ("GET", _D + "/agent-hooks"), "api_dictation_agent_hooks",
        lambda s, p, a: s.agent_hooks(p, _flag(a.get("capture_messages"))),
        "Read the Claude and Codex hook templates and each agent's last session.",
        properties={"capture_messages": {"type": "boolean"}}),
    _op("dictation.project_hs.get", "project_hs", ("GET", _D + "/project-hs"), "api_dictation_project_hs_get",
        lambda s, p, a: s.project_hs(p, a.get("project_root")),
        "Read the project's .hs context files.", properties=_ROOT),
    _op("dictation.project_hs.put", "write_project_hs", ("PUT", _D + "/project-hs"), "api_dictation_project_hs_put",
        lambda s, p, a: s.write_project_hs(p, a.get("files"), a.get("project_root")),
        "Write the project's .hs context files (name to content).", write=True,
        properties={"files": {"type": "object"}, **_ROOT}, required=("files", "project_root")),
    _op("dictation.project_kb.get", "project_kb", ("GET", _D + "/project-kb"), "api_dictation_project_kb_get",
        lambda s, p, a: s.project_kb(p, a.get("project_root")),
        "Read the project's facts (.holdspeak/project.yaml).", properties=_ROOT),
    _op("dictation.project_kb.put", "write_project_kb", ("PUT", _D + "/project-kb"), "api_dictation_project_kb_put",
        lambda s, p, a: s.write_project_kb(p, a.get("kb"), a.get("project_root")),
        "Replace the project's facts.", write=True, properties={"kb": {"type": "object"}, **_ROOT},
        required=("kb", "project_root")),
    _op("dictation.project_kb.start", "start_project_kb", ("POST", _D + "/project-kb/starter"),
        "api_dictation_project_kb_starter", lambda s, p, a: s.start_project_kb(p, a.get("project_root")),
        "Write the starter facts file for the project. A project with facts refuses.", write=True, status=201,
        properties=_ROOT, required=("project_root",)),
    # ── the blocks ──
    _op("dictation.block_templates", "block_templates", ("GET", _D + "/block-templates"),
        "api_dictation_block_templates", lambda s, p, a: s.block_templates(p),
        "List the starter block templates."),
    _op("dictation.blocks.list", "list_blocks", ("GET", _D + "/blocks"), "api_dictation_blocks_list",
        lambda s, p, a: s.list_blocks(p, str(a.get("scope") or "global"), a.get("project_root")),
        "Read the dictation blocks of one scope (global or project).", properties=_SCOPE),
    _op("dictation.blocks.create", "create_block", ("POST", _D + "/blocks"), "api_dictation_blocks_create",
        lambda s, p, a: s.create_block(p, a.get("block"), str(a.get("scope") or "global"), a.get("project_root")),
        "Add one dictation block. An id that exists refuses.", write=True, status=201,
        properties={"block": {"type": "object"}, **_SCOPE}, required=("block",)),
    _op("dictation.blocks.update", "update_block", ("PUT", _D + "/blocks/{block_id}"), "api_dictation_blocks_update",
        lambda s, p, a: s.update_block(p, str(a.get("block_id") or ""), a.get("block"),
                                       str(a.get("scope") or "global"), a.get("project_root")),
        "Replace one dictation block.", write=True, properties={"block": {"type": "object"}, **_SCOPE},
        required=("block",)),
    _op("dictation.blocks.delete", "delete_block", ("DELETE", _D + "/blocks/{block_id}"),
        "api_dictation_blocks_delete",
        lambda s, p, a: s.delete_block(p, str(a.get("block_id") or ""), str(a.get("scope") or "global"),
                                       a.get("project_root")),
        "Remove one dictation block. The last block refuses.", write=True, properties=_SCOPE),
)

__all__ = ["DICTATION_OPERATIONS"]
