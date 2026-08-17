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


_VISIBILITIES = frozenset({"shared_intent", "leader_private"})
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
        self._transition(commitment_id, state)
        return {"card_id": card_id, "verb": verb}

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
        return {key: record.get(key) for key in ("id", "display_name", "relationship_kind", "role_context", "timezone", "cadence", "state", "created_at", "updated_at")}

    @staticmethod
    def _entry_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "relationship_id", "agenda", "private_prep", "visibility", "state", "created_at", "updated_at")}

    @staticmethod
    def _agenda_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "session_id", "relationship_id", "body", "visibility", "state", "rolled_from_id", "created_at", "updated_at")}

    @staticmethod
    def _record_view(record: dict[str, Any]) -> dict[str, Any]:
        return {key: record.get(key) for key in ("id", "relationship_id", "request_id", "topic", "body", "visibility", "direction", "state", "commitment_id", "source", "created_at", "updated_at", "accepted_at")}
