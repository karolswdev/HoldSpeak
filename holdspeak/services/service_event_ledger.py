"""Typed, append-only application events shared by every HoldSpeak service."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from holdspeak.principals import Principal
from holdspeak.services.errors import ValidationError


def deterministic_event_id(*, producer: str, event_type: str, subject_ref: str,
                           source_revision: str, facts: dict[str, Any]) -> str:
    material = json.dumps(
        [producer, event_type, subject_ref, source_revision, facts],
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )
    return "sevt_" + hashlib.sha256(material.encode()).hexdigest()[:24]


class ServiceEventLedger:
    """Explicit domain facts, unlike the automatic operational observer log."""

    def __init__(self, db: Any) -> None:
        self._repo = db.automations

    def envelope(self, principal: Principal, *, event_type: str, producer: str,
                 subject_ref: str, facts: dict[str, Any], source_revision: str = "",
                 refs: list[str] | None = None, correlation_id: str = "",
                 causation_id: str = "", privacy_class: str = "private",
                 event_id: str | None = None) -> dict[str, Any]:
        if not event_type.strip() or "." not in event_type:
            raise ValidationError("event_type must be a namespaced type")
        if not producer.strip() or not subject_ref.strip():
            raise ValidationError("producer and subject_ref are required")
        if not isinstance(facts, dict):
            raise ValidationError("event facts must be an object")
        clean_refs = sorted({str(ref).strip() for ref in refs or [] if str(ref).strip()})
        return {
            "id": event_id or deterministic_event_id(
                producer=producer, event_type=event_type, subject_ref=subject_ref,
                source_revision=source_revision, facts=facts,
            ),
            "event_type": event_type, "event_version": 1, "producer": producer,
            "subject_ref": subject_ref, "source_revision": source_revision,
            "facts": facts, "refs": clean_refs,
            "principal_kind": principal.kind.value,
            "principal_identity": principal.identity,
            "correlation_id": correlation_id or "corr_" + uuid.uuid4().hex,
            "causation_id": causation_id, "privacy_class": privacy_class,
        }

    def append(self, principal: Principal, **values: Any) -> dict[str, Any]:
        event = self.envelope(principal, **values)
        self._repo.append_event(event)
        return self._repo.get_event(event["id"]) or event

    def append_in_transaction(self, conn: Any, principal: Principal,
                              **values: Any) -> dict[str, Any]:
        event = self.envelope(principal, **values)
        self._repo.append_event_in_transaction(conn, event)
        return event

    def list(self, principal: Principal, *, event_type: str | None = None,
             producer: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        del principal
        return self._repo.list_events(event_type=event_type, producer=producer, limit=limit)
