"""The desk's tools for an automation on an HTTP engine (MCP M5).

An agent CLI run gets the desk's tools through its run credential (MCP M1,
``intel/cli_engine.py``): the CLI is the agent and loops by itself. An HTTP
engine (the owner's LAN llama.cpp box, an OpenRouter model) is only a model,
so when the Check says its server takes tool calls
(``ask_desk.server_takes_tools``, the same answer Ask uses), the hub runs the
loop inside the item's one admitted child:

1. send the task with the tool schemas (OpenAI ``tools``);
2. run each ``tool_calls`` entry through the same MCP gate an agent run
   meets on ``POST /api/mcp``: an ``agent:run:<run_id>`` AGENT principal, the
   ASK palette (the part of CONDUCTOR that fits a local engine's context; every
   name is a CONDUCTOR name) and ``conductor_call_allowed`` (a call that would
   schedule or delegate is refused). Egress, config and authority tools are in
   neither set: they stop for the owner's press;
3. send the results back and go again, up to the Thread's pass cap and inside
   the child's time limit; the answer is the first pass that calls no tool.

Each answered call is recorded for the result's Looked at, Wrote and Prepared
(MCP M2) under the item's trace key (``run_trace.item_trace``).

The Thread's own pass loop (``ThreadService._run_streaming_turn``) is not
called: it admits each pass as a ``chat.turn`` on the Thread's engine and
writes thread rows, holds and frames. This loop keeps the item on its frozen
route and reuses the Thread's parts: the engine's tool-call stream
(``run_prompt_stream``), the tool schemas (``thread_tools.tool_schemas_for``),
the result byte cap and the pass cap.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.engine_tool_loop")

#: Added to the item's system prompt when its engine gets the desk's tools.
TOOLS_PROMPT = (
    "You can use the tools of the owner's desk (HoldSpeak) to look up his meetings, notes, "
    "people, projects, decisions and memory. Name the records you used. Change the desk only "
    "when the job says so. Never send anything: channel.prepare only prepares a send, and he "
    "presses Send. If a tool is refused, say so and go on without it."
)

#: Seconds kept free before the child's own deadline for the last pass.
_DEADLINE_MARGIN_SECONDS = 1.0

# A project update is a source-scoped automation.  The ordinary MCP palettes
# remain unchanged; these names are the read surfaces that can return a
# project's linked private meeting or People note after the first grounding
# pass.
_PROJECT_UPDATE_READ_TOOLS = frozenset({
    "meeting.get", "meeting.list", "memory.observations", "memory.page",
    "memory.search", "project.get", "project.get_delta", "project.get_room", "project.list_updates",
    "project.resource.list",
})
_PROJECT_UPDATE_ROW_KEYS = frozenset({
    "meetings", "resources", "hits", "observations", "actions", "action_items",
    "artifacts", "decisions", "commitments", "proposals", "sentences", "sources", "evidence", "updates",
})

# A CLI automation receives its durable CONDUCTOR credential before the
# process starts.  A project-update run is the one narrow exception: it may
# read the project/update source surfaces and save the resulting draft.  The
# credential's project_id is the binding; ordinary launch credentials keep
# the unchanged CONDUCTOR palette.
_PROJECT_UPDATE_SAFE_TOOLS = _PROJECT_UPDATE_READ_TOOLS | {"project.update_draft"}


def project_update_scope(principal: Any) -> str:
    """Return the project bound to an update-run credential, if any."""
    from ..principals import PrincipalKind, agent_credentials
    from .conductor_launch import RUN_IDENTITY_PREFIX

    if getattr(principal, "kind", None) is not PrincipalKind.AGENT:
        return ""
    identity = str(getattr(principal, "identity", "") or "")
    if not identity.startswith(RUN_IDENTITY_PREFIX):
        return ""
    credential = agent_credentials.launch_credential(identity)
    if credential is None or credential.palette_name != "CONDUCTOR":
        return ""
    return str(credential.project_id or "").strip()


def project_update_palette(principal: Any, palette: frozenset[str] | None) -> frozenset[str] | None:
    """Scope a project-update run to its existing safe read tools plus its writer."""
    if not project_update_scope(principal):
        return palette
    if palette is None:
        return frozenset(_PROJECT_UPDATE_SAFE_TOOLS)
    return frozenset(set(palette) & set(_PROJECT_UPDATE_SAFE_TOOLS)) | {"project.update_draft"}


def prepare_project_update_call(
    principal: Any, name: str, arguments: Mapping[str, Any], project_id: str,
) -> tuple[dict[str, Any], set[str], str | None]:
    """Bind and filter one MCP call for a durable project-update credential."""
    from ..db import get_database

    args = dict(arguments or {})
    _service, excluded = _project_update_service(principal, project_id)
    folded_excluded = {str(ref).casefold() for ref in excluded}
    if name == "meeting.get":
        meeting_id = str(args.get("meeting_id") or "").strip().casefold()
        _private_ids, eligible_ids = _service._project_update_meeting_ids(principal, project_id)
        if meeting_id not in {value.casefold() for value in eligible_ids}:
            return args, excluded, "meeting is outside project update sources"
    if name in {"project.get", "project.get_delta", "project.get_room", "project.list_updates",
                "project.resource.list", "memory.search", "memory.page", "memory.observations"}:
        requested = str(args.get("project_id") or "").strip()
        if requested and requested != project_id:
            return args, excluded, "project update reads are scoped to its project"
        args["project_id"] = project_id
    if name in {"memory.page", "memory.observations"}:
        args["scope"] = "project"
    if name == "project.update_draft":
        update_id = str(args.get("update_id") or "").strip()
        row = get_database().project_updates.get_update(update_id) if update_id else None
        if row is not None and str(row["project_id"]) != project_id:
            return args, excluded, "draft is outside the project update scope"
        refs = args.get("source_refs")
        if isinstance(refs, list):
            args["source_refs"] = [
                ref for ref in refs
                if str(ref).split("#", 1)[0].casefold() not in folded_excluded
            ]
    return args, excluded, None


def _project_update_refusal(ordinal: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0", "id": ordinal,
        "result": {
            "content": [{"type": "text", "text": json.dumps({"error": message})}],
            "isError": True,
        },
    }


def _project_update_service(principal: Any, project_id: str) -> Any:
    from ..db import get_database
    from .project_service import ProjectService
    from .project_update_service import ProjectUpdateService

    db = get_database()
    service = ProjectUpdateService(db, project_service=ProjectService(db))
    return service, service.project_update_excluded_refs(principal, project_id)


def _row_has_private_ref(row: Any, key: str, excluded: set[str], excluded_meetings: set[str]) -> bool:
    if not isinstance(row, Mapping):
        return False
    if key in {"meetings", "latest"}:
        from .meeting_kind import title_says_one_on_one

        if title_says_one_on_one(str(row.get("title") or "")):
            return True
    candidates: set[str] = set()
    for field in ("ref", "source_ref", "resource_ref", "meeting_ref"):
        value = str(row.get(field) or "").strip()
        if value:
            candidates.add(value.split("#", 1)[0].casefold())
    for field in ("refs", "sources", "evidence"):
        values = row.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, Mapping):
                ref = str(value.get("ref") or value.get("source_ref") or "").strip()
                if ref:
                    candidates.add(ref.split("#", 1)[0].casefold())
    for field in ("week_source_refs", "agent_sources"):
        values = row.get(field)
        if isinstance(values, list):
            candidates.update(
                str(ref).split("#", 1)[0].casefold()
                for ref in values if str(ref).strip()
            )
    for field in ("source_manifest_json", "claims_json"):
        raw = row.get(field)
        if not raw:
            continue
        try:
            manifest = json.loads(str(raw))
        except (TypeError, ValueError):
            continue
        if _row_has_private_ref(manifest, field, excluded, excluded_meetings):
            return True
    for meeting_field in ("meeting_id", "source_meeting_id"):
        meeting_id = str(row.get(meeting_field) or "").strip()
        if meeting_id and meeting_id.casefold() in excluded_meetings:
            return True
    identifier = str(row.get("id") or "").strip()
    if identifier:
        kind = {
            "meetings": "meeting", "actions": "action", "action_items": "action_item",
            "artifacts": "artifact", "decisions": "decision", "proposals": "decision",
        }.get(key)
        if kind:
            candidates.add(f"{kind}:{identifier}".casefold())
        if key == "latest" and (row.get("title") or row.get("started_at") or row.get("summary")):
            candidates.add(f"meeting:{identifier}".casefold())
    # A page/observation can carry its source refs below the row itself.
    for nested_key in ("sentences", "sources", "evidence"):
        nested = row.get(nested_key)
        if isinstance(nested, list):
            for entry in nested:
                if _row_has_private_ref(entry, nested_key, excluded, excluded_meetings):
                    return True
    return bool(candidates & excluded)


def _filter_project_update_payload(value: Any, excluded: set[str], *, key: str = "") -> Any:
    """Remove excluded source rows from one MCP JSON value.

    The MCP transport has already converted service objects to JSON text.  A
    row-level filter keeps the exact positive project refs and response shape,
    while preventing a private row's body or snippet from reaching the model.
    """
    excluded = {str(ref).casefold() for ref in excluded}
    excluded_meetings = {
        ref.removeprefix("meeting:")
        for ref in excluded
        if ref.startswith("meeting:")
    }
    if isinstance(value, list):
        filtered: list[Any] = []
        for row in value:
            if key in _PROJECT_UPDATE_ROW_KEYS and _row_has_private_ref(row, key, excluded, excluded_meetings):
                continue
            filtered.append(_filter_project_update_payload(row, excluded, key=key))
        return filtered
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for child_key, child in value.items():
            # A direct meeting/read payload has no enclosing list key.
            if child_key in {"meeting", "meeting_detail"} and _row_has_private_ref(child, "meetings", excluded, excluded_meetings):
                result[child_key] = None
                continue
            if child_key in {"latest", "latest_published"} and _row_has_private_ref(child, "latest", excluded, excluded_meetings):
                result[child_key] = None
                continue
            result[child_key] = _filter_project_update_payload(child, excluded, key=child_key)
        if key == "page" and isinstance(value.get("sentences"), list):
            safe_sentences = result.get("sentences") or []
            if len(safe_sentences) != len(value["sentences"]):
                result["answer"] = " ".join(
                    str(sentence.get("text") or "").strip()
                    for sentence in safe_sentences
                    if isinstance(sentence, Mapping) and str(sentence.get("text") or "").strip()
                )
        return result
    return value


def _filter_project_update_response(response: Any, excluded: set[str], name: str, *, project_id: str = "", principal: Any = None) -> Any:
    if not isinstance(response, dict):
        return response
    result = response.get("result")
    if not isinstance(result, dict):
        return response
    for content in result.get("content") or []:
        if not isinstance(content, dict) or content.get("type") != "text":
            continue
        try:
            payload = json.loads(str(content.get("text") or "{}"))
        except (TypeError, ValueError):
            continue
        if name == "meeting.list" and project_id and isinstance(payload, dict):
            service, _excluded = _project_update_service(principal, project_id)
            _private, eligible = service._project_update_meeting_ids(principal, project_id)
            payload["meetings"] = [
                row for row in payload.get("meetings", [])
                if isinstance(row, dict) and str(row.get("id") or "") in eligible
            ]
        root_key = {
            "meeting.list": "meetings", "project.get_delta": "proposals", "project.list_updates": "updates",
            "project.resource.list": "resources",
            "memory.search": "hits", "memory.observations": "observations",
        }.get(name, "")
        content["text"] = json.dumps(
            _filter_project_update_payload(payload, excluded, key=root_key),
            sort_keys=True,
            default=str,
        )
    return response


@dataclass
class LoopAnswer:
    output: str
    tokens: int
    calls: int


def takes_tools(engine: Any) -> bool:
    """True when ``engine`` is an HTTP engine whose server takes tool calls."""
    from .ask_desk import server_tools_on

    if hasattr(engine, "preset") or not hasattr(engine, "run_prompt_stream"):
        return False  # an agent CLI gets its tools from M1
    if str(getattr(engine, "provider", "") or "") != "cloud" or not server_tools_on():
        return False
    endpoint = str(getattr(engine, "cloud_base_url", "") or "").strip()
    if not endpoint.startswith(("http://", "https://")):
        return False
    from . import ask_desk

    try:
        answer = ask_desk.server_takes_tools(
            endpoint, str(getattr(engine, "cloud_model", "") or ""),
            key_env=str(getattr(engine, "cloud_api_key_env", "") or ""),
        )
    except Exception as exc:
        log.info(f"tool support not read for {endpoint}: {exc}")
        return False
    return answer == "yes"


def _deadline(engine: Any) -> float:
    """The child's execution deadline (epoch seconds); 0 when none is known."""
    from ..kernel.dispatch_context import dispatch_context_of

    context = dispatch_context_of(engine)
    if context is None:
        return 0.0
    try:
        return float(context.warrant.get("execution_expires_at") or 0)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    try:
        value = json.loads(str(raw or "") or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _tool_answer(response: Any) -> str:
    """The text the model reads for one call: the tool's value, or its refusal."""
    from .thread_tools import TOOL_RESULT_BYTE_CAP, _truncate_utf8

    if not isinstance(response, Mapping):
        text = json.dumps({"error": "no answer"})
    elif "error" in response:
        text = json.dumps({"error": (response["error"] or {}).get("message", "refused")}, default=str)
    else:
        result = response.get("result") if isinstance(response.get("result"), Mapping) else {}
        parts = [str(p.get("text") or "") for p in result.get("content") or []
                 if isinstance(p, Mapping) and p.get("type") == "text"]
        text = "\n".join(parts) or "{}"
        if result.get("isError"):
            text = json.dumps({"error": text})
    return _truncate_utf8(text, TOOL_RESULT_BYTE_CAP)


def call_tool(
    run_id: str,
    trace: str,
    name: str,
    arguments: dict[str, Any],
    ordinal: int,
    *,
    palette: str = "ASK",
    allow_project_update: bool = False,
    project_id: str = "",
    project_update_excluded_refs: list[str] | None = None,
) -> str:
    """One tool call through the agent-run MCP gate; recorded under ``trace``."""
    from ..mcp.palettes import ASK, CONDUCTOR, conductor_call_allowed, conductor_resource_allowed, resolve_palette
    from ..mcp.server import handle_message_for_principal
    from ..principals import Principal, PrincipalKind
    from . import run_trace
    from .conductor_launch import RUN_IDENTITY_PREFIX, project_scope

    principal = Principal(PrincipalKind.AGENT, f"{RUN_IDENTITY_PREFIX}{run_id}")
    arguments = dict(arguments or {})
    if name == "project.update_draft" and allow_project_update:
        # The agent may omit the manifest in its tool call.  The application
        # producer still receives the exact refs recorded by the preceding
        # real reads in this run.
        try:
            from ..db import get_database
            seen = run_trace.use_by_trace(get_database(), [trace]).get(trace, {})
            refs = list(dict.fromkeys(
                str(entry.get("ref") or "").strip()
                for entry in seen.get("looked_at", [])
                if str(entry.get("ref") or "").strip()
            ))
            if refs and not arguments.get("source_refs"):
                arguments["source_refs"] = refs
        except Exception:
            pass
    request = {"jsonrpc": "2.0", "id": ordinal, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
    selected = resolve_palette(CONDUCTOR if str(palette).upper() == CONDUCTOR else ASK)
    if allow_project_update:
        # Project update automations are the one scoped CONDUCTOR write. Keep
        # the normal palette and authority table intact for every other run;
        # this only exposes the already-registered draft editor to the
        # automation whose output target names a project update.
        selected = frozenset(set(selected) & set(_PROJECT_UPDATE_SAFE_TOOLS)) | {"project.update_draft"}

        def project_update_gate(tool: str, args: Any) -> bool:
            return tool == "project.update_draft" or conductor_call_allowed(tool, args)

        call_gate = project_update_gate
    else:
        call_gate = conductor_call_allowed
    # The HTTP engine has the same run identity as a CLI engine, but no
    # durable credential row. Bind its project for the one MCP dispatch so the
    # launch gate can enforce the update draft's project scope.
    target_project = str(project_id or "").strip()
    if name == "project.update_draft" and allow_project_update and not target_project:
        target_project = str(arguments.get("project_id") or "").strip()
    excluded_refs: set[str] | None = None
    if allow_project_update and name in _PROJECT_UPDATE_SAFE_TOOLS and target_project:
        try:
            arguments, excluded_refs, refusal = prepare_project_update_call(
                principal, name, arguments, target_project,
            )
            if project_update_excluded_refs is not None:
                excluded_refs.update(str(ref) for ref in project_update_excluded_refs if str(ref).strip())
        except Exception:
            refusal = "project update sources are unavailable"
        if refusal:
            response = _project_update_refusal(ordinal, refusal)
            run_trace.record_call(trace, name, arguments, response)
            return _tool_answer(response)
    try:
        with project_scope(target_project):
            response = handle_message_for_principal(
                request, principal,
                palette=selected,
                call_gate=call_gate, resource_gate=conductor_resource_allowed,
            )
    except Exception as exc:  # a tool that breaks is a refused call, never a failed run
        log.warning(f"tool {name} failed in an automation run: {exc}")
        response = {"jsonrpc": "2.0", "id": ordinal, "error": {"code": -32603, "message": str(exc)}}
    if excluded_refs is not None:
        response = _filter_project_update_response(response, excluded_refs, name, project_id=target_project, principal=principal)
    run_trace.record_call(trace, name, arguments, response)
    return _tool_answer(response)


def run(engine: Any, payload: Mapping[str, Any], cancellation: Any, *, item_id: str) -> LoopAnswer:
    """Run one automation item through the tool loop; return its answer."""
    from ..mcp.palettes import ASK, CONDUCTOR, resolve_palette
    from . import run_trace
    from .thread_service import _CHAT_PASS_CAP
    from .thread_tools import tool_schemas_for

    palette = str(payload.get("tool_palette") or ASK).upper()
    project_updates_target = str(payload.get("output_target") or "").startswith("project_updates:")
    selected = resolve_palette(CONDUCTOR if palette == CONDUCTOR else ASK)
    if project_updates_target:
        selected = frozenset(set(selected) & set(_PROJECT_UPDATE_SAFE_TOOLS)) | {"project.update_draft"}
    tools = tool_schemas_for(selected)
    system = "\n\n".join(x for x in (str(payload.get("system_prompt") or ""), TOOLS_PROMPT) if x)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": str(payload.get("user_prompt") or "")},
    ]
    run_id = "run_" + uuid.uuid4().hex[:16]
    trace = run_trace.item_trace(item_id)
    deadline = _deadline(engine)
    tokens = calls = 0
    for _pass in range(_CHAT_PASS_CAP):
        if cancellation is not None and cancellation.is_set():
            raise RuntimeError("The run was stopped.")
        if deadline and time.time() > deadline - _DEADLINE_MARGIN_SECONDS:
            raise RuntimeError("The engine did not finish in the time limit.")
        text: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        error = ""
        for delta in engine.run_prompt_stream(
            messages=messages, temperature=payload.get("temperature"),
            max_tokens=payload.get("max_tokens"), tools=tools,
        ):
            if delta.kind == "text":
                text.append(str(delta.text or ""))
            elif delta.kind == "tool_calls":
                tool_calls.extend(delta.meta.get("tool_calls") or [])
            elif delta.kind == "usage":
                meta = dict(delta.meta or {})
                tokens += int(meta.get("total_tokens")
                              or int(meta.get("prompt_tokens") or 0) + int(meta.get("completion_tokens") or 0))
            elif delta.kind == "error":
                error = str(delta.text or "The engine did not answer.")
        if error:
            raise RuntimeError(error)
        if not tool_calls:
            return LoopAnswer(output="".join(text).strip(), tokens=tokens, calls=calls)
        asked: list[dict[str, Any]] = []
        answers: list[dict[str, Any]] = []
        for call in tool_calls:
            call_id = str(call.get("id") or uuid.uuid4().hex[:16])
            name = str(call.get("name") or "")
            raw = call.get("arguments")
            calls += 1
            asked.append({"id": call_id, "type": "function", "function": {
                "name": name, "arguments": raw if isinstance(raw, str) else json.dumps(raw or {})}})
            answers.append({"role": "tool", "tool_call_id": call_id,
                            "content": call_tool(run_id, trace, name, _arguments(raw), calls,
                                                 palette=palette,
                                                 allow_project_update=project_updates_target,
                                                 project_id=str(payload.get("output_target") or "").removeprefix("project_updates:"),
                                                 project_update_excluded_refs=payload.get("project_update_excluded_refs"))})
        messages.append({"role": "assistant", "tool_calls": asked})
        messages.extend(answers)
    raise RuntimeError(f"The engine did not finish in {_CHAT_PASS_CAP} turns.")


def answer_item(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Optional[tuple[dict[str, str], int]]:
    """The item's result through the loop, or None when its engine takes no tools."""
    if not takes_tools(engine):
        return None
    answer = run(engine, payload, cancellation, item_id=str(payload.get("item_id") or ""))
    result = {
        "output": answer.output,
        "provider": str(getattr(engine, "active_provider", "") or ""),
        "model": str(getattr(engine, "active_model", "") or getattr(engine, "model", "") or ""),
    }
    return result, answer.tokens


__all__ = ["LoopAnswer", "TOOLS_PROMPT", "answer_item", "call_tool", "run", "takes_tools"]
