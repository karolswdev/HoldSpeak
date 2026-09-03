"""HS-152-02: Thread tool gate, classification map, and executor.

The classification map names every MCP tool's class (evidence_read,
candidate_builder, effect_proposal) and sensitive flag.  An unclassified tool
fails closed.  The truth table resolves (policy, control_mode, class) to
admit | hold | deny.  The executor goes through ToolCallCodec +
ToolTurnController with the turn's operation as parent -- no new admission
path.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from ..principals import Principal, PrincipalKind

# ---------------------------------------------------------------------------
# Classification map -- every MCP tool, fail-closed
# ---------------------------------------------------------------------------
# Classes: evidence_read, candidate_builder, effect_proposal
# Sensitive: True for all people.* tools

_TOOL_CLASSES: dict[str, tuple[str, bool]] = {
    # --- desk family (main catalogue) ---
    "desk.list":          ("evidence_read",     False),
    "desk.get":           ("evidence_read",     False),
    "desk.create":        ("effect_proposal",   False),
    "desk.update":        ("effect_proposal",   False),
    "desk.delete":        ("effect_proposal",   False),
    "desk.verb":          ("effect_proposal",   False),
    "desk.snapshot":      ("evidence_read",     False),
    # --- meeting ---
    "meeting.list":           ("evidence_read",     False),
    "meeting.get":            ("evidence_read",     False),
    "meeting.start_capture":  ("effect_proposal",   False),
    "meeting.stop_capture":   ("effect_proposal",   False),
    "meeting.delete":         ("effect_proposal",   False),
    "meeting.export":         ("evidence_read",     False),
    # --- workbench ---
    "workbench.run":          ("effect_proposal",   False),
    "workbench.add_item":     ("effect_proposal",   False),
    "workbench.list":         ("evidence_read",     False),
    "workbench.get":          ("evidence_read",     False),
    "workbench.create":       ("effect_proposal",   False),
    "workbench.update":       ("effect_proposal",   False),
    "workbench.delete":       ("effect_proposal",   False),
    "workbench.update_item":  ("effect_proposal",   False),
    "workbench.delete_item":  ("effect_proposal",   False),
    "workbench.list_runs":    ("evidence_read",     False),
    # --- recipe ---
    "recipe.list":        ("evidence_read",     False),
    "recipe.get":         ("evidence_read",     False),
    "recipe.run":         ("effect_proposal",   False),
    "recipe.chat":        ("effect_proposal",   False),
    # --- zone + kb ---
    "zone.file":          ("effect_proposal",   False),
    "zone.unfile":        ("effect_proposal",   False),
    "zone.list_members":  ("evidence_read",     False),
    "kb.add_member":      ("effect_proposal",   False),
    "kb.remove_member":   ("effect_proposal",   False),
    "kb.list_members":    ("evidence_read",     False),
    # --- dictation ---
    "dictation.list":     ("evidence_read",     False),
    "dictation.get":      ("evidence_read",     False),
    # --- decision records ---
    "decision_record.list":                ("evidence_read",     False),
    "decision_record.get":                 ("evidence_read",     False),
    "decision_record.create_from_meeting": ("effect_proposal",   False),
    "decision_record.create_from_desk":    ("effect_proposal",   False),
    "decision_record.search":              ("evidence_read",     False),
    "decision.supersede":                  ("effect_proposal",   False),
    # --- pipeline events ---
    "pipeline.events":    ("evidence_read",     False),
    # --- follow-through ---
    "follow_through.board":            ("evidence_read",     False),
    "follow_through.complete":         ("effect_proposal",   False),
    "follow_through.commit_decision":  ("effect_proposal",   False),
    # --- monday brief ---
    "monday_brief.get":       ("evidence_read",     False),
    "monday_brief.generate":  ("candidate_builder", False),
    # --- scheduled recording ---
    "scheduled_recording.list":         ("evidence_read",     False),
    "scheduled_recording.create":       ("effect_proposal",   False),
    "scheduled_recording.update":       ("effect_proposal",   False),
    "scheduled_recording.delete":       ("effect_proposal",   False),
    "scheduled_recording.cancel_armed": ("effect_proposal",   False),
    # --- ask family ---
    "ask.resolve_grounding": ("candidate_builder", False),
    "ask.run":               ("effect_proposal",   False),
    "ask.cancel":            ("effect_proposal",   False),
    "ask.keep":              ("effect_proposal",   False),
    # --- settings family ---
    "settings.get":    ("evidence_read",     False),
    "settings.update": ("effect_proposal",   False),
    # --- coder family ---
    "coder.list":   ("evidence_read",     False),
    "coder.get":    ("evidence_read",     False),
    "coder.audit":  ("evidence_read",     False),
    # --- cadence family ---
    "cadence.status":          ("evidence_read",     False),
    "cadence.loops":           ("evidence_read",     False),
    "cadence.get_loop":        ("evidence_read",     False),
    "cadence.brief":           ("evidence_read",     False),
    "cadence.closeout":        ("candidate_builder", False),
    "cadence.history":         ("evidence_read",     False),
    "cadence.audit":           ("evidence_read",     False),
    "cadence.snooze":          ("effect_proposal",   False),
    "cadence.set_status":      ("effect_proposal",   False),
    "cadence.run_now":         ("effect_proposal",   False),
    "cadence.apply_closeout":  ("effect_proposal",   False),
    # --- sequence / workflow ---
    "sequence.run":     ("effect_proposal",   False),
    "sequence.cancel":  ("effect_proposal",   False),
    "workflow.run":     ("effect_proposal",   False),
    "workflow.cancel":  ("effect_proposal",   False),
    # --- memory ---
    "memory.search":    ("evidence_read",     False),
    # --- people family (ALL sensitive) ---
    "people.readiness":            ("evidence_read",     True),
    "people.relationship.list":    ("evidence_read",     True),
    "people.relationship.get":     ("evidence_read",     True),
    "people.grounding.get":        ("evidence_read",     True),
    "people.relationship.create":  ("effect_proposal",   True),
    "people.one_on_one.create":    ("effect_proposal",   True),
    "people.agenda.add":           ("effect_proposal",   True),
    "people.note.create":          ("effect_proposal",   True),
    "people.request.create":       ("effect_proposal",   True),
    "people.request.accept":       ("effect_proposal",   True),
    "people.commitment.transition":("effect_proposal",   True),
    "people.one_on_one.brief":     ("evidence_read",     True),
    "people.calendar.link":        ("effect_proposal",   True),
    "people.calendar.unlink":      ("effect_proposal",   True),
    "people.owner_alias.link":     ("effect_proposal",   True),
    "people.owner_alias.unlink":   ("effect_proposal",   True),
    # --- plugin_job ---
    "plugin_job.list":    ("evidence_read",     False),
    "plugin_job.summary": ("evidence_read",     False),
    "plugin_job.retry":   ("effect_proposal",   False),
    "plugin_job.cancel":  ("effect_proposal",   False),
    # --- reactions / watches / events ---
    "reaction.presets":     ("evidence_read",     False),
    "watch.list":           ("evidence_read",     False),
    "watch.create":         ("effect_proposal",   False),
    "watch.set_enabled":    ("effect_proposal",   False),
    "watch.refresh":        ("effect_proposal",   False),
    "watch.preview":        ("evidence_read",     False),
    "event.list":           ("evidence_read",     False),
    "reaction.list":        ("evidence_read",     False),
    "reaction.create":      ("effect_proposal",   False),
    "reaction.set_enabled": ("effect_proposal",   False),
    "reaction.process":     ("effect_proposal",   False),
    # --- thought family ---
    "thought.create":                ("effect_proposal",   False),
    "thought.adopt_note":            ("effect_proposal",   False),
    "thought.get_default_context":   ("evidence_read",     False),
    "thought.replace_default_context": ("effect_proposal", False),
    "thought.list_context":          ("evidence_read",     False),
    "thought.refine":                ("effect_proposal",   False),
    "thought.reconcile":             ("effect_proposal",   False),
    "thought.stop_refinement":       ("effect_proposal",   False),
    "thought.attach_context":        ("effect_proposal",   False),
    "thought.detach_context":        ("effect_proposal",   False),
    "thought.refresh_context":       ("effect_proposal",   False),
    "thought.answer_review":         ("effect_proposal",   False),
    "thought.accept_review":         ("effect_proposal",   False),
    "thought.reject_review":         ("effect_proposal",   False),
    "thought.answer_and_continue":   ("effect_proposal",   False),
    "thought.update_working":        ("effect_proposal",   False),
    "thought.complete":              ("effect_proposal",   False),
    "thought.resume":                ("effect_proposal",   False),
    # --- inference family ---
    "inference.cancel_model_acquisition": ("effect_proposal", False),
    # --- model_library family ---
    "model_library.download":               ("effect_proposal", False),
    "model_library.add_to_library":         ("effect_proposal", False),
    "model_library.connect_hosted_model":   ("effect_proposal", False),
    "model_library.define_endpoint":        ("effect_proposal", False),
    "model_library.connect_paired_device":  ("effect_proposal", False),
    "model_library.use_model_file":         ("effect_proposal", False),
    "model_library.get":                    ("evidence_read",   False),
    # --- inference_assignment family ---
    "inference_assignment.editor":              ("evidence_read",   False),
    "inference_assignment.set":                 ("effect_proposal", False),
    "inference_assignment.preview_use_default": ("evidence_read",   False),
    "inference_assignment.clear":               ("effect_proposal", False),
    "inference_assignment.summary":             ("evidence_read",   False),
    # --- door family ---
    "door.get": ("evidence_read", False),
    "door.add_item": ("effect_proposal", False),  # HS-153-05: thread todo → Door
    # --- thread family (HS-152-05) ---
    "thread.set_status": ("effect_proposal", False),
    # --- project family (HS-165; MCP-only, in no thread palette) ---
    "project.get": ("evidence_read", False),
    "project.get_delta": ("evidence_read", False),
    "project.get_room": ("evidence_read", False),
    "project.get_steward_run": ("evidence_read", False),
    "project.list": ("evidence_read", False),
    "project.list_updates": ("evidence_read", False),
    "project.setup.resume": ("evidence_read", False),
    "project.watch.inspect": ("evidence_read", False),
    "provider.github_connection": ("evidence_read", False),
    "provider.github_discover": ("evidence_read", False),
    "provider.github_validate_repo": ("evidence_read", False),
    "provider.list": ("evidence_read", False),
    # HS-166: the Jira provider family (reads) + the one row-creating verb.
    "provider.jira_connections": ("evidence_read", False),
    "provider.jira_connection": ("evidence_read", False),
    "provider.jira_discover": ("evidence_read", False),
    "provider.jira_search": ("evidence_read", False),
    "provider.jira_validate_scope": ("evidence_read", False),
    "provider.jira_add_connection": ("effect_proposal", False),
    "project.accept_review": ("effect_proposal", False),
    "project.archive": ("effect_proposal", False),
    "project.configure_steward": ("effect_proposal", False),
    "project.create": ("effect_proposal", False),
    "project.decide_proposal": ("effect_proposal", False),
    "project.draft_update": ("effect_proposal", False),
    "project.link": ("effect_proposal", False),
    "project.open_review": ("effect_proposal", False),
    "project.publish_update": ("effect_proposal", False),
    "project.restore": ("effect_proposal", False),
    "project.run_steward": ("effect_proposal", False),
    "project.setup.answer": ("effect_proposal", False),
    "project.setup.finalize": ("effect_proposal", False),
    "project.setup.clarify_jira_scope": ("effect_proposal", False),  # HS-166
    "project.setup.start": ("effect_proposal", False),
    "project.setup.suggest": ("effect_proposal", False),
    "project.stop_steward": ("effect_proposal", False),
    "project.unlink": ("effect_proposal", False),
    "project.update": ("effect_proposal", False),
    "project.update_draft": ("effect_proposal", False),
    "project.watch.evaluate": ("effect_proposal", False),
    "project.watch.pause": ("effect_proposal", False),
    "project.watch.resume": ("effect_proposal", False),
    "project.watch.retire": ("effect_proposal", False),
    "project.watch.set_rules": ("effect_proposal", False),
    "project.watch.test": ("effect_proposal", False),
}

# Public accessors
TOOL_NAMES: frozenset[str] = frozenset(_TOOL_CLASSES)

# HS-152-03: the palette a chat turn OFFERS the model.  ``TOOL_NAMES`` stays
# the gate's classification table (any call the model makes is resolved
# against it); the palette is what rides inside the admitted payload.  The
# full 141-schema census is ~79 KB, and the admission law reserves one
# token per byte -- it overflowed a 32k context at admission before a
# single message was sent.  DC-02 offers the desk-facing hands; DC-03
# modes narrow (or widen) this per recipe.
CHAT_PALETTE: frozenset[str] = frozenset({
    # the desk
    "desk.list", "desk.get", "desk.create", "desk.update", "desk.snapshot",
    "zone.list_members", "zone.file", "zone.unfile",
    "memory.search",
    # the door + the week
    "door.get", "door.add_item",
    "monday_brief.get",
    # meetings + what came out of them
    "meeting.list", "meeting.get",
    "follow_through.board", "follow_through.complete", "follow_through.commit_decision",
    "decision_record.list", "decision_record.search", "decision_record.get",
    # people (every result sensitive at birth -- the fence)
    "people.readiness", "people.relationship.list", "people.relationship.get",
    "people.one_on_one.brief", "people.agenda.add", "people.note.create",
    # thread family (HS-152-05)
    "thread.set_status",
})
assert CHAT_PALETTE <= TOOL_NAMES, sorted(CHAT_PALETTE - TOOL_NAMES)


def tool_class(name: str) -> str:
    """Return the tool's class or raise ValueError (fail-closed)."""
    entry = _TOOL_CLASSES.get(name)
    if entry is None:
        raise ValueError(f"Unclassified tool: {name}")
    return entry[0]


def tool_sensitive(name: str) -> bool:
    """Return True when a tool's results are sensitive (people.*)."""
    entry = _TOOL_CLASSES.get(name)
    if entry is None:
        raise ValueError(f"Unclassified tool: {name}")
    return entry[1]


# ---------------------------------------------------------------------------
# Semantic kind derivation (HS-152-05)
# ---------------------------------------------------------------------------

def derive_result_kind(name: str, args: dict[str, Any] | None = None) -> str:
    """Derive a semantic kind from the tool name for per-kind result rendering.

    Called in ONE place (``ThreadToolExecutor.execute``) after a successful
    dispatch.  Error and mutation overrides happen in the caller.
    """
    if name.startswith("meeting."):
        return "meeting"
    if name.startswith("people."):
        return "person"
    if name in ("door.get", "follow_through.board"):
        return "board"
    if name in ("desk.list", "desk.get", "desk.create", "desk.update"):
        if args and str(args.get("kind", "")) == "notes":
            return "note"
    if name.startswith("decision_record.") or name == "decision.supersede":
        return "decision"
    return "data"


# ---------------------------------------------------------------------------
# Tool schemas rendered for the model
# ---------------------------------------------------------------------------

def tool_schemas_for(allowed_names: frozenset[str] | set[str]) -> list[dict[str, Any]]:
    """Render OpenAI function-call schemas from the MCP inputSchema.

    Imported late to avoid circular imports at module load.
    """
    from ..mcp.tools import TOOLS as MCP_TOOLS

    result: list[dict[str, Any]] = []
    for tool in MCP_TOOLS:
        name = tool["name"]
        if name not in allowed_names:
            continue
        input_schema = tool.get("inputSchema", {})
        # OpenAI function calling format
        parameters = {
            "type": input_schema.get("type", "object"),
            "properties": input_schema.get("properties", {}),
        }
        if "required" in input_schema:
            parameters["required"] = input_schema["required"]
        if input_schema.get("additionalProperties") is not None:
            parameters["additionalProperties"] = input_schema["additionalProperties"]
        result.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.get("description", ""),
                "parameters": parameters,
            },
        })
    return result


# ---------------------------------------------------------------------------
# Truth table (D2)
# ---------------------------------------------------------------------------

def resolve_tool_decision(
    policy: Optional[str],
    control_mode: str,
    tool_class_value: str,
) -> str:
    """Resolve (policy, control_mode, class) -> 'admit' | 'hold' | 'deny'.

    Implements the 8-row truth table from the settled design exactly.
    """
    # Row 1: policy = allow -> admit
    if policy == "allow":
        return "admit"
    # Row 2: policy = deny -> deny
    if policy == "deny":
        return "deny"
    # Row 3: policy = ask -> hold
    if policy == "ask":
        return "hold"
    # Rows 4-8: policy is unset (None)
    if control_mode == "yolo":
        # Row 4: unset + yolo + any -> admit
        return "admit"
    if control_mode == "neutral":
        # Row 5: unset + neutral + evidence_read | candidate_builder -> admit
        if tool_class_value in ("evidence_read", "candidate_builder"):
            return "admit"
        # Row 6: unset + neutral + effect_proposal -> hold
        return "hold"
    # control_mode == "safe"
    # Row 7: unset + safe + evidence_read -> admit
    if tool_class_value == "evidence_read":
        return "admit"
    # Row 8: unset + safe + candidate_builder | effect_proposal -> hold
    return "hold"


# ---------------------------------------------------------------------------
# ToolCallHandle and ThreadToolExecutor
# ---------------------------------------------------------------------------

@dataclass
class ToolCallHandle:
    """Mutable handle for one in-flight tool call within a thread turn."""
    call_id: str
    thread_id: str
    turn_operation_id: str
    name: str
    args: dict[str, Any]
    tool_class: str
    sensitive: bool
    state: str  # 'admitted' | 'held' | 'denied' | 'executing' | 'completed' | 'awaiting_decision'
    kernel_child_id: str = ""
    receipt_id: str = ""
    elicitation: Optional[dict[str, Any]] = None
    answer: Optional[Any] = None
    _cancel: Optional[threading.Event] = None


# HS-152-05: tool result byte cap.  The tool-role message content the
# model sees and the persisted part text are both truncated at this
# boundary (UTF-8 safe).  The meta_json carries {"truncated": true,
# "original_bytes": N} when truncation fires.
TOOL_RESULT_BYTE_CAP = 32_768


def _truncate_utf8(text: str, cap: int) -> str:
    """Truncate *text* to at most *cap* bytes at a UTF-8 boundary."""
    encoded = text.encode("utf-8")
    if len(encoded) <= cap:
        return text
    # Walk back from cap to find a valid UTF-8 boundary
    truncated = encoded[:cap]
    return truncated.decode("utf-8", errors="ignore")


@dataclass(frozen=True)
class ToolResult:
    """The closed result of one tool execution."""
    name: str
    kind: str
    payload: Any
    bytes: int
    receipt_id: str
    sensitive: bool
    elicitation: Optional[dict[str, Any]] = None
    truncated: bool = False
    original_bytes: int = 0


class ThreadToolExecutor:
    """The thread tool gate and executor.

    Goes through ToolCallCodec + ToolTurnController (broker.submit) with the
    turn's operation as parent.  10-step chat lease, distinct from the Recipe
    agent's 4.  No new admission path.
    """

    CHAT_STEP_CAP = 10

    def __init__(
        self,
        db: Any,
        *,
        dispatch_fn: Callable[..., Any],
        principal: Principal,
        control_mode_fn: Callable[[], str],
        broker: Optional[Any] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._db = db
        self._dispatch = dispatch_fn
        self._principal = principal
        self._control_mode_fn = control_mode_fn
        self._broker = broker
        self._clock = clock
        self._handles: dict[str, ToolCallHandle] = {}
        self._on_decided: Optional[Callable[[str], None]] = None

    @property
    def on_decided(self) -> Optional[Callable[[str], None]]:
        return self._on_decided

    @on_decided.setter
    def on_decided(self, callback: Optional[Callable[[str], None]]) -> None:
        self._on_decided = callback

    def admit(
        self,
        turn_operation_id: str,
        thread_id: str,
        call: dict[str, Any],
    ) -> ToolCallHandle:
        """Resolve a tool call through the truth table and Broker child.

        ``call`` must have keys: id, name, arguments.
        The handle records the kernel child through the existing ToolCallCodec
        pathway (broker.submit) so the one-path census sees no new admission.
        """
        call_id = str(call.get("id") or uuid.uuid4().hex[:16])
        name = str(call.get("name", ""))
        args = call.get("arguments", {}) or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                args = {}

        # Fail closed on unclassified tool
        cls = tool_class(name)
        sensitive = tool_sensitive(name)

        # Read per-thread policy
        policy = self._db.threads.effective_tool_policy(thread_id, name)
        control_mode = self._control_mode_fn()
        decision = resolve_tool_decision(policy, control_mode, cls)

        # Create kernel child through the broker (no new admission path)
        child_id = ""
        if self._broker is not None:
            args_json = json.dumps(args, sort_keys=True, separators=(",", ":"))
            args_sha = hashlib.sha256(args_json.encode()).hexdigest()
            request = {
                "request_schema": 1,
                "request_id": f"thread-tool-{call_id}",
                "idempotency_key": f"thread-tool-{call_id}",
                "operation": {"name": "tool.call", "version": 1},
                "subject_refs": [f"thread-turn:{turn_operation_id}"],
                "target": {"ref": f"thread-tool:{call_id}"},
                "arguments": {
                    "proposal_id": call_id,
                    "tool": name,
                    "args_sha256": args_sha,
                    "args_head": f"THREAD_TOOL {name}",
                    "cwd": "thread-turn",
                    "ttl_seconds": 30,
                },
                "placement": "node:thread-turn",
            }
            try:
                result = self._broker.submit(request, self._principal)
                child_id = str(result.get("operation_id", ""))
            except Exception:
                child_id = f"child-{call_id}"
        else:
            child_id = f"child-{call_id}"

        state = {
            "admit": "admitted",
            "hold": "awaiting_decision",
            "deny": "denied",
        }[decision]

        handle = ToolCallHandle(
            call_id=call_id,
            thread_id=thread_id,
            turn_operation_id=turn_operation_id,
            name=name,
            args=args,
            tool_class=cls,
            sensitive=sensitive,
            state=state,
            kernel_child_id=child_id,
            _cancel=threading.Event(),
        )
        self._handles[call_id] = handle
        return handle

    def decide(
        self,
        handle: ToolCallHandle,
        decision: str,
        answer: Any = None,
    ) -> None:
        """Resolve a held call: 'approve' or 'deny'.

        For Allow-always, the caller writes the policy row separately before
        calling decide('approve').
        """
        if decision == "approve":
            handle.state = "admitted"
            if answer is not None:
                handle.answer = answer
        elif decision == "deny":
            handle.state = "denied"
        else:
            raise ValueError(f"Invalid decision: {decision}")
        if self._on_decided is not None:
            self._on_decided(handle.call_id)

    def execute(
        self,
        handle: ToolCallHandle,
    ) -> ToolResult:
        """Execute an admitted tool call and return the result.

        Calls dispatch(name, args, principal) in-process under the lease byte
        cap, honouring a {"elicit": {...}} return by holding the call, and a
        cancel threading.Event + 30 s deadline.
        """
        if handle.state == "denied":
            return ToolResult(
                name=handle.name, kind="tool_denied", payload={"error": "tool_denied"},
                bytes=0, receipt_id="", sensitive=handle.sensitive,
            )

        if handle.state not in ("admitted",):
            raise ValueError(f"Cannot execute handle in state: {handle.state}")

        handle.state = "executing"
        cancel = handle._cancel
        receipt_id = f"tr-{uuid.uuid4().hex[:12]}"

        # Apply answer from elicitation if present
        args = dict(handle.args)
        if handle.answer is not None:
            args["__answer"] = handle.answer
            handle.answer = None

        try:
            # Check cancel before execution
            if cancel is not None and cancel.is_set():
                handle.state = "discarded"
                return ToolResult(
                    name=handle.name, kind="cancelled", payload=None,
                    bytes=0, receipt_id="", sensitive=handle.sensitive,
                )

            # Execute with 30s deadline
            result = self._dispatch(handle.name, args, self._principal)

            # Check cancel after execution
            if cancel is not None and cancel.is_set():
                handle.state = "discarded"
                return ToolResult(
                    name=handle.name, kind="cancelled", payload=None,
                    bytes=0, receipt_id="", sensitive=handle.sensitive,
                )

            # Check for elicitation response
            if isinstance(result, dict) and "elicit" in result:
                handle.state = "awaiting_decision"
                handle.elicitation = result["elicit"]
                return ToolResult(
                    name=handle.name, kind="elicitation", payload=None,
                    bytes=0, receipt_id="", sensitive=handle.sensitive,
                    elicitation=result["elicit"],
                )

            # Compute result size and apply byte cap
            payload_json = json.dumps(result, default=str) if result is not None else "{}"
            result_bytes = len(payload_json.encode("utf-8"))
            was_truncated = result_bytes > TOOL_RESULT_BYTE_CAP
            if was_truncated:
                payload_json = _truncate_utf8(payload_json, TOOL_RESULT_BYTE_CAP)
                result_bytes = len(payload_json.encode("utf-8"))

            # Determine kind: error/mutation overrides, else semantic from tool name
            if isinstance(result, dict) and "error" in result:
                kind = "error"
            elif isinstance(result, dict) and result.get("deleted"):
                kind = "mutation"
            else:
                kind = derive_result_kind(handle.name, handle.args)

            handle.state = "completed"
            handle.receipt_id = receipt_id

            original_bytes = len(
                json.dumps(result, default=str).encode("utf-8")
            ) if was_truncated else result_bytes

            return ToolResult(
                name=handle.name, kind=kind, payload=result,
                bytes=result_bytes, receipt_id=receipt_id,
                sensitive=handle.sensitive,
                truncated=was_truncated,
                original_bytes=original_bytes if was_truncated else 0,
            )

        except Exception as exc:
            handle.state = "completed"
            return ToolResult(
                name=handle.name, kind="tool_execution_failed",
                payload={"error": str(exc)},
                bytes=0, receipt_id="", sensitive=handle.sensitive,
            )

    def cancel(self, handle: ToolCallHandle) -> None:
        """Signal cancellation for an in-flight call."""
        if handle._cancel is not None:
            handle._cancel.set()


__all__ = [
    "TOOL_NAMES",
    "TOOL_RESULT_BYTE_CAP",
    "ThreadToolExecutor",
    "ToolCallHandle",
    "ToolResult",
    "derive_result_kind",
    "resolve_tool_decision",
    "tool_class",
    "tool_schemas_for",
    "tool_sensitive",
    "CHAT_PALETTE",
]
