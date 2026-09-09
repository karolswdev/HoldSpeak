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

from ..db.refinement_thoughts import canonical_json
from ..db.relationships import qualified_ref
from ..principals import Principal, PrincipalKind
from ..project_contracts import _deterministic_hex
from .errors import ConflictError, ServiceError, ValidationError
from .interview_contracts import (
    CONTROL_TOOLS, DESCRIPTOR_VERSION, INTERVIEW_MODE_ID, SECTION_BY_ID, SECTIONS,
)

# HS-200-10: the only target kind this story ships.  A Thought needs two hashes
# (its attachments and its working body) and a Project facet has no content
# comparator at all, so both refuse `promotion_target_unsupported` rather than
# pretend (settled design D2.2).
PROMOTION_TARGET_KINDS = frozenset({"note"})


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _content_sha256(*, ref: str, title: str, body_markdown: str, tags: list[Any]) -> str:
    """The promotion's revision comparator: a content hash containing CONTENT.

    Deliberately NOT ``RefinementContextService._leaf``'s recipe, which folds
    ``last_modified`` and ``deleted`` into the digest.  ``NoteRepository``
    writes ``last_modified`` unconditionally on every upsert, so that digest is
    ``f(content, counter)`` and would report a byte-identical re-save as
    ``corrected`` -- telling the owner his constraint moved when it did not
    (settled design D2.2, counsel P0-1).
    """
    return _sha(canonical_json({"ref": ref, "title": title,
                                "body_markdown": body_markdown, "tags": list(tags)}))


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
        outcome: dict[str, Any] | None = None
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
                # F2 for a promotion is FREE and lands here: the same predicate
                # that recorded the fact is re-run INSIDE this transaction, so a
                # source part re-classified sensitive/draft or deleted between
                # recording and promotion has already removed the fact from the
                # state the reducer sees (settled design D2.4, fence F2).
                self._prune_unavailable_facts(conn, thread_id, state)
                outcome = self._reduce(conn, thread_id, state, event, now, digest)
                conn.execute(
                    "INSERT INTO interview_sessions(thread_id,revision,state_json,updated_at) VALUES(?,?,?,?) "
                    "ON CONFLICT(thread_id) DO UPDATE SET revision=excluded.revision,state_json=excluded.state_json,updated_at=excluded.updated_at",
                    (thread_id, revision + 1, _json(state), now),
                )
                # Keep event identity/digest, not a second copy of deletable facts.
                conn.execute("INSERT INTO interview_events(thread_id,command_id,request_digest,revision,event_kind,created_at) VALUES(?,?,?,?,?,?)", (thread_id, command_id, digest, revision + 1, event["kind"], now))
        result: dict[str, Any] = {**self.get(thread_id), "replayed": bool(prior)}
        # A replay returns the durable state and no outcome: the reducer did not
        # run, so there is nothing new to name.
        if outcome is not None:
            result["promotion"] = outcome
        return result

    def _reduce(self, conn: Any, thread_id: str, state: dict[str, Any], event: dict[str, Any], now: str, digest: str) -> dict[str, Any] | None:
        """Apply one event. `conn` is the command's OWN open transaction.

        Every fence a promotion runs reads on this connection (counsel C7).
        The `_fact` branch below reads through a SECOND connection
        (`self._db.threads.*`), which is safe today only because
        `BEGIN IMMEDIATE` holds the write lock -- an accident, not a pattern to
        copy.
        """
        kind = event.get("kind")
        if kind == "section":
            if set(event) != {"kind", "section"} or event["section"] not in SECTION_BY_ID:
                raise ValidationError("Unknown interview section")
            state["section"] = event["section"]
            state["status"] = "needs_input" if SECTION_BY_ID[event["section"]].handoff else "exploring"
        elif kind == "fact":
            self._fact(thread_id, state, event, now)
        elif kind == "remove_fact":
            # HS-200-10: removing a fact does NOT revoke its promotion.  The
            # canonical record is his now -- his words, in his Note -- and the
            # interview no longer holds the only copy.  The asymmetry is
            # deliberate and stated here rather than discovered later.
            if set(event) != {"kind", "fact_id"} or event["fact_id"] not in state["facts"]:
                raise ValidationError("Unknown interview fact")
            del state["facts"][event["fact_id"]]
            state["suggestions"] = {key: value for key, value in state["suggestions"].items() if event["fact_id"] not in value["fact_ids"]}
        elif kind == "promote":
            return self._promote(conn, thread_id, state, event, now, digest)
        elif kind == "revoke_promotion":
            return self._revoke_promotion(conn, thread_id, state, event, now)
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
        # HS-200-10: re-recording a fact does not un-promote it. The canonical
        # record already exists and is his; the durable record of where his
        # words went survives the model rewriting its own paraphrase.
        if prior and prior.get("promoted_to"):
            fact["promoted_to"] = list(prior["promoted_to"])
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

    # ── HS-200-10: promotion into a canonical record ────────────────────
    #
    # A promotion writes ONE canonical record carrying HIS words and NOTHING
    # else.  It never attaches, and (fence F0, built in the boundary lane) the
    # record it writes never enters the relevance pool: reachable by reference,
    # never by relevance.  The verb lives here because a promotion is an
    # interview DISPOSITION -- the category `remove_fact` already occupies --
    # and because `command()`'s single `BEGIN IMMEDIATE` is what makes the
    # fences, the promotion row, the Note write and the interview revision one
    # transaction.  No second state machine over `notes` is created: the
    # ordinary Note edit remains the only way to change one.

    @staticmethod
    def _minted_title(quote: str) -> str:
        """The title is minted from HIS words, never the model's paraphrase.

        The context picker searches `title LIKE ?` over TITLE ONLY
        (`refinement_context_service.py`), so with the model's paraphrase as the
        title he would search for the sentence he said and find it by neither
        route -- not by relevance (F0 removed it) and not by the picker.  One
        leading clause is the difference between a bounded cost and a useless
        one (settled design D2.2, counsel C1).
        """
        text = " ".join(str(quote or "").split())
        cut = min((pos for pos in (text.find(mark) for mark in (".", "!", "?", ";")) if pos > 0), default=-1)
        if cut > 0:
            text = text[:cut]
        text = text.strip()
        if len(text) > 120:
            head = text[:120]
            space = head.rfind(" ")
            text = (head[:space] if space > 40 else head).rstrip()
        return text or " ".join(str(quote or "").split())[:120] or "Promoted context"

    @staticmethod
    def _quote_locator(conn: Any, thread_id: str, fact: dict[str, Any]) -> dict[str, Any]:
        """Where the quote lives -- an ordinal and an offset, never the words.

        Provenance is a LOCATOR and a HASH, never a copy: revoking the source
        actually removes the text while the promotion stays provable.
        """
        quote = str(fact["quote"])
        rows = conn.execute(
            "SELECT p.ordinal, p.text FROM thread_messages m JOIN thread_message_parts p ON p.message_id=m.id "
            "WHERE m.id=? AND m.thread_id=? AND m.role='user' AND m.deleted_at IS NULL "
            "AND p.kind='text' AND p.sensitive=0 AND p.draft=0 ORDER BY p.ordinal",
            (fact["source_message_id"], thread_id),
        ).fetchall()
        for row in rows:
            start = str(row["text"] or "").find(quote)
            if start >= 0:
                return {"message_id": str(fact["source_message_id"]), "part_ordinal": int(row["ordinal"]),
                        "char_start": int(start), "char_length": len(quote)}
        # Unreachable while `_prune_unavailable_facts` runs first on this same
        # connection; recorded rather than guessed if it ever is.
        raise ValidationError("Fact source is no longer available", code="promotion_source_unavailable")

    @staticmethod
    def _in_default_context(conn: Any, target_ref: str) -> bool:
        """F3: is this record already auto-attached to every refinement?

        Append mode only.  In new-Note mode the service mints the ref, so a
        newly minted record cannot already be in default context -- the fence is
        structurally unreachable there (counsel C8).
        """
        from .refinement_context_service import EVERYDAY_CONTEXT_REF
        row = conn.execute("SELECT refs_json FROM refinement_default_context_current WHERE id=1").fetchone()
        try:
            refs = json.loads(row["refs_json"]) if row else []
        except Exception:
            refs = []
        if target_ref in {str(ref) for ref in refs if isinstance(ref, str)}:
            return True
        everyday_id = EVERYDAY_CONTEXT_REF.split(":", 1)[1]
        member = conn.execute(
            "SELECT 1 FROM knowledge_memberships WHERE knowledge_id=? AND resource_ref=? AND deleted=0",
            (everyday_id, target_ref),
        ).fetchone()
        return bool(member)

    @staticmethod
    def _mark_promoted(state: dict[str, Any], fact_id: str, target_ref: str) -> None:
        fact = state["facts"][fact_id]
        refs = [ref for ref in fact.get("promoted_to", []) if isinstance(ref, str)]
        if target_ref not in refs:
            refs.append(target_ref)
        fact["promoted_to"] = sorted(refs)

    def _promote(self, conn: Any, thread_id: str, state: dict[str, Any], event: dict[str, Any], now: str, digest: str) -> dict[str, Any]:
        """Promote one stated Interview fact into one canonical Note.

        The ORDER below is not stylistic.  The `context_promotions` row is
        written BEFORE the Note, so when `notes_memory_ai` fires its guard
        already sees the promotion and the body is never written to the
        relevance corpus at all -- not even transiently.  That is what makes
        F0/L1 construction rather than filtering, and it is only possible
        because the target ref is deterministic and therefore knowable before
        the Note exists (settled design D2.4 L1 part 1, counsel P0-4).
        """
        if set(event) - {"kind", "fact_id", "target_ref", "expected_target_revision"}:
            raise ValidationError("Invalid promotion fields")
        # F1 -- the People section refuses promotion, from both directions.
        if state["section"] == "people":
            raise ValidationError("Promotion is outside this interview's storage boundary")
        fact_id = _text(event.get("fact_id"), "fact_id", 80)
        fact = state["facts"].get(fact_id)
        if not fact:
            # Either it never existed, or F2 pruned it inside this transaction.
            raise ValidationError("Unknown interview fact")
        if fact.get("section") == "people":
            raise ValidationError("Promotion is outside this interview's storage boundary")
        # The canonical record carries HIS words: only a stated fact qualifies.
        if fact.get("basis") != "stated":
            raise ValidationError("Only a stated fact may be promoted")
        quote = str(fact["quote"])
        locator = self._quote_locator(conn, thread_id, fact)

        supplied = event.get("target_ref")
        append = supplied is not None
        if append:
            # F4 -- `person:` refuses itself: `qualified_ref` has no `person`
            # kind and raises.  Inherited, not re-implemented.
            try:
                target_ref = qualified_ref(supplied)
            except ValueError as exc:
                raise ValidationError(str(exc), code="promotion_target_unsupported",
                                      context={"target_ref": str(supplied)}) from exc
        else:
            target_ref = "note:note-" + _deterministic_hex(parts=["hs-200-10-promotion", thread_id, fact_id])
        # The ref names its own kind; a caller-supplied `target_kind` is not
        # read at all (counsel C10).  Without this, `artifact:a1` would pass
        # `qualified_ref` and the note branch would then read `notes` by that id.
        target_kind, _, note_id = target_ref.partition(":")
        if target_kind not in PROMOTION_TARGET_KINDS:
            raise ValidationError("Only a Note can carry a promoted record today",
                                  code="promotion_target_unsupported",
                                  context={"target_ref": target_ref, "target_kind": target_kind})
        if append and self._in_default_context(conn, target_ref):
            raise ValidationError("That record is already attached to every refinement",
                                  code="promotion_into_default_context",
                                  context={"target_ref": target_ref})
        # Forgetting is not suppressing: an explicit revocation is durable and
        # keyed by identity, so re-typing the quote cannot resurrect it.
        if conn.execute("SELECT 1 FROM context_promotion_suppressions WHERE thread_id=? AND fact_id=? AND target_ref=?",
                        (thread_id, fact_id, target_ref)).fetchone():
            raise ValidationError("That promotion was revoked", code="promotion_suppressed",
                                  context={"target_ref": target_ref})

        promotion_id = "cprom_" + _deterministic_hex(parts=[thread_id, fact_id, target_ref])
        existing = conn.execute("SELECT * FROM context_promotions WHERE promotion_id=?", (promotion_id,)).fetchone()
        if existing:
            # Two clicks, two command ids: the deterministic mint collides here
            # instead of minting a second Note, and the Note is NOT rewritten --
            # in append mode a second write would append the quote twice.
            conn.execute("UPDATE context_promotions SET updated_at=? WHERE promotion_id=?", (now, promotion_id))
            self._mark_promoted(state, fact_id, target_ref)
            return {"kind": "promote", "promotion_id": promotion_id, "target_ref": target_ref,
                    "minted": False, "mode": "append" if append else "new_note"}

        note_row = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if append:
            if note_row is None or note_row["deleted"]:
                raise ConflictError("That Note is unavailable", code="promotion_target_conflict",
                                    context={"status": 409, "target_ref": target_ref})
            # A Thought's working Note has its own revision machinery; writing
            # through it here would desynchronise the ledger that owns it.
            if conn.execute("SELECT 1 FROM refinement_thoughts WHERE working_note_id=?", (note_id,)).fetchone():
                raise ConflictError("That Note belongs to a Thought", code="promotion_target_conflict",
                                    context={"status": 409, "target_ref": target_ref, "reason": "thought_owned"})
            if str(event.get("expected_target_revision") or "") != str(note_row["last_modified"]):
                raise ConflictError("That Note changed; reload before promoting into it",
                                    code="promotion_target_conflict",
                                    context={"status": 409, "target_ref": target_ref,
                                             "target_revision_label": str(note_row["last_modified"])})
            title = str(note_row["title"])
            try:
                tags = json.loads(note_row["tags_json"] or "[]")
            except Exception:
                tags = []
            body = (str(note_row["body_markdown"]).rstrip() + "\n\n" + quote).strip()
            created_at = str(note_row["created_at"])
        else:
            if note_row is not None:
                raise ConflictError("That Note already exists", code="promotion_target_conflict",
                                    context={"status": 409, "target_ref": target_ref})
            title, tags, body, created_at = self._minted_title(quote), [], quote, now

        conn.execute(
            "INSERT INTO context_promotions(promotion_id,thread_id,fact_id,source_message_id,quote_sha256,"
            "quote_locator_json,target_kind,target_ref,target_revision_label,target_content_sha256,"
            "disclosure_state,request_sha256,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (promotion_id, thread_id, fact_id, str(fact["source_message_id"]),
             _sha(quote.encode("utf-8")), _json(locator), target_kind, target_ref, now,
             _content_sha256(ref=target_ref, title=title, body_markdown=body, tags=tags),
             "active", digest, now, now),
        )
        self._db.notes._upsert_in_transaction(
            conn, note_id=note_id, title=title, body_markdown=body, tags=tags,
            last_modified=now, created_at=created_at, now=now,
        )
        if append:
            # The Note was already in the corpus, so its rows go now, atomically
            # with the promotion.  Belt: the guarded `notes_memory_au` above has
            # already declined to re-insert it.
            conn.execute("DELETE FROM notes_memory_fts WHERE source_id=?", (note_id,))
        self._mark_promoted(state, fact_id, target_ref)
        return {"kind": "promote", "promotion_id": promotion_id, "target_ref": target_ref,
                "target_kind": target_kind, "minted": True, "mode": "append" if append else "new_note",
                "target_revision_label": now, "title": title}

    def _revoke_promotion(self, conn: Any, thread_id: str, state: dict[str, Any], event: dict[str, Any], now: str) -> dict[str, Any]:
        """Revoke the CLAIM THAT A SOURCE BACKS the record -- not the record.

        The Note stays, deliberately: it is his work, in his words.  What goes
        is the assertion that an Interview answer backs it, plus the right to
        re-promote the same quotation into the same record.  "Revoke" is the
        word the owner will read most literally, so it is said plainly here and
        in the response (counsel P0-6).
        """
        if set(event) != {"kind", "promotion_id"}:
            raise ValidationError("Invalid revocation fields")
        promotion_id = _text(event["promotion_id"], "promotion_id", 128)
        row = conn.execute("SELECT * FROM context_promotions WHERE promotion_id=? AND thread_id=?",
                           (promotion_id, thread_id)).fetchone()
        if not row:
            raise ValidationError("Unknown promotion")
        target_ref, fact_id = str(row["target_ref"]), str(row["fact_id"])
        conn.execute("UPDATE context_promotions SET disclosure_state='revoked', updated_at=? WHERE promotion_id=?",
                     (now, promotion_id))
        conn.execute("INSERT OR IGNORE INTO context_promotion_suppressions(thread_id,fact_id,target_ref,reason,created_at) "
                     "VALUES(?,?,?,?,?)", (thread_id, fact_id, target_ref, "revoked", now))
        # `UNIQUE (thread_id, fact_id, target_ref)` deliberately permits N
        # promotions into one record, so revoking the first must not poison a
        # record the others still legitimately back -- and `forbidden` is
        # TERMINAL, so the poison would be permanent.  One index seek on
        # `idx_context_promotions_target` decides it (counsel P0-3).
        surviving = int(conn.execute(
            "SELECT count(*) FROM context_promotions WHERE target_ref=? AND disclosure_state='active'",
            (target_ref,)).fetchone()[0])
        reason = "stale" if surviving else "forbidden"
        cursor = conn.execute(
            "UPDATE context_dependents SET stale_since=COALESCE(stale_since,?), "
            "stale_reason=CASE WHEN stale_reason='forbidden' THEN 'forbidden' ELSE ? END "
            "WHERE canonical_ref=?",
            (now, reason, target_ref))
        fact = state["facts"].get(fact_id)
        return {"kind": "revoke_promotion", "promotion_id": promotion_id, "target_ref": target_ref,
                "revoked": "source_claim", "record_retained": True,
                "removed_quote": str(fact["quote"]) if fact else "",
                "removed_quote_locator": json.loads(str(row["quote_locator_json"]) or "{}"),
                "quote_sha256": str(row["quote_sha256"]),
                "surviving_active_promotions": surviving,
                "dependents_marked": int(cursor.rowcount or 0), "dependent_state": reason}

    def promotions(self, thread_id: str) -> list[dict[str, Any]]:
        """Every promotion this Thread made, with its state derived on read.

        `active`/`revoked` is the only STORED axis.  `current`, `corrected`,
        `unavailable` and `source_unavailable` are computed here by comparing
        hashes -- the same detect-on-read discipline the refinement context
        service already uses (settled design D2.7).
        """
        self._thread(thread_id)
        with self._db._connection() as conn:
            rows = conn.execute("SELECT * FROM context_promotions WHERE thread_id=? ORDER BY created_at, promotion_id",
                                (thread_id,)).fetchall()
            return [self._promotion_view(conn, thread_id, row) for row in rows]

    def _promotion_view(self, conn: Any, thread_id: str, row: Any) -> dict[str, Any]:
        target_ref = str(row["target_ref"])
        note_id = target_ref.partition(":")[2]
        note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if note is None or note["deleted"]:
            target_state = "unavailable"
        else:
            try:
                tags = json.loads(note["tags_json"] or "[]")
            except Exception:
                tags = []
            current = _content_sha256(ref=target_ref, title=str(note["title"]),
                                      body_markdown=str(note["body_markdown"]), tags=tags)
            target_state = "current" if current == str(row["target_content_sha256"]) else "corrected"
        source_available = self._source_still_backs(conn, thread_id, row)
        state = target_state if target_state != "current" else ("current" if source_available else "source_unavailable")
        return {"promotion_id": str(row["promotion_id"]), "fact_id": str(row["fact_id"]),
                "target_ref": target_ref, "target_kind": str(row["target_kind"]),
                "disclosure_state": str(row["disclosure_state"]),
                "target_revision_label": str(row["target_revision_label"]),
                "target_state": target_state, "source_available": source_available,
                "state": state, "source_message_id": str(row["source_message_id"]),
                "quote_sha256": str(row["quote_sha256"]),
                "quote_locator": json.loads(str(row["quote_locator_json"]) or "{}"),
                "created_at": str(row["created_at"]), "updated_at": str(row["updated_at"])}

    @staticmethod
    def _source_still_backs(conn: Any, thread_id: str, row: Any) -> bool:
        """Does the recorded locator still address the quotation it named?

        This is what the locator-plus-hash design buys: the words are not
        stored, so the only way to answer is to re-read the source at the
        recorded offset and re-hash it.  A deleted message, a re-classified
        part, or an edit at that offset all answer no.
        """
        try:
            locator = json.loads(str(row["quote_locator_json"]) or "{}")
            ordinal = int(locator["part_ordinal"])
            start = int(locator["char_start"])
            length = int(locator["char_length"])
        except Exception:
            return False
        part = conn.execute(
            "SELECT p.text FROM thread_messages m JOIN thread_message_parts p ON p.message_id=m.id "
            "WHERE m.id=? AND m.thread_id=? AND m.role='user' AND m.deleted_at IS NULL "
            "AND p.kind='text' AND p.sensitive=0 AND p.draft=0 AND p.ordinal=?",
            (str(row["source_message_id"]), thread_id, ordinal),
        ).fetchone()
        if part is None:
            return False
        excerpt = str(part["text"] or "")[start:start + length]
        return len(excerpt) == length and _sha(excerpt.encode("utf-8")) == str(row["quote_sha256"])
