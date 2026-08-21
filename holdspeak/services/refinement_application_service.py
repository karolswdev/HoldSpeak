"""Transport-neutral owner API for developing one durable Thought."""
from __future__ import annotations

from typing import Any

from ..principals import Principal
from .errors import ConflictError, ServiceError
from .refinement_coordinator import RefinementCoordinator
from .refinement_thought_service import RefinementThoughtService


class RefinementApplicationService:
    """Exact SOA boundary shared by HTTP, MCP, and future transports."""

    def __init__(self, database: Any, *, coordinator: RefinementCoordinator | None) -> None:
        self._database = database
        self._thoughts = RefinementThoughtService(database)
        from .refinement_context_service import RefinementContextService
        self._context = RefinementContextService(database)
        self._coordinator = coordinator

    def create_thought(self, principal: Principal, *, request_id: str, raw_text: str,
                       source: dict[str, Any] | None = None,
                       initial_note: dict[str, Any] | None = None) -> dict[str, Any]:
        thought, receipt = self._thoughts.create_with_default(
            principal, request_id=request_id, raw_text=raw_text, source=source,
            initial_note=initial_note,
        )
        return {"thought": thought, "default_context_receipt": receipt}

    def adopt_note(self, principal: Principal, *, request_id: str, note_id: str,
                   expected_source_content_sha256: str,
                   expected_source_last_modified: str) -> dict[str, Any]:
        thought, receipt = self._thoughts.adopt_note_with_default(
            principal, request_id=request_id, note_id=note_id,
            expected_source_content_sha256=expected_source_content_sha256,
            expected_source_last_modified=expected_source_last_modified,
        )
        return {"thought": thought, "default_context_receipt": receipt}

    def get_default_context(self, principal: Principal) -> dict[str, Any]:
        return self._context.get_default_context(principal)

    def replace_default_context(self, principal: Principal, *, request_id: str,
                                expected_revision: int, refs: list[str]) -> dict[str, Any]:
        return self._context.replace_default_context(
            principal, request_id=request_id, expected_revision=expected_revision,
            refs=refs,
        )

    def list_context(self, principal: Principal, *, thought_id: str, query: str = "",
                     view: str = "compact", cursor: str | None = None,
                     limit: int = 20) -> dict[str, Any]:
        return self._context.list_context(principal, thought_id, query=query, view=view,
                                          cursor=cursor, limit=limit)

    def get_workbench(self, principal: Principal, *, thought_id: str) -> dict[str, Any]:
        intended = None
        target_ready = False
        try:
            if self._coordinator and hasattr(self._coordinator, "admission_claim"):
                claim = self._coordinator.admission_claim()
                from ..inference_targets import resolve_placement
                target = resolve_placement(self._database, invocation=claim["target_id"]).target
                intended = {"target_id":claim["target_id"],"target_name":target.name,
                            "target_kind":claim["target_kind"],"boundary":claim["boundary"],
                            "readiness":claim["readiness"]}
                target_ready = claim["readiness"] == "ready"
            else:
                from ..inference_targets import resolve_placement
                target = resolve_placement(self._database).target
                intended = {"target_id":target.id,"target_name":target.name,
                            "target_kind":target.kind,"boundary":target.boundary,
                            "readiness":target.readiness_state}
                target_ready = target.readiness_state == "ready"
        except Exception:
            target_ready = False
        return self._thoughts.get_workbench(
            principal, thought_id,
            inference_available=bool(self._coordinator and getattr(self._coordinator, "accepting", True) and target_ready),
            intended_placement=intended,
        )

    def get_original(self, principal: Principal, *, thought_id: str) -> dict[str, Any]:
        return {"thought": self._thoughts.get(principal, thought_id, include_raw=True)}

    def mutate_context(self, principal: Principal, *, action: str, thought_id: str,
                       ref: str, request_id: str, expected_aggregate_revision: int,
                       expected_working_revision: int,
                       expected_attachment_revision: int,
                       workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        method = {"attach": self._context.attach_context,
                  "detach": self._context.detach_context,
                  "refresh": self._context.refresh_context}.get(action)
        if method is None:
            raise ServiceError("context_action_invalid", "Unknown context action")
        result = method(principal, thought_id, visible_ref=ref, request_id=request_id,
                      expected_aggregate_revision=expected_aggregate_revision,
                      expected_working_revision=expected_working_revision,
                      expected_attachment_revision=expected_attachment_revision,
                      workspace_cursor=workspace_cursor)
        return {**result, "workbench": self.get_workbench(principal, thought_id=thought_id)}

    async def refine(
        self,
        principal: Principal,
        *,
        thought_id: str,
        request_id: str,
        expected_aggregate_revision: int,
        expected_working_revision: int,
        expected_attachment_revision: int,
        workspace_cursor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        coordinator = self._require_coordinator()
        kwargs = {"thought_id":thought_id,"request_id":request_id,
                  "expected_aggregate_revision":expected_aggregate_revision,
                  "expected_working_revision":expected_working_revision,
                  "expected_attachment_revision":expected_attachment_revision}
        if workspace_cursor is not None:
            kwargs["workspace_cursor"] = workspace_cursor
        try:
            thought, _invocation = await coordinator.begin(principal, **kwargs)
        except ServiceError as exc:
            if exc.code != "refinement_continuation_unavailable":
                raise
            raise ServiceError(
                exc.code, exc.detail,
                context={**exc.context,"workbench":self.get_workbench(principal, thought_id=thought_id)},
            ) from exc
        return {"thought": thought, "continuity": dict(thought["continuity"]),
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

    async def stop(
        self,
        principal: Principal,
        *,
        thought_id: str,
        invocation_id: str,
        expected_aggregate_revision: int,
        workspace_cursor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        coordinator = self._require_coordinator()
        kwargs = {"thought_id":thought_id,"invocation_id":invocation_id,
                  "expected_aggregate_revision":expected_aggregate_revision}
        if workspace_cursor is not None:
            kwargs["workspace_cursor"] = workspace_cursor
        thought, disposition = await coordinator.stop(principal, **kwargs)
        return {"thought": thought, "cancellation": {"disposition": disposition},
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

    def reconcile(
        self,
        principal: Principal,
        *,
        thought_id: str,
        expected_aggregate_revision: int,
        invocation_id: str | None = None,
        workspace_cursor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        thought = self._thoughts.reconcile(
                principal,
                thought_id,
                expected_aggregate_revision=expected_aggregate_revision,
                invocation_id=invocation_id,
                workspace_cursor=workspace_cursor,
            )
        return {"thought": thought,
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

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
        workspace_cursor: dict[str, Any] | None = None,
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
            workspace_cursor=workspace_cursor,
        )
        return {"thought": thought, "receipt": receipt,
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

    async def answer_and_continue(
        self, principal: Principal, *, thought_id: str, review_result_id: str,
        command_id: str, answer: str, expected_aggregate_revision: int,
        expected_working_revision: int, expected_attachment_revision: int,
        workspace_cursor: dict[str, Any],
    ) -> dict[str, Any]:
        coordinator = self._require_coordinator()
        try:
            thought, receipt = await coordinator.answer_and_continue(
                principal, thought_id=thought_id, review_result_id=review_result_id,
                command_id=command_id, answer=answer,
                expected_aggregate_revision=expected_aggregate_revision,
                expected_working_revision=expected_working_revision,
                expected_attachment_revision=expected_attachment_revision,
                workspace_cursor=workspace_cursor,
            )
        except ServiceError as exc:
            if exc.code != "refinement_continuation_unavailable":
                raise
            raise ServiceError(
                exc.code, exc.detail,
                context={**exc.context,"workbench":self.get_workbench(principal, thought_id=thought_id)},
            ) from exc
        return {"thought": thought, "receipt": receipt,
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

    def update_working(self, principal: Principal, *, thought_id: str,
                       workspace_cursor: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
        try:
            thought = self._thoughts.update_working(
                principal, thought_id, workspace_cursor=workspace_cursor, **fields
            )
        except ConflictError as exc:
            if exc.code != "workspace_cursor_conflict":
                raise
            raise ConflictError(
                exc.detail, code=exc.code,
                context={**exc.context,"workbench":self.get_workbench(principal, thought_id=thought_id)},
            ) from exc
        return {"thought": thought, "workbench": self.get_workbench(principal, thought_id=thought_id)}

    def complete(self, principal: Principal, *, thought_id: str,
                 workspace_cursor: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
        thought, receipt = self._thoughts.complete_with_receipt(
            principal, thought_id, workspace_cursor=workspace_cursor, **fields
        )
        return {"thought": thought, "receipt": receipt,
                "workbench": self.get_workbench(principal, thought_id=thought_id)}

    def resume(self, principal: Principal, *, thought_id: str,
               workspace_cursor: dict[str, Any] | None = None, **fields: Any) -> dict[str, Any]:
        thought = self._thoughts.resume(
            principal, thought_id, workspace_cursor=workspace_cursor, **fields
        )
        return {"thought": thought, "workbench": self.get_workbench(principal, thought_id=thought_id)}

    def _require_coordinator(self) -> RefinementCoordinator:
        if self._coordinator is None:
            raise ServiceError(
                "refinement_coordinator_unavailable",
                "Refinement is not accepting work",
                context={"status": 503},
            )
        return self._coordinator
