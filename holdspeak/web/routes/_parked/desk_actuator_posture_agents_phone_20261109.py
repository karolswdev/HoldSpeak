# PARKED: desk proposals wait for an owner decision in every posture.
from __future__ import annotations

class _ParkedBody:
    def apply(self, proposal: Any, target: str) -> Any:
        return apply_control_posture(self._ctx, self._db, proposal, executors=self._executors(target))


def apply_control_posture(
    ctx: WebContext,
    db: Any,
    proposal: Any,
    *,
    executors: dict[str, Any],
) -> Any:
    """Execute a proposal whose immutable creation snapshot authorizes it.

    This is the zero-prompt YOLO seam. It never re-resolves against the current
    configuration: changing posture affects future proposals only. Only a
    fixed, registered destination with a concrete executor can cross the seam;
    payload/destination/preview parity is still rechecked by ActuatorExecutor
    immediately before the effect.
    """

    if proposal.status != "proposed":
        return proposal
    policy = dict(getattr(proposal, "policy_snapshot", {}) or {})
    if not (
        policy.get("outcome") == "allowed"
        and policy.get("authority_basis") == "control_posture"
    ):
        return proposal

    from ...operation_policy import operation_for_proposal

    operation = operation_for_proposal(proposal)
    execute = executors.get(proposal.target)
    if not operation.fixed_destination or execute is None:
        return proposal

    updated = db.actuators.transition_proposal(
        proposal.id,
        to_status="approved",
        actor=f"control-posture:{policy.get('mode') or 'unknown'}",
        detail="configured operation authorized by captured control posture",
        policy_snapshot=policy,
    )
    return execute(
        ctx,
        db,
        updated,
        actor=f"control-posture:{policy.get('mode') or 'unknown'}",
    )
