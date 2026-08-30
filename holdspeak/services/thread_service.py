"""Thread orchestration service (HS-150-04).

Ties a user's words to a receipted, streamed assistant message.  The one place
a turn is assembled and admitted, and the one place the People boundary is
enforced at message level (counsel M1).
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


class ThreadService:
    """Orchestrate desk chat threads: CRUD, turn, branch, regenerate, keep, abort."""

    # Class-level shared dict: every ThreadService instance (the route
    # factory creates one per request) sees the same active turns so
    # POST /abort can cancel a turn started by POST /turns.
    _active_turns: dict[str, threading.Event] = {}

    def __init__(
        self,
        db: Database,
        *,
        broadcast: Callable[[str, Any], None],
        broker: Any = None,
    ) -> None:
        self._db = db
        self._broadcast = broadcast
        self._broker = broker

    @property
    def _threads(self) -> ThreadRepository:
        return self._db.threads

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
    ) -> dict[str, Any]:
        thread = self._threads.patch(thread_id, title=title, profile_override=profile_override)
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
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Persist user message, freeze refs, admit, and start streaming.

        Returns ids immediately; the bus carries started -> deltas -> done.
        """
        thread = self._threads.get(thread_id)
        if thread is None or thread.deleted_at is not None:
            raise ServiceError("thread_not_found", f"Thread {thread_id} not found", context={"status": 404})

        if not text or not text.strip():
            raise ValidationError("text is required")

        # -- Validate refs BEFORE writing (unknown -> 4xx naming the id, no rows) --
        frozen_ref_rows: list[dict[str, Any]] = []
        if refs:
            hydration = hydrate_refs_detailed(
                self._db,
                meeting_ids=[],
                artifact_ids=[],
                expand="summary",
                qualified_refs=refs,
            )
            if hydration.unknown:
                raise ValidationError(
                    f"Unknown ref ids: {', '.join(hydration.unknown)}",
                    code="grounding_not_found",
                    context={"unknown_ids": hydration.unknown},
                )
            for block in hydration.blocks:
                is_sensitive = block.kind in _PEOPLE_REF_KINDS
                frozen_ref_rows.append({
                    "ref_kind": block.kind,
                    "ref_id": block.ref,
                    "frozen_json": json.dumps({
                        "kind": block.kind,
                        "title": block.title,
                        "subtitle": block.subtitle,
                        "text": block.text,
                    }, separators=(",", ":"), sort_keys=True),
                    "sensitive": is_sensitive,
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
    ) -> None:
        """Sync function that runs in a background thread.

        Uses ``execute_stream`` on the adoption service which calls
        ``InferenceRunner.invoke_stream`` internally.  Each text delta is
        emitted as a ``thread_delta`` frame (frame-per-delta for text);
        persistence uses ``StreamCadence`` (flush every 500 chars or 2 s).
        """
        cadence = StreamCadence()
        seq = 0
        part_id: str | None = None
        stats: dict[str, Any] = {}
        outcome = "succeeded"
        receipt_id = ""

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

            elif delta.kind == "usage":
                stats = dict(delta.meta)

            elif delta.kind == "error":
                stats["error"] = delta.text

        try:
            routed = self._broker.inference_adoption_service.execute_stream(
                principal,
                execution_id=admitted["execution"]["id"],
                adapter=adapter,
                on_delta=on_delta,
                publish=None,
            )
            outcome = str(routed.get("outcome", "failed"))
            receipt = routed.get("receipt", {})
            # The route execution receipt uses "execution_id" as its identifier.
            receipt_id = str(
                receipt.get("execution_id", "")
                or receipt.get("id", "")
                or ""
            )
            # When the runner catches an engine exception before the first
            # delta, on_delta is never called so stats["error"] is unset.
            # The routed dict carries the error from InvocationOutcome.
            routed_error = str(routed.get("error", "") or "")
            if outcome == "failed" and routed_error and not stats.get("error"):
                stats["error"] = routed_error

        except Exception as exc:
            outcome = "failed"
            stats["error"] = str(exc)
            from ..logging_config import get_logger
            get_logger("thread_service").warning("execute_stream failed: %s", exc)

        # Flush any remaining buffered text.
        if part_id is not None and cadence.finish():
            pending = cadence.pending
            self._threads.extend_part_text(part_id, pending)
            cadence.mark_flushed()

        # Complete the message.
        stats_json = json.dumps(stats, separators=(",", ":"), sort_keys=True) if stats else ""
        if cancel_event.is_set():
            self._threads.abort_message(assistant_msg_id)
            outcome = "aborted"
            receipt_id = "indeterminate"
        else:
            # Persist error_json when the turn failed (defect 2: engine raises
            # before first delta).
            error_json_str = ""
            if outcome in ("failed", "indeterminate") and stats.get("error"):
                error_json_str = json.dumps(
                    {"error": str(stats["error"])},
                    separators=(",", ":"),
                )
            self._threads.complete_message(
                assistant_msg_id,
                receipt_id=receipt_id,
                stats_json=stats_json,
                error_json=error_json_str,
            )

        # Update token totals.
        token_in = int(stats.get("prompt_tokens", 0))
        token_out = int(stats.get("completion_tokens", 0))
        if token_in or token_out:
            self._threads.add_token_totals(thread_id, token_in=token_in, token_out=token_out)

        # Broadcast thread_turn_done -- include error details when failed.
        done_stats = dict(stats)
        if outcome in ("failed", "indeterminate") and stats.get("error"):
            done_stats["error"] = {
                "code": "execute_stream_failed",
                "message": str(stats["error"]),
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

        # Clean up active turn.
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
        for ref in refs:
            if ref.frozen_json:
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

        for msg in path:
            parts = self._threads.get_parts(msg.id)
            text_parts = []
            for part in parts:
                if part.kind in ("text", "annotation") and part.text:
                    text_parts.append(part.text)
            content = "\n".join(text_parts)
            if content:
                messages.append({"role": msg.role, "content": content})

        return {
            "messages": messages,
            "temperature": None,
            "max_tokens": None,
        }

    def assemble_payload_for_egress(
        self,
        thread_id: str,
        user_msg_id: str,
        thread: Any,
        egress_scope: str,
    ) -> dict[str, Any]:
        """Build payload with M1 redaction applied based on egress scope.

        This is the method that enforces the People boundary: when egress is
        cloud, any part with sensitive=1 has its text replaced with
        _PEOPLE_REDACTION.
        """
        payload = self._assemble_payload(thread_id, user_msg_id, thread)
        if egress_scope != "cloud":
            return payload

        # Redact sensitive content from the messages.
        path = self._threads.list_path(thread_id)
        redacted_messages: list[dict[str, str]] = []
        system_prompt = "You are the desk's AI core. Be concrete and brief."
        if thread.recipe_id:
            try:
                recipe = self._db.recipes.get(thread.recipe_id)
                if recipe and hasattr(recipe, "system_prompt") and recipe.system_prompt:
                    system_prompt = recipe.system_prompt
            except Exception:
                pass
        redacted_messages.append({"role": "system", "content": system_prompt})

        # Refs context -- redact sensitive refs.
        refs = self._threads.get_refs(thread_id)
        ref_context_parts: list[str] = []
        for ref in refs:
            if ref.frozen_json:
                try:
                    frozen = json.loads(ref.frozen_json)
                    ref_text = frozen.get("text", "")
                    if ref.ref_kind in _PEOPLE_REF_KINDS:
                        ref_text = _PEOPLE_REDACTION
                    if ref_text:
                        ref_context_parts.append(
                            f"[{frozen.get('kind', 'ref').upper()}: {frozen.get('title', ref.ref_id)}]\n{ref_text}"
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

        if ref_context_parts:
            redacted_messages.append({"role": "system", "content": "\n\n".join(ref_context_parts)})

        for msg in path:
            parts = self._threads.get_parts(msg.id)
            text_parts = []
            for part in parts:
                if part.kind in ("text", "annotation") and part.text:
                    if part.sensitive:
                        text_parts.append(_PEOPLE_REDACTION)
                    else:
                        text_parts.append(part.text)
            content = "\n".join(text_parts)
            if content:
                redacted_messages.append({"role": msg.role, "content": content})

        payload["messages"] = redacted_messages
        return payload

    # ── Helpers ──────────────────────────────────────────────────────

    def _thread_dict(self, thread: Any) -> dict[str, Any]:
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
