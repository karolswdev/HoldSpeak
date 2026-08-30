"""Thread orchestration service (HS-151-04, HS-152-01 pass loop).

Ties a user's words to a receipted, streamed assistant message.  The one place
a turn is assembled and admitted, and the one place the People boundary is
enforced at message level (counsel M1).

HS-152-01 adds the pass loop: the model may call the desk's MCP tools
(up to 10 passes); each tool call is resolved through the truth table
(ThreadToolExecutor from thread_tools.py), and the result is injected
into the next pass's payload.
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from typing import Any, Callable, Optional

from ..db.core import Database
from ..db.threads import ThreadRepository
from ..grounding import hydrate_refs_detailed
from ..kernel.inference_runner import InvocationRequest, ServiceContract
from ..kernel.inference_stream import (
    Delta,
    StreamCadence,
    emit_thread_delta,
    emit_thread_status_line,
    emit_thread_tool_pending,
    emit_thread_tool_result,
    emit_thread_turn_done,
    emit_thread_turn_started,
)
from ..kernel.prompt_adapter import StreamingPromptAdapter
from ..principals import Principal, PrincipalKind
from .errors import ServiceError, ValidationError


THREAD_SERVICE_CONTRACT = "holdspeak.thread"
THREAD_SERVICE_SCHEMA_VERSION = "1"

# The literal replacement text for sensitive parts on cloud egress (counsel M1).
_PEOPLE_REDACTION = "[people content withheld]"

# Kinds whose frozen leaves originate from the People store.
_PEOPLE_REF_KINDS = frozenset({"person"})

_UNSET = object()  # sentinel for "caller did not provide parent_id"

# Maximum tool passes for a chat turn (HS-152-01 D1).
_CHAT_PASS_CAP = 10

# Per-tool execution deadline in seconds (HS-152-01 M5).
_TOOL_DEADLINE_S = 30.0


class _ToolExecutorAggregator:
    """Class-level view across concurrent per-turn tool executors.

    The ``/decide`` route (HS-152-02) accesses ``svc._tool_executor``
    and looks up handles by ``call_id``; this aggregator merges handles
    from all active executors so concurrent turns coexist.
    """

    def __init__(self) -> None:
        self._executors: dict[str, Any] = {}  # assistant_msg_id -> executor

    @property
    def _handles(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for ex in self._executors.values():
            merged.update(ex._handles)
        return merged

    def decide(self, handle: Any, decision: str, answer: Any = None) -> None:
        for ex in self._executors.values():
            if handle.call_id in ex._handles:
                ex.decide(handle, decision, answer)
                return
        raise ValueError(f"No active executor for call {handle.call_id}")

    def register(self, msg_id: str, executor: Any) -> None:
        self._executors[msg_id] = executor

    def unregister(self, msg_id: str) -> None:
        self._executors.pop(msg_id, None)


class ThreadService:
    """Orchestrate desk chat threads: CRUD, turn, branch, regenerate, keep, abort."""

    # Class-level shared dict: every ThreadService instance (the route
    # factory creates one per request) sees the same active turns so
    # POST /abort can cancel a turn started by POST /turns.
    _active_turns: dict[str, threading.Event] = {}

    # Class-level aggregator for the /decide route (HS-152-02).
    _tool_executor: _ToolExecutorAggregator = _ToolExecutorAggregator()

    def __init__(
        self,
        db: Database,
        *,
        broadcast: Callable[[str, Any], None],
        broker: Any = None,
        tool_dispatch_fn: Callable[..., Any] | None = None,
        control_mode_fn: Callable[[], str] | None = None,
    ) -> None:
        self._db = db
        self._broadcast = broadcast
        self._broker = broker
        self._tool_dispatch_fn = tool_dispatch_fn
        self._control_mode_fn = control_mode_fn or (lambda: "yolo")

    @property
    def _threads(self) -> ThreadRepository:
        return self._db.threads

    def _palette_for(self, thread_id: str) -> frozenset[str] | None:
        """Resolve the tool palette for a thread at admission time.

        Returns None when no mode is bound (caller uses CHAT_PALETTE).
        Returns the mode's allow-list intersected with TOOL_NAMES when bound.
        Draft (empty allow-list) returns an empty frozenset -- the caller
        must omit the ``tools`` key entirely so the pass loop runs one
        pass (no tool schemas).

        HS-153-01: ONE helper used by both ``start_turn`` (initial
        payload) and ``_run_streaming_turn`` (per-pass payload).
        A mid-turn PATCH does not change the in-flight palette -- the
        palette is resolved once at admission for the turn.
        """
        from .thread_modes import palette_for
        return palette_for(self._db, thread_id)

    # ── Thread CRUD ─────────────────────────────────────────────────

    def create(
        self,
        *,
        title: str = "",
        recipe_id: str = "",
        seed_refs: list[str] | None = None,
        profile_override: str = "",
    ) -> dict[str, Any]:
        thread = self._threads.create_thread(
            title=title,
            recipe_id=recipe_id,
            profile_override=profile_override,
        )
        if seed_refs:
            self._threads.freeze_refs(
                thread.id, None,
                [{"ref_kind": "seed", "ref_id": ref} for ref in seed_refs],
            )
        return self._thread_dict(thread)

    def list_threads(self, *, limit: int = 100, ref_id: str = "") -> list[dict[str, Any]]:
        return [self._thread_dict(t) for t in self._threads.list(limit=limit, ref_id=ref_id)]

    def get(self, thread_id: str) -> dict[str, Any]:
        thread = self._threads.get(thread_id)
        if thread is None or thread.deleted_at is not None:
            raise ServiceError("thread_not_found", f"Thread {thread_id} not found", context={"status": 404})
        result = self._thread_dict(thread)
        path = self._threads.list_path(thread_id)
        result["messages"] = [self._message_dict(m) for m in path]
        # Build siblings map: message_id -> (n, m).
        siblings_map: dict[str, list[int]] = {}
        for m in path:
            n, total = self._threads.siblings(m.id)
            if total > 1:
                siblings_map[m.id] = [n, total]
        result["siblings"] = siblings_map
        result["refs"] = [self._ref_dict(r) for r in self._threads.get_refs(thread_id)]
        return result

    def patch(
        self,
        thread_id: str,
        *,
        title: Optional[str] = None,
        profile_override: Optional[str] = None,
        recipe_id: Optional[str] = None,
    ) -> dict[str, Any]:
        # HS-153-01: validate recipe_id -- empty string unbinds; non-empty
        # must reference a kind='mode' recipe (400 otherwise).
        if recipe_id is not None and recipe_id != "":
            recipe = self._db.recipes.get(recipe_id)
            if recipe is None:
                raise ValidationError(
                    f"Unknown recipe: {recipe_id}",
                    code="recipe_not_found",
                    context={"status": 400},
                )
            if recipe.kind != "mode":
                raise ValidationError(
                    f"Recipe {recipe_id} is not a mode (kind={recipe.kind!r})",
                    code="recipe_not_mode",
                    context={"status": 400},
                )
        thread = self._threads.patch(
            thread_id,
            title=title,
            profile_override=profile_override,
            recipe_id=recipe_id,
        )
        if thread is None:
            raise ServiceError("thread_not_found", f"Thread {thread_id} not found", context={"status": 404})
        return self._thread_dict(thread)

    def soft_delete(self, thread_id: str) -> bool:
        return self._threads.soft_delete(thread_id)

    # ── Turn pipeline ───────────────────────────────────────────────

    async def start_turn(
        self,
        principal: Principal,
        thread_id: str,
        text: str,
        refs: list[str] | None = None,
        parent_id: Any = _UNSET,
    ) -> dict[str, Any]:
        """Persist user message, freeze refs, admit, and start streaming.

        Returns ids immediately; the bus carries started -> deltas -> done.
        When ``parent_id`` is not provided (``_UNSET``), the new message
        auto-chains to the current leaf of the thread.  An explicit ``None``
        creates a root message (used by ``branch`` to create siblings of
        root messages).
        """
        thread = self._threads.get(thread_id)
        if thread is None or thread.deleted_at is not None:
            raise ServiceError("thread_not_found", f"Thread {thread_id} not found", context={"status": 404})

        if not text or not text.strip():
            raise ValidationError("text is required")

        # Auto-chain to the current leaf when no parent is specified.
        if parent_id is _UNSET:
            path = self._threads.list_path(thread_id)
            parent_id = path[-1].id if path else None

        # -- Validate refs BEFORE writing (unknown -> 4xx naming the id, no rows) --
        frozen_ref_rows: list[dict[str, Any]] = []
        if refs:
            # Separate person refs from grounding refs.
            person_refs: list[str] = []
            grounding_refs: list[str] = []
            for ref in refs:
                if ref.startswith("person:"):
                    person_refs.append(ref)
                else:
                    grounding_refs.append(ref)

            # Resolve person refs through the People service (HS-149 law:
            # People content never leaves the encrypted store; the thread
            # gets only the display name as a sensitive frozen leaf).
            for pref in person_refs:
                person_id = pref.split(":", 1)[1] if ":" in pref else pref
                try:
                    from .people_service import PeopleService
                    people = PeopleService(self._db)
                    from ..principals import Principal, PrincipalKind
                    rel = people.get_relationship(
                        Principal(PrincipalKind.OWNER, "owner-session"),
                        person_id,
                    )
                    display_name = str(rel.get("display_name", ""))
                    if not display_name:
                        raise ValidationError(
                            f"Unknown ref ids: {person_id}",
                            code="grounding_not_found",
                            context={"unknown_ids": [person_id]},
                        )
                    frozen_ref_rows.append({
                        "ref_kind": "person",
                        "ref_id": person_id,
                        "frozen_json": json.dumps({
                            "kind": "person",
                            "title": display_name,
                            "subtitle": "",
                            "text": "",
                        }, separators=(",", ":"), sort_keys=True),
                        "sensitive": True,
                    })
                except ValidationError:
                    raise
                except Exception:
                    raise ValidationError(
                        f"Unknown ref ids: {person_id}",
                        code="grounding_not_found",
                        context={"unknown_ids": [person_id]},
                    )

            # Resolve grounding refs through hydrate_refs_detailed.
            if grounding_refs:
                hydration = hydrate_refs_detailed(
                    self._db,
                    meeting_ids=[],
                    artifact_ids=[],
                    expand="summary",
                    qualified_refs=grounding_refs,
                )
                if hydration.unknown:
                    raise ValidationError(
                        f"Unknown ref ids: {', '.join(hydration.unknown)}",
                        code="grounding_not_found",
                        context={"unknown_ids": hydration.unknown},
                    )
                for block in hydration.blocks:
                    frozen_ref_rows.append({
                        "ref_kind": block.kind,
                        "ref_id": block.ref,
                        "frozen_json": json.dumps({
                            "kind": block.kind,
                            "title": block.title,
                            "subtitle": block.subtitle,
                            "text": block.text,
                        }, separators=(",", ":"), sort_keys=True),
                        "sensitive": False,
                    })

        # -- Persist user message --
        user_msg = self._threads.append_message(
            thread_id,
            role="user",
            parent_id=parent_id,
        )
        self._threads.append_part(user_msg.id, kind="text", text=text)

        # -- Freeze refs with sensitive marking --
        if frozen_ref_rows:
            ref_dicts = []
            for fref in frozen_ref_rows:
                ref_dicts.append({
                    "ref_kind": fref["ref_kind"],
                    "ref_id": fref["ref_id"],
                    "frozen_json": fref["frozen_json"],
                })
            self._threads.freeze_refs(thread_id, user_msg.id, ref_dicts)

            # Mark People-sourced leaves sensitive=1 on the user message parts.
            for fref in frozen_ref_rows:
                if fref["sensitive"]:
                    # Add frozen ref content as a sensitive annotation part.
                    frozen = json.loads(fref["frozen_json"])
                    self._threads.append_part(
                        user_msg.id,
                        kind="annotation",
                        text=frozen.get("text", ""),
                        sensitive=True,
                        meta_json=json.dumps({"ref_kind": fref["ref_kind"], "ref_id": fref["ref_id"]}),
                    )

        # -- Admit chat.turn through the adoption service exactly like Ask --
        invocation_id = "chat_turn_" + uuid.uuid4().hex
        capability_id = "chat.turn"

        # Assemble the payload (assembler law).
        payload = self._assemble_payload(thread_id, user_msg.id, thread)

        # HS-152-03 + HS-153-01: the tool palette rides INSIDE the admitted
        # payload.  Resolved once at admission so a mid-turn PATCH does not
        # change the in-flight palette (the "next turn" rule).
        # Draft (empty palette) = no ``tools`` key → one pass, no tools.
        if self._tool_dispatch_fn is not None:
            from .thread_tools import tool_schemas_for, CHAT_PALETTE

            palette = self._palette_for(thread_id)
            effective_palette = palette if palette is not None else CHAT_PALETTE
            if effective_palette:
                payload["tools"] = tool_schemas_for(effective_palette)

        # HS-152-03: the thread's model pick is honored at admission.
        profile_override = str(getattr(thread, "profile_override", "") or "")
        if profile_override:
            await asyncio.to_thread(
                self._apply_profile_override,
                principal,
                invocation_id=invocation_id,
                profile_override=profile_override,
            )

        # Admit through the adoption service.
        admitted = await asyncio.to_thread(
            self._broker.inference_adoption_service.admit,
            principal,
            command_id=f"admit-{invocation_id}",
            capability_id=capability_id,
            operation_id=invocation_id,
            payload=payload,
            invocation_id=invocation_id,
            reserved_output_tokens=512,
        )

        route_plan = admitted["route_plan"]
        # Derive egress_scope from the first route entry's boundary.
        entries = route_plan.get("entries", [])
        egress_scope = str(entries[0].get("boundary", "")) if entries else ""
        if not egress_scope:
            egress_scope = str(route_plan.get("egress_scope", "") or "")
        model_id = str(route_plan.get("model_id", "") or "")
        if not model_id and entries:
            model_id = str(entries[0].get("profile_id", "") or "")

        # -- Commit assistant row with streaming=1 --
        assistant_msg = self._threads.append_message(
            thread_id,
            role="assistant",
            parent_id=user_msg.id,
            operation_id=invocation_id,
            invocation_id=invocation_id,
            egress_scope=egress_scope,
            model_id=model_id,
            route_plan_id=str(route_plan.get("id", "")),
        )
        self._threads.mark_streaming(assistant_msg.id)

        # -- Broadcast thread_turn_started --
        emit_thread_turn_started(
            self._broadcast,
            thread_id=thread_id,
            message_id=assistant_msg.id,
            user_message_id=user_msg.id,
            model_id=model_id,
            egress=egress_scope,
        )

        # -- Run streaming turn in a daemon thread --
        cancel_event = threading.Event()
        self._active_turns[assistant_msg.id] = cancel_event

        adapter = StreamingPromptAdapter(external_cancel=cancel_event)

        bg = threading.Thread(
            target=self._run_streaming_turn,
            kwargs=dict(
                principal=principal,
                admitted=admitted,
                adapter=adapter,
                thread_id=thread_id,
                assistant_msg_id=assistant_msg.id,
                cancel_event=cancel_event,
                egress_scope=egress_scope,
                payload=payload,
                turn_operation_id=invocation_id,
                profile_override=profile_override,
            ),
            daemon=True,
        )
        bg.start()

        return {
            "thread_id": thread_id,
            "user_message_id": user_msg.id,
            "assistant_message_id": assistant_msg.id,
        }

    def _run_streaming_turn(
        self,
        *,
        principal: Principal,
        admitted: dict[str, Any],
        adapter: Any,
        thread_id: str,
        assistant_msg_id: str,
        cancel_event: threading.Event,
        egress_scope: str,
        payload: dict[str, Any],
        turn_operation_id: str = "",
        profile_override: str = "",
    ) -> None:
        """Sync function that runs in a background thread.

        Uses ``execute_stream`` on the adoption service which calls
        ``InferenceRunner.invoke_stream`` internally.  Each text delta is
        emitted as a ``thread_delta`` frame (frame-per-delta for text);
        persistence uses ``StreamCadence`` (flush every 500 chars or 2 s).

        HS-152-01: when a tool executor is available the method runs a
        pass loop (up to ``_CHAT_PASS_CAP`` passes).  Each pass streams
        via ``execute_stream`` with ``tools`` in the payload.  When the
        model emits ``tool_calls``, each call is resolved through the
        executor, persisted, and the result is injected into the next
        pass's payload.  When no ``tool_calls`` arrive, the text is the
        answer and the turn is done.
        """
        # -- Compose the per-turn tool executor if the dispatch seam is wired --
        # HS-153-01: the palette is resolved from the payload, which was
        # frozen at admission (start_turn).  Draft = no tools key = no
        # executor (one pass, text only).
        tool_executor: Any = None
        tool_schemas: list[dict[str, Any]] = []
        if self._tool_dispatch_fn is not None and "tools" in payload:
            from .thread_tools import ThreadToolExecutor

            tool_executor = ThreadToolExecutor(
                self._db,
                dispatch_fn=self._tool_dispatch_fn,
                principal=principal,
                control_mode_fn=self._control_mode_fn,
                broker=self._broker,
            )
            tool_schemas = list(payload["tools"])
            ThreadService._tool_executor.register(assistant_msg_id, tool_executor)

        max_passes = _CHAT_PASS_CAP if tool_executor is not None else 1

        cadence = StreamCadence()
        seq = 0
        part_id: str | None = None
        stats: dict[str, Any] = {}
        outcome = "succeeded"
        receipt_id = ""
        error_code = ""

        # D3 hook: sensitive text accumulator across passes (counsel M1).
        sensitive_texts: list[str] = list(payload.get("_sensitive_texts", []))

        # OpenAI-format messages accumulated across passes for tool exchange.
        tool_exchange_messages: list[dict[str, Any]] = []

        current_execution_id = admitted["execution"]["id"]

        # Per-pass list of tool calls captured from tool_calls deltas.
        tool_calls_this_pass: list[dict[str, Any]] = []

        # Decision events for held tool calls (HS-152-01 M5).
        decision_events: dict[str, threading.Event] = {}

        if tool_executor is not None:
            def _on_decided(call_id: str) -> None:
                ev = decision_events.get(call_id)
                if ev is not None:
                    ev.set()
            tool_executor.on_decided = _on_decided

        def on_delta(delta: Delta) -> None:
            nonlocal seq, part_id, stats
            if cancel_event.is_set():
                return

            if delta.kind == "text":
                if part_id is None:
                    part = self._threads.append_part(assistant_msg_id, kind="text", text="")
                    part_id = part.id
                should_flush = cadence.feed(delta.text)
                if should_flush:
                    pending = cadence.pending
                    self._threads.extend_part_text(part_id, pending)
                    cadence.mark_flushed()
                # Frame-per-delta for text: every token gets a frame.
                emit_thread_delta(
                    self._broadcast,
                    thread_id=thread_id,
                    message_id=assistant_msg_id,
                    ordinal=0,
                    kind="text",
                    text=delta.text,
                    seq=seq,
                )
                seq += 1

            elif delta.kind == "reasoning":
                emit_thread_delta(
                    self._broadcast,
                    thread_id=thread_id,
                    message_id=assistant_msg_id,
                    ordinal=1,
                    kind="reasoning",
                    text=delta.text,
                    seq=seq,
                )
                seq += 1

            elif delta.kind == "tool_calls":
                tool_calls_this_pass.extend(delta.meta.get("tool_calls", []))

            elif delta.kind == "usage":
                stats = dict(delta.meta)

            elif delta.kind == "error":
                stats["error"] = delta.text

        try:
            for pass_num in range(max_passes + 1):
                # -- Cap check: 11th tool request --
                if pass_num == max_passes:
                    error_code = "pass_cap_reached"
                    outcome = "failed"
                    stats.setdefault("error", f"Tool pass cap reached (max {max_passes})")
                    break

                # -- Abort check (M5) --
                if cancel_event.is_set():
                    outcome = "aborted"
                    break

                # -- Build payload for this pass --
                pass_payload = dict(payload)
                if tool_exchange_messages:
                    msgs = list(pass_payload.get("messages", []))
                    msgs.extend(tool_exchange_messages)
                    pass_payload["messages"] = msgs

                # Inject tool schemas
                if tool_schemas:
                    pass_payload["tools"] = tool_schemas

                # Inject sensitive texts for M1 redactor (D3 accumulator)
                if sensitive_texts:
                    pass_payload["_sensitive_texts"] = list(sensitive_texts)

                # -- For pass > 0: re-admit with the updated payload --
                if pass_num > 0:
                    try:
                        new_inv = f"chat_turn_{uuid.uuid4().hex}"
                        if profile_override:
                            self._apply_profile_override(
                                principal,
                                invocation_id=new_inv,
                                profile_override=profile_override,
                            )
                        new_admitted = self._broker.inference_adoption_service.admit(
                            principal,
                            command_id=f"admit-{new_inv}",
                            capability_id="chat.turn",
                            operation_id=new_inv,
                            payload=pass_payload,
                            invocation_id=new_inv,
                            reserved_output_tokens=512,
                        )
                        current_execution_id = new_admitted["execution"]["id"]
                    except Exception as exc:
                        outcome = "failed"
                        stats["error"] = f"Re-admission failed: {exc}"
                        error_code = "execute_stream_failed"
                        break

                    emit_thread_status_line(
                        self._broadcast,
                        thread_id=thread_id,
                        text=f"Processing (pass {pass_num + 1})...",
                    )

                # -- Reset per-pass state --
                tool_calls_this_pass.clear()

                # -- Stream this pass --
                routed = self._broker.inference_adoption_service.execute_stream(
                    principal,
                    execution_id=current_execution_id,
                    adapter=adapter,
                    on_delta=on_delta,
                    publish=None,
                    payload_redactor=self._m1_redactor,
                )

                # -- No tool calls: text answer, done --
                if not tool_calls_this_pass:
                    outcome = str(routed.get("outcome", "failed"))
                    receipt = routed.get("receipt", {})
                    receipt_id = str(
                        receipt.get("execution_id", "")
                        or receipt.get("id", "")
                        or ""
                    )
                    routed_error = str(routed.get("error", "") or "")
                    if outcome == "failed" and routed_error and not stats.get("error"):
                        stats["error"] = routed_error
                    break

                # -- Tool calls: resolve each through the executor --
                if tool_executor is None:
                    # Safety: tool_calls received but no executor.
                    break

                assistant_tc_openai: list[dict[str, Any]] = []
                new_tool_msgs: list[dict[str, Any]] = []

                for tc in tool_calls_this_pass:
                    call_id = str(tc.get("id", ""))
                    name = str(tc.get("name", ""))
                    args_str = str(tc.get("arguments", "{}"))
                    args_head = args_str[:80]

                    # -- Admit through the executor --
                    tc_dict = {"id": call_id, "name": name, "arguments": args_str}
                    try:
                        handle = tool_executor.admit(
                            turn_operation_id, thread_id, tc_dict,
                        )
                    except ValueError:
                        # Unknown tool (fail-closed classification)
                        self._threads.append_part(
                            assistant_msg_id, kind="tool_call",
                            tool_call_id=call_id,
                            meta_json=json.dumps(
                                {"id": call_id, "name": name, "arguments": args_str,
                                 "class": "unknown", "state": "error"},
                                separators=(",", ":")),
                        )
                        err_text = json.dumps({"error": "tool_unknown", "name": name})
                        tool_msg = self._threads.append_message(
                            thread_id, role="tool", parent_id=assistant_msg_id,
                        )
                        self._threads.append_part(
                            tool_msg.id, kind="text", text=err_text,
                            tool_call_id=call_id,
                        )
                        assistant_tc_openai.append({
                            "id": call_id, "type": "function",
                            "function": {"name": name, "arguments": args_str},
                        })
                        new_tool_msgs.append({
                            "role": "tool", "tool_call_id": call_id,
                            "content": err_text,
                        })
                        error_code = "tool_unknown"
                        continue

                    # -- Persist tool_call part on the assistant message --
                    self._threads.append_part(
                        assistant_msg_id, kind="tool_call",
                        tool_call_id=call_id,
                        meta_json=json.dumps(
                            {"id": call_id, "name": name, "arguments": args_str,
                             "class": handle.tool_class, "state": handle.state},
                            separators=(",", ":")),
                    )

                    # -- Emit thread_tool_pending --
                    emit_thread_tool_pending(
                        self._broadcast,
                        thread_id=thread_id,
                        message_id=assistant_msg_id,
                        call_id=call_id,
                        name=name,
                        args_head=args_head,
                        tool_class=handle.tool_class,
                        decision_required=(handle.state == "awaiting_decision"),
                        elicitation=getattr(handle, "elicitation", None),
                    )

                    # -- Resolve: admitted -> execute; held -> wait then execute or deny --
                    result = None

                    if handle.state == "denied":
                        from .thread_tools import ToolResult
                        result = ToolResult(
                            name=name, kind="tool_denied",
                            payload={"error": "tool_denied"},
                            bytes=0, receipt_id="", sensitive=False,
                        )

                    elif handle.state == "awaiting_decision":
                        # Block until decide() is called from /decide route
                        ev = threading.Event()
                        decision_events[call_id] = ev
                        deadline = time.monotonic() + _TOOL_DEADLINE_S
                        while not ev.is_set() and not cancel_event.is_set():
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                break
                            ev.wait(timeout=min(0.1, remaining))
                        decision_events.pop(call_id, None)

                        if cancel_event.is_set():
                            outcome = "aborted"
                            break

                        if not ev.is_set():
                            # Timeout
                            from .thread_tools import ToolResult
                            result = ToolResult(
                                name=name, kind="tool_timeout",
                                payload={"error": "tool_timeout"},
                                bytes=0, receipt_id="", sensitive=False,
                            )
                            error_code = "tool_timeout"
                        elif handle.state == "admitted":
                            pass  # fall through to execute below
                        elif handle.state == "denied":
                            from .thread_tools import ToolResult
                            result = ToolResult(
                                name=name, kind="tool_denied",
                                payload={"error": "tool_denied"},
                                bytes=0, receipt_id="", sensitive=False,
                            )

                    # Execute admitted calls
                    if result is None and handle.state == "admitted":
                        if cancel_event.is_set():
                            outcome = "aborted"
                            break
                        emit_thread_status_line(
                            self._broadcast,
                            thread_id=thread_id,
                            text=f"Running {name}...",
                        )
                        result = tool_executor.execute(handle)
                        # Check cancel after execution (M5: discard in-flight)
                        if cancel_event.is_set():
                            outcome = "aborted"
                            break

                        # HS-152-04: elicitation — the tool returned
                        # {"elicit": {schema, prompt}}; the executor set
                        # handle.state = awaiting_decision and stored the
                        # schema. Re-emit pending with elicitation, wait
                        # for the user's answer, then re-execute.
                        if result is not None and result.kind == "elicitation":
                            emit_thread_tool_pending(
                                self._broadcast,
                                thread_id=thread_id,
                                message_id=assistant_msg_id,
                                call_id=call_id,
                                name=name,
                                args_head=args_head,
                                tool_class=handle.tool_class,
                                decision_required=True,
                                elicitation=result.elicitation,
                            )
                            # Block for user answer
                            ev2 = threading.Event()
                            decision_events[call_id] = ev2
                            deadline2 = time.monotonic() + _TOOL_DEADLINE_S
                            while not ev2.is_set() and not cancel_event.is_set():
                                remaining2 = deadline2 - time.monotonic()
                                if remaining2 <= 0:
                                    break
                                ev2.wait(timeout=min(0.1, remaining2))
                            decision_events.pop(call_id, None)

                            if cancel_event.is_set():
                                outcome = "aborted"
                                break

                            if not ev2.is_set():
                                from .thread_tools import ToolResult as _TR
                                result = _TR(
                                    name=name, kind="tool_timeout",
                                    payload={"error": "tool_timeout"},
                                    bytes=0, receipt_id="", sensitive=False,
                                )
                            elif handle.state == "admitted":
                                # Re-execute with the answer
                                result = tool_executor.execute(handle)
                                if cancel_event.is_set():
                                    outcome = "aborted"
                                    break
                            elif handle.state == "denied":
                                from .thread_tools import ToolResult as _TR
                                result = _TR(
                                    name=name, kind="tool_denied",
                                    payload={"error": "tool_denied"},
                                    bytes=0, receipt_id="", sensitive=False,
                                )

                    if result is None:
                        continue

                    # -- Derive text from result payload --
                    # HS-152-05: apply the byte cap (the executor already
                    # set result.truncated when the raw payload exceeded it)
                    from .thread_tools import TOOL_RESULT_BYTE_CAP, _truncate_utf8
                    result_text = (
                        json.dumps(result.payload, default=str)
                        if result.payload is not None
                        else ""
                    )
                    if result.truncated:
                        result_text = _truncate_utf8(result_text, TOOL_RESULT_BYTE_CAP)

                    # -- Persist tool-role message --
                    tool_msg = self._threads.append_message(
                        thread_id, role="tool", parent_id=assistant_msg_id,
                    )
                    part_meta: dict[str, Any] = {
                        "kind": result.kind,
                        "receipt_id": result.receipt_id,
                    }
                    if result.truncated:
                        part_meta["truncated"] = True
                        part_meta["original_bytes"] = result.original_bytes
                    self._threads.append_part(
                        tool_msg.id, kind="text", text=result_text,
                        tool_call_id=call_id,
                        sensitive=result.sensitive,
                        meta_json=json.dumps(part_meta, separators=(",", ":")),
                    )

                    # -- Emit thread_tool_result --
                    is_error = result.kind in (
                        "tool_execution_failed", "tool_denied",
                        "tool_timeout", "cancelled", "error",
                    )
                    emit_thread_tool_result(
                        self._broadcast,
                        thread_id=thread_id,
                        message_id=assistant_msg_id,
                        call_id=call_id,
                        name=name,
                        receipt_id=result.receipt_id,
                        outcome="failed" if is_error else "succeeded",
                        kind=result.kind,
                        summary=result_text[:200] if result_text else "",
                        sensitive=result.sensitive,
                    )

                    # -- HS-152-05: thread.set_status — broadcast after dispatch --
                    if name == "thread.set_status" and not is_error:
                        status_text = str(handle.args.get("text", ""))
                        emit_thread_status_line(
                            self._broadcast,
                            thread_id=thread_id,
                            text=status_text,
                        )

                    # -- D3 hook: collect sensitive result text --
                    if result.sensitive and result_text:
                        sensitive_texts.append(result_text)

                    # -- Accumulate OpenAI-format messages for next pass --
                    assistant_tc_openai.append({
                        "id": call_id, "type": "function",
                        "function": {"name": name, "arguments": args_str},
                    })
                    if result.kind == "tool_denied":
                        content = json.dumps({"error": "tool_denied"})
                    elif is_error:
                        content = json.dumps({"error": result.kind})
                    else:
                        content = result_text
                    new_tool_msgs.append({
                        "role": "tool", "tool_call_id": call_id,
                        "content": content,
                    })

                # end for tc in tool_calls_this_pass

                if outcome == "aborted":
                    break

                if assistant_tc_openai:
                    tool_exchange_messages.append({
                        "role": "assistant",
                        "tool_calls": assistant_tc_openai,
                    })
                    tool_exchange_messages.extend(new_tool_msgs)

            # end for pass_num

        except Exception as exc:
            outcome = "failed"
            stats["error"] = str(exc)
            from ..logging_config import get_logger
            get_logger("thread_service").warning("pass loop failed: %s", exc)

        # -- Flush any remaining buffered text --
        if part_id is not None and cadence.finish():
            pending = cadence.pending
            self._threads.extend_part_text(part_id, pending)
            cadence.mark_flushed()

        # -- Complete the message --
        stats_json = json.dumps(stats, separators=(",", ":"), sort_keys=True) if stats else ""
        if cancel_event.is_set():
            self._threads.abort_message(assistant_msg_id)
            outcome = "aborted"
            receipt_id = "indeterminate"
        else:
            error_json_str = ""
            if outcome in ("failed", "indeterminate") and (stats.get("error") or error_code):
                error_obj: dict[str, str] = {}
                if error_code:
                    error_obj["code"] = error_code
                if stats.get("error"):
                    error_obj["error"] = str(stats["error"])
                error_json_str = json.dumps(error_obj, separators=(",", ":"))
            self._threads.complete_message(
                assistant_msg_id,
                receipt_id=receipt_id,
                stats_json=stats_json,
                error_json=error_json_str,
            )

        # -- Update token totals --
        token_in = int(stats.get("prompt_tokens", 0))
        token_out = int(stats.get("completion_tokens", 0))
        if token_in or token_out:
            self._threads.add_token_totals(thread_id, token_in=token_in, token_out=token_out)

        # -- HS-152-05: emit persisted status_line before turn_done so the
        #    client clears the transient "Processing..." and falls back to the
        #    correct value. Only when tool calls happened (tool_executor exists).
        if tool_executor is not None:
            try:
                thread_row = self._threads.get(thread_id)
                persisted_status = thread_row.status_line if thread_row else ""
            except Exception:
                persisted_status = ""
            emit_thread_status_line(
                self._broadcast,
                thread_id=thread_id,
                text=persisted_status,
            )

        # -- Broadcast thread_turn_done --
        done_stats = dict(stats)
        if outcome in ("failed", "indeterminate") and (stats.get("error") or error_code):
            done_stats["error"] = {
                "code": error_code or "execute_stream_failed",
                "message": str(stats.get("error", "")),
            }
        emit_thread_turn_done(
            self._broadcast,
            thread_id=thread_id,
            message_id=assistant_msg_id,
            receipt_id=receipt_id,
            outcome=outcome,
            egress=egress_scope,
            stats=done_stats,
        )

        # -- Clean up --
        if tool_executor is not None:
            ThreadService._tool_executor.unregister(assistant_msg_id)
        self._active_turns.pop(assistant_msg_id, None)

    # ── Abort ───────────────────────────────────────────────────────

    def abort(self, thread_id: str) -> dict[str, Any]:
        """Cancel a running turn within 250 ms."""
        # Find any active streaming message for this thread.
        for msg_id, cancel_event in list(self._active_turns.items()):
            msg = self._threads.get_message(msg_id)
            if msg and msg.thread_id == thread_id:
                cancel_event.set()
                return {"aborted": True, "message_id": msg_id}
        return {"aborted": False}

    # ── Branch ──────────────────────────────────────────────────────

    async def branch(
        self,
        principal: Principal,
        thread_id: str,
        message_id: str,
        text: str,
    ) -> dict[str, Any]:
        """Edit-and-resend: create a sibling user message + start a new turn."""
        msg = self._threads.get_message(message_id)
        if msg is None or msg.thread_id != thread_id:
            raise ServiceError("message_not_found", "Message not found", context={"status": 404})
        # The branch's parent_id is the SAME parent as the original message.
        return await self.start_turn(
            principal,
            thread_id,
            text,
            parent_id=msg.parent_id,
        )

    # ── Regenerate ──────────────────────────────────────────────────

    async def regenerate(
        self,
        principal: Principal,
        thread_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Regenerate: create a sibling assistant turn for the same user message."""
        msg = self._threads.get_message(message_id)
        if msg is None or msg.thread_id != thread_id:
            raise ServiceError("message_not_found", "Message not found", context={"status": 404})
        if msg.role != "assistant":
            raise ValidationError("Can only regenerate assistant messages")
        # Get the user message this assistant message is a child of.
        if not msg.parent_id:
            raise ValidationError("Cannot regenerate a root message")
        user_msg = self._threads.get_message(msg.parent_id)
        if user_msg is None:
            raise ServiceError("message_not_found", "Parent user message not found", context={"status": 404})
        # Get the user's text from parts.
        parts = self._threads.get_parts(user_msg.id)
        user_text = ""
        for part in parts:
            if part.kind == "text" and part.text:
                user_text = part.text
                break
        if not user_text:
            raise ValidationError("No user text found to regenerate from")
        # Start a new turn with the same parent as the original user message.
        return await self.start_turn(
            principal,
            thread_id,
            user_text,
            parent_id=user_msg.parent_id,
        )

    # ── Keep ────────────────────────────────────────────────────────

    def keep(
        self,
        principal: Principal,
        thread_id: str,
        message_id: str,
        as_kind: str = "artifact",
    ) -> dict[str, Any]:
        """Keep an assistant message as an artifact or note via the Ask keep path.

        Uses db.plugins.record_artifact directly with provenance
        ``thread:<thread_id>/<message_id>`` — the same persistence as
        AskService.keep but without constructing a full broker.
        """
        msg = self._threads.get_message(message_id)
        if msg is None or msg.thread_id != thread_id:
            raise ServiceError("message_not_found", "Message not found", context={"status": 404})
        parts = self._threads.get_parts(message_id)
        text_parts = [p.text for p in parts if p.kind == "text" and p.text]
        output = "\n".join(text_parts)
        if not output:
            raise ValidationError("No text to keep")

        provenance = f"thread:{thread_id}/{message_id}"
        artifact_id = "artifact_" + uuid.uuid4().hex[:12]
        sources = [{"source_type": "ask", "source_ref": provenance}]
        self._db.plugins.record_artifact(
            artifact_id=artifact_id,
            meeting_id="",
            artifact_type="plugin_output",
            title="Thread",
            body_markdown=output,
            structured_json={
                "lens": "Thread",
                "source": provenance,
                "provenance": {"source_card_title": provenance},
            },
            confidence=1.0,
            status="draft",
            plugin_id="web.desk",
            plugin_version="0",
            sources=sources,
        )
        return {"artifact_id": artifact_id}

    # ── Import ──────────────────────────────────────────────────────

    def import_threads(self, payload: list[dict[str, Any]]) -> dict[str, str]:
        return self._threads.import_threads(payload)

    # ── profile_override → next-run override (HS-152-03) ─────────────

    def _override_entries(self, profile_override: str) -> list[dict[str, Any]]:
        """Resolve a thread's ``profile_override`` to assignment entries.

        A v2 model profile pins its newest revision; a legacy ``profiles``
        row (the hosted / OpenAI-compatible path) pins ``legacy-<id>@1``.
        Unknown ids resolve to nothing -- the assignment stays in charge.
        """
        pid = str(profile_override or "").strip()
        if not pid:
            return []
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT MAX(revision) AS revision FROM model_profile_revisions WHERE profile_id=?",
                (pid,),
            ).fetchone()
            if row is not None and row["revision"] is not None:
                return [{"profile_id": pid, "profile_revision": int(row["revision"])}]
            legacy = conn.execute(
                "SELECT id FROM profiles WHERE id=? AND deleted=0",
                (pid.removeprefix("legacy-"),),
            ).fetchone()
        if legacy is not None:
            return [{"profile_id": "legacy-" + str(legacy["id"]), "profile_revision": 1}]
        return []

    def _apply_profile_override(
        self, principal: Principal, *, invocation_id: str, profile_override: str,
    ) -> None:
        """Honor ``thread.profile_override`` for ONE admission.

        The thread row stores the owner's pick; routing truth stays the
        assignment ledger, so the pick is written as an invocation-scoped
        next-run override right before admit (the Phase 143 mechanism), and
        every pass of a tool turn re-applies it for its own invocation.
        """
        entries = self._override_entries(profile_override)
        if not entries or self._broker is None:
            return
        self._broker.inference_adoption_service.apply_next_run_override(
            principal,
            command_id=f"override-{invocation_id}",
            invocation_id=invocation_id,
            capability_id="chat.turn",
            entries=entries,
        )

    # ── M1 redactor (counsel M1, close counsel M5) ────────────────────

    @staticmethod
    def _m1_redactor(payload: dict[str, Any], route: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive message parts when the frozen route's egress is cloud.

        This is the SINGLE redaction point for the production turn path
        (HS-151-04 M5).  It runs inside ``execute_stream`` after the payload
        is reconstructed from frozen admission evidence and before it reaches
        the engine.  The frozen route plan carries the boundary at this point;
        admission evidence is never altered.

        Why here and not before admit: the egress scope is determined by the
        frozen route plan, which is only known after ``admit()`` returns.
        Why not a separate redaction pass in ThreadService: the payload
        handed to the engine MUST be the admitted payload, so redaction must
        happen at the exact reconstruction-to-dispatch seam.
        """
        entries = route.get("entries", [])
        boundary = str(entries[0].get("boundary", "")) if entries else ""
        # "cloud" is the boundary value that indicates non-local egress.
        # Local boundaries (same_device, local, private_network) keep
        # sensitive data verbatim.
        # The sentinel key is bookkeeping for THIS seam; it never travels
        # to an engine on any boundary (close counsel S2).
        if boundary not in ("cloud", "external_service"):
            return {k: v for k, v in payload.items() if k != "_sensitive_texts"}

        messages = payload.get("messages")
        if not isinstance(messages, list):
            return {k: v for k, v in payload.items() if k != "_sensitive_texts"}

        redacted_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                redacted_messages.append(msg)
                continue
            content = msg.get("content", "")
            # The sensitive annotation parts are embedded in the message
            # content by _assemble_payload.  We redact any message whose
            # content block was marked sensitive by checking the thread
            # parts.  Since the payload is a flat messages list and
            # sensitive parts were concatenated into the content, we
            # must replace the content wholesale.
            #
            # The payload_redactor sees the reconstructed payload dict;
            # it has no access to the DB.  Sensitive annotations were
            # concatenated into user-message content by _assemble_payload.
            # We apply a text-level search-and-replace: any content block
            # that appears in the messages is left alone unless the caller
            # has embedded the sentinel metadata.
            #
            # Since we do not have DB access here, the honest approach is
            # to carry a `_sensitive_texts` list in the payload at assembly
            # time.  This list is consumed by the redactor and removed
            # before dispatch.
            redacted_messages.append(msg)

        # Check for the _sensitive_texts annotation set by _assemble_payload.
        sensitive_texts = payload.get("_sensitive_texts", [])
        if sensitive_texts:
            for i, msg in enumerate(redacted_messages):
                if not isinstance(msg, dict):
                    continue
                content = str(msg.get("content", ""))
                for st in sensitive_texts:
                    if st and st in content:
                        content = content.replace(st, _PEOPLE_REDACTION)
                redacted_messages[i] = {**msg, "content": content}

        result = {**payload, "messages": redacted_messages}
        result.pop("_sensitive_texts", None)
        return result

    # ── Assembler (counsel M1) ──────────────────────────────────────

    def _assemble_payload(
        self,
        thread_id: str,
        user_msg_id: str,
        thread: Any,
    ) -> dict[str, Any]:
        """Build the inference payload from the thread's message path.

        Assembler law: context = recipe/system prompt + leaf-path messages
        after the last compaction cut + frozen ref leaves.  Any part with
        sensitive=1 is redacted when the egress scope is cloud.
        """
        # Get the system prompt from the recipe, if any.
        system_prompt = "You are the desk's AI core. Be concrete and brief."
        if thread.recipe_id:
            try:
                recipe = self._db.recipes.get(thread.recipe_id)
                if recipe and hasattr(recipe, "system_prompt") and recipe.system_prompt:
                    system_prompt = recipe.system_prompt
            except Exception:
                pass

        # Build messages from the leaf path.
        path = self._threads.list_path(thread_id)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Gather frozen refs for context.
        refs = self._threads.get_refs(thread_id)
        ref_context_parts: list[str] = []
        person_names: list[str] = []
        for ref in refs:
            if ref.ref_kind == "person" and ref.frozen_json:
                # Person refs: title-only context line (HS-149 law).
                try:
                    frozen = json.loads(ref.frozen_json)
                    name = frozen.get("title", "")
                    if name:
                        person_names.append(name)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif ref.frozen_json:
                try:
                    frozen = json.loads(ref.frozen_json)
                    ref_text = frozen.get("text", "")
                    if ref_text:
                        ref_context_parts.append(
                            f"[{frozen.get('kind', 'ref').upper()}: {frozen.get('title', ref.ref_id)}]\n{ref_text}"
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

        if ref_context_parts:
            messages.append({"role": "system", "content": "\n\n".join(ref_context_parts)})

        # Person context: one sensitive line per person (title only).
        if person_names:
            person_line = "Person in this thread: " + ", ".join(person_names)
            messages.append({"role": "system", "content": person_line})

        sensitive_texts: list[str] = []
        for msg in path:
            parts = self._threads.get_parts(msg.id)
            text_parts = []
            for part in parts:
                if part.kind in ("text", "annotation") and part.text:
                    text_parts.append(part.text)
                    if part.sensitive and part.text:
                        sensitive_texts.append(part.text)
            content = "\n".join(text_parts)
            if content:
                messages.append({"role": msg.role, "content": content})

        # Person names are sensitive (redacted on cloud egress).
        if person_names:
            person_line = "Person in this thread: " + ", ".join(person_names)
            sensitive_texts.append(person_line)
            for name in person_names:
                sensitive_texts.append(name)

        # Also check frozen refs for People-sourced leaves.
        for ref in refs:
            if ref.ref_kind in _PEOPLE_REF_KINDS and ref.frozen_json:
                try:
                    frozen = json.loads(ref.frozen_json)
                    ref_text = frozen.get("text", "")
                    if ref_text:
                        sensitive_texts.append(ref_text)
                except (json.JSONDecodeError, TypeError):
                    pass

        result: dict[str, Any] = {
            "messages": messages,
            "temperature": None,
            "max_tokens": None,
        }
        # Carry the sensitive-text list for the M1 redactor. This key is
        # consumed by _m1_redactor and stripped before dispatch.
        if sensitive_texts:
            result["_sensitive_texts"] = sensitive_texts
        return result

    def assemble_payload_for_egress(
        self,
        thread_id: str,
        user_msg_id: str,
        thread: Any,
        egress_scope: str,
    ) -> dict[str, Any]:
        """Build payload with M1 redaction applied based on egress scope.

        Convenience wrapper: assembles the payload, then applies
        ``_m1_redactor`` with a synthetic route whose boundary matches
        *egress_scope*.  Used by the metal walk (LEG 2) and unit pins.
        """
        payload = self._assemble_payload(thread_id, user_msg_id, thread)
        synthetic_route = {"entries": [{"boundary": egress_scope}]}
        return self._m1_redactor(payload, synthetic_route)

    # ── Helpers ──────────────────────────────────────────────────────

    def _thread_dict(self, thread: Any) -> dict[str, Any]:
        # HS-153-01: resolve the mode for GET responses.
        from .thread_modes import mode_for_thread
        mode = mode_for_thread(self._db, thread.id)
        mode_dict = (
            {"id": mode.id, "name": mode.name, "avatar": mode.avatar}
            if mode is not None else None
        )
        return {
            "id": thread.id,
            "title": thread.title,
            "recipe_id": thread.recipe_id,
            "profile_override": thread.profile_override,
            "directory_id": thread.directory_id,
            "token_in": thread.token_in,
            "token_out": thread.token_out,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at,
            "last_turn_at": thread.last_turn_at,
            "mode": mode_dict,
        }

    def _message_dict(self, msg: Any) -> dict[str, Any]:
        parts = self._threads.get_parts(msg.id)
        # Parse error_json / stats_json from DB strings to dicts for the wire.
        error_json = None
        if msg.error_json:
            try:
                error_json = json.loads(msg.error_json)
            except (json.JSONDecodeError, TypeError):
                error_json = {"error": str(msg.error_json)}
        stats_json = None
        if msg.stats_json:
            try:
                stats_json = json.loads(msg.stats_json)
            except (json.JSONDecodeError, TypeError):
                stats_json = None
        return {
            "id": msg.id,
            "role": msg.role,
            "parent_id": msg.parent_id,
            "streaming": msg.streaming,
            "receipt_id": msg.receipt_id,
            "egress_scope": msg.egress_scope,
            "model_id": msg.model_id,
            "error_json": error_json,
            "stats_json": stats_json,
            "parts": [
                {
                    "id": p.id,
                    "kind": p.kind,
                    "text": p.text,
                    "ordinal": p.ordinal,
                    "sensitive": p.sensitive,
                    **({"meta_json": json.loads(p.meta_json)}
                       if p.meta_json else {}),
                    **({"tool_call_id": p.tool_call_id}
                       if p.tool_call_id else {}),
                }
                for p in parts
            ],
            "created_at": msg.created_at,
            "updated_at": msg.updated_at,
            "completed_at": msg.completed_at,
            "aborted_at": msg.aborted_at,
        }

    def _ref_dict(self, ref: Any) -> dict[str, Any]:
        return {
            "id": ref.id,
            "ref_kind": ref.ref_kind,
            "ref_id": ref.ref_id,
            "frozen_json": ref.frozen_json,
            "created_at": ref.created_at,
        }
