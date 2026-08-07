"""Transport-neutral authority policy and scoped-grant lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..db.core import Database
from ..principals import Principal
from ..services.errors import ConflictError, NotFound, ValidationError


@dataclass(frozen=True)
class EvaluationRequest:
    operation_id: str
    family: str
    effect_class: str
    destination: str
    data_classes: list[str]
    project_scope: Any
    resource_scope: Any
    fixed_destination: bool
    consequence: str
    grant_id: str = ""
    configured_preview: bool = False


class AuthorityService:
    """Own authority policy decisions and the durable scoped-grant lifecycle."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def get_policy(self, principal: Principal) -> dict[str, Any]:
        from ..config import Config
        from ..operation_policy import (
            HARD_INVARIANTS,
            INITIAL_FAMILIES,
            POLICY_CONTRACT_VERSION,
            POLICY_VERSION,
        )
        from ..product_language import PRODUCT_LANGUAGE, control_mode_label

        mode = Config.load().control_mode
        return {
            "version": POLICY_CONTRACT_VERSION,
            "policy_version": POLICY_VERSION,
            "control_mode": mode,
            "control_mode_label": control_mode_label(mode),
            "control_mode_description": PRODUCT_LANGUAGE.control_mode_description(mode),
            "applies_to": "future_operations_only",
            "source": "config",
            "precedence": [
                "hard_invariants",
                "revocation",
                "scoped_grant",
                "control_mode",
                "feature_default",
            ],
            "hard_invariants": list(HARD_INVARIANTS),
            "supported_families": sorted(INITIAL_FAMILIES),
            "unsupported_family_behavior": "refused",
        }

    def get_control_mode(self, principal: Principal) -> str:
        from ..config import Config

        return Config.load().control_mode

    def set_control_mode(self, principal: Principal, mode: str) -> dict[str, Any]:
        from ..config import Config
        from ..product_language import ProductLanguageError, control_mode_label, control_mode_wire

        try:
            requested = control_mode_wire(mode)
        except ProductLanguageError as exc:
            raise ValidationError("Control mode must be Secure, Normal, or YOLO.") from exc

        config = Config.load()
        previous = config.control_mode
        config.control_mode = requested
        config.save()
        changed = previous != requested
        revoked = (
            self._db.actuators.revoke_active_grants(reason="control_mode_changed")
            if changed
            else 0
        )
        from .. import coder_steering

        revoked_coder_grants = coder_steering.clear_grants() if changed else 0
        return {
            "control_mode": requested,
            "control_mode_label": control_mode_label(requested),
            "previous_control_mode": previous,
            "previous_control_mode_label": control_mode_label(previous),
            "applies_to": "future_operations_only",
            "source": "config",
            "revoked_grants": revoked,
            "revoked_coder_grants": revoked_coder_grants,
        }

    def evaluate(
        self, principal: Principal, request: EvaluationRequest
    ) -> dict[str, Any]:
        from ..config import Config
        from ..operation_policy import describe_operation, resolve_policy

        operation = describe_operation(
            operation_id=request.operation_id,
            family=request.family,
            effect_class=request.effect_class,
            actor=principal.identity,
            destination=request.destination,
            data_classes=request.data_classes,
            project_scope=request.project_scope,
            resource_scope=request.resource_scope,
            fixed_destination=request.fixed_destination,
            consequence=request.consequence,
        )
        grant = None
        if request.grant_id:
            row = self._db.actuators.get_grant(request.grant_id)
            grant = row.to_dict() if row else None
        decision = resolve_policy(
            operation,
            mode=Config.load().control_mode,
            source="config",
            grant=grant,
            configured_preview=request.configured_preview,
        )
        return {"operation": operation.to_dict(), "policy": decision.to_dict()}

    def list_grants(
        self, principal: Principal, actor: str | None = None
    ) -> list[dict[str, Any]]:
        return [row.to_dict() for row in self._db.actuators.list_grants(actor=actor)]

    def issue_grant(
        self,
        principal: Principal,
        proposal_id: str,
        *,
        ttl_seconds: int = 3600,
        max_uses: int = 1,
    ) -> dict[str, Any]:
        from ..config import Config
        from ..operation_policy import operation_for_proposal

        proposal = self._db.actuators.get_proposal(proposal_id)
        if proposal is None:
            raise NotFound("proposal", proposal_id)
        operation = operation_for_proposal(proposal, actor=principal.identity)
        if not operation.fixed_destination:
            raise ConflictError(
                "Grants may only bind an already configured fixed destination"
            )
        control_mode = Config.load().control_mode
        if control_mode == "yolo":
            raise ConflictError(
                "YOLO uses the captured posture for eligible configured operations. "
                "Use Secure or Normal to issue a bounded grant."
            )
        try:
            grant = self._db.actuators.issue_grant(
                actor=operation.actor,
                operation_family=operation.family,
                effect_class=operation.effect_class,
                destination=operation.destination,
                data_classes=list(operation.data_classes),
                project_scope=operation.project_scope,
                resource_scope=operation.resource_scope,
                ttl_seconds=ttl_seconds,
                max_uses=max_uses,
                control_mode=control_mode,
            )
        except (TypeError, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        return grant.to_dict()

    def revoke_grant(self, principal: Principal, grant_id: str) -> dict[str, Any]:
        if not self._db.actuators.revoke_grant(grant_id):
            raise NotFound("grant", grant_id)
        return {"success": True, "grant_id": grant_id, "state": "revoked"}

    def list_grant_uses(
        self, principal: Principal, grant_id: str
    ) -> list[dict[str, Any]]:
        if self._db.actuators.get_grant(grant_id) is None:
            raise NotFound("grant", grant_id)
        return self._db.actuators.list_grant_uses(grant_id)
