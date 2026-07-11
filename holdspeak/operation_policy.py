"""Typed consequence and authority policy (HS-92-08).

Every operation is described once, then resolved once against ControlMode and
an optional scoped Grant.  Feature code consumes the result; it does not grow
its own safe/neutral/yolo branches.  Hard invariants are deliberately absent
from the mode matrix because no mode is allowed to weaken them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Optional


POLICY_CONTRACT_VERSION = 1
POLICY_VERSION = "operation-policy/v1"
CONTROL_MODES = frozenset({"safe", "neutral", "yolo"})
INITIAL_FAMILIES = frozenset(
    {"dictation_commit", "coder_steering", "external_write", "sync_cadence"}
)
HARD_INVARIANTS = (
    "authentication",
    "secret_custody",
    "destination_binding",
    "payload_binding",
    "pane_identity",
    "audit_receipt",
    "configuration_integrity",
    "schema_safety",
)
STEERING_TTL_BY_MODE = {"safe": 5 * 60, "neutral": 15 * 60, "yolo": 60 * 60}


def normalize_control_mode(value: Any) -> str:
    mode = str(value or "neutral").strip().lower()
    return mode if mode in CONTROL_MODES else "neutral"


@dataclass(frozen=True)
class OperationDescriptor:
    """The exact consequence being considered, independent of UI wording."""

    operation_id: str
    family: str
    effect_class: str
    actor: str
    destination: str
    data_classes: tuple[str, ...]
    project_scope: Optional[str] = None
    resource_scope: Optional[str] = None
    fixed_destination: bool = False
    consequence: str = "execute_now"
    version: int = POLICY_CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["data_classes"] = list(self.data_classes)
        return result


@dataclass(frozen=True)
class PolicyDecision:
    mode: str
    source: str
    precedence: tuple[str, ...]
    outcome: str
    reason_code: str
    consequence: str
    requires_review: bool
    requires_authorization: bool
    requires_grant: bool
    hard_invariants: tuple[str, ...] = HARD_INVARIANTS
    policy_version: str = POLICY_VERSION

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["precedence"] = list(self.precedence)
        result["hard_invariants"] = list(self.hard_invariants)
        return result


def describe_operation(
    *,
    operation_id: str,
    family: str,
    effect_class: str,
    actor: str,
    destination: str,
    data_classes: Iterable[str],
    project_scope: Optional[str] = None,
    resource_scope: Optional[str] = None,
    fixed_destination: bool = False,
    consequence: str = "execute_now",
) -> OperationDescriptor:
    return OperationDescriptor(
        operation_id=str(operation_id).strip(),
        family=str(family).strip().lower(),
        effect_class=str(effect_class).strip().lower(),
        actor=str(actor or "owner").strip() or "owner",
        destination=str(destination).strip().lower(),
        data_classes=tuple(
            dict.fromkeys(
                str(item).strip().lower() for item in data_classes if str(item).strip()
            )
        ),
        project_scope=str(project_scope).strip() if project_scope else None,
        resource_scope=str(resource_scope).strip() if resource_scope else None,
        fixed_destination=bool(fixed_destination),
        consequence=str(consequence or "execute_now"),
    )


def operation_for_proposal(
    proposal: Any, *, actor: str = "owner"
) -> OperationDescriptor:
    stored = getattr(proposal, "operation", None)
    if isinstance(stored, Mapping) and stored.get("operation_id"):
        return describe_operation(
            operation_id=str(stored.get("operation_id")),
            family=str(stored.get("family") or "external_write"),
            effect_class=str(stored.get("effect_class") or ""),
            actor=actor,
            destination=str(stored.get("destination") or ""),
            data_classes=(
                stored.get("data_classes")
                if isinstance(stored.get("data_classes"), (list, tuple))
                else ()
            ),
            project_scope=stored.get("project_scope"),
            resource_scope=stored.get("resource_scope"),
            fixed_destination=bool(stored.get("fixed_destination")),
            consequence=str(stored.get("consequence") or "execute_now"),
        )
    payload = getattr(proposal, "payload", {}) or {}
    target = str(getattr(proposal, "target", "") or "").strip().lower()
    action = str(getattr(proposal, "action", "") or "").strip().lower()
    project = payload.get("project") or payload.get("repo")
    resource = getattr(proposal, "meeting_id", None) or getattr(
        proposal, "window_id", None
    )
    return describe_operation(
        operation_id=f"actuator:{getattr(proposal, 'id', '')}",
        family="external_write",
        effect_class=f"{target}/{action}",
        actor=actor,
        destination=str(getattr(proposal, "approved_destination", "") or target),
        data_classes=("proposed_content", "connector_metadata"),
        project_scope=str(project) if project else None,
        resource_scope=str(resource) if resource else None,
        fixed_destination=target in {"slack", "webhook", "github"},
        consequence="execute_now"
        if target in {"slack", "webhook", "github"}
        else "queue_executor",
    )


def grant_matches(
    grant: Optional[Mapping[str, Any]], operation: OperationDescriptor
) -> bool:
    if not grant or str(grant.get("state") or "") != "active":
        return False
    if str(grant.get("actor") or "") != operation.actor:
        return False
    if str(grant.get("operation_family") or "") != operation.family:
        return False
    if str(grant.get("effect_class") or "") != operation.effect_class:
        return False
    if str(grant.get("destination") or "") != operation.destination:
        return False
    allowed_data = {str(item) for item in grant.get("data_classes", [])}
    if not set(operation.data_classes).issubset(allowed_data):
        return False
    for key, actual in (
        ("project_scope", operation.project_scope),
        ("resource_scope", operation.resource_scope),
    ):
        allowed = grant.get(key)
        if str(allowed or "") != str(actual or ""):
            return False
    return True


def resolve_policy(
    operation: OperationDescriptor,
    *,
    mode: str,
    source: str = "config",
    grant: Optional[Mapping[str, Any]] = None,
    configured_preview: bool = False,
    explicit_authorization: bool = False,
) -> PolicyDecision:
    """Resolve one future operation. Unsupported families keep current behavior."""
    selected = normalize_control_mode(mode)
    precedence = (
        "hard_invariants",
        "revocation",
        "scoped_grant",
        "control_mode",
        "feature_default",
    )

    if operation.family not in INITIAL_FAMILIES:
        return PolicyDecision(
            mode=selected,
            source=source,
            precedence=precedence,
            outcome="current_behavior",
            reason_code="unsupported_family_current_behavior",
            consequence=operation.consequence,
            requires_review=False,
            requires_authorization=False,
            requires_grant=False,
        )

    if operation.family == "dictation_commit":
        review = selected == "safe" or (selected == "neutral" and configured_preview)
        return PolicyDecision(
            mode=selected,
            source=source,
            precedence=precedence,
            outcome="review_required" if review else "allowed",
            reason_code="dictation_preview_required"
            if review
            else "dictation_commit_allowed",
            consequence="content_only",
            requires_review=review,
            requires_authorization=False,
            requires_grant=False,
        )

    if operation.family == "coder_steering":
        # Pane identity + an expiring grant remain invariant in every mode.
        return PolicyDecision(
            mode=selected,
            source=source,
            precedence=precedence,
            outcome="allowed" if grant_matches(grant, operation) else "grant_required",
            reason_code="steering_grant_active"
            if grant_matches(grant, operation)
            else "steering_grant_required",
            consequence="execute_now",
            requires_review=False,
            requires_authorization=False,
            requires_grant=True,
        )

    if operation.family == "external_write":
        reusable = (
            selected == "yolo"
            and operation.fixed_destination
            and grant_matches(grant, operation)
        )
        allowed = reusable or explicit_authorization
        return PolicyDecision(
            mode=selected,
            source=source,
            precedence=precedence,
            outcome="allowed"
            if allowed
            else ("grant_required" if selected == "yolo" else "authorization_required"),
            reason_code=(
                "fixed_destination_grant_active"
                if reusable
                else "per_action_authorization_accepted"
                if explicit_authorization
                else "fixed_destination_grant_required"
                if selected == "yolo"
                else "per_action_authorization_required"
            ),
            consequence=operation.consequence,
            requires_review=True,
            requires_authorization=not allowed,
            requires_grant=selected == "yolo" and not explicit_authorization,
        )

    # Sync preserves auth/schema/config invariants in all modes. Safe asks for a
    # deliberate start; neutral/yolo may use configured cadence.
    manual = selected == "safe"
    return PolicyDecision(
        mode=selected,
        source=source,
        precedence=precedence,
        outcome="authorization_required" if manual else "allowed",
        reason_code="manual_sync_required"
        if manual
        else "configured_sync_cadence_allowed",
        consequence="queue_executor",
        requires_review=False,
        requires_authorization=manual,
        requires_grant=False,
    )


def steering_ttl_for_mode(mode: str, requested_ttl: Any = None) -> int:
    """Apply the mode preset to a future arm without weakening the 1h ceiling."""
    selected = normalize_control_mode(mode)
    preset = STEERING_TTL_BY_MODE[selected]
    if requested_ttl is None:
        return preset
    try:
        requested = int(requested_ttl)
    except (TypeError, ValueError):
        return preset
    return max(10, min(requested, preset))


def resolve_dictation_policy(config: Any) -> tuple[dict[str, Any], PolicyDecision]:
    """Build and snapshot the next dictation commit at the central seam."""
    operation = describe_operation(
        operation_id="dictation:next-commit",
        family="dictation_commit",
        effect_class="desktop/type_text",
        actor="owner",
        destination="focused_input",
        data_classes=("dictated_text",),
        consequence="content_only",
    )
    decision = resolve_policy(
        operation,
        mode=getattr(config, "control_mode", "neutral"),
        source="config",
        configured_preview=bool(
            getattr(config.dictation, "preview_before_type", False)
        ),
    )
    return {"operation": operation.to_dict(), "policy": decision.to_dict()}, decision


def commitment_labels(operation: OperationDescriptor) -> dict[str, str]:
    """Exact UI verbs derived from consequence and named destination."""
    destination = operation.destination
    effect = operation.effect_class
    target_kind = destination.split(":", 1)[0].lower()
    if effect == "slack/post_message" or target_kind == "slack":
        approve = "Approve and send to Slack"
    elif effect == "github/create_issue" or target_kind == "github":
        approve = f"Approve and create issue in {operation.project_scope or 'GitHub'}"
    elif effect == "webhook/post_message" or target_kind == "webhook":
        approve = "Approve and send to configured webhook"
    elif operation.consequence == "queue_executor":
        approve = f"Approve for {destination} executor"
    else:
        approve = f"Approve and run on {destination}"
    return {"approve": approve, "reject": "Reject proposed action"}


__all__ = [
    "CONTROL_MODES",
    "HARD_INVARIANTS",
    "INITIAL_FAMILIES",
    "OperationDescriptor",
    "POLICY_CONTRACT_VERSION",
    "POLICY_VERSION",
    "PolicyDecision",
    "commitment_labels",
    "STEERING_TTL_BY_MODE",
    "describe_operation",
    "grant_matches",
    "normalize_control_mode",
    "operation_for_proposal",
    "resolve_dictation_policy",
    "resolve_policy",
    "steering_ttl_for_mode",
]
