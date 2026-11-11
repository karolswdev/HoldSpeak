"""Durable decision record operations (HS-127-01)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import Any

from uuid import uuid4

from ..db.search import like_literal

from holdspeak.principals import PrincipalRight
from holdspeak.services.brief_carry import require_right
from holdspeak.services.observer import (
    NullObserver,
    PipelineObserver,
    current_correlation_id,
    observe_service,
)
from holdspeak.services.errors import NotFound
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.db.relationships import ProjectRelationshipRepository


_SOURCE_TYPES = frozenset({"meeting", "desk"})
#: HS-200-13: the record lifecycles.  ``active`` / ``published`` are CURRENT;
#: ``superseded`` names a successor; ``disputed`` is contested -- discoverable
#: on recall, never presented as current, never accented (story 13 AC2).
#: ``disputed`` is defined minimally here: a verb, a reason, a revision row;
#: no resolution workflow (out of scope: enterprise approval).
LIFECYCLES = frozenset({"active", "superseded", "published", "disputed"})
CURRENT_LIFECYCLES = frozenset({"active", "published"})
#: A supersession may seal an active OR a disputed predecessor (the usual
#: way a dispute ends is a newer decision).
_SUPERSEDABLE = frozenset({"active", "disputed"})
#: The id prefix of a revision ``sync_from_desk`` writes: a copy of a Desk
#: edit, not a hand edit of the record (the sync guard ignores these rows).
_SYNC_REVISION = "record-sync-revision-"

_EDITABLE_FIELDS = frozenset(
    {"decision_text", "rationale", "alternatives", "owner", "review_date"}
)


#: PHILO-15 08 (Astra MISSED 1): a confirmed ACTION writes a record row as the
#: Room's join anchor for its commitment (proposal_bridge_service.py, step 2).
#: That row is an action, not a decision: no decision list shows it.
_NOT_AN_ACTION = (
    "COALESCE(r.kind, 'decision') != 'action' AND "
    # A record written before the kind column read its kind from its proposal.
    "NOT EXISTS (SELECT 1 FROM follow_through_proposals AS fp "
    "WHERE fp.decision_record_id = r.id AND fp.kind = 'action')"
)


@observe_service
class DecisionRecordService:
    """Create and retrieve the durable canon for a decision."""

    def __init__(
        self, db: Any, *, observer: PipelineObserver | None = None, people: Any = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        # The People lookup that turns an owner's words into a Person
        # reference. None: the hub's composed People service, when a hub runs.
        self._people = people

    def create_desk_command(self, principal: Any, *, body: dict[str, Any], registry_factory: Any) -> tuple[int, dict[str, Any]]:
        """Create the admitted source and return its canonical record without a second writer."""
        title = str(body.get("decision_text") or body.get("title") or "").strip()
        if not title:
            return 400, {"detail": "decision text is required"}
        status = str(body.get("status") or "accepted").strip().lower()
        if status not in {"accepted", "proposed"}:
            return 400, {"detail": "status must be accepted or proposed"}
        project_id = str(body.get("project_id") or "").strip()
        project_name = str(body.get("project_name") or "").strip()
        about = str(body.get("about") or project_name or "").strip()
        why = str(body.get("why") or "").strip()
        if project_id and self.live_project([project_id]) is None:
            return 400, {"error": f"Unknown Project: {project_id}"}
        tags = [str(tag).strip() for tag in (body.get("tags") or []) if str(tag).strip()]
        if project_id and f"project:{project_id}" not in tags:
            tags.append(f"project:{project_id}")
        meeting_id = str(body.get("meeting_id") or "").strip()
        if meeting_id and f"meeting:{meeting_id}" not in tags:
            tags.append(f"meeting:{meeting_id}")
        owner_person_id = str(body.get("owner_person_id") or "").strip()
        if owner_person_id and f"person:{owner_person_id}" not in tags:
            tags.append(f"person:{owner_person_id}")
        raw_deciders = body.get("deciders") or []
        deciders = list(dict.fromkeys(
            str(name).strip() for name in (raw_deciders if isinstance(raw_deciders, list) else [])
            if str(name).strip()
        ))
        principal_value = principal
        registry = registry_factory()
        args = {
            "title": title,
            "status": status,
            "deciders": deciders,
            "context_markdown": f"About: {about}" if about else "",
            "decision_markdown": title,
            "alternatives": [],
            "consequences_markdown": f"Why: {why}" if why else "",
            "tags": tags,
        }
        decision, kernel = registry.invoke_receipted(principal_value, "decision.create", args)
        records = self
        matches = records.records_for_source(principal_value, "desk", str(decision["id"]))
        record = matches[0] if matches else None
        if record is None:
            return 500, {"detail": "canonical decision record was not created"}
        record = records.get(principal_value, record["id"]) or record
        return 201, {"decision": decision, "record": record, **(kernel or {})}

    def migrate_legacy_desk_decisions(self, principal: Any) -> dict[str, int]:
        """Copy retained Desk decisions into the record ledger once per source.

        ``desk_decisions`` remains the editable Desk projection for existing
        callers.  The record is the durable identity used by the Decisions
        window and Project reads.  Re-running this method is safe because
        ``create_from_desk`` is keyed by the legacy source identity.
        """
        copied = 0
        existing = 0
        # The repository list is intentionally capped for web faces. Startup
        # migration is a data operation and must copy the complete retained
        # table, including rows beyond that face limit.
        with self._db._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM desk_decisions WHERE deleted = 0 ORDER BY updated_at DESC, id DESC"
            ).fetchall()
        for decision in (self._db.desk_decisions._row(row) for row in rows):
            before = self._record_for_source("desk", decision.id)
            record = self.create_from_desk(principal, decision.id)
            if before is None and record is not None:
                copied += 1
            else:
                existing += 1
        return {"copied": copied, "existing": existing}

    def create(
        self,
        principal: Any,
        *,
        decision_text: str,
        rationale: str | None = None,
        alternatives: str | None = None,
        owner: str | None = None,
        review_date: str | None = None,
        source_type: str,
        source_id: str,
        project_id: str | None = None,
        owner_person_id: str | None = None,
        sources: tuple[tuple[str, str], ...] = (),
        kind: str = "decision",
        record_id: str | None = None,
        conn: Any = None,
    ) -> dict[str, Any]:
        """Create a decision record: the ONE writer of ``decision_records``.

        One transaction writes the record, its sources, its Person reference
        (a ``person`` source) and its Project filing (``project_resources``
        ``decision_record:<id>`` as a member, where every Project reader
        looks). ``conn`` joins a caller's open transaction (proposal confirm);
        such a caller resolves the owner to a Person BEFORE it opens the
        transaction and passes ``owner_person_id``, because a People read
        must not hold the database write lock.

        An accepted record with an owner Person and a Project is committed in
        the same transaction (2026-11-08): the follow-through commitment the
        owner sees in Needs you (``FollowThroughService
        .commit_decision_in_transaction``, keyed by the record).
        """
        text = self._required("decision_text", decision_text)
        source_kind = self._required("source_type", source_type)
        if source_kind not in _SOURCE_TYPES:
            raise ValueError("source_type must be 'meeting' or 'desk'")
        source = self._required("source_id", source_id)
        record_kind = "action" if kind == "action" else "decision"
        new_id = str(record_id or "").strip() or f"record-{uuid4().hex}"
        project = str(project_id or "").strip() or None
        person = str(owner_person_id or "").strip() or None
        owner_words = str(owner or "").strip() or None
        if person is None and conn is None:
            person = self.person_for(owner_words)
        if person is not None and owner_words is None:
            owner_words = self._person_name(person)
        # The commitment names the Person; a People read comes before the
        # write transaction. A joined transaction uses the owner's words.
        committed_name = None
        if person is not None and project is not None:
            committed_name = (self._person_name(person) if conn is None else None) or owner_words

        def write(connection: Any) -> dict[str, Any]:
            now = datetime.now(UTC).isoformat()
            connection.execute(
                """INSERT INTO decision_records
                   (id, decision_text, rationale, alternatives, owner, review_date,
                    source_type, source_id, created_at, updated_at, kind)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_id, text, rationale, alternatives, owner_words,
                 review_date or None, source_kind, source, now, now, record_kind),
            )
            refs = list(dict.fromkeys(
                (str(kind_ or "").strip(), str(ref or "").strip()) for kind_, ref in sources
            ))
            if person is not None:
                refs.append(("person", person))
            for source_type_, source_ref in refs:
                if not source_type_ or not source_ref:
                    continue
                connection.execute(
                    """INSERT INTO decision_record_sources
                       (id, record_id, source_type, source_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (f"record-source-{uuid4().hex}", new_id, source_type_, source_ref, now),
                )
            if project is not None:
                ProjectRelationshipRepository.upsert_in(
                    connection, project_id=project,
                    resource_ref=f"decision_record:{new_id}", relationship="member",
                    source="decision",
                )
            row = connection.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (new_id,)
            ).fetchone()
            assert row is not None
            if committed_name is not None:
                self._commit(connection, principal, new_id, committed_name)
            record = self._record_dict(row)
            record["project_id"] = project
            record["owner_person_id"] = person
            return record

        if conn is not None:
            return write(conn)
        with self._db._connection() as connection:
            return write(connection)

    def _commit(self, conn: Any, principal: Any, record_id: str, owner: str) -> None:
        """Commit an owned, filed record in the caller's transaction.

        A record whose source is not accepted yet (a proposed Desk decision)
        is not committed; its accept commits it (``sync_from_desk``).
        """
        from .follow_through_service import FollowThroughService

        try:
            FollowThroughService(self._db).commit_decision_in_transaction(
                conn, principal, record_id, owner=owner,
            )
        except ValueError:
            return

    def _commit_if_owned(self, principal: Any, record_id: str) -> None:
        """An accept: commit the record when it names a Person and a Project."""
        with self._db._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM decision_commitments WHERE id = ?", (f"commitment-{record_id}",),
            ).fetchone() is not None:
                return
            person = conn.execute(
                "SELECT source_ref FROM decision_record_sources WHERE record_id = ? "
                "AND source_type = 'person' ORDER BY created_at, id LIMIT 1", (record_id,),
            ).fetchone()
            filed = conn.execute(
                "SELECT 1 FROM project_resources WHERE resource_ref = ? AND deleted = 0 "
                "AND relationship = 'member' LIMIT 1", (f"decision_record:{record_id}",),
            ).fetchone()
            owner = conn.execute(
                "SELECT owner FROM decision_records WHERE id = ?", (record_id,),
            ).fetchone()
        if person is None or filed is None:
            return
        name = self._person_name(str(person["source_ref"])) or (owner["owner"] if owner else None)
        if not name:
            return
        with self._db._connection() as conn:
            self._commit(conn, principal, record_id, name)

    def person_for(self, owner: str | None) -> str | None:
        """The one Person an owner's words name, else None.

        Several names (``Mira, Theo``) name the first that resolves. Free
        text stays the record's display name either way; a locked or absent
        People store resolves nobody (never a guess).
        """
        people = self._people_service()
        if people is None:
            return None
        for name in str(owner or "").split(","):
            if not name.strip():
                continue
            try:
                found = people.resolve_owner_candidates(name.strip())
            except Exception:
                return None
            if found.get("state") != "ready":
                return None
            person = found.get("relationship") if found.get("link") == "linked" else None
            if isinstance(person, dict) and str(person.get("id") or "").strip():
                return str(person["id"]).strip()
        return None

    def _person_name(self, person_id: str) -> str | None:
        people = self._people_service()
        if people is None:
            return None
        try:
            return people.display_names().get(person_id) or None
        except Exception:
            return None

    def _people_service(self) -> Any:
        if self._people is not None:
            return self._people
        try:
            from holdspeak.runtime.composition import service as runtime_service

            return runtime_service("people_service", lambda: None)
        except Exception:
            return None

    def create_from_meeting(self, principal: Any, decision_id: str) -> dict[str, Any]:
        """Mint a record from a meeting-derived decision."""
        decision = self._db.decisions.get(decision_id)
        if decision is None:
            raise NotFound("decision", str(decision_id or "").strip())
        existing = self._record_for_source("meeting", decision.id)
        if existing is not None:
            return existing

        # A segment is precision evidence, not a prerequisite for minting the
        # record.  Keep its absence honest when the decision's moment cannot
        # be resolved from the current transcript.
        try:
            moment = self._db.decisions.resolve_decision_moment(decision.id)
        except Exception:
            moment = None
        sources: list[tuple[str, str]] = [
            ("meeting", decision.source_meeting_id),
            ("artifact", decision.source_artifact_id),
        ]
        if moment is not None:
            sources.append(("segment", str(moment.segment_id)))
        return self.create(
            principal,
            decision_text=decision.text,
            rationale=decision.rationale,
            source_type="meeting",
            source_id=decision.id,
            sources=tuple(sources),
        )

    def create_from_desk(self, principal: Any, desk_decision_id: str) -> dict[str, Any]:
        """Mint a record from an authored desk decision."""
        decision = self._db.desk_decisions.get(desk_decision_id)
        if decision is None:
            raise NotFound("decision", str(desk_decision_id or "").strip())
        existing = self._record_for_source("desk", decision.id)
        if existing is not None:
            return existing

        # A New Decision is named before its editor has a body.  Keep that
        # authored title as the initial record text; a later editor save
        # reconciles the record to the body through ``sync_from_desk``.
        decision_text = decision.decision_markdown.strip() or decision.title.strip()
        if not decision_text:
            raise ValueError("desk decision title or decision_markdown is required")
        rationale = self._join_text(
            decision.context_markdown, decision.consequences_markdown
        )
        alternatives = self._alternatives_text(decision.alternatives_json)
        owner = ", ".join(decider.strip() for decider in decision.deciders if decider.strip())
        # The Desk row's `kind:id` tags carry what its producer named: the
        # meeting (a record source), the Project (the record's filing) and
        # the Person who decided (the record's People reference).
        tagged: dict[str, list[str]] = {"meeting": [], "project": [], "person": []}
        for tag in decision.tags:
            kind, separator, ref = str(tag).partition(":")
            if separator and kind in tagged and ref.strip() and ref.strip() not in tagged[kind]:
                tagged[kind].append(ref.strip())
        return self.create(
            principal,
            decision_text=decision_text,
            rationale=rationale or None,
            alternatives=alternatives or None,
            owner=owner or None,
            source_type="desk",
            source_id=decision.id,
            sources=tuple(("meeting", ref) for ref in tagged["meeting"]),
            project_id=self.live_project(tagged["project"]),
            owner_person_id=(tagged["person"] or [None])[0],
        )

    def live_project(self, project_ids: list[str]) -> str | None:
        """The first named Project that is live (not archived), else None."""
        if not project_ids:
            return None
        with self._db._connection() as conn:
            for project_id in project_ids:
                if conn.execute(
                    "SELECT 1 FROM projects WHERE id = ? AND is_archived = 0", (project_id,)
                ).fetchone() is not None:
                    return project_id
        return None

    def sync_from_desk(self, principal: Any, desk_decision_id: str) -> dict[str, Any]:
        """Create or reconcile the canonical record for one Desk decision."""
        decision = self._db.desk_decisions.get(desk_decision_id)
        if decision is None:
            raise NotFound("decision", str(desk_decision_id or "").strip())
        record = self.create_from_desk(principal, desk_decision_id)
        if record.get("lifecycle") != "active":
            return record
        # An accept commits an owned, filed record once (a replay is a no-op).
        if str(decision.status or "").lower() == "accepted":
            self._commit_if_owned(principal, record["id"])
        # The legacy row remains for compatibility. Once the canonical record
        # has a HAND revision, reopening the old editor must not replace
        # canonical words with its stale projection. The revisions this sync
        # writes carry the ``_SYNC_REVISION`` id prefix and do not count, so
        # every later Desk edit still reaches the record.
        with self._db._connection() as conn:
            authored = conn.execute(
                "SELECT 1 FROM decision_record_revisions WHERE record_id = ? "
                "AND id NOT LIKE ? LIMIT 1",
                (record["id"], f"{_SYNC_REVISION}%"),
            ).fetchone()
            named = conn.execute(
                "SELECT 1 FROM decision_record_sources WHERE record_id = ? "
                "AND source_type = 'person' LIMIT 1",
                (record["id"],),
            ).fetchone()
        if authored is not None:
            return self._decorate(record)
        deciders = ", ".join(decider.strip() for decider in decision.deciders if decider.strip())
        fields = {
            "decision_text": decision.decision_markdown.strip() or decision.title.strip(),
            "rationale": self._join_text(
                decision.context_markdown, decision.consequences_markdown
            ) or None,
            "alternatives": self._alternatives_text(decision.alternatives_json) or None,
            # A record that names its Person keeps that Person's name when
            # the Desk row names no decider.
            "owner": deciders or (record.get("owner") if named is not None else None),
        }
        return self._decorate(self.update_record(
            principal,
            record["id"],
            {field: value for field, value in fields.items() if record.get(field) != value},
            revision_prefix=_SYNC_REVISION,
        ))

    def add_source(self, principal: Any, record_id: str, source_type: str, source_ref: str) -> None:
        """Attach one navigable source to a canonical record idempotently."""
        del principal
        kind = self._required("source_type", source_type)
        reference = self._required("source_ref", source_ref)
        with self._db._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone() is None:
                raise KeyError(str(record_id or "").strip())
            if conn.execute(
                """SELECT 1 FROM decision_record_sources
                   WHERE record_id = ? AND source_type = ? AND source_ref = ?""",
                (record_id, kind, reference),
            ).fetchone() is None:
                conn.execute(
                    """INSERT INTO decision_record_sources
                       (id, record_id, source_type, source_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (f"record-source-{uuid4().hex}", record_id, kind, reference, datetime.now(UTC).isoformat()),
                )

    def update_record(
        self,
        principal: Any,
        record_id: str,
        fields: dict[str, Any],
        *,
        revision_prefix: str = "record-revision-",
    ) -> dict[str, Any]:
        """Update record facts and record every changed field as a revision."""
        unknown_fields = set(fields) - _EDITABLE_FIELDS
        if unknown_fields:
            raise ValueError(f"record fields cannot be edited: {', '.join(sorted(unknown_fields))}")
        if "decision_text" in fields:
            fields = {**fields, "decision_text": self._required("decision_text", fields["decision_text"])}

        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone()
            if row is None:
                raise KeyError(str(record_id or "").strip())
            if row["lifecycle"] != "active":
                raise ValueError(f"record is sealed: {record_id}")
            changes = {
                field: value for field, value in fields.items() if row[field] != value
            }
            if not changes:
                return self._record_dict(row)

            now = datetime.now(UTC).isoformat()
            conn.execute(
                f"UPDATE decision_records SET {', '.join(f'{field} = ?' for field in changes)}, "
                "updated_at = ? WHERE id = ?",
                (*changes.values(), now, record_id),
            )
            for field, value in changes.items():
                conn.execute(
                    """INSERT INTO decision_record_revisions
                       (id, record_id, field_name, old_value, new_value, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        f"{revision_prefix}{uuid4().hex}",
                        record_id,
                        field,
                        row[field],
                        value,
                        now,
                    ),
                )
            updated = conn.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone()
        assert updated is not None
        return self._record_dict(updated)

    def link_work(
        self, principal: Any, record_id: str, work_type: str, work_ref: str
    ) -> dict[str, Any]:
        """Link typed affected work to a record without duplicating the link."""
        kind = self._required("work_type", work_type)
        reference = self._required("work_ref", work_ref)
        with self._db._connection() as conn:
            if conn.execute(
                "SELECT 1 FROM decision_records WHERE id = ?", (record_id,)
            ).fetchone() is None:
                raise KeyError(str(record_id or "").strip())
            row = conn.execute(
                """SELECT * FROM decision_record_work
                   WHERE record_id = ? AND work_type = ? AND work_ref = ?""",
                (record_id, kind, reference),
            ).fetchone()
            if row is None:
                now = datetime.now(UTC).isoformat()
                work_id = f"record-work-{uuid4().hex}"
                conn.execute(
                    """INSERT INTO decision_record_work
                       (id, record_id, work_type, work_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (work_id, record_id, kind, reference, now),
                )
                row = conn.execute(
                    "SELECT * FROM decision_record_work WHERE id = ?", (work_id,)
                ).fetchone()
        assert row is not None
        return dict(row)

    def unlink_work(
        self, principal: Any, record_id: str, work_type: str, work_ref: str
    ) -> bool:
        """Remove one typed record-to-work link without deleting either end."""
        with self._db._connection() as conn:
            result = conn.execute(
                """DELETE FROM decision_record_work
                   WHERE record_id = ? AND work_type = ? AND work_ref = ?""",
                (record_id, self._required("work_type", work_type), self._required("work_ref", work_ref)),
            )
        return result.rowcount > 0

    def list_work(self, principal: Any, record_id: str) -> list[dict[str, Any]]:
        """List typed work governed by a record."""
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT * FROM decision_record_work
                   WHERE record_id = ? ORDER BY created_at, id""",
                (record_id,),
            ).fetchall()
        return self._rows(rows)

    def records_for_work(
        self, principal: Any, work_type: str, work_ref: str
    ) -> list[dict[str, Any]]:
        """List records that govern one typed work item."""
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT r.* FROM decision_records AS r
                   JOIN decision_record_work AS w ON w.record_id = r.id
                   WHERE w.work_type = ? AND w.work_ref = ? AND {_NOT_AN_ACTION}
                   ORDER BY r.created_at DESC, r.id DESC""",
                (self._required("work_type", work_type), self._required("work_ref", work_ref)),
            ).fetchall()
        return [self._decorate(self._record_dict(row)) for row in rows]

    def records_for_source(
        self, principal: Any, source_type: str, source_id: str
    ) -> list[dict[str, Any]]:
        """List records minted from one stable source identity."""
        del principal
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT r.* FROM decision_records AS r
                   WHERE r.source_type = ? AND r.source_id = ? AND r.deleted = 0
                     AND {_NOT_AN_ACTION}
                   ORDER BY r.created_at DESC, r.id DESC""",
                (self._required("source_type", source_type), self._required("source_id", source_id)),
            ).fetchall()
        return [self._decorate(self._record_dict(row)) for row in rows]

    def confirmed_for_meeting(self, meeting_id: str) -> list[dict[str, Any]]:
        """Current confirmed meeting evidence, using canonical edited words.

        Retained accepted rows with no canonical record remain readable. A
        canonical record that was superseded or disputed never falls back to
        its old source text.
        """
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT DISTINCT r.decision_text, r.rationale, d.source_timestamp
                    FROM decision_records r
                    JOIN decision_record_sources s ON s.record_id = r.id
                        AND s.source_type = 'meeting' AND s.source_ref = ?
                    LEFT JOIN decisions d ON r.source_type = 'meeting' AND d.id = r.source_id
                    LEFT JOIN desk_decisions dd ON r.source_type = 'desk' AND dd.id = r.source_id
                    WHERE r.deleted = 0 AND r.lifecycle IN ('active', 'published')
                      AND {_NOT_AN_ACTION}
                      AND ((d.deleted = 0 AND d.lifecycle = 'accepted')
                        OR (dd.deleted = 0 AND LOWER(dd.status) = 'accepted')
                        OR EXISTS (SELECT 1 FROM follow_through_proposals fp
                            WHERE fp.decision_record_id = r.id AND fp.kind = 'decision'
                              AND fp.state = 'confirmed'))
                    UNION ALL
                    SELECT d.text AS decision_text, d.rationale, d.source_timestamp
                    FROM decisions d
                    WHERE d.source_meeting_id = ? AND d.deleted = 0 AND d.lifecycle = 'accepted'
                      AND NOT EXISTS (SELECT 1 FROM decision_records r
                          WHERE r.source_type = 'meeting' AND r.source_id = d.id)""",
                (str(meeting_id).strip(), str(meeting_id).strip()),
            ).fetchall()
        return self._rows(rows)

    def supersede(
        self,
        principal: Any,
        record_id: str,
        successor_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Seal a record while retaining its navigable successor lineage.

        HS-200-13: the DECIDE right is required (an UNAUTHENTICATED caller is
        refused by name), as for ``dispute`` and the carry mark.
        """
        require_right(principal, PrincipalRight.DECIDE)
        if record_id == successor_id:
            raise ValueError("record cannot supersede itself")
        with self._db._connection() as conn:
            predecessor = conn.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone()
            if predecessor is None:
                raise KeyError(str(record_id or "").strip())
            successor = conn.execute(
                "SELECT * FROM decision_records WHERE id = ?", (successor_id,)
            ).fetchone()
            if successor is None:
                raise KeyError(str(successor_id or "").strip())
            if predecessor["lifecycle"] not in _SUPERSEDABLE:
                raise ValueError(f"record is sealed: {record_id}")
            if successor["lifecycle"] != "active":
                raise ValueError(f"successor is sealed: {successor_id}")
            if conn.execute(
                """SELECT 1 FROM decision_record_sources
                   WHERE record_id = ? AND source_type = 'predecessor'""",
                (successor_id,),
            ).fetchone() is not None:
                raise ValueError(f"successor already has a predecessor: {successor_id}")

            now = datetime.now(UTC).isoformat()
            conn.execute(
                "UPDATE decision_records SET lifecycle = 'superseded', updated_at = ? WHERE id = ?",
                (now, record_id),
            )
            for field_name, old_value, new_value in (
                ("lifecycle", predecessor["lifecycle"], "superseded"),
                ("successor_id", None, successor_id),
                ("supersession_reason", None, reason),
            ):
                conn.execute(
                    """INSERT INTO decision_record_revisions
                       (id, record_id, field_name, old_value, new_value, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        f"record-revision-{uuid4().hex}",
                        record_id,
                        field_name,
                        old_value,
                        new_value,
                        now,
                    ),
                )
            for linked_record_id, source_type, source_ref in (
                (record_id, "successor", successor_id),
                (successor_id, "predecessor", record_id),
            ):
                conn.execute(
                    """INSERT INTO decision_record_sources
                       (id, record_id, source_type, source_ref, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        f"record-source-{uuid4().hex}",
                        linked_record_id,
                        source_type,
                        source_ref,
                        now,
                    ),
                )
        sealed = self.get(principal, record_id)
        assert sealed is not None
        return sealed

    def dispute(
        self, principal: Any, record_id: str, reason: str | None = None,
    ) -> dict[str, Any]:
        """HS-200-13 (AC2): mark an active record DISPUTED.

        Minimal by design: the lifecycle flips, the reason is a revision row,
        a kernel receipt is written.  A disputed record stays discoverable
        and is never presented as current; superseding it with a newer
        decision is how a dispute ends.  The DECIDE right is required.
        """
        require_right(principal, PrincipalRight.DECIDE)
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone()
            if row is None:
                raise KeyError(str(record_id or "").strip())
            if row["lifecycle"] == "disputed":
                return self.get(principal, record_id) or self._record_dict(row)
            if row["lifecycle"] not in CURRENT_LIFECYCLES:
                raise ValueError(f"record is sealed: {record_id}")
            now = datetime.now(UTC).isoformat()
            conn.execute(
                "UPDATE decision_records SET lifecycle = 'disputed', updated_at = ? WHERE id = ?",
                (now, record_id),
            )
            for field_name, old_value, new_value in (
                ("lifecycle", row["lifecycle"], "disputed"),
                ("dispute_reason", None, (str(reason).strip() or None) if reason else None),
            ):
                conn.execute(
                    """INSERT INTO decision_record_revisions
                       (id, record_id, field_name, old_value, new_value, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (f"record-revision-{uuid4().hex}", record_id, field_name, old_value, new_value, now),
                )
            ServiceEventLedger(self._db).append_in_transaction(
                conn, principal,
                event_type="decision.disputed",
                producer=type(self).__name__,
                subject_ref=f"decision_record:{record_id}",
                source_revision=now,
                facts={
                    "record_id": record_id,
                    "reason": (str(reason).strip() if reason else ""),
                    "entity_title": str(row["decision_text"] or ""),
                },
                refs=[f"decision_record:{record_id}"],
                correlation_id=current_correlation_id(),
                causation_id=f"decision_record:{record_id}",
            )
        disputed = self.get(principal, record_id)
        assert disputed is not None
        return disputed

    def carry(self, principal: Any, record_id: str, *, project_id: str | None = None) -> dict[str, Any]:
        """`Carry into brief`: queue the record, by reference, for its Project's
        next preparation (``brief_carry.carry_into_brief``)."""
        from holdspeak.services.brief_carry import carry_into_brief

        try:
            return carry_into_brief(self._db, principal, record_id, project_id=project_id)
        except KeyError as exc:  # an unknown record is a typed not_found on every transport
            raise NotFound("decision_record", str(exc.args[0] if exc.args else record_id)) from exc

    def due_for_review(self, principal: Any) -> list[dict[str, Any]]:
        """Return active records whose review date is today or earlier."""
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT r.* FROM decision_records AS r
                   WHERE r.review_date IS NOT NULL AND r.review_date <= ?
                     AND r.lifecycle = 'active' AND r.deleted = 0 AND {_NOT_AN_ACTION}
                     AND NOT EXISTS (
                       SELECT 1 FROM desk_decisions AS dd
                       WHERE r.source_type = 'desk' AND dd.id = r.source_id
                         AND dd.deleted = 0 AND LOWER(dd.status) = 'proposed'
                     )
                   ORDER BY review_date, created_at, id""",
                (date.today().isoformat(),),
            ).fetchall()
        return [self._decorate(self._record_dict(row)) for row in rows]

    def get(self, principal: Any, record_id: str) -> dict[str, Any] | None:
        """Get a record by ID with its sources, work links, and revisions."""
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_records WHERE id = ? AND deleted = 0", (record_id,)
            ).fetchone()
            if row is None:
                return None
            record = self._decorate(self._record_dict(row), conn)
            record["sources"] = [
                self._source_dict(conn, source)
                for source in conn.execute(
                    """SELECT * FROM decision_record_sources
                       WHERE record_id = ? ORDER BY created_at, id""",
                    (record_id,),
                ).fetchall()
            ]
            record["work"] = self._rows(
                conn.execute(
                    """SELECT * FROM decision_record_work
                       WHERE record_id = ? ORDER BY created_at, id""",
                    (record_id,),
                ).fetchall()
            )
            record["revisions"] = self._rows(
                conn.execute(
                    """SELECT * FROM decision_record_revisions
                       WHERE record_id = ? ORDER BY created_at, id""",
                    (record_id,),
                ).fetchall()
            )
            # The record's Person reference and its Project filing (the one
            # place every Project reader joins: `decision_record:<id>`).
            record["owner_person_id"] = next(
                (source["source_ref"] for source in record["sources"] if source["source_type"] == "person"),
                None,
            )
            filed = conn.execute(
                """SELECT project_id FROM project_resources
                   WHERE resource_ref = ? AND deleted = 0 AND relationship = 'member'
                   ORDER BY created_at, project_id LIMIT 1""",
                (f"decision_record:{record_id}",),
            ).fetchone()
            record["project_id"] = str(filed["project_id"]) if filed is not None else None
            # 2026-11-08: the name the record is committed to, or None.
            committed = conn.execute(
                "SELECT owner FROM decision_commitments WHERE id = ?", (f"commitment-{record_id}",),
            ).fetchone()
            record["committed_to"] = (str(committed["owner"] or "") or None) if committed else None
            record["successor_id"] = next(
                (source["source_ref"] for source in record["sources"] if source["source_type"] == "successor"),
                None,
            )
            record["predecessor_id"] = next(
                (source["source_ref"] for source in record["sources"] if source["source_type"] == "predecessor"),
                None,
            )
            record["supersession_reason"] = next(
                (revision["new_value"] for revision in record["revisions"]
                 if revision["field_name"] == "supersession_reason"),
                None,
            )
            record["dispute_reason"] = next(
                (revision["new_value"] for revision in reversed(record["revisions"])
                 if revision["field_name"] == "dispute_reason"),
                None,
            )
            return record

    def list_records(
        self, principal: Any, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List records, newest first."""
        bounded_limit = max(1, min(int(limit), 500))
        bounded_offset = max(0, int(offset))
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT r.* FROM decision_records AS r
                   WHERE r.deleted = 0 AND {_NOT_AN_ACTION}
                   ORDER BY r.created_at DESC, r.id DESC LIMIT ? OFFSET ?""",
                (bounded_limit, bounded_offset),
            ).fetchall()
        return [self._decorate(self._record_dict(row)) for row in rows]

    def search(
        self, principal: Any, query: str, *, limit: int = 50, recent: bool = False
    ) -> list[dict[str, Any]]:
        """Find records by their decision facts or linked affected-work labels.

        Record tables deliberately remain ordinary SQLite tables, so this uses a
        portable case-insensitive LIKE search rather than requiring an FTS build.
        The CASE expression keeps direct decision matches ahead of supporting
        rationale, owner, and work-link matches.
        """
        terms = [
            term.strip("?!.,:;\"'()[]{}")
            for term in str(query or "").strip().split()
            if term.strip("?!.,:;\"'()[]{}") and term.lower().strip("?!.,:;\"'()[]{}")
            not in {"why", "what", "when", "where", "who", "how", "is", "are", "was", "were", "the", "a", "an"}
        ]
        bounded_limit = max(1, min(int(limit), 500))
        if not terms:
            # HS-202-02 — `recent` is an EXPLICIT read: the newest records,
            # in the same shape a search answers. Without it a wordless
            # search is still a search with no words, and answers nothing.
            if not recent:
                return []
            with self._db._connection() as conn:
                rows = conn.execute(
                    f"""SELECT r.*, 0 AS relevance
                       FROM decision_records AS r
                       WHERE r.deleted = 0 AND {_NOT_AN_ACTION}
                       ORDER BY r.updated_at DESC, r.id DESC
                       LIMIT ?""",
                    (bounded_limit,),
                ).fetchall()
            return [self._decorate(self._record_dict(row)) for row in rows]
        predicates: list[str] = []
        params: list[str] = []
        for term in terms:
            pattern = like_literal(term)
            predicates.append(
                "(r.decision_text LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                "COALESCE(r.rationale, '') LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                "COALESCE(r.alternatives, '') LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                "COALESCE(r.owner, '') LIKE ? ESCAPE '\\' COLLATE NOCASE OR "
                "EXISTS (SELECT 1 FROM decision_record_work AS w "
                "WHERE w.record_id = r.id AND "
                "(w.work_type LIKE ? ESCAPE '\\' COLLATE NOCASE OR w.work_ref LIKE ? ESCAPE '\\' COLLATE NOCASE)))"
            )
            params.extend([pattern] * 6)
        relevance = (
            "CASE WHEN r.decision_text LIKE ? ESCAPE '\\' COLLATE NOCASE THEN 4 "
            "WHEN COALESCE(r.rationale, '') LIKE ? ESCAPE '\\' COLLATE NOCASE THEN 3 "
            "WHEN COALESCE(r.alternatives, '') LIKE ? ESCAPE '\\' COLLATE NOCASE THEN 2 "
            "WHEN COALESCE(r.owner, '') LIKE ? ESCAPE '\\' COLLATE NOCASE THEN 1 "
            "ELSE 0 END"
        )
        phrase = like_literal(" ".join(terms))
        with self._db._connection() as conn:
            rows = conn.execute(
                f"""SELECT r.*, {relevance} AS relevance
                    FROM decision_records AS r
                    WHERE r.deleted = 0 AND {_NOT_AN_ACTION} AND {' AND '.join(predicates)}
                    ORDER BY relevance DESC, r.updated_at DESC, r.id DESC
                    LIMIT ?""",
                [phrase] * 4 + params + [bounded_limit],
            ).fetchall()
        return [self._decorate(self._record_dict(row)) for row in rows]

    def _record_for_source(self, source_type: str, source_id: str) -> dict[str, Any] | None:
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT * FROM decision_records
                   WHERE source_type = ? AND source_id = ?
                   ORDER BY created_at, id LIMIT 1""",
                (source_type, source_id),
            ).fetchone()
        return self._record_dict(row) if row is not None else None

    @staticmethod
    def _join_text(*values: str) -> str:
        return "\n\n".join(str(value or "").strip() for value in values if str(value or "").strip())

    @staticmethod
    def _alternatives_text(value: str) -> str:
        try:
            alternatives = json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError):
            return ""
        return json.dumps(alternatives, ensure_ascii=False) if alternatives else ""

    @staticmethod
    def _required(name: str, value: str) -> str:
        clean = str(value or "").strip()
        if not clean:
            raise ValueError(f"{name} is required")
        return clean

    def _decorate(self, record: dict[str, Any], conn: Any | None = None) -> dict[str, Any]:
        """Expose the retained Desk source status with the canonical row."""
        if record.get("source_type") != "desk":
            return record
        query = "SELECT status, title FROM desk_decisions WHERE id = ? AND deleted = 0"
        if conn is not None:
            row = conn.execute(query, (record.get("source_id"),)).fetchone()
        else:
            with self._db._connection() as connection:
                row = connection.execute(query, (record.get("source_id"),)).fetchone()
        if row is not None:
            record["status"] = str(row["status"] or "proposed")
            # W1-TRUTH (atlas 2026-10-27): a Desk decision's list row is
            # named by its title; the record holds only the decision text.
            title = str(row["title"] or "").strip()
            if title:
                record["title"] = title
        return record

    @staticmethod
    def _record_dict(row: Any) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _source_dict(conn: Any, row: Any) -> dict[str, Any]:
        """Enrich a record source with the target data needed to open it."""
        source = dict(row)
        source_type = source["source_type"]
        source_ref = source["source_ref"]
        if source_type == "segment":
            target = conn.execute(
                """SELECT id, meeting_id, text, speaker, start_time, end_time
                   FROM segments WHERE id = ?""",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = dict(target)
                source.update(details)
                source["details"] = details
        elif source_type == "meeting":
            target = conn.execute(
                "SELECT id, title, started_at FROM meetings WHERE id = ?",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = {"title": target["title"], "date": target["started_at"]}
                source.update(details)
                source["details"] = details
        elif source_type == "artifact":
            target = conn.execute(
                "SELECT id, artifact_type FROM artifacts WHERE id = ?",
                (source_ref,),
            ).fetchone()
            if target is not None:
                details = {"artifact_type": target["artifact_type"]}
                source.update(details)
                source["details"] = details
        return source

    @staticmethod
    def _rows(rows: list[Any]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]
