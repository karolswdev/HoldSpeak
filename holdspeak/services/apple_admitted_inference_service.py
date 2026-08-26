"""Versioned server boundary for one admitted Apple inference transport attempt.

This service deliberately has no placement resolver or provider SDK.  It composes
an already-installed :class:`RoutedInferenceCoordinator` with its fallback
controller: admission freezes one route, the controller reserves one attempt,
and a companion can only begin/reconcile that opaque ticket once.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from typing import Any, Mapping

from ..principals import Principal, PrincipalKind
from .errors import ConflictError, ValidationError
from .inference_adoption_service import RoutedInferenceCoordinator
from .inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY

APPLE_ADMITTED_ATTEMPT_SCHEMA = "AppleAdmittedAttempt@1"
APPLE_ADMITTED_TRANSPORT_SCHEMA = "AppleAdmittedTransport@1"


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


class AppleAdmittedInferenceService:
    """The one server-owned admission/reconciliation surface for Apple clients."""

    def __init__(
        self,
        coordinator: RoutedInferenceCoordinator,
        *,
        signing_secret: bytes | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.controller = coordinator.controller
        # Tickets are signed, not persisted: the controller's reservation remains
        # the durable authority and a restart never gains a mutable selector row.
        self._signing_secret = signing_secret or secrets.token_bytes(32)

    def admit(
        self,
        principal: Principal,
        *,
        command_id: str,
        capability_id: str,
        operation_id: str,
        payload: Mapping[str, Any],
        invocation_id: str | None = None,
        subject_kind: str | None = None,
        subject_id: str | None = None,
        reserved_output_tokens: int = 512,
    ) -> dict[str, Any]:
        """Freeze one route and claim exactly one companion transport reservation."""
        self._require_owner(principal)
        admitted = self.coordinator.admit(
            principal,
            command_id=command_id,
            capability_id=capability_id,
            operation_id=operation_id,
            payload=payload,
            invocation_id=invocation_id,
            subject_kind=subject_kind,
            subject_id=subject_id,
            reserved_output_tokens=reserved_output_tokens,
        )
        execution_id = str(admitted["execution"]["id"])
        return self.reserve_frozen_attempt(
            principal, command_id=f"apple-{command_id}", execution_id=execution_id
        )

    def reserve_frozen_attempt(
        self,
        principal: Principal,
        *,
        command_id: str,
        execution_id: str,
    ) -> dict[str, Any]:
        """Claim the controller's next lawful attempt without selecting a leg."""
        self._require_owner(principal)
        effect = self.controller.reserve_next_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"reserve-apple-{command_id}",
            execution_id=execution_id,
        )
        reservation = effect.get("reservation")
        if not isinstance(reservation, dict):
            raise ConflictError(
                "No active admitted attempt is available.",
                code="apple_admitted_reservation_required",
            )
        self.controller.claim_reservation(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"claim-{reservation['attempt_id']}",
            reservation=reservation,
        )
        ticket = {
            "schema": APPLE_ADMITTED_ATTEMPT_SCHEMA,
            "attempt_id": str(reservation["attempt_id"]),
            "execution_id": str(reservation["execution_id"]),
            "route_plan_id": str(reservation["route_plan_id"]),
            "deployment_revision_id": str(reservation["deployment_revision_id"]),
        }
        return {
            "schema": APPLE_ADMITTED_ATTEMPT_SCHEMA,
            # The mobile client gets no route/deployment selector.  The signed
            # authorization is its sole stable identity for begin/reconcile.
            "authorization": self._seal(ticket),
            "transport": {
                "schema": APPLE_ADMITTED_TRANSPORT_SCHEMA,
                "begin_path": "/api/inference/apple/attempts/begin",
                "reconcile_path": "/api/inference/apple/attempts/reconcile",
            },
            "execution_id": ticket["execution_id"],
            "attempt_id": ticket["attempt_id"],
        }

    def begin(self, principal: Principal, *, authorization: str) -> dict[str, Any]:
        """Persist dispatch intent immediately before the one companion wire call."""
        self._require_owner(principal)
        ticket = self._open(authorization)
        effect = self.controller.mark_external_dispatch_intent(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"dispatch-{ticket['attempt_id']}",
            attempt_id=ticket["attempt_id"],
        )
        return {"schema": "AppleAdmittedBeginResult@1", "attempt_id": ticket["attempt_id"], "effect": effect}

    def reconcile(
        self,
        principal: Principal,
        *,
        authorization: str,
        classified_outcome: str,
        result: str | None = None,
    ) -> dict[str, Any]:
        """Reconcile one named client outcome to that exact frozen attempt."""
        self._require_owner(principal)
        ticket = self._open(authorization)
        result_sha256 = _digest(result) if classified_outcome == "succeeded" and isinstance(result, str) else None
        return self.controller.reconcile_external_attempt(
            INFERENCE_FALLBACK_AUTHORITY,
            command_id=f"settle-{ticket['attempt_id']}",
            attempt_id=ticket["attempt_id"],
            classified_outcome=classified_outcome,
            result_sha256=result_sha256,
        )

    def receipt(self, principal: Principal, *, authorization: str) -> dict[str, Any]:
        self._require_owner(principal)
        ticket = self._open(authorization)
        return self.controller.get_route_execution_receipt(
            principal, execution_id=ticket["execution_id"]
        )

    def _seal(self, ticket: Mapping[str, str]) -> str:
        payload = base64.urlsafe_b64encode(_canonical(ticket)).rstrip(b"=")
        signature = hmac.new(self._signing_secret, payload, hashlib.sha256).hexdigest().encode()
        return f"{payload.decode()}.{signature.decode()}"

    def _open(self, authorization: str) -> dict[str, str]:
        try:
            encoded, supplied = authorization.split(".", 1)
            payload = encoded.encode()
            expected = hmac.new(self._signing_secret, payload, hashlib.sha256).hexdigest()
            padded = payload + b"=" * (-len(payload) % 4)
            ticket = json.loads(base64.urlsafe_b64decode(padded))
        except (AttributeError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ValidationError("Apple attempt authorization is invalid.", code="apple_admitted_authorization_invalid") from exc
        if not hmac.compare_digest(expected, supplied) or not isinstance(ticket, dict) or set(ticket) != {
            "schema", "attempt_id", "execution_id", "route_plan_id", "deployment_revision_id"
        } or ticket.get("schema") != APPLE_ADMITTED_ATTEMPT_SCHEMA or not all(
            isinstance(ticket.get(name), str) and ticket[name] for name in ticket if name != "schema"
        ):
            raise ValidationError("Apple attempt authorization is invalid.", code="apple_admitted_authorization_invalid")
        return {name: str(value) for name, value in ticket.items()}

    @staticmethod
    def _require_owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("Owner authority is required.", code="apple_admitted_owner_required")


__all__ = [
    "APPLE_ADMITTED_ATTEMPT_SCHEMA",
    "APPLE_ADMITTED_TRANSPORT_SCHEMA",
    "AppleAdmittedInferenceService",
]
