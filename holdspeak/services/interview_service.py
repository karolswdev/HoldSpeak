"""Durable, revision-checked control state for the existing LLM Thread loop.

Domain services continue to own Projects, decisions, schedules, and artifacts.
This service owns interview context and candidate suggestions, never execution
authority. Commands are atomic and replay-safe across services/process restarts.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from ..principals import Principal, PrincipalKind
from .errors import ServiceError, ValidationError
from .interview_contracts import (
    CONTROL_TOOLS, DESCRIPTOR_VERSION, INTERVIEW_MODE_ID, SECTION_BY_ID, SECTIONS,
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _text(value: Any, field: str, maximum: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValidationError(f"{field} must contain 1–{maximum} characters")
    return value.strip()


class InterviewService:
    def __init__(self, db: Any) -> None:
        self._db = db

    @staticmethod
    def require_owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_required", "Interview context requires the owner", context={"status": 403})

    def _thread(self, thread_id: str) -> Any:
        thread = self._db.threads.get(thread_id)
        if not thread or thread.deleted_at:
            raise ServiceError("thread_not_found", "Thread not found", context={"status": 404})
        if thread.recipe_id != INTERVIEW_MODE_ID:
            raise ServiceError("interview_mode_required", "Select Interview mode", context={"status": 409})
        return thread

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {"section": "goals", "status": "exploring", "facts": {}, "suggestions": {}, "setup_session_id": None}

    def get(self, thread_id: str) -> dict[str, Any]:
        self._thread(thread_id)
        with self._db._connection() as conn:
            row = conn.execute("SELECT revision, state_json, updated_at FROM interview_sessions WHERE thread_id=?", (thread_id,)).fetchone()
            state = json.loads(row["state_json"]) if row else self._empty()
            self._prune_unavailable_facts(conn, thread_id, state)
        return {
            "thread_id": thread_id, "revision": row["revision"] if row else 0,
            "descriptor_version": DESCRIPTOR_VERSION,
            "updated_at": row["updated_at"] if row else None,
            **state,
            "sections": [{"id": s.id, "name": s.name, "handoff": s.handoff} for s in SECTIONS],
        }

    @staticmethod
    def _prune_unavailable_facts(conn: Any, thread_id: str, state: dict[str, Any]) -> None:
        """Recheck disclosure before projecting or using saved source excerpts."""
        available = {}
        for fact_id, fact in state["facts"].items():
            parts = conn.execute(
                "SELECT p.text FROM thread_messages m JOIN thread_message_parts p ON p.message_id=m.id "
                "WHERE m.id=? AND m.thread_id=? AND m.role='user' AND m.deleted_at IS NULL "
                "AND p.kind='text' AND p.sensitive=0 AND p.draft=0",
                (fact["source_message_id"], thread_id),
            ).fetchall()
            if any(fact["quote"] in (part["text"] or "") for part in parts):
                available[fact_id] = fact
        state["facts"] = available
        state["suggestions"] = {key: value for key, value in state["suggestions"].items() if all(fact_id in available for fact_id in value["fact_ids"])}

    def palette(self, thread_id: str) -> frozenset[str]:
        from ..mcp.tools import TOOLS
        available = {tool["name"] for tool in TOOLS}
        state = self.get(thread_id)
        section = SECTION_BY_ID[state["section"]]
        domain_tools = section.tools
        controls = CONTROL_TOOLS
        if state["status"] == "drafting":
            domain_tools = frozenset(name for name in domain_tools if not name.startswith("project.setup."))
            controls = frozenset({"interview.get"})
        return (controls | domain_tools) & available

    def context(self, thread_id: str, user_message_id: str) -> dict[str, Any]:
        from ..mcp.tools import TOOLS
        state = self.get(thread_id)
        state.pop("sections")
        facts = sorted(state["facts"].values(), key=lambda f: (f["section"] in {state["section"], "goals"}, f["updated_at"]), reverse=True)
        state["fact_index"] = [{"id": f["id"], "section": f["section"], "text_head": f["text"][:80]} for f in facts]
        selected = facts[:8]
        state["facts"] = {f["id"]: {**f, "text": f["text"][:500], "quote": f["quote"][:200], "details_truncated": len(f["text"]) > 500 or len(f["quote"]) > 200} for f in selected}
        suggestions = list(state["suggestions"].values())
        state["suggestion_choices"] = [{"id": s["id"], "title": s["title"][:100], "disposition": s["disposition"]} for s in suggestions]
        relevant = [s for s in suggestions if s["section"] == state["section"] and s["disposition"] in {"proposed", "try"}][:3]
        state["suggestions"] = {s["id"]: {key: value[:400] if isinstance(value, str) else value for key, value in s.items()} for s in relevant}
        state["coverage"] = {"facts_total": len(facts), "facts_in_detail": len(selected), "suggestions_total": len(suggestions), "suggestions_in_detail": len(relevant)}
        state["user_message_id"] = user_message_id
        state["purpose"] = SECTION_BY_ID[state["section"]].purpose
        state["capabilities"] = sorted(self.palette(thread_id))
        # Stable catalog evidence; changing registration or descriptors changes it.
        schemas = {tool["name"]: tool["inputSchema"] for tool in TOOLS if tool["name"] in state["capabilities"]}
        state["catalog_digest"] = hashlib.sha256(_json({"version": DESCRIPTOR_VERSION, "schemas": schemas}).encode()).hexdigest()
        return state

    def command(
        self, principal: Principal, thread_id: str, *, command_id: str,
        expected_revision: int, event: dict[str, Any],
    ) -> dict[str, Any]:
        self.require_owner(principal)
        self._thread(thread_id)
        command_id = _text(command_id, "command_id", 128)
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValidationError("expected_revision must be a nonnegative integer")
        if not isinstance(event, dict) or len(_json(event)) > 16000:
            raise ValidationError("Invalid interview event")
        digest = hashlib.sha256(_json(event).encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            live = conn.execute("SELECT recipe_id,deleted_at FROM threads WHERE id=?", (thread_id,)).fetchone()
            if not live or live["deleted_at"] is not None or live["recipe_id"] != INTERVIEW_MODE_ID:
                raise ServiceError("interview_mode_required", "Conversation changed; reload before editing", context={"status": 409})
            prior = conn.execute("SELECT request_digest FROM interview_events WHERE thread_id=? AND command_id=?", (thread_id, command_id)).fetchone()
            if prior:
                if prior["request_digest"] != digest:
                    raise ServiceError("interview_command_conflict", "Command identity was already used for a different change", context={"status": 409})
            else:
                row = conn.execute("SELECT revision, state_json FROM interview_sessions WHERE thread_id=?", (thread_id,)).fetchone()
                revision = row["revision"] if row else 0
                if revision != expected_revision:
                    raise ServiceError("interview_revision_conflict", "Interview changed; reload before applying this change", context={"status": 409, "revision": revision})
                state = json.loads(row["state_json"]) if row else self._empty()
                self._prune_unavailable_facts(conn, thread_id, state)
                self._reduce(thread_id, state, event, now)
                conn.execute(
                    "INSERT INTO interview_sessions(thread_id,revision,state_json,updated_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(thread_id) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=excluded.updated_at",
                    (thread_id, revision + 1, _json(state), now),
                )
                # Keep event identity/digest, not a second copy of deletable facts.
                conn.execute("INSERT INTO interview_events(thread_id,command_id,request_digest,revision,event_kind,created_at) VALUES(?,?,?,?,?,?)", (thread_id, command_id, digest, revision + 1, event["kind"], now))
        return {**self.get(thread_id), "replayed": bool(prior)}

    def _reduce(self, thread_id: str, state: dict[str, Any], event: dict[str, Any], now: str) -> None:
        kind = event.get("kind")
        if kind == "section":
            if set(event) != {"kind", "section"} or event["section"] not in SECTION_BY_ID:
                raise ValidationError("Unknown interview section")
            state["section"] = event["section"]
            state["status"] = "needs_input" if SECTION_BY_ID[event["section"]].handoff else "exploring"
        elif kind == "fact":
            self._fact(thread_id, state, event, now)
        elif kind == "remove_fact":
            if set(event) != {"kind", "fact_id"} or event["fact_id"] not in state["facts"]:
                raise ValidationError("Unknown interview fact")
            del state["facts"][event["fact_id"]]
            state["suggestions"] = {key: value for key, value in state["suggestions"].items() if event["fact_id"] not in value["fact_ids"]}
        elif kind == "suggestion":
            self._suggestion(state, event, now)
        elif kind == "disposition":
            if set(event) != {"kind", "suggestion_id", "disposition"} or event["disposition"] not in {"kept", "deferred", "dismissed", "try"}:
                raise ValidationError("Invalid suggestion choice")
            suggestion = state["suggestions"].get(event["suggestion_id"])
            if not suggestion:
                raise ValidationError("Unknown suggestion")
            if event["disposition"] == "try" and (suggestion["feasibility"] != "manual" or suggestion["disposition"] == "stale"):
                raise ValidationError("This idea needs review or an existing setup handoff")
            suggestion["disposition"] = event["disposition"]
            suggestion["updated_at"] = now
            if event["disposition"] == "try":
                state["status"] = "drafting"
        elif kind == "status":
            if set(event) != {"kind", "status"} or event["status"] not in {"exploring", "paused", "complete_for_scope"}:
                raise ValidationError("Invalid interview status")
            state["status"] = event["status"]
        elif kind == "setup_session":
            if set(event) != {"kind", "session_id"}:
                raise ValidationError("Invalid setup continuation")
            state["setup_session_id"] = _text(event["session_id"], "session_id", 128)
        else:
            raise ValidationError("Unknown interview event")

    @staticmethod
    def _invalidate(state: dict[str, Any], fact_id: str) -> None:
        for suggestion in state["suggestions"].values():
            if fact_id in suggestion["fact_ids"] and suggestion["disposition"] not in {"dismissed", "deferred"}:
                suggestion["disposition"] = "stale"

    def _fact(self, thread_id: str, state: dict[str, Any], event: dict[str, Any], now: str) -> None:
        allowed = {"kind", "fact_id", "text", "basis", "source_message_id", "quote"}
        if set(event) - allowed or state["section"] == "people":
            raise ValidationError("Fact is outside this interview's storage boundary")
        fact_id = _text(event.get("fact_id"), "fact_id", 80)
        text = _text(event.get("text"), "text")
        basis = event.get("basis")
        if basis not in {"stated", "inferred"}:
            raise ValidationError("basis must be stated or inferred")
        message_id = _text(event.get("source_message_id"), "source_message_id", 128)
        message = self._db.threads.get_message(message_id)
        if not message or message.thread_id != thread_id or message.role != "user" or message.deleted_at:
            raise ValidationError("Fact source must be a user message in this conversation")
        quote = _text(event.get("quote"), "quote")
        parts = self._db.threads.get_parts(message_id)
        if not any(quote in (part.text or "") and not part.sensitive and not part.draft and part.kind == "text" for part in parts):
            raise ValidationError("Fact quote must match ordinary user input")
        if fact_id not in state["facts"] and len(state["facts"]) >= 50:
            raise ValidationError("Interview context is full; remove an obsolete fact")
        prior = state["facts"].get(fact_id)
        fact = {"id": fact_id, "section": state["section"], "text": text, "basis": basis, "source_message_id": message_id, "quote": quote, "updated_at": now}
        if prior and any(prior.get(key) != fact[key] for key in ("text", "basis", "section")):
            self._invalidate(state, fact_id)
        state["facts"][fact_id] = fact

    def _suggestion(self, state: dict[str, Any], event: dict[str, Any], now: str) -> None:
        fields = {"kind", "suggestion_id", "title", "benefit", "behavior", "basis", "prerequisites", "fact_ids", "feasibility"}
        if set(event) != fields or state["section"] == "people":
            raise ValidationError("Invalid suggestion fields or disclosure boundary")
        suggestion_id = _text(event["suggestion_id"], "suggestion_id", 80)
        facts = event["fact_ids"]
        if not isinstance(facts, list) or not facts or any(not isinstance(f, str) or f not in state["facts"] for f in facts):
            raise ValidationError("Suggestions must name at least one existing interview fact")
        if event["feasibility"] not in {"manual", "needs_input", "needs_connection", "unsupported_idea"}:
            raise ValidationError("Automatic setup is not implied by an interview suggestion")
        suggestion = {field: _text(event[field], field) for field in ("title", "benefit", "behavior", "basis", "prerequisites")}
        # Prevent identical ideas resurfacing under a new generated identifier.
        for existing in state["suggestions"].values():
            if existing["title"].casefold() == suggestion["title"].casefold() and existing["section"] == state["section"]:
                suggestion_id = existing["id"]
                break
        prior = state["suggestions"].get(suggestion_id)
        if prior and prior["disposition"] in {"dismissed", "deferred", "kept", "try"}:
            return
        if not prior and len(state["suggestions"]) >= 24:
            raise ValidationError("Suggestion limit reached; revisit existing ideas")
        state["suggestions"][suggestion_id] = {**suggestion, "id": suggestion_id, "section": state["section"], "fact_ids": list(dict.fromkeys(facts)), "feasibility": event["feasibility"], "disposition": "proposed", "updated_at": now}
