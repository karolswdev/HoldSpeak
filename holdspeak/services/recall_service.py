"""HS-200-13 -- recall: the Desk memory face's one read (posture 5).

The settled design (D2(e)) draws a recall as CURRENT / SUPERSEDED / OWED
sections over one query, with each decision carrying its rationale, its
original source (``MTG 09-07 · 11:31``, which opens the transcript span),
its Project and `Carry into brief`.  This service composes that read from
the records that already exist -- ``decision_records`` and their sources,
``decision_commitments`` and their action items, the memory index for the
other kinds -- and returns it in ONE shape the face draws without deciding
anything itself:

    {
      "query", "filter", "searched_at", "projects_searched",
      "current":    [card ...]   # lifecycle active|published, accented
      "superseded": [card ...]   # dimmed, `SUPERSEDED BY DEC mm-dd`
      "disputed":   [card ...]   # `DISPUTED`, never accented
      "owed":       [row  ...]   # open commitments, typed unknowns, ONE verb
      "meetings":   [hit  ...]   # memory hits of kind meeting
      "briefs":     [hit  ...]   # Monday brief items whose text matches
      "also":       [hit  ...]   # every other memory kind (artifact, note, thread ...)
      "remembered": n            # the head's one count
    }

Laws the shape enforces (story 13 AC1/AC2): a card's ``state`` is derived
from the record's lifecycle and NOTHING else -- a superseded or disputed
record can never land in ``current``; the current section is ordered newest
first so the current decision comes back first; every card names its
successor when it has one.  Filters narrow the sections; ``all`` returns
every section.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from holdspeak.services.brief_carry import (
    CURRENT_LIFECYCLES,
    pending_carry_refs,
    project_for_record,
    record_ref,
    successor_of,
)
from holdspeak.principals import PrincipalKind, PrincipalRight, refusal
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.errors import ServiceError, ValidationError

FILTERS = ("all", "decisions", "commitments", "briefs", "meetings")

#: The commitment states that are no longer owed (the same set the Room's
#: attention producer uses).
_SETTLED = frozenset({"closed", "completed", "done", "dismissed"})

#: Memory kinds drawn under ``also`` (never decision records: those are cards).
_ALSO_KINDS = ("artifact", "note", "thread", "desk_decision", "project_item")

_SUPPORT_TOKENS = {
    "supported": "SUPPORTED",
    "source_linked": "LINKED",
    "linked": "LINKED",
    "disputed": "DISPUTED",
    "unknown": "NO SOURCE",
    "": "NO SOURCE",
}


def _parse(stamp: Any) -> datetime | None:
    if not stamp or not isinstance(stamp, str):
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def dec_token(stamp: Any) -> str:
    """``DEC 09-07`` -- the decision's day, the way every board names it."""
    parsed = _parse(stamp)
    return f"DEC {parsed.strftime('%m-%d')}" if parsed else "DEC"


def mtg_token(started_at: Any, offset_seconds: float | None) -> str:
    """``MTG 09-07 · 11:31`` -- the meeting's day and the moment's clock."""
    parsed = _parse(started_at)
    if parsed is None:
        return "MTG"
    moment = parsed + timedelta(seconds=float(offset_seconds or 0.0))
    return f"MTG {parsed.strftime('%m-%d')} · {moment.strftime('%H:%M')}"


def due_token(due_at: str | None, today: datetime) -> tuple[str, str]:
    """The DUE token and its tone for an owed row."""
    if not due_at:
        return "DUE · UNKNOWN", "idle"
    parsed = _parse(due_at)
    if parsed is None:
        return f"DUE {due_at}", "idle"
    days = (today.date() - parsed.date()).days
    if days > 0:
        return f"OVERDUE · {days} D", "danger"
    if days == 0:
        return "DUE TODAY", "warn"
    return f"DUE {parsed.strftime('%m-%d')}", "idle"


def next_action_for(owner: str | None, due_at: str | None) -> str:
    """ONE lawful next action (AC3/AC4): an unknown is named before anything
    can be marked done."""
    if not owner:
        return "name_owner"
    if not due_at:
        return "set_date"
    return "mark_done"


class RecallService:
    def __init__(self, db: Any) -> None:
        self._db = db
        self._records = DecisionRecordService(db)

    # ── the read ─────────────────────────────────────────────────────

    def recall(
        self, principal: Any, query: str, *, filter: str = "all",
        limit: int = 50, now: datetime | None = None, recent: bool = False,
    ) -> dict[str, Any]:
        """HS-202-02 — `recent=True` with no query is the DESK MEMORY read.

        The face named "Desk memory" opened on a desk that held a meeting,
        two decision records and a brief, and showed an empty body, because
        its only read needs a query and it had not been given one
        (03-interaction-walk.md finding 7). `recent` answers the newest of
        each kind in the same shape a search answers. A bare blank query is
        still refused: a search with no words is still a search with no
        words.
        """
        if not principal.permits(PrincipalRight.READ):
            status = 401 if principal.kind is PrincipalKind.NONE else 403
            raise ServiceError(
                "read_forbidden", "principal does not permit memory reads",
                context={"status": status, "response": refusal(principal, PrincipalRight.READ)},
            )
        q = str(query or "").strip()
        chosen = str(filter or "all").strip().lower() or "all"
        if chosen not in FILTERS:
            raise ValidationError(f"unknown filter: {filter}")
        newest = bool(recent) and not q
        if not q and not newest:
            raise ValidationError("query is required")
        clock = now or datetime.now()
        bounded = max(1, min(int(limit), 200))

        result: dict[str, Any] = {
            "query": q,
            "recent": newest,
            "filter": chosen,
            "searched_at": clock.isoformat(),
            "projects_searched": self._projects_searched(),
            "current": [], "superseded": [], "disputed": [],
            "owed": [], "meetings": [], "briefs": [], "also": [],
        }

        cards: list[dict[str, Any]] = []
        if chosen in ("all", "decisions", "commitments"):
            cards = self._decision_cards(principal, q, bounded, recent=newest)
        if chosen in ("all", "decisions"):
            for card in cards:
                result[card["state"]].append(card)
        if chosen in ("all", "commitments"):
            result["owed"] = self._owed(q, cards, clock, bounded, recent=newest)
        if chosen == "meetings":
            result["meetings"] = self._memory_hits(
                q, ("meeting",), bounded, recent=newest)
        if chosen in ("all", "briefs"):
            result["briefs"] = self._brief_hits(q, bounded, recent=newest)
        if chosen == "all":
            # ONE memory read over every drawn kind, so a hit reached over a
            # durable relationship edge (a meeting's artifact) still arrives
            # beside its seed; the hits are then split by kind.
            hits = self._memory_hits(
                q, ("meeting",) + _ALSO_KINDS, bounded, recent=newest)
            result["meetings"] = [h for h in hits if h.get("kind") == "meeting"]
            result["also"] = [h for h in hits if h.get("kind") != "meeting"]

        result["remembered"] = sum(
            len(result[key]) for key in
            ("current", "superseded", "disputed", "owed", "meetings", "briefs", "also")
        )
        return result

    # ── decisions ────────────────────────────────────────────────────

    def _decision_cards(
        self, principal: Any, query: str, limit: int, *, recent: bool = False
    ) -> list[dict[str, Any]]:
        found = self._records.search(principal, query, limit=limit, recent=recent)
        if not found:
            return []
        cards: list[dict[str, Any]] = []
        carried_by_project: dict[str, set[str]] = {}
        with self._db._connection() as conn:
            for brief in found:
                record = self._records.get(principal, brief["id"])
                if record is None:
                    continue
                # HS-200-12's confirm mints the FULL chain for every proposal,
                # so an action-kind proposal also leaves a decision_records
                # row.  A commitment is not a decision: it is drawn under
                # OWED, never as a CURRENT card (reported to 12's backlog).
                if self._proposal_kind(conn, str(record["id"])) == "action":
                    continue
                cards.append(self._card(conn, record, carried_by_project))
        # AC1: the current decision comes back FIRST -- newest current first,
        # then the sealed ones, each section newest first.
        order = {"current": 0, "disputed": 1, "superseded": 2}
        cards.sort(key=lambda c: (order[c["state"]], -(_parse(c["decided_at"]) or datetime.min).timestamp(), c["id"]))
        return cards

    def _card(self, conn: Any, record: dict[str, Any], carried_by_project: dict[str, set[str]]) -> dict[str, Any]:
        rid = str(record["id"])
        lifecycle = str(record.get("lifecycle") or "active")
        state = (
            "superseded" if lifecycle == "superseded"
            else "disputed" if lifecycle == "disputed"
            else "current" if lifecycle in CURRENT_LIFECYCLES
            else "superseded"   # an unknown lifecycle is never drawn as current
        )
        successor_id = record.get("successor_id") or successor_of(conn, rid)
        successor = None
        if successor_id:
            srow = conn.execute(
                "SELECT id, created_at, decision_text FROM decision_records WHERE id = ?", (successor_id,)
            ).fetchone()
            if srow is not None:
                sday = self._decided_day(conn, str(srow["id"])) or srow["created_at"]
                successor = {"id": str(srow["id"]), "dec_token": dec_token(sday),
                             "text": str(srow["decision_text"] or "")}
        project_id = project_for_record(conn, rid)
        project = None
        if project_id:
            prow = conn.execute("SELECT id, name FROM projects WHERE id = ?", (project_id,)).fetchone()
            if prow is not None:
                project = {"id": str(prow["id"]), "name": str(prow["name"] or "")}
                if project_id not in carried_by_project:
                    carried_by_project[project_id] = pending_carry_refs(self._db, project_id)
        source, support_hint = self._source(conn, record)
        support = self._support(conn, rid, support_hint)
        acceptance = {"current": "ACCEPTED", "superseded": "SUPERSEDED", "disputed": "DISPUTED"}[state]
        commitment_ids = [
            str(r["id"]) for r in conn.execute(
                "SELECT id FROM decision_commitments WHERE decision_id = ? ORDER BY created_at",
                (record.get("source_id") or "",),
            ).fetchall()
        ]
        return {
            "id": rid,
            "ref": record_ref(rid),
            "text": str(record.get("decision_text") or ""),
            "rationale": str(record.get("rationale") or ""),
            "lifecycle": lifecycle,
            "state": state,
            # The decision's day is the day it was decided -- the source
            # meeting's -- not the day the record row was written.
            "dec_token": dec_token((source or {}).get("started_at") or record.get("created_at")),
            "decided_at": (source or {}).get("started_at") or record.get("created_at"),
            "axes": ["DECISION", support, acceptance],
            "support": support,
            "acceptance": acceptance,
            "successor": successor,
            "predecessor_id": record.get("predecessor_id"),
            "supersession_reason": record.get("supersession_reason"),
            "dispute_reason": record.get("dispute_reason"),
            "project": project,
            "source": source,
            "carried": bool(project_id and record_ref(rid) in carried_by_project.get(project_id, set())),
            "commitment_ids": commitment_ids,
        }

    @staticmethod
    def _decided_day(conn: Any, record_id: str) -> str | None:
        """The source meeting's start for a record (its decided day)."""
        row = conn.execute(
            """SELECT m.started_at FROM decision_record_sources s
               JOIN meetings m ON m.id IN (s.source_ref, replace(s.source_ref, 'meeting:', ''))
               WHERE s.record_id = ? AND s.source_type = 'meeting' LIMIT 1""",
            (record_id,),
        ).fetchone()
        return str(row["started_at"]) if row and row["started_at"] else None

    def _source(self, conn: Any, record: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
        """The original source: the meeting, and the transcript moment when
        one is anchored.  Returns (source, support hint)."""
        sources = record.get("sources") or []
        meeting_id = None
        segment_index: int | None = None
        offset: float | None = None
        for src in sources:
            kind = str(src.get("source_type") or "")
            ref = str(src.get("source_ref") or "")
            if kind == "meeting" and not meeting_id:
                meeting_id = ref.removeprefix("meeting:")
            elif kind == "transcript" and "#segment:" in ref:
                head, _, idx = ref.partition("#segment:")
                meeting_id = meeting_id or head.removeprefix("meeting:")
                try:
                    segment_index = int(idx)
                except ValueError:
                    segment_index = None
            elif kind == "segment":
                seg = conn.execute(
                    "SELECT meeting_id, start_time FROM segments WHERE id = ?", (ref,)
                ).fetchone()
                if seg is not None:
                    meeting_id = meeting_id or str(seg["meeting_id"])
                    offset = float(seg["start_time"] or 0.0)
                    idx_row = conn.execute(
                        """SELECT COUNT(*) AS n FROM segments
                           WHERE meeting_id = ? AND (start_time < ? OR (start_time = ? AND id < ?))""",
                        (seg["meeting_id"], offset, offset, ref),
                    ).fetchone()
                    segment_index = int(idx_row["n"]) if idx_row else None
        if not meeting_id and str(record.get("source_type")) == "meeting":
            # A record minted straight from a `decisions` row.
            drow = conn.execute(
                "SELECT source_meeting_id, source_timestamp FROM decisions WHERE id = ?",
                (record.get("source_id") or "",),
            ).fetchone()
            if drow is not None and drow["source_meeting_id"]:
                meeting_id = str(drow["source_meeting_id"])
                offset = float(drow["source_timestamp"]) if drow["source_timestamp"] is not None else None
        if not meeting_id:
            return None, "none"
        mrow = conn.execute(
            "SELECT id, title, started_at FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        if mrow is None:
            return None, "none"
        if offset is None and segment_index is not None:
            seg = conn.execute(
                "SELECT start_time FROM segments WHERE meeting_id = ? ORDER BY start_time, id LIMIT 1 OFFSET ?",
                (meeting_id, segment_index),
            ).fetchone()
            if seg is not None:
                offset = float(seg["start_time"] or 0.0)
        if offset is None:
            drow = conn.execute(
                "SELECT source_timestamp FROM decisions WHERE id = ?", (record.get("source_id") or "",)
            ).fetchone()
            if drow is not None and drow["source_timestamp"] is not None:
                offset = float(drow["source_timestamp"])
        scope = f"meeting:{meeting_id}" + (f"?segment={segment_index}" if segment_index is not None else "")
        source = {
            "kind": "meeting",
            "meeting_id": str(mrow["id"]),
            "title": str(mrow["title"] or ""),
            "started_at": mrow["started_at"],
            "offset_seconds": offset,
            "segment_index": segment_index,
            "token": mtg_token(mrow["started_at"], offset),
            "scope": scope,
        }
        return source, ("linked" if segment_index is not None or offset is not None else "meeting")

    @staticmethod
    def _proposal_kind(conn: Any, record_id: str) -> str | None:
        prow = conn.execute(
            "SELECT kind FROM follow_through_proposals WHERE decision_record_id = ? LIMIT 1",
            (record_id,),
        ).fetchone()
        return str(prow["kind"]) if prow is not None and prow["kind"] else None

    def _support(self, conn: Any, record_id: str, hint: str) -> str:
        """The support axis: the confirmed proposal's own verdict when the
        record came through the review face; else LINKED when a transcript
        moment is anchored; else NO SOURCE."""
        prow = conn.execute(
            "SELECT support FROM follow_through_proposals WHERE decision_record_id = ? ORDER BY decided_at DESC LIMIT 1",
            (record_id,),
        ).fetchone()
        if prow is not None and prow["support"]:
            return _SUPPORT_TOKENS.get(str(prow["support"]).lower(), "NO SOURCE")
        if hint == "linked":
            return "LINKED"
        return "NO SOURCE"

    # ── commitments ──────────────────────────────────────────────────

    def _owed(
        self, query: str, cards: list[dict[str, Any]], clock: datetime, limit: int,
        *, recent: bool = False,
    ) -> list[dict[str, Any]]:
        terms = [t for t in query.split() if t.strip()]
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        by_record = {card["id"]: card for card in cards}
        with self._db._connection() as conn:
            fetched: list[Any] = []
            record_ids = list(by_record)
            if record_ids:
                placeholders = ",".join("?" * len(record_ids))
                fetched.extend(conn.execute(
                    f"""SELECT c.*, ai.task AS text, ai.status AS action_status, r.id AS record_id,
                               (SELECT p.kind FROM follow_through_proposals p WHERE p.commitment_id = c.id LIMIT 1) AS proposal_kind
                        FROM decision_commitments c
                        JOIN decision_records r ON r.source_id = c.decision_id AND r.deleted = 0
                        LEFT JOIN action_items ai ON ai.id = c.action_item_id
                        WHERE r.id IN ({placeholders})
                        ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC""",
                    record_ids,
                ).fetchall())
            if terms or recent:
                # HS-202-02 — the recent read drops the word predicate and
                # keeps the order the owed list already has: soonest due
                # first, then oldest.
                predicate = (
                    " AND ".join("ai.task LIKE ? COLLATE NOCASE" for _ in terms)
                    if terms
                    else "1 = 1"
                )
                fetched.extend(conn.execute(
                    f"""SELECT c.*, ai.task AS text, ai.status AS action_status, r.id AS record_id,
                               (SELECT p.kind FROM follow_through_proposals p WHERE p.commitment_id = c.id LIMIT 1) AS proposal_kind
                        FROM decision_commitments c
                        JOIN action_items ai ON ai.id = c.action_item_id
                        LEFT JOIN decision_records r ON r.source_id = c.decision_id AND r.deleted = 0
                        WHERE {predicate}
                        ORDER BY c.due_at ASC NULLS LAST, c.created_at ASC
                        LIMIT ?""",
                    [f"%{t}%" for t in terms] + [limit],
                ).fetchall())
            for row in fetched:
                cid = str(row["id"])
                if cid in seen:
                    continue
                seen.add(cid)
                status = str(row["status"] or "open").lower()
                if status in _SETTLED or str(row["action_status"] or "").lower() in _SETTLED:
                    continue
                # The mirror of the card rule above: a decision-kind proposal's
                # chain row is a decision, not something owed.
                if str(row["proposal_kind"] or "") == "decision":
                    continue
                owner = (row["owner"] or "").strip() or None
                due_at = (row["due_at"] or "").strip() or None
                token, tone = due_token(due_at, clock)
                record_id = str(row["record_id"] or "") or None
                card = by_record.get(record_id or "")
                project = card["project"] if card else None
                if project is None and record_id:
                    pid = project_for_record(conn, record_id)
                    if pid:
                        prow = conn.execute("SELECT id, name FROM projects WHERE id = ?", (pid,)).fetchone()
                        if prow is not None:
                            project = {"id": str(prow["id"]), "name": str(prow["name"] or "")}
                unknowns = [k for k, v in (("owner", owner), ("due", due_at)) if not v]
                rows.append({
                    "id": cid,
                    "ref": f"commitment:{cid}",
                    "action_item_id": str(row["action_item_id"] or ""),
                    "text": str(row["text"] or "").strip() or "Untitled commitment",
                    "owner": owner,
                    "owner_token": f"OWNER · {owner.upper()}" if owner else "OWNER · UNKNOWN",
                    "due_at": due_at,
                    "due_token": token,
                    "due_tone": tone,
                    "status": status,
                    "unknowns": unknowns,
                    "next_action": next_action_for(owner, due_at),
                    "project": project,
                    "decision_record_id": record_id,
                    "decision_state": card["state"] if card else None,
                })
        return rows[:limit]

    # ── the other kinds ──────────────────────────────────────────────

    def _memory_hits(
        self, query: str, kinds: tuple[str, ...], limit: int, *, recent: bool = False
    ) -> list[dict[str, Any]]:
        """Lexical hits, or — with no query — the newest of each kind.

        HS-202-02 (Astra's counsel finding 5): a wordless query raised
        inside the FTS matcher and was swallowed into `[]`, so a desk
        holding only meetings, or only notes, read EMPTY.
        """
        if recent:
            return self._db.memory.recent(kinds=list(kinds), limit=limit)
        try:
            found = self._db.memory.search(query, kinds=list(kinds), limit=limit)
        except ValueError:
            return []
        return [hit.to_dict() if hasattr(hit, "to_dict") else dict(hit) for hit in found.hits]

    def _brief_hits(
        self, query: str, limit: int, *, recent: bool = False
    ) -> list[dict[str, Any]]:
        terms = [t for t in query.split() if t.strip()]
        if not terms and not recent:
            return []
        params: list[Any] = []
        if terms:
            predicate = " AND ".join("(i.text LIKE ? COLLATE NOCASE OR COALESCE(i.detail,'') LIKE ? COLLATE NOCASE)" for _ in terms)
            for t in terms:
                params.extend([f"%{t}%", f"%{t}%"])
        else:
            # HS-202-02 — the recent read: the newest brief's items, in the
            # order the brief itself ranked them.
            predicate = "1 = 1"
        params.append(limit)
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT i.id, i.section, i.text, i.detail, i.source_ref, b.id AS brief_id,
                           b.headline, b.generated_at, b.period_start
                    FROM monday_brief_items i JOIN monday_briefs b ON b.id = i.brief_id
                    WHERE {predicate}
                    ORDER BY b.generated_at DESC, i.priority DESC LIMIT ?""",
                params,
            ).fetchall()
        return [{
            "kind": "brief",
            "source_ref": f"monday_brief_item:{r['id']}",
            "brief_id": str(r["brief_id"]),
            "title": str(r["text"] or ""),
            "snippet": str(r["detail"] or r["headline"] or ""),
            "section": str(r["section"] or ""),
            "occurred_at": str(r["generated_at"] or ""),
            "period_start": str(r["period_start"] or ""),
            "project_id": None,
        } for r in rows]

    def _projects_searched(self) -> int:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM projects WHERE is_archived = 0 AND lifecycle != 'archived'"
            ).fetchone()
        return int(row["n"]) if row else 0


__all__ = ["FILTERS", "RecallService", "dec_token", "due_token", "mtg_token", "next_action_for"]
