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


def call_tool(run_id: str, trace: str, name: str, arguments: dict[str, Any], ordinal: int) -> str:
    """One tool call through the agent-run MCP gate; recorded under ``trace``."""
    from ..mcp.palettes import ASK, conductor_call_allowed, conductor_resource_allowed, resolve_palette
    from ..mcp.server import handle_message_for_principal
    from ..principals import Principal, PrincipalKind
    from . import run_trace
    from .conductor_launch import RUN_IDENTITY_PREFIX

    principal = Principal(PrincipalKind.AGENT, f"{RUN_IDENTITY_PREFIX}{run_id}")
    request = {"jsonrpc": "2.0", "id": ordinal, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
    try:
        response = handle_message_for_principal(
            request, principal, palette=resolve_palette(ASK),
            call_gate=conductor_call_allowed, resource_gate=conductor_resource_allowed,
        )
    except Exception as exc:  # a tool that breaks is a refused call, never a failed run
        log.warning(f"tool {name} failed in an automation run: {exc}")
        response = {"jsonrpc": "2.0", "id": ordinal, "error": {"code": -32603, "message": str(exc)}}
    run_trace.record_call(trace, name, arguments, response)
    return _tool_answer(response)


def run(engine: Any, payload: Mapping[str, Any], cancellation: Any, *, item_id: str) -> LoopAnswer:
    """Run one automation item through the tool loop; return its answer."""
    from ..mcp.palettes import ASK, resolve_palette
    from . import run_trace
    from .thread_service import _CHAT_PASS_CAP
    from .thread_tools import tool_schemas_for

    tools = tool_schemas_for(resolve_palette(ASK))
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
                            "content": call_tool(run_id, trace, name, _arguments(raw), calls)})
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
