"""The dictation verbs on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``calls_operations.py`` is. Each row states one
``DictationService`` verb once: its call, its HTTP method and path, and (where
an owner or agent may call it) its MCP tool schema.
``web/routes/dictation/_declared.py`` produces the routes with
``operation_router``; ``mcp/families/declared.py`` produces the tools. The
hand-written ``dictation.list`` and ``dictation.get`` tools are gone from
``mcp/tools.py``: these rows make them.

The edge gives every ``/api/dictation/*`` route the OWNER right
(``principals.required_right``). Deleting a journal entry, clearing the
journal and forgetting a correction are his alone (``owner_only``).

Kept hand-written, and why (``web/routes/dictation/pipeline.py``,
``blocks.py``, ``web/routes/system/voice.py``): the verbs that run the speech
pipeline or a model (dry-run, remote, journal replay, a template's preview,
transcribe), the open-mic session lifetime (mic open/close), and the three
one-time typing tokens (wake/type, preview/type, preview/discard). They are
the speech session's own entries (the engine-door lane moves their model
calls); the remote route's delivery ledger (``claim_delivery``,
``complete_delivery``, ``fail_delivery``) is the idempotency of that one
turn, not a verb.

No tool, and why:

- ``dictation.floor.claim`` / ``dictation.floor.release``: the browser's open
  mic on the one audio arbiter; an agent holds no microphone.

The project writes (``dictation.project_hs.put``, ``dictation.project_kb.put``
/ ``.start``) write into a repository on his disk; their tools REQUIRE
``project_root`` (over HTTP an empty root is the hub's own working tree, as it
always was for the Dictation settings face).

Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_ANY = "derived by the transport (HTTP edge right OWNER; MCP auth resolver) and passed to the service unchanged"
_OWNER = "the owner only: the hub token (HTTP edge right OWNER; MCP auth resolver), passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + (
    "owner_required",
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
        status: int = 200, quiet: bool = False, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = ()) -> OperationDescriptor:
    """One verb; its tool (when it has one) requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in (http[1] if http else "").split("/") if part.startswith("{")]
    schema = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
              "required": ids + list(required), "additionalProperties": False}
    exposure = ((f"http:{http[0]} {http[1]}",) if http else ()) + ((f"mcp:{name}",) if tool else ())
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"},
        principal=_OWNER if owner_only else _ANY, effect="write" if write else "read",
        result="the DictationService answer", refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus (kind dictation)"
        if write and not quiet else "synchronous",
        exposure=exposure, service="dictation_service", method=method, owner_only=owner_only, call=call,
        http=http, http_status=status, handler=handler, tool_schema=schema if tool else None,
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
        "Claim the microphone for the browser's open mic, on a lease.", write=True, tool=False, quiet=True),
    _op("dictation.floor.release", "release_floor", ("POST", _D + "/floor/release"), "api_audio_floor_release",
        lambda s, p, a: s.release_floor(p), "Release the browser's claim on the microphone.", write=True,
        tool=False, quiet=True),
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
