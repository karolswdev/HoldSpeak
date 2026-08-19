"""Transport-neutral owner API for developing one durable Thought."""
from __future__ import annotations

from typing import Any

from ..principals import Principal
from .errors import ServiceError
from .refinement_coordinator import RefinementCoordinator
from .refinement_thought_service import RefinementThoughtService


class RefinementApplicationService:
    """Exact SOA boundary shared by HTTP, MCP, and future transports."""

    def __init__(self, database: Any, *, coordinator: RefinementCoordinator | None) -> None:
        self._thoughts = RefinementThoughtService(database)
        self._coordinator = coordinator

    async def refine(
        self,
        principal: Principal,
        *,
        thought_id: str,
        request_id: str,
        expected_aggregate_revision: int,
        expected_working_revision: int,
        expected_attachment_revision: int,
    ) -> dict[str, Any]:
        coordinator = self._require_coordinator()
        thought, _invocation = await coordinator.begin(
            principal,
            thought_id=thought_id,
            request_id=request_id,
            expected_aggregate_revision=expected_aggregate_revision,
            expected_working_revision=expected_working_revision,
            expected_attachment_revision=expected_attachment_revision,
        )
        return {"thought": thought, "continuity": dict(thought["continuity"])}

    async def stop(
        self,
        principal: Principal,
        *,
        thought_id: str,
        invocation_id: str,
        expected_aggregate_revision: int,
    ) -> dict[str, Any]:
        coordinator = self._require_coordinator()
        thought, disposition = await coordinator.stop(
            principal,
            thought_id=thought_id,
            invocation_id=invocation_id,
            expected_aggregate_revision=expected_aggregate_revision,
        )
        return {"thought": thought, "cancellation": {"disposition": disposition}}

    def reconcile(
        self,
        principal: Principal,
        *,
        thought_id: str,
        expected_aggregate_revision: int,
        invocation_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "thought": self._thoughts.reconcile(
                principal,
                thought_id,
                expected_aggregate_revision=expected_aggregate_revision,
                invocation_id=invocation_id,
            )
        }

    def review(
        self, principal: Principal, *, thought_id: str, review_result_id: str
    ) -> dict[str, Any]:
        return self._thoughts.review(principal, thought_id, review_result_id)

    def act_on_review(
        self,
        principal: Principal,
        *,
        thought_id: str,
        review_result_id: str,
        request_id: str,
        action: str,
        expected_aggregate_revision: int,
        expected_working_revision: int,
        expected_attachment_revision: int,
        answer: str = "",
    ) -> dict[str, Any]:
        thought, receipt = self._thoughts.review_action(
            principal,
            thought_id,
            review_result_id,
            request_id=request_id,
            action=action,
            expected_aggregate_revision=expected_aggregate_revision,
            expected_working_revision=expected_working_revision,
            expected_attachment_revision=expected_attachment_revision,
            answer=answer,
        )
        return {"thought": thought, "receipt": receipt}

    def _require_coordinator(self) -> RefinementCoordinator:
        if self._coordinator is None:
            raise ServiceError(
                "refinement_coordinator_unavailable",
                "Refinement is not accepting work",
                context={"status": 503},
            )
        return self._coordinator
