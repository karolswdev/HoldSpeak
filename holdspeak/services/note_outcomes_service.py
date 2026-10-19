"""Betterment Q9 "Find the tasks": the meeting's extraction, over one note.

One press on a note runs the SAME analysis a meeting gets (the prompt
``_json_only_messages``, the schema ``intel_response_format`` and the parser
``_extract_json`` / ``_coerce_action_items`` / ``_coerce_decisions`` of
holdspeak/intel/parsing.py), on the engine the owner set for meeting
analysis (``meeting.deferred_analysis``), through the runner like every
other service call (a receipt, no direct engine). Nothing is copied.

The rows are the meeting's outcome rows: a task with its owner and date, or
a proposed decision. An owner is matched to People (an alias, a unique name,
or a unique first name, ``PeopleService.resolve_owner_candidates``); "Me"
and a task with no owner are his (he wrote the note). Confirm makes the task
(a Door item, so it shows in Needs you and in that person's window) or the
proposed decision, with the note as its source. The rows stay with the note
(``note_outcomes``): a new Find replaces the rows still proposed and keeps
the confirmed ones.
"""
from __future__ import annotations

import re
import time
import uuid
from typing import Any

from holdspeak.timestamps import utc_now_iso

from ..principals import Principal
from .errors import ConflictError, NotFound, ServiceError, ValidationError

CAPABILITY = "meeting.deferred_analysis"
CONTRACT = "note.find_tasks"
CONTRACT_REVISION = "1"
DEADLINE_SECONDS = 180
#: The meeting's reserved name for the speaker; in a note, the writer.
ME = "Me"
_WORD = re.compile(r"[a-z0-9]+")


class NoteFindRefused(ServiceError):
    """The extraction could not run or gave nothing usable, said in words."""

    def __init__(self, code: str, message: str, status: int = 409) -> None:
        super().__init__(code, message, context={"status": status})


def _key(text: str) -> str:
    return " ".join(_WORD.findall(str(text or "").lower()))


class NoteOutcomesService:
    def __init__(self, db: Any, *, broker: Any = None, people_service: Any = None,
                 door_service: Any = None) -> None:
        self._db = db
        self._broker = broker
        self._people = people_service
        self._door = door_service

    # ── reads ─────────────────────────────────────────────────────────

    def _note(self, note_id: str) -> Any:
        note = self._db.notes.get(str(note_id or ""))
        if note is None or getattr(note, "deleted", False):
            raise NotFound("note", str(note_id))
        return note

    def _rows(self, note_id: str, *, dismissed: bool = False) -> list[dict[str, Any]]:
        """The note's rows; a dismissed row only when asked (Find reads it so
        it never proposes that row again)."""
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM note_outcomes WHERE note_id=?"
                + ("" if dismissed else " AND state<>'dismissed'") + " ORDER BY ordinal", (note_id,)
            ).fetchall()
        return [{
            "id": row["id"], "kind": row["kind"], "text": row["text"],
            "owner": row["owner"], "due": row["due"],
            "rationale": row["rationale"], "state": row["state"], "made_ref": row["made_ref"],
            "found_at": row["found_at"], "model": row["model"],
        } for row in rows]

    def read(self, principal: Principal, note_id: str) -> dict[str, Any]:
        note = self._note(note_id)
        return {"note_id": note.id, "rows": self._rows(note.id)}

    # ── Find the tasks ────────────────────────────────────────────────

    def _broker_for_db(self) -> Any:
        broker = self._broker
        if broker is None:
            from ..kernel.runtime import _service
            broker = _service()
        if getattr(broker, "database", self._db) is not self._db:
            from ..kernel.runtime import _configure
            broker = _configure(self._db)
        return broker

    def _extract(self, principal: Principal, text: str) -> tuple[Any, str]:
        """One routed call: the meeting's prompt over the note's text."""
        from ..intel.parsing import (
            _coerce_action_items, _coerce_decisions, _extract_json,
            _json_only_messages, intel_response_format,
        )
        from ..kernel.inference_runner import InvocationRequest, ServiceContract
        from ..kernel.prompt_adapter import CanonicalPromptAdapter
        from ..kernel.runtime import _as_principal
        from .project_update_service import _resolve_for_capability

        broker = self._broker_for_db()
        try:
            revision, _assignment, _profile = _resolve_for_capability(broker, CAPABILITY)
        except RuntimeError as exc:
            raise NoteFindRefused(
                "no_engine", "No engine is set for meeting analysis. Choose one in Engines.") from exc
        system, user = _json_only_messages(text)
        payload = {
            "system_prompt": system["content"], "user_prompt": user["content"],
            "temperature": 0.2, "max_tokens": 1200,
            "response_format": intel_response_format(),
        }
        request = InvocationRequest(
            deployment_revision=revision,
            definition_origin=ServiceContract.for_payload(CONTRACT, CONTRACT_REVISION, payload),
            deadline_at=time.time() + DEADLINE_SECONDS,
            payload=payload,
        )
        captured: list[Any] = []

        def _capture(value: Any) -> str:
            captured.append(value)
            return f"note-find-tasks:{revision}"

        with _as_principal(principal):
            outcome = broker.inference_runner.invoke(request, CanonicalPromptAdapter(), publish=_capture)
        if str(getattr(outcome, "outcome", "")) != "succeeded" or not captured:
            raise NoteFindRefused(
                "engine_failed", "The engine did not answer. The note is unchanged. Try again.", status=502)
        result = captured[0] if isinstance(captured[0], dict) else {"output": captured[0]}
        data = _extract_json(str(result.get("output") or ""))
        if data is None:
            raise NoteFindRefused(
                "engine_unusable", "The engine's answer could not be read. The note is unchanged. Try again.",
                status=502)
        items = _coerce_action_items(data.get("action_items", data.get("actionItems", data.get("actions", []))))
        decisions = _coerce_decisions(data["decisions"]) if "decisions" in data else []
        return (items, decisions), str(result.get("model") or "")

    def _owner(self, raw: Any) -> str:
        """The owner: "Me" for his own; a People match takes the person's name.

        Only the NAME is kept in this plaintext table (the 138 law: no
        People-referencing column outside the encrypted store); a person's
        window matches it at read time, as it does a meeting's action items."""
        owner = " ".join(str(raw or "").split())
        if not owner:
            return ME
        try:
            from .needs_you_membership import self_check
            if self_check()(owner):
                return ME
        except Exception:
            pass
        if self._people is not None:
            try:
                match = self._people.resolve_owner_candidates(owner)
            except Exception:
                match = {}
            if match.get("link") == "linked" and match.get("relationship"):
                person = match["relationship"]
                return str(person.get("display_name") or owner)
        return owner

    def find(self, principal: Principal, note_id: str) -> dict[str, Any]:
        note = self._note(note_id)
        text = "\n".join(part for part in (str(note.title or "").strip(), str(note.body_markdown or "").strip()) if part)
        if not text.strip():
            raise NoteFindRefused("note_empty", "The note has no words yet.", status=422)
        (items, decisions), model = self._extract(principal, text)
        now = utc_now_iso()
        # Confirmed and dismissed rows stay; neither is proposed again.
        kept = [row for row in self._rows(note.id, dismissed=True) if row["state"] in ("confirmed", "dismissed")]
        kept_keys = {(row["kind"], _key(row["text"])) for row in kept}
        found: list[dict[str, Any]] = []
        for item in items:
            task = str(item.task or "").strip()
            if not task or ("task", _key(task)) in kept_keys:
                continue
            owner = self._owner(item.owner)
            found.append({"kind": "task", "text": task, "owner": owner,
                          "due": str(item.due or "").strip(), "rationale": ""})
        task_keys = {_key(row["text"]) for row in found} | {key for kind, key in kept_keys if kind == "task"}
        for decision in decisions:
            words = str(decision.get("decision") or "").strip()
            # A task the reply also called a decision is one row: the task.
            if not words or _key(words) in task_keys or ("decision", _key(words)) in kept_keys:
                continue
            found.append({"kind": "decision", "text": words, "owner": "",
                          "due": "", "rationale": str(decision.get("rationale") or "").strip()})
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM note_outcomes WHERE note_id=? AND state='proposed'", (note.id,))
            start = 1 + max([0] + [int(r["ordinal"]) for r in conn.execute(
                "SELECT ordinal FROM note_outcomes WHERE note_id=?", (note.id,)).fetchall()])
            for offset, row in enumerate(found):
                conn.execute(
                    """INSERT INTO note_outcomes (id, note_id, ordinal, kind, text, owner, due,
                       rationale, state, made_ref, model, found_at) VALUES (?,?,?,?,?,?,?,?,'proposed','',?,?)""",
                    ("no_" + uuid.uuid4().hex[:16], note.id, start + offset, row["kind"], row["text"],
                     row["owner"], row["due"], row["rationale"], model, now),
                )
        return self.read(principal, note.id)

    # ── Edit and Dismiss, before Confirm (as a meeting's rows) ────────

    def _proposed(self, note_id: str, row_id: str) -> tuple[Any, dict[str, Any]]:
        note = self._note(note_id)
        row = next((r for r in self._rows(note.id) if r["id"] == row_id), None)
        if row is None:
            raise NotFound("note outcome", str(row_id))
        if row["state"] != "proposed":
            raise ConflictError("only a proposed row changes", code="note_outcome_not_proposed")
        return note, row

    def edit(self, principal: Principal, note_id: str, row_id: str, *, text: str | None = None,
             owner_name: str | None = None, due: str | None = None) -> dict[str, Any]:
        """Change a proposed row's words, owner or date before Confirm. A new
        owner is matched to People again."""
        note, row = self._proposed(note_id, row_id)
        new_text = row["text"] if text is None else " ".join(str(text).split())
        if not new_text:
            raise ValidationError("the row needs words", code="note_outcome_text_required")
        new_owner, person_id = row["owner"], row["person_id"]
        if owner_name is not None and row["kind"] == "task":
            new_owner, person_id = self._owner(owner_name)
        new_due = row["due"] if due is None else " ".join(str(due).split())
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE note_outcomes SET text=?, owner=?, person_id=?, due=? WHERE id=? AND state='proposed'",
                (new_text, new_owner, person_id, new_due, row_id),
            )
        return self.read(principal, note.id)

    def dismiss(self, principal: Principal, note_id: str, row_id: str) -> dict[str, Any]:
        """Take a proposed row away. It is kept (never proposed again), not drawn."""
        note, _row = self._proposed(note_id, row_id)
        with self._db._connection() as conn:
            conn.execute("UPDATE note_outcomes SET state='dismissed' WHERE id=? AND state='proposed'", (row_id,))
        return self.read(principal, note.id)

    # ── Confirm ───────────────────────────────────────────────────────

    def confirm(self, principal: Principal, note_id: str, row_id: str) -> dict[str, Any]:
        note = self._note(note_id)
        row = next((r for r in self._rows(note.id, dismissed=True) if r["id"] == row_id), None)
        if row is None:
            raise NotFound("note outcome", str(row_id))
        if row["state"] == "confirmed":
            return self.read(principal, note.id)
        if row["state"] == "dismissed":
            raise ConflictError("a dismissed row is not confirmed", code="note_outcome_dismissed")
        source_ref = f"note:{note.id}"
        if row["kind"] == "task":
            if self._door is None:
                raise ValidationError("the Door is not composed on this hub", code="door_unavailable")
            item = self._door.add_item(principal, row["text"], owner=row["owner"] or ME,
                                       due=row["due"] or None, source_type="thought", source_ref=source_ref)
            made = f"action_item:{item.get('id')}"
        elif row["kind"] == "decision":
            from .primitive_service import PrimitiveService

            context = f"From the note \"{note.title or 'Note'}\" ({source_ref})."
            if row["rationale"]:
                context += f"\n\nWhy: {row['rationale']}"
            decision = PrimitiveService(self._db).create_decision(
                principal, title=row["text"][:120], status="proposed",
                decision_markdown=row["text"], context_markdown=context, tags=[source_ref])
            made = f"decision:{decision.get('id')}"
        else:
            raise ConflictError("unknown outcome kind", code="note_outcome_invalid")
        with self._db._connection() as conn:
            conn.execute(
                "UPDATE note_outcomes SET state='confirmed', made_ref=?, confirmed_at=? WHERE id=? AND state='proposed'",
                (made, utc_now_iso(), row_id),
            )
        return self.read(principal, note.id)
