"""Encrypted, local-only People application boundary.

This service deliberately knows no normal HoldSpeak database, inference target,
sync service, or logger.  It is the only application-facing adapter over the
encrypted sidecar for the manual People slice.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..principals import PrincipalKind
from .follow_through_service import CardProvenance, FollowThroughCard


class PeopleServiceError(ValueError):
    """A stable, content-free error suitable for a local HTTP edge."""


class PeopleUnavailable(PeopleServiceError):
    """The encrypted sidecar is not available; never fall back to plaintext."""


class SeriesAlreadyLinked(PeopleServiceError):
    """Invariant P1: a calendar series is already linked to another relationship."""

    def __init__(self, holder_id: str, holder_name: str) -> None:
        self.holder_id = holder_id
        self.holder_name = holder_name
        super().__init__("series_already_linked")


class OwnerAliasTaken(PeopleServiceError):
    """Invariant P2: an owner alias is already linked to another relationship."""

    def __init__(self, holder_id: str, holder_name: str) -> None:
        self.holder_id = holder_id
        self.holder_name = holder_name
        super().__init__("owner_alias_taken")


_VISIBILITIES = frozenset({"shared_intent", "leader_private"})
_RESERVED_OWNER_ALIASES = frozenset({"me", "remote", "you"})
_RELATIONSHIP_KINDS = frozenset({"direct_report", "peer", "extended"})
_ENTRY_KINDS = frozenset({"one_on_one"})
_RECORD_KINDS = frozenset({"request", "commitment", "grounding_note"})
_OPEN_COMMITMENT = "open"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class UnavailablePeopleStore:
    """Composition-time key/backend failure without a plaintext substitute."""

    def readiness(self) -> str:
        return "unavailable"

    def initialize(self) -> str:
        raise RuntimeError("people_store_unavailable")


class PeopleService:
    """Principal-aware domain operations over an ``EncryptedPeopleStore``.

    The store has encrypted payloads at rest.  This boundary validates the small
    PR1 ontology and keeps an accidental route payload from becoming a new
    capture, connector, export, or AI feature.
    """

    def __init__(self, store: Any, *, setup_runner: Any = None) -> None:
        self._store = store
        self._setup_runner = setup_runner

    def readiness(self, principal: Any) -> dict[str, str]:
        self._require_owner(principal)
        try:
            state = self._store.readiness()
        except Exception as exc:  # Store errors intentionally contain no content.
            raise PeopleUnavailable("people_store_unavailable") from exc
        return self._readiness_view(state)

    def setup(self, principal: Any) -> dict[str, str]:
        """The one deliberate owner gesture that can create an encrypted sidecar."""
        self._require_owner(principal)
        try:
            runner = self._setup_runner
            if runner is None:
                from ..kernel.people_store_setup import run_people_store_setup
                runner = run_people_store_setup
            state = runner(initialize=self._store.initialize, principal=principal)
        except Exception as exc:
            raise PeopleUnavailable("people_store_unavailable") from exc
        return self._readiness_view(state)

    def list_relationships(self, principal: Any, *, include_archived: bool = False) -> list[dict[str, Any]]:
        self._require_ready_owner(principal)
        return [self._relationship_view(item) for item in self._list("relationship", active_only=not include_archived)]

    def create_relationship(self, principal: Any, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_ready_owner(principal)
        name = self._text(payload, "display_name", required=True, limit=240)
        kind = str(payload.get("relationship_kind") or "direct_report")
        if kind not in _RELATIONSHIP_KINDS:
            raise PeopleServiceError("people_relationship_kind_unsupported")
        record = self._create("relationship", {
            "display_name": name, "relationship_kind": kind,
            "role_context": self._text(payload, "role_context", limit=500),
            "timezone": self._text(payload, "timezone", limit=80),
            "cadence": self._text(payload, "cadence", limit=80),
            "state": "active", "lifecycle": "active", "created_at": _now(), "updated_at": _now(),
        })
        return self._relationship_view(record)

    def get_relationship(self, principal: Any, relationship_id: str) -> dict[str, Any]:
        self._require_ready_owner(principal)
        record = self._get(relationship_id, "relationship")
        if record is None or str(record.get("state") or "") == "archived":
            raise PeopleServiceError("people_relationship_not_found")
        view = self._relationship_view(record)
        sessions = self.list_one_on_ones(principal, relationship_id)
        requests = [self._record_view(item) for item in self._list("request", relationship_id=relationship_id)]
        commitments = [self._record_view(item) for item in self._list("commitment", relationship_id=relationship_id)]
        notes = [self._record_view(item) for item in self._list("grounding_note", relationship_id=relationship_id)]
        view.update({"sessions": sessions, "requests": requests, "commitments": commitments, "notes": notes})
        return view

    def archive_relationship(self, principal: Any, relationship_id: str) -> dict[str, Any]:
        self._require_ready_owner(principal)
        record = self._get(relationship_id, "relationship")
        if record is None:
            raise PeopleServiceError("people_relationship_not_found")
        return self._relationship_view(self._archive(relationship_id))

    def link_project(self, principal: Any, relationship_id: str, project_id: str) -> dict[str, Any]:
        relationship = self._require_relationship(principal, relationship_id)
        clean_project_id = str(project_id or "").strip()
        if not clean_project_id:
            raise PeopleServiceError("people_project_required")
        refs = [str(value) for value in relationship.get("project_refs") or [] if str(value).strip()]
        if clean_project_id not in refs:
            refs.append(clean_project_id)
        value = dict(relationship)
        value.update({"project_refs": refs, "updated_at": _now()})
        return self._relationship_view(self._replace(relationship_id, value))

    def unlink_project(self, principal: Any, relationship_id: str, project_id: str) -> dict[str, Any]:
        relationship = self._require_relationship(principal, relationship_id)
        value = dict(relationship)
        value.update({
            "project_refs": [
                str(ref) for ref in relationship.get("project_refs") or []
                if str(ref) != str(project_id)
            ],
            "updated_at": _now(),
        })
        return self._relationship_view(self._replace(relationship_id, value))

    def list_one_on_ones(self, principal: Any, relationship_id: str) -> list[dict[str, Any]]:
        self._require_relationship(principal, relationship_id)
        sessions = [self._entry_view(item) for item in self._list("one_on_one", relationship_id=relationship_id)]
        for session in sessions:
            session["agenda"] = [self._agenda_view(item) for item in self._list("agenda_item", relationship_id=relationship_id) if item.get("session_id") == session["id"]]
        return sessions

    def create_one_on_one(self, principal: Any, relationship_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_relationship(principal, relationship_id)
        visibility = self._visibility(payload)
        record = self._create("one_on_one", {
            "relationship_id": relationship_id,
            "agenda": self._text(payload, "agenda", limit=20_000),
            "private_prep": self._text(payload, "private_prep", limit=20_000),
            "visibility": visibility, "state": "active", "lifecycle": "active", "created_at": _now(), "updated_at": _now(),
        })
        return self._entry_view(record)

    def create_request(self, principal: Any, relationship_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_relationship(principal, relationship_id)
        record = self._create("request", {
            "relationship_id": relationship_id,
            "body": self._text(payload, "body", required=True, limit=20_000),
            "visibility": self._visibility(payload), "state": "requested", "lifecycle": "requested",
            "created_at": _now(), "updated_at": _now(),
        })
        return self._record_view(record)

    def list_notes(self, principal: Any, relationship_id: str) -> list[dict[str, Any]]:
        """Return durable manual context notes for one active relationship."""
        self._require_relationship(principal, relationship_id)
        return [
            self._record_view(item)
            for item in self._list("grounding_note", relationship_id=relationship_id)
        ]

    def create_note(self, principal: Any, relationship_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Create explicit grounding material without running or scheduling a model."""
        self._require_relationship(principal, relationship_id)
        record = self._create("grounding_note", {
            "relationship_id": relationship_id,
            "topic": self._text(payload, "topic", limit=240),
            "body": self._text(payload, "body", required=True, limit=20_000),
            "visibility": self._visibility(payload),
            "source": "manual",
            "state": "active",
            "lifecycle": "active",
            "created_at": _now(),
            "updated_at": _now(),
        })
        return self._record_view(record)

    def accept_request(self, principal: Any, request_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Explicitly mint one manager commitment; a request alone is never a card."""
        self._require_ready_owner(principal)
        request = self._get(request_id, "request")
        if request is None:
            raise PeopleServiceError("people_request_not_found")
        self._require_relationship(principal, str(request.get("relationship_id") or ""))
        body = self._text(payload or {}, "body", limit=20_000) or str(request.get("body") or "")
        commitment_payload = {
            "relationship_id": str(request.get("relationship_id") or ""),
            "request_id": request_id, "body": body, "visibility": str(request.get("visibility") or "leader_private"),
            "direction": "leader_owes", "state": _OPEN_COMMITMENT, "lifecycle": _OPEN_COMMITMENT,
            "execution_links": [],
            "history": [{"event": "accepted", "state": _OPEN_COMMITMENT, "at": _now(), "source": "people"}],
            "created_at": _now(), "updated_at": _now(),
        }
        try:
            _accepted, commitment = self._store.accept_request(request_id, commitment_payload)
        except ValueError as exc:
            code = str(exc)
            if code == "people_relationship_inactive":
                raise PeopleServiceError("people_relationship_not_found") from exc
            if code == "people_request_not_acceptable":
                raise PeopleServiceError(code) from exc
            raise PeopleUnavailable("people_store_write_failed") from exc
        except Exception as exc:
            # The store performs the idempotent check and both encrypted writes in
            # one immediate transaction; content never crosses this error edge.
            raise PeopleUnavailable("people_store_write_failed") from exc
        return self._record_view(commitment)

    def get_request(self, principal: Any, request_id: str) -> dict[str, Any]:
        """Read one request through the domain boundary for scoped adapters."""
        self._require_ready_owner(principal)
        request = self._get(request_id, "request")
        if request is None:
            raise PeopleServiceError("people_request_not_found")
        self._require_relationship(principal, str(request.get("relationship_id") or ""))
        return self._record_view(request)

    def get_commitment(self, principal: Any, commitment_id: str) -> dict[str, Any]:
        """Read one commitment through the domain boundary for scoped adapters."""
        self._require_ready_owner(principal)
        commitment = self._get(commitment_id, "commitment")
        if commitment is None:
            raise PeopleServiceError("people_commitment_not_found")
        self._require_relationship(principal, str(commitment.get("relationship_id") or ""))
        return self._record_view(commitment)

    def attach_execution(
        self,
        principal: Any,
        commitment_id: str,
        *,
        workbench_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """Link durable execution work without creating a second commitment authority."""
        self._require_ready_owner(principal)
        commitment = self._get(commitment_id, "commitment")
        if commitment is None:
            raise PeopleServiceError("people_commitment_not_found")
        self._require_relationship(principal, str(commitment.get("relationship_id") or ""))
        links = [dict(link) for link in commitment.get("execution_links") or [] if isinstance(link, dict)]
        for link in links:
            if link.get("workbench_id") == workbench_id and link.get("item_id") == item_id:
                return self._record_view(commitment)
        now = _now()
        links.append({"kind": "workbench_item", "workbench_id": workbench_id, "item_id": item_id, "linked_at": now})
        history = self._history(commitment)
        history.append({"event": "delegated", "state": str(commitment.get("state") or "open"), "at": now, "source": "workbench", "workbench_id": workbench_id, "item_id": item_id})
        value = dict(commitment)
        value.update({"execution_links": links, "history": history, "updated_at": now})
        return self._record_view(self._replace(commitment_id, value))

    def satisfy_commitment(
        self,
        principal: Any,
        commitment_id: str,
        *,
        rationale: str = "",
        evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self._require_ready_owner(principal)
        commitment = self._get(commitment_id, "commitment")
        if commitment is None:
            raise PeopleServiceError("people_commitment_not_found")
        self._require_relationship(principal, str(commitment.get("relationship_id") or ""))
        return self._transition_commitment(
            commitment,
            "done",
            event="satisfied",
            source="people",
            rationale=str(rationale or "").strip()[:2000],
            evidence=evidence or [],
        )

    def history_summary(self, principal: Any, relationship_id: str | None = None) -> dict[str, Any]:
        """Compute relationship follow-through history from the encrypted authority."""
        self._require_ready_owner(principal)
        if relationship_id is not None:
            self._require_relationship(principal, relationship_id)
        rows = [
            self._record_view(item)
            for item in self._list("commitment", **({"relationship_id": relationship_id} if relationship_id else {}))
        ]
        satisfied = sum(1 for item in rows if item.get("state") == "done")
        dismissed = sum(1 for item in rows if item.get("state") == "dismissed")
        reopened = sum(
            1 for item in rows
            if any(event.get("event") == "reopened" for event in item.get("history") or [] if isinstance(event, dict))
        )
        return {
            "accepted": len(rows),
            "open": sum(1 for item in rows if item.get("state") == "open"),
            "satisfied": satisfied,
            "dismissed": dismissed,
            "reopened": reopened,
            "with_evidence": sum(
                1 for item in rows
                if any(event.get("evidence") for event in item.get("history") or [] if isinstance(event, dict))
            ),
            "commitments": rows,
        }

    def add_agenda_item(self, principal: Any, session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_ready_owner(principal)
        session = self._get(session_id, "one_on_one")
        if session is None:
            raise PeopleServiceError("people_one_on_one_not_found")
        relationship_id = str(session.get("relationship_id") or "")
        self._require_relationship(principal, relationship_id)
        rolled_from = self._text(payload, "rolled_from_id", limit=100)
        item_payload = {
            "session_id": session_id, "relationship_id": relationship_id,
            "body": self._text(payload, "body", required=True, limit=20_000),
            "visibility": self._visibility(payload), "state": "open", "lifecycle": "active",
            "rolled_from_id": rolled_from or None, "created_at": _now(), "updated_at": _now(),
        }
        if rolled_from:
            try:
                _rolled, item = self._store.roll_agenda_item(rolled_from, item_payload)
            except ValueError as exc:
                raise PeopleServiceError(str(exc)) from exc
            except Exception as exc:
                raise PeopleUnavailable("people_store_write_failed") from exc
        else:
            item = self._create("agenda_item", item_payload)
        return self._agenda_view(item)

    # -- Brief (D5, D6) — read-time, NEVER persisted --------------------------------

    def one_on_one_brief(
        self, principal: Any, relationship_id: str, *, db: Any = None,
    ) -> dict[str, Any]:
        """Compute a read-time 1:1 brief across the encrypted/plaintext boundary.

        The brief aggregates encrypted People content (commitments, agenda,
        grounding notes) with plaintext meeting data (linked meetings, their
        open action items, decision records) and returns it as a transient dict.
        It NEVER writes to any store — the 138 law.

        ``db`` is the main HoldSpeak database; when ``None`` the plaintext
        sections degrade gracefully to empty lists.
        """
        relationship = self._require_relationship(principal, relationship_id)

        # Encrypted: open commitments for this relationship.
        open_commitments = [
            self._record_view(item)
            for item in self._list("commitment", relationship_id=relationship_id)
            if item.get("state") == _OPEN_COMMITMENT
        ]

        # Encrypted: open agenda items across all sessions.
        sessions = self._list("one_on_one", relationship_id=relationship_id)
        session_ids = {str(s.get("id") or "") for s in sessions}
        agenda_items = [
            self._agenda_view(item)
            for item in self._list("agenda_item", relationship_id=relationship_id)
            if str(item.get("session_id") or "") in session_ids
            and str(item.get("state") or "") == "open"
        ]

        # Encrypted: grounding note count.
        grounding_note_count = len(
            self._list("grounding_note", relationship_id=relationship_id)
        )

        # Plaintext: linked meetings via the uid chain.
        linked_meetings: list[dict[str, Any]] = []
        unlinked_meeting_count = 0
        calendar_links = relationship.get("calendar_links") or []
        N = 5

        if db is not None and calendar_links:
            linked_meetings, unlinked_meeting_count = self._brief_plaintext(
                db, calendar_links, limit=N,
            )

        # HS-172-05: Watch-derived summary from persisted snapshots.
        # Reads are free (Article V.5); never triggers an evaluation.
        watch_summary = self._brief_watch_summary(db, relationship)

        # HS-172-05: last meeting (most recent linked meeting summary).
        last_meeting: dict[str, Any] | None = None
        if linked_meetings:
            lm = linked_meetings[0]
            item_count = len(lm.get("open_action_items") or []) + len(
                [1 for _ in (lm.get("decisions") or [])]
            )
            open_count = len(lm.get("open_action_items") or [])
            last_meeting = {
                "meeting_id": lm.get("meeting_id"),
                "title": lm.get("title"),
                "item_count": item_count,
                "open_count": open_count,
            }

        return {
            "relationship_id": relationship_id,
            "display_name": relationship.get("display_name"),
            "open_commitments": open_commitments,
            "agenda_items": agenda_items,
            "grounding_note_count": grounding_note_count,
            "linked_meetings": linked_meetings,
            "unlinked_meeting_count": unlinked_meeting_count,
            "watch_summary": watch_summary,
            "last_meeting": last_meeting,
        }

    def _brief_watch_summary(
        self, db: Any, relationship: dict[str, Any],
    ) -> dict[str, Any]:
        """HS-172-05: Watch-derived summary from persisted snapshots.

        Scans the active Rooms' watch snapshots for entities matching the
        person's aliases/display_name.  Returns counts and lists for PRs
        waiting on them, PRs they own waiting on others, and Jira
        assignments.  NEVER writes; NEVER triggers a new evaluation.
        """
        empty: dict[str, Any] = {
            "prs_waiting": [],
            "oldest_waiting_days": 0,
            "open_assignments": [],
        }
        if db is None:
            return empty

        # Collect identity strings for matching (case-insensitive).
        display_name = str(relationship.get("display_name") or "")
        aliases: list[str] = [
            str(a) for a in (relationship.get("owner_aliases") or [])
            if isinstance(a, str) and str(a).strip()
        ]
        identities = set()
        if display_name.strip():
            identities.add(display_name.strip().casefold())
        for a in aliases:
            identities.add(a.strip().casefold())
        if not identities:
            return empty

        # Find linked projects from the relationship.
        project_refs: list[str] = relationship.get("project_refs") or []
        if not project_refs:
            return empty

        prs_waiting: list[dict[str, Any]] = []
        open_assignments: list[dict[str, Any]] = []
        now = datetime.now()

        try:
            conn = db._connection()
        except Exception:
            return empty

        for project_id in project_refs:
            try:
                watches = conn.execute(
                    "SELECT * FROM connector_watches WHERE project_id=? "
                    "ORDER BY created_at,id",
                    (project_id,),
                ).fetchall()
            except Exception:
                continue

            # Get project name for host context.
            try:
                proj_row = conn.execute(
                    "SELECT name FROM projects WHERE id=?", (project_id,),
                ).fetchone()
                project_name = proj_row["name"] if proj_row else project_id
            except Exception:
                project_name = project_id

            for watch in watches:
                connector_id = watch["connector_id"] if isinstance(watch, dict) else (watch[2] if len(watch) > 2 else "")
                try:
                    connector_id = watch["connector_id"]
                except (KeyError, TypeError):
                    continue
                try:
                    import json as _json
                    snapshot_raw = watch["snapshot"]
                    if isinstance(snapshot_raw, str):
                        snapshot = _json.loads(snapshot_raw)
                    elif isinstance(snapshot_raw, dict):
                        snapshot = snapshot_raw
                    else:
                        continue
                except Exception:
                    continue

                query_kind_raw = ""
                try:
                    query_kind_raw = watch["query_kind"]
                except (KeyError, TypeError):
                    pass

                # Extract entities from the persisted snapshot shape.
                entities_raw = snapshot.get("entities") if isinstance(snapshot, dict) else None
                if isinstance(entities_raw, dict):
                    entities = list(entities_raw.values())
                elif isinstance(entities_raw, list):
                    entities = entities_raw
                else:
                    entities = []

                if connector_id == "gh" and query_kind_raw == "pull_requests":
                    for entity in entities:
                        if not isinstance(entity, dict):
                            continue
                        review_requests = (
                            entity.get("review_requests")
                            or entity.get("reviewRequests")
                            or []
                        )
                        state = str(entity.get("state") or "").lower()
                        if state != "open":
                            continue
                        # Check if any identity matches a reviewer.
                        matched = any(
                            str(r).casefold() in identities
                            for r in review_requests
                        )
                        if matched:
                            updated_at_str = (
                                entity.get("updated_at")
                                or entity.get("updatedAt")
                                or ""
                            )
                            days_waiting = 0
                            if updated_at_str:
                                try:
                                    updated_dt = datetime.fromisoformat(
                                        str(updated_at_str).replace("Z", "+00:00")
                                    )
                                    days_waiting = max(
                                        0,
                                        (now.replace(tzinfo=None)
                                         - updated_dt.replace(tzinfo=None)).days,
                                    )
                                except (ValueError, TypeError):
                                    pass
                            pr_number = entity.get("number")
                            repo = ""
                            url = entity.get("url") or ""
                            # Extract repo from URL if available.
                            if url and "github.com/" in url:
                                parts = url.split("github.com/")[1].split("/")
                                if len(parts) >= 2:
                                    repo = f"{parts[0]}/{parts[1]}"
                            prs_waiting.append({
                                "title": entity.get("title") or "",
                                "repo": repo,
                                "pr_number": pr_number,
                                "days_waiting": days_waiting,
                                "url": url,
                                "room_id": project_id,
                                "room_name": project_name,
                            })

                elif connector_id == "jira" and query_kind_raw == "issues":
                    for entity in entities:
                        if not isinstance(entity, dict):
                            continue
                        assignee = str(entity.get("assignee") or "")
                        if not assignee.strip():
                            continue
                        if assignee.strip().casefold() not in identities:
                            continue
                        status_cat = str(
                            entity.get("status_category") or ""
                        ).lower()
                        if status_cat == "done":
                            continue
                        due_at = entity.get("due_at") or entity.get("dueDate") or ""
                        overdue = False
                        if due_at:
                            try:
                                due_dt = datetime.fromisoformat(
                                    str(due_at).replace("Z", "+00:00").split("T")[0]
                                )
                                overdue = (
                                    now.replace(tzinfo=None)
                                    - due_dt.replace(tzinfo=None)
                                ).days > 0
                            except (ValueError, TypeError):
                                pass
                        open_assignments.append({
                            "summary": entity.get("summary")
                                       or entity.get("title") or "",
                            "key": entity.get("key") or "",
                            "status": entity.get("status") or "",
                            "url": entity.get("url") or "",
                            "overdue": overdue,
                            "room_id": project_id,
                            "room_name": project_name,
                        })

        oldest = max((p["days_waiting"] for p in prs_waiting), default=0)
        return {
            "prs_waiting": prs_waiting,
            "oldest_waiting_days": oldest,
            "open_assignments": open_assignments,
        }

    @staticmethod
    def _brief_plaintext(
        db: Any,
        calendar_links: list[dict[str, Any]],
        *,
        limit: int = 5,
    ) -> tuple[list[dict[str, Any]], int]:
        """Query the plaintext DB for linked meetings, action items, and decisions.

        Returns ``(linked_meetings, unlinked_meeting_count)``.

        The uid chain: relationship.calendar_links -> calendar_events by
        (uid, source_id) -> their IDs -> meetings.calendar_event_id IN those IDs.
        """
        # Step 1: Collect all calendar_event IDs for the linked UIDs.
        uid_source_pairs = [
            (str(link.get("uid") or ""), str(link.get("source_id") or ""))
            for link in calendar_links
            if isinstance(link, dict) and link.get("uid") and link.get("source_id")
        ]
        if not uid_source_pairs:
            return [], 0

        try:
            conn_factory = db._connection
        except AttributeError:
            return [], 0

        with conn_factory() as conn:
            # Find calendar_events matching any linked (uid, source_id).
            # Build per-pair OR clauses.
            where_clauses = " OR ".join(
                "(uid = ? AND source_id = ?)" for _ in uid_source_pairs
            )
            params: list[str] = []
            for uid, source_id in uid_source_pairs:
                params.extend([uid, source_id])

            event_rows = conn.execute(
                f"SELECT id FROM calendar_events WHERE {where_clauses}",
                params,
            ).fetchall()
            calendar_event_ids = [str(row["id"]) for row in event_rows]

            if not calendar_event_ids:
                return [], 0

            # Step 2: Find linked meetings (have calendar_event_id in our set).
            placeholders = ",".join("?" for _ in calendar_event_ids)
            meeting_rows = conn.execute(
                f"""SELECT id, title, started_at, ended_at, calendar_event_id
                    FROM meetings
                    WHERE calendar_event_id IN ({placeholders})
                    ORDER BY started_at DESC
                    LIMIT ?""",
                [*calendar_event_ids, limit],
            ).fetchall()

            if not meeting_rows:
                return [], 0

            # Determine the time window for counting unlinked meetings.
            # Window = from oldest linked meeting to now.
            oldest_start = str(meeting_rows[-1]["started_at"])

            # Step 3: Count unlinked meetings in the same window.
            # Unlinked = meetings WITHOUT calendar_event_id in the same window.
            unlinked_count_row = conn.execute(
                """SELECT COUNT(*) as cnt FROM meetings
                   WHERE (calendar_event_id IS NULL OR calendar_event_id = '')
                   AND started_at >= ?""",
                (oldest_start,),
            ).fetchone()
            unlinked_count = int(unlinked_count_row["cnt"]) if unlinked_count_row else 0

            # Step 4: For each linked meeting, get open action items and decisions.
            linked = []
            for row in meeting_rows:
                meeting_id = str(row["id"])

                # Open action items BY REFERENCE (never copied).
                action_rows = conn.execute(
                    """SELECT id, task, owner, due, delegated_at
                       FROM action_items
                       WHERE meeting_id = ? AND status = 'pending'
                       ORDER BY created_at""",
                    (meeting_id,),
                ).fetchall()
                open_action_items = [
                    {
                        "id": str(r["id"]),
                        "task": str(r["task"]),
                        "owner": r["owner"],
                        "due": r["due"],
                        "delegated_at": r["delegated_at"],
                    }
                    for r in action_rows
                ]

                # Decision records minted from this meeting via the
                # decision_record_sources join table (source_type='meeting',
                # source_ref=meeting_id).
                decision_rows = conn.execute(
                    """SELECT dr.id, dr.decision_text, dr.rationale, dr.lifecycle
                       FROM decision_records dr
                       JOIN decision_record_sources drs ON drs.record_id = dr.id
                       WHERE drs.source_type = 'meeting' AND drs.source_ref = ?
                       AND dr.deleted = 0
                       ORDER BY dr.created_at DESC""",
                    (meeting_id,),
                ).fetchall()
                decisions = [
                    {
                        "id": str(r["id"]),
                        "decision_text": str(r["decision_text"]),
                        "rationale": r["rationale"],
                        "lifecycle": str(r["lifecycle"]),
                    }
                    for r in decision_rows
                ]

                linked.append({
                    "meeting_id": meeting_id,
                    "title": row["title"],
                    "started_at": str(row["started_at"]),
                    "ended_at": row["ended_at"],
                    "calendar_event_id": row["calendar_event_id"],
                    "open_action_items": open_action_items,
                    "decisions": decisions,
                })

        return linked, unlinked_count

    # -- Calendar series links (D2) ------------------------------------------------

    def link_calendar_series(
        self,
        principal: Any,
        relationship_id: str,
        uid: str,
        source_id: str,
        label: str,
    ) -> dict[str, Any]:
        """Link a calendar series to a relationship inside the encrypted payload.

        Invariant P1: if ANY other relationship holds ``(uid, source_id)``,
        refuse with :class:`SeriesAlreadyLinked` naming the holder.  Re-linking
        the SAME relationship is idempotent (refreshes label and linked_at).
        """
        relationship = self._require_relationship(principal, relationship_id)
        clean_uid = str(uid or "").strip()
        clean_source = str(source_id or "").strip()
        clean_label = str(label or "").strip()[:500]
        if not clean_uid or not clean_source:
            raise PeopleServiceError("people_calendar_link_required")

        # P1: scan all relationships for an existing holder of (uid, source_id).
        for other in self._list("relationship"):
            other_id = str(other.get("id") or "")
            if other_id == relationship_id:
                continue
            if str(other.get("state") or "") == "archived":
                continue
            for link in other.get("calendar_links") or []:
                if isinstance(link, dict) and str(link.get("uid") or "") == clean_uid and str(link.get("source_id") or "") == clean_source:
                    raise SeriesAlreadyLinked(
                        holder_id=other_id,
                        holder_name=str(other.get("display_name") or ""),
                    )

        # Idempotent: update existing or append.
        now = _now()
        links: list[dict[str, Any]] = [
            dict(item) for item in relationship.get("calendar_links") or []
            if isinstance(item, dict)
        ]
        found = False
        for link in links:
            if str(link.get("uid") or "") == clean_uid and str(link.get("source_id") or "") == clean_source:
                link["label"] = clean_label
                link["linked_at"] = now
                found = True
                break
        if not found:
            links.append({"uid": clean_uid, "source_id": clean_source, "label": clean_label, "linked_at": now})

        value = dict(relationship)
        value.update({"calendar_links": links, "updated_at": now})
        return self._relationship_view(self._replace(relationship_id, value))

    def unlink_calendar_series(
        self,
        principal: Any,
        relationship_id: str,
        uid: str,
        source_id: str,
    ) -> dict[str, Any]:
        """Remove a calendar series link from a relationship.  Idempotent."""
        relationship = self._require_relationship(principal, relationship_id)
        clean_uid = str(uid or "").strip()
        clean_source = str(source_id or "").strip()
        if not clean_uid or not clean_source:
            raise PeopleServiceError("people_calendar_link_required")
        now = _now()
        links = [
            dict(item) for item in relationship.get("calendar_links") or []
            if isinstance(item, dict)
            and not (str(item.get("uid") or "") == clean_uid and str(item.get("source_id") or "") == clean_source)
        ]
        value = dict(relationship)
        value.update({"calendar_links": links, "updated_at": now})
        return self._relationship_view(self._replace(relationship_id, value))

    # -- Owner alias links (D1, HS-150-01) ----------------------------------------

    def link_owner_alias(
        self,
        principal: Any,
        relationship_id: str,
        alias: str,
    ) -> dict[str, Any]:
        """Link an owner-string alias to a relationship inside the encrypted payload.

        Invariant P2: if ANY other active relationship holds this alias
        (case-insensitive compare in memory, store as given), refuse with
        :class:`OwnerAliasTaken` naming the holder.  Re-linking the SAME
        relationship is idempotent.  Reserved strings and empty/whitespace
        are refused.
        """
        relationship = self._require_relationship(principal, relationship_id)
        clean_alias = str(alias or "").strip()
        if not clean_alias:
            raise PeopleServiceError("owner_alias_required")
        if clean_alias.casefold() in _RESERVED_OWNER_ALIASES:
            raise PeopleServiceError("owner_alias_reserved")

        # P2: scan all relationships for an existing holder (case-insensitive).
        for other in self._list("relationship"):
            other_id = str(other.get("id") or "")
            if other_id == relationship_id:
                continue
            if str(other.get("state") or "") == "archived":
                continue
            for existing in other.get("owner_aliases") or []:
                if str(existing).casefold() == clean_alias.casefold():
                    raise OwnerAliasTaken(
                        holder_id=other_id,
                        holder_name=str(other.get("display_name") or ""),
                    )

        # Idempotent: if already present (case-insensitive), no-op.
        aliases: list[str] = [
            str(a) for a in relationship.get("owner_aliases") or []
            if isinstance(a, str) and str(a).strip()
        ]
        if any(a.casefold() == clean_alias.casefold() for a in aliases):
            return self._relationship_view(relationship)
        aliases.append(clean_alias)

        now = _now()
        value = dict(relationship)
        value.update({"owner_aliases": aliases, "updated_at": now})
        return self._relationship_view(self._replace(relationship_id, value))

    def unlink_owner_alias(
        self,
        principal: Any,
        relationship_id: str,
        alias: str,
    ) -> dict[str, Any]:
        """Remove an owner alias from a relationship.  Idempotent."""
        relationship = self._require_relationship(principal, relationship_id)
        clean_alias = str(alias or "").strip()
        if not clean_alias:
            raise PeopleServiceError("owner_alias_required")
        now = _now()
        aliases = [
            str(a) for a in relationship.get("owner_aliases") or []
            if isinstance(a, str) and str(a).strip()
            and str(a).casefold() != clean_alias.casefold()
        ]
        value = dict(relationship)
        value.update({"owner_aliases": aliases, "updated_at": now})
        return self._relationship_view(self._replace(relationship_id, value))

    def resolve_relationship_by_owner(self, owner_string: str) -> dict[str, Any]:
        """Find the relationship whose owner_aliases contain this string.

        Readiness-guarded: a locked/absent store returns
        ``{"state": "unavailable"}``, NEVER a bare no-match.  A ready store
        with no matching alias returns ``{"state": "ready", "relationship": None}``.
        Case-insensitive compare in memory; never logged or persisted as comparison.
        """
        try:
            state = self._store.readiness()
            if str(getattr(state, "value", state)) != "ready":
                return {"state": "unavailable"}
        except Exception:
            return {"state": "unavailable"}

        clean = str(owner_string or "").strip()
        if not clean:
            return {"state": "ready", "relationship": None}

        try:
            relationships = self._store.list(kind="relationship")
        except Exception:
            return {"state": "unavailable"}

        folded = clean.casefold()
        for record in relationships:
            if not isinstance(record, dict):
                continue
            if str(record.get("state") or "") == "archived":
                continue
            for alias in record.get("owner_aliases") or []:
                if isinstance(alias, str) and alias.casefold() == folded:
                    return {"state": "ready", "relationship": self._relationship_view(record)}
        return {"state": "ready", "relationship": None}

    def resolve_relationship_by_watch_identity(
        self, identity_string: str,
    ) -> dict[str, Any]:
        """Find the relationship whose owner_aliases or display_name match.

        HS-172-04: maps a Watch entity's assignee or reviewer string to a
        People relationship.  The match is case-insensitive, in-memory,
        and NEVER egressed or persisted as a comparison (Article III).

        Order: owner_aliases first (exact alias match), then display_name.
        Returns ``{state, relationship}`` -- same shape as
        :meth:`resolve_relationship_by_owner`.

        Readiness-guarded: a locked/absent store returns
        ``{"state": "unavailable"}``, NEVER a bare no-match.  A ready store
        with no matching identity returns ``{"state": "ready", "relationship": None}``.
        """
        try:
            state = self._store.readiness()
            if str(getattr(state, "value", state)) != "ready":
                return {"state": "unavailable"}
        except Exception:
            return {"state": "unavailable"}

        clean = str(identity_string or "").strip()
        if not clean:
            return {"state": "ready", "relationship": None}

        try:
            relationships = self._store.list(kind="relationship")
        except Exception:
            return {"state": "unavailable"}

        folded = clean.casefold()

        # Pass 1: owner_aliases (exact case-insensitive match).
        for record in relationships:
            if not isinstance(record, dict):
                continue
            if str(record.get("state") or "") == "archived":
                continue
            for alias in record.get("owner_aliases") or []:
                if isinstance(alias, str) and alias.casefold() == folded:
                    return {"state": "ready", "relationship": self._relationship_view(record)}

        # Pass 2: display_name (case-insensitive).
        for record in relationships:
            if not isinstance(record, dict):
                continue
            if str(record.get("state") or "") == "archived":
                continue
            display = str(record.get("display_name") or "")
            if display and display.casefold() == folded:
                return {"state": "ready", "relationship": self._relationship_view(record)}

        return {"state": "ready", "relationship": None}

    def resolve_relationship_by_series(self, uid: str, source_id: str) -> dict[str, Any]:
        """Find the relationship linked to a calendar series.

        Readiness-guarded: a locked/absent store returns
        ``{"state": "unavailable"}``, NEVER a bare no-match.  A ready store
        with no link returns ``{"state": "ready", "relationship": None}``.
        """
        try:
            state = self._store.readiness()
            if str(getattr(state, "value", state)) != "ready":
                return {"state": "unavailable"}
        except Exception:
            return {"state": "unavailable"}

        clean_uid = str(uid or "").strip()
        clean_source = str(source_id or "").strip()
        if not clean_uid or not clean_source:
            return {"state": "ready", "relationship": None}

        try:
            relationships = self._store.list(kind="relationship")
        except Exception:
            return {"state": "unavailable"}

        for record in relationships:
            if not isinstance(record, dict):
                continue
            if str(record.get("state") or "") == "archived":
                continue
            for link in record.get("calendar_links") or []:
                if isinstance(link, dict) and str(link.get("uid") or "") == clean_uid and str(link.get("source_id") or "") == clean_source:
                    return {"state": "ready", "relationship": self._relationship_view(record)}
        return {"state": "ready", "relationship": None}

    # -- Follow-through projection -------------------------------------------------

    def list_cards(self, principal: Any, *, owner: str | None = None) -> list[FollowThroughCard]:
        self._require_ready_owner(principal)
        if owner not in (None, "", "you", "manager"):
            return []
        cards: list[FollowThroughCard] = []
        for commitment in self._open_commitments():
            card_id = f"people:{commitment['id']}"
            cards.append(FollowThroughCard(
                id=card_id,
                text=str(commitment.get("body") or ""),
                owner="you",
                due=None,
                status=str(commitment.get("state") or _OPEN_COMMITMENT),
                meeting_id=None,
                decision_id=None,
                stale_score=None,
                source="people_commitment",
                lane="now",
                provenance=CardProvenance(None, None, None, None, None, False),
                # The Desk opens a relationship scope; commitments deliberately
                # have no standalone inspector or GET endpoint in PR1.
                target_ref=f"people:{commitment['relationship_id']}",
            ))
        return cards

    def transition(self, principal: Any, card_id: str, verb: str) -> dict[str, Any]:
        self._require_ready_owner(principal)
        if verb not in {"done", "dismiss", "reopen"}:
            raise PeopleServiceError("people_commitment_verb_unsupported")
        commitment_id = str(card_id).removeprefix("people:")
        if not commitment_id or commitment_id == card_id:
            raise PeopleServiceError("people_commitment_not_found")
        commitment = self._get(commitment_id, "commitment")
        if commitment is None:
            raise PeopleServiceError("people_commitment_not_found")
        state = {"done": "done", "dismiss": "dismissed", "reopen": _OPEN_COMMITMENT}[verb]
        event = {"done": "satisfied", "dismiss": "dismissed", "reopen": "reopened"}[verb]
        self._transition_commitment(commitment, state, event=event, source="follow_through")
        return {"card_id": card_id, "verb": verb}

    def _transition_commitment(
        self,
        commitment: dict[str, Any],
        state: str,
        *,
        event: str,
        source: str,
        rationale: str = "",
        evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        now = _now()
        history = self._history(commitment)
        entry: dict[str, Any] = {"event": event, "state": state, "at": now, "source": source}
        if rationale:
            entry["rationale"] = rationale
        if evidence:
            entry["evidence"] = evidence
        history.append(entry)
        value = dict(commitment)
        value.update({"state": state, "lifecycle": state, "history": history, "updated_at": now})
        return self._record_view(self._replace(str(commitment["id"]), value))

    @staticmethod
    def _history(commitment: dict[str, Any]) -> list[dict[str, Any]]:
        return [dict(item) for item in commitment.get("history") or [] if isinstance(item, dict)]

    # -- Store isolation and validation -------------------------------------------

    def _require_owner(self, principal: Any) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise PeopleServiceError("people_owner_required")

    def _require_ready_owner(self, principal: Any) -> None:
        self._require_owner(principal)
        try:
            state = self._store.readiness()
            ready = str(getattr(state, "value", state)) == "ready"
        except Exception as exc:
            raise PeopleUnavailable("people_store_unavailable") from exc
        if not ready:
            raise PeopleUnavailable("people_store_unavailable")

    def _require_relationship(self, principal: Any, relationship_id: str) -> dict[str, Any]:
        self._require_ready_owner(principal)
        relationship = self._get(relationship_id, "relationship")
        if relationship is None or str(relationship.get("state") or "") == "archived":
            raise PeopleServiceError("people_relationship_not_found")
        return relationship

    def _create(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return dict(self._store.create(kind, payload))
        except Exception as exc:
            raise PeopleUnavailable("people_store_write_failed") from exc

    def _get(self, record_id: str, kind: str) -> dict[str, Any] | None:
        try:
            item = self._store.get(record_id, kind)
            return dict(item) if item is not None else None
        except Exception as exc:
            raise PeopleUnavailable("people_store_unavailable") from exc

    def _list(self, kind: str, **kwargs: Any) -> list[dict[str, Any]]:
        try:
            return [dict(item) for item in self._store.list(kind, **kwargs)]
        except Exception as exc:
            raise PeopleUnavailable("people_store_unavailable") from exc

    def _open_commitments(self) -> list[dict[str, Any]]:
        try:
            return [dict(item) for item in self._store.open_commitments()]
        except Exception as exc:
            raise PeopleUnavailable("people_store_unavailable") from exc

    def _replace(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return dict(self._store.replace(record_id, payload))
        except Exception as exc:
            raise PeopleUnavailable("people_store_write_failed") from exc

    def _archive(self, record_id: str) -> dict[str, Any]:
        try:
            return dict(self._store.archive(record_id))
        except Exception as exc:
            raise PeopleUnavailable("people_store_write_failed") from exc

    def _transition(self, record_id: str, state: str) -> dict[str, Any]:
        try:
            return dict(self._store.transition(record_id, state))
        except Exception as exc:
            raise PeopleUnavailable("people_store_write_failed") from exc

    @staticmethod
    def _text(payload: dict[str, Any], key: str, *, required: bool = False, limit: int = 0) -> str:
        value = payload.get(key, "")
        if not isinstance(value, str):
            raise PeopleServiceError("people_payload_invalid")
        value = value.strip()
        if required and not value:
            raise PeopleServiceError("people_payload_required")
        if limit and len(value) > limit:
            raise PeopleServiceError("people_payload_too_large")
        return value

    @staticmethod
    def _visibility(payload: dict[str, Any]) -> str:
        value = str(payload.get("visibility") or "leader_private")
        if value not in _VISIBILITIES:
            raise PeopleServiceError("people_visibility_invalid")
        return value

    @staticmethod
    def _readiness_view(state: Any) -> dict[str, str]:
        value = str(getattr(state, "value", state))
        # An existing encrypted sidecar remains encrypted even when its native
        # key is locked/missing or ciphertext is corrupt.  Only no sidecar (or an
        # unavailable construction) truthfully reports absent.
        store = "absent" if value in {"unconfigured", "unavailable"} else "encrypted"
        result = {"readiness": value, "state": value, "store": store, "sync": "local_only", "capture": "notes_only"}
        if value != "ready":
            result["reason_code"] = f"people_store_{value}"
        return result

    @staticmethod
    def _relationship_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "display_name", "relationship_kind", "role_context", "timezone", "cadence", "project_refs", "calendar_links", "owner_aliases", "state", "created_at", "updated_at")}

    @staticmethod
    def _entry_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "relationship_id", "agenda", "private_prep", "visibility", "state", "created_at", "updated_at")}

    @staticmethod
    def _agenda_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "session_id", "relationship_id", "body", "visibility", "state", "rolled_from_id", "created_at", "updated_at")}

    @staticmethod
    def _record_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "relationship_id", "request_id", "topic", "body", "visibility", "direction", "state", "commitment_id", "source", "execution_links", "history", "created_at", "updated_at", "accepted_at")}
