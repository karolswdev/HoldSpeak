"""Transport-neutral CRUD for desk primitives (HS-122-01).

Every primitive operation flows through this service regardless of caller —
FastAPI routes, MCP tools, test fixtures, CLI.  The service takes a Principal
and a Database; it never imports FastAPI or touches HTTP request/response types.
"""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import uuid
from typing import Any

from ..db.core import Database
from ..db.primitives import ZoneNameTaken, normalize_zone_name
from ..principals import Principal
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from .support import capability_descriptor, linearize


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@observe_service
class PrimitiveService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None) -> None:
        self._db = db
        self._observer = observer or NullObserver()

    # ── Notes ────────────────────────────────────────────────────────────

    def list_notes(self, principal: Principal) -> list[dict[str, Any]]:
        return [n.to_dict() for n in self._db.notes.list()]

    def get_note(self, principal: Principal, note_id: str) -> dict[str, Any]:
        note = self._db.notes.get(note_id)
        if note is None:
            raise NotFound("note", note_id)
        return note.to_dict()

    def create_note(
        self,
        principal: Principal,
        *,
        note_id: str | None = None,
        title: str = "",
        body_markdown: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        target_id = note_id or _new_id("note")
        if self._db.refinement_thoughts.get_by_note(target_id) is not None:
            raise ConflictError("thought-owned notes require expected revision", code="thought_expected_revision_required")
        try:
            note = self._db.notes.upsert(
                note_id=target_id,
                title=title,
                body_markdown=body_markdown,
                tags=tags or [],
            )
        except ValueError as exc:
            if "thought-owned notes require expected revision" not in str(exc):
                raise
            raise ConflictError("thought-owned notes require expected revision", code="thought_expected_revision_required") from exc
        return note.to_dict()

    def update_note(
        self,
        principal: Principal,
        note_id: str,
        *,
        title: str | None = None,
        body_markdown: str | None = None,
        tags: list[str] | None = None,
        expected_aggregate_revision: int | None = None,
        expected_working_revision: int | None = None,
    ) -> dict[str, Any]:
        if self._db.refinement_thoughts.get_by_note(note_id) is not None:
            from .refinement_thought_service import RefinementThoughtService
            thought = RefinementThoughtService(self._db).update_note(
                principal, note_id, expected_aggregate_revision=expected_aggregate_revision,
                expected_working_revision=expected_working_revision, title=title,
                body_markdown=body_markdown, tags=tags,
            )
            return self._owned_note_response(thought)
        existing = self._db.notes.get(note_id)
        if existing is None:
            raise NotFound("note", note_id)
        try:
            note = self._db.notes.upsert(
                note_id=note_id,
                title=title if title is not None else existing.title,
                body_markdown=body_markdown if body_markdown is not None else existing.body_markdown,
                tags=tags if tags is not None else existing.tags,
            )
        except ValueError as exc:
            if "thought-owned notes require expected revision" not in str(exc):
                raise
            raise ConflictError("thought-owned notes require expected revision", code="thought_expected_revision_required") from exc
        return note.to_dict()

    def delete_note(self, principal: Principal, note_id: str, *, expected_aggregate_revision: int | None = None,
                    expected_lifecycle_revision: int | None = None) -> bool:
        if self._db.refinement_thoughts.get_by_note(note_id) is not None:
            from .refinement_thought_service import RefinementThoughtService
            return self._owned_note_response(RefinementThoughtService(self._db).tombstone_note(
                principal, note_id, expected_aggregate_revision=expected_aggregate_revision,
                expected_lifecycle_revision=expected_lifecycle_revision,
            ))
        try:
            removed = self._db.notes.delete(note_id)
        except ValueError as exc:
            if "thought-owned notes require expected revision" not in str(exc):
                raise
            raise ConflictError("thought-owned notes require expected revision", code="thought_expected_revision_required") from exc
        if not removed:
            raise NotFound("note", note_id)
        return True

    @staticmethod
    def _owned_note_response(thought: dict[str, Any]) -> dict[str, Any]:
        """A normal Note payload plus mandatory aggregate retry cursors."""
        return dict(thought["working_note"] or {}) | {key: thought[key] for key in (
            "state", "aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision",
        )}

    # ── Decisions ────────────────────────────────────────────────────────

    def list_decisions(self, principal: Principal) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._db.desk_decisions.list()]

    def get_decision(self, principal: Principal, decision_id: str) -> dict[str, Any]:
        decision = self._db.desk_decisions.get(decision_id)
        if decision is None:
            raise NotFound("decision", decision_id)
        return decision.to_dict()

    def create_decision(
        self,
        principal: Principal,
        *,
        decision_id: str | None = None,
        title: str = "New decision",
        status: str = "proposed",
        deciders: list[str] | None = None,
        decided_at: str | None = None,
        context_markdown: str = "",
        decision_markdown: str = "",
        alternatives: list[str] | None = None,
        consequences_markdown: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        decision = self._db.desk_decisions.upsert(
            decision_id=decision_id or _new_id("decision"),
            title=title,
            status=status,
            deciders=deciders or [],
            decided_at=decided_at,
            context_markdown=context_markdown,
            decision_markdown=decision_markdown,
            alternatives=alternatives or [],
            consequences_markdown=consequences_markdown,
            tags=tags or [],
        )
        return decision.to_dict()

    def update_decision(
        self, principal: Principal, decision_id: str, **fields: Any
    ) -> dict[str, Any]:
        decision = self._db.desk_decisions.update(decision_id, **fields)
        if decision is None:
            raise NotFound("decision", decision_id)
        return decision.to_dict()

    def delete_decision(self, principal: Principal, decision_id: str) -> bool:
        if not self._db.desk_decisions.delete(decision_id):
            raise NotFound("decision", decision_id)
        return True

    def update_decision_status(
        self, principal: Principal, decision_id: str, status: str
    ) -> dict[str, Any]:
        decision = self._db.desk_decisions.update(decision_id, status=status)
        if decision is None:
            raise NotFound("decision", decision_id)
        return decision.to_dict()

    def supersede_decision(
        self, principal: Principal, decision_id: str
    ) -> dict[str, Any]:
        successor = self._db.desk_decisions.supersede(
            decision_id, _new_id("decision")
        )
        if successor is None:
            raise NotFound("decision", decision_id)
        return successor.to_dict()

    # ── Knowledge bases ──────────────────────────────────────────────────

    def list_kbs(self, principal: Principal) -> list[dict[str, Any]]:
        return [k.to_dict() for k in self._db.kbs.list()]

    def get_kb(self, principal: Principal, kb_id: str) -> dict[str, Any]:
        kb = self._db.kbs.get(kb_id)
        if kb is None:
            raise NotFound("kb", kb_id)
        return kb.to_dict()

    def create_kb(
        self,
        principal: Principal,
        *,
        kb_id: str | None = None,
        name: str = "",
        member_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("kb name is required")
        kb = self._db.kbs.upsert(
            kb_id=kb_id or _new_id("kb"),
            name=name,
            member_ids=member_ids or [],
        )
        return kb.to_dict()

    def update_kb(
        self,
        principal: Principal,
        kb_id: str,
        *,
        name: str | None = None,
        member_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        existing = self._db.kbs.get(kb_id)
        if existing is None:
            raise NotFound("kb", kb_id)
        kb = self._db.kbs.upsert(
            kb_id=kb_id,
            name=name if name is not None else existing.name,
            member_ids=member_ids if member_ids is not None else existing.member_ids,
        )
        return kb.to_dict()

    def delete_kb(self, principal: Principal, kb_id: str) -> bool:
        if not self._db.kbs.delete(kb_id):
            raise NotFound("kb", kb_id)
        return True

    def list_kb_members(
        self, principal: Principal, kb_id: str
    ) -> list[dict[str, Any]]:
        if self._db.kbs.get(kb_id) is None:
            raise NotFound("kb", kb_id)
        members = self._db.knowledge_memberships.list_for_knowledge(kb_id)
        return [m.to_dict() for m in members]

    def add_kb_member(
        self, principal: Principal, kb_id: str, resource_ref: str
    ) -> dict[str, Any]:
        member = self._db.knowledge_memberships.upsert(
            knowledge_id=kb_id, resource_ref=resource_ref
        )
        return member.to_dict()

    def remove_kb_member(
        self, principal: Principal, kb_id: str, resource_ref: str
    ) -> bool:
        return self._db.knowledge_memberships.delete(kb_id, resource_ref)

    # ── Directories (zones) ──────────────────────────────────────────────

    def list_directories(self, principal: Principal) -> list[dict[str, Any]]:
        directories = self._db.directories.list()
        out = []
        for d in directories:
            item = d.to_dict()
            members = self._db.directory_memberships.list_for_directory(d.id)
            item["member_ids"] = [m.primitive_id for m in members]
            out.append(item)
        return out

    def get_directory(
        self, principal: Principal, directory_id: str
    ) -> dict[str, Any]:
        directory = self._db.directories.get(directory_id)
        if directory is None:
            raise NotFound("directory", directory_id)
        members = self._db.directory_memberships.list_for_directory(directory_id)
        return {
            "directory": directory.to_dict(),
            "member_ids": [m.primitive_id for m in members],
            "members": [m.to_dict() for m in members],
        }

    def create_directory(
        self,
        principal: Principal,
        *,
        directory_id: str | None = None,
        name: str = "",
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        self._validate_zone_name(name)
        try:
            directory = self._db.directories.upsert(
                directory_id=directory_id or _new_id("dir"),
                name=name,
                parent_id=parent_id,
            )
        except ZoneNameTaken as exc:
            raise ConflictError(
                "zone_name_taken", existing_name=exc.existing_name
            ) from exc
        return directory.to_dict()

    def update_directory(
        self,
        principal: Principal,
        directory_id: str,
        *,
        name: str | None = None,
        parent_id: str | None = ...,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        existing = self._db.directories.get(directory_id)
        if existing is None:
            raise NotFound("directory", directory_id)
        new_name = name if name is not None else existing.name
        self._validate_zone_name(new_name)
        try:
            directory = self._db.directories.upsert(
                directory_id=directory_id,
                name=new_name,
                parent_id=parent_id if parent_id is not ... else existing.parent_id,
            )
        except ZoneNameTaken as exc:
            raise ConflictError(
                "zone_name_taken", existing_name=exc.existing_name
            ) from exc
        return directory.to_dict()

    def delete_directory(self, principal: Principal, directory_id: str) -> bool:
        if not self._db.directories.delete(directory_id):
            raise NotFound("directory", directory_id)
        return True

    def list_directory_members(
        self, principal: Principal, directory_id: str
    ) -> list[dict[str, Any]]:
        if self._db.directories.get(directory_id) is None:
            raise NotFound("directory", directory_id)
        members = self._db.directory_memberships.list_for_directory(directory_id)
        return [m.to_dict() for m in members]

    def file_member(
        self, principal: Principal, directory_id: str, primitive_id: str
    ) -> dict[str, Any]:
        from ..db.relationships import qualified_ref

        if self._db.directories.get(directory_id) is None:
            raise NotFound("directory", directory_id)
        primitive_ref = qualified_ref(primitive_id)
        from .refinement_thought_service import RefinementThoughtService
        RefinementThoughtService(self._db).assert_live_filing_allowed(primitive_ref)
        membership = self._db.directory_memberships.upsert(
            primitive_id=primitive_ref,
            directory_id=directory_id,
        )
        return membership.to_dict()

    def unfile_member(
        self, principal: Principal, directory_id: str, primitive_id: str
    ) -> bool:
        from ..db.relationships import qualified_ref

        ref = qualified_ref(primitive_id)
        from .refinement_thought_service import RefinementThoughtService
        RefinementThoughtService(self._db).assert_live_filing_allowed(ref)
        existing = self._db.directory_memberships.get(ref)
        if existing is None or existing.directory_id != directory_id:
            raise NotFound("membership", f"{primitive_id} in {directory_id}")
        self._db.directory_memberships.delete(ref)
        return True

    # ── Workflows ────────────────────────────────────────────────────────

    def list_workflows(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._workflow_payload(w) for w in self._db.workflows.list()]

    def get_workflow(self, principal: Principal, workflow_id: str) -> dict[str, Any]:
        workflow = self._db.workflows.get(workflow_id)
        if workflow is None:
            raise NotFound("workflow", workflow_id)
        return self._workflow_payload(workflow)

    def create_workflow(
        self,
        principal: Principal,
        *,
        workflow_id: str | None = None,
        name: str = "",
        prompt: str = "",
        graph_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("workflow name is required")
        workflow = self._db.workflows.upsert(
            workflow_id=workflow_id or _new_id("workflow"),
            name=name,
            prompt=prompt,
            graph_json=graph_json or {},
        )
        return self._workflow_payload(workflow)

    def update_workflow(
        self,
        principal: Principal,
        workflow_id: str,
        *,
        name: str | None = None,
        prompt: str | None = None,
        graph_json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        existing = self._db.workflows.get(workflow_id)
        if existing is None:
            raise NotFound("workflow", workflow_id)
        workflow = self._db.workflows.upsert(
            workflow_id=workflow_id,
            name=name if name is not None else existing.name,
            prompt=prompt if prompt is not None else existing.prompt,
            graph_json=graph_json if graph_json is not None else existing.graph_json,
        )
        return self._workflow_payload(workflow)

    def delete_workflow(self, principal: Principal, workflow_id: str) -> bool:
        if not self._db.workflows.delete(workflow_id):
            raise NotFound("workflow", workflow_id)
        return True

    # ── Chains ───────────────────────────────────────────────────────────

    def list_chains(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._chain_payload(c) for c in self._db.chains.list()]

    def get_chain(self, principal: Principal, chain_id: str) -> dict[str, Any]:
        chain = self._db.chains.get(chain_id)
        if chain is None:
            raise NotFound("chain", chain_id)
        return self._chain_payload(chain)

    def create_chain(
        self,
        principal: Principal,
        *,
        chain_id: str | None = None,
        name: str = "",
        steps: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("Sequence name is required")
        chain = self._db.chains.upsert(
            chain_id=chain_id or _new_id("chain"),
            name=name,
            steps=steps or [],
        )
        return self._chain_payload(chain)

    def update_chain(
        self,
        principal: Principal,
        chain_id: str,
        *,
        name: str | None = None,
        steps: list[str] | None = None,
    ) -> dict[str, Any]:
        existing = self._db.chains.get(chain_id)
        if existing is None:
            raise NotFound("chain", chain_id)
        chain = self._db.chains.upsert(
            chain_id=chain_id,
            name=name if name is not None else existing.name,
            steps=steps if steps is not None else existing.steps,
        )
        return self._chain_payload(chain)

    def delete_chain(self, principal: Principal, chain_id: str) -> bool:
        if not self._db.chains.delete(chain_id):
            raise NotFound("chain", chain_id)
        return True

    # ── Internal helpers ─────────────────────────────────────────────────

    @staticmethod
    def _validate_zone_name(raw: str) -> None:
        norm = normalize_zone_name(raw)
        if not norm:
            raise ValidationError("zone name is required")
        if len(norm) > 64:
            raise ValidationError("zone name must be 64 characters or fewer")

    def _workflow_payload(self, workflow: Any) -> dict[str, Any]:
        plan = linearize(workflow.graph_json) if workflow.graph_json else None
        if plan is not None and plan.linearizable:
            readiness, detail, support = "ready", "", "linear_graph"
        elif plan is not None:
            readiness = "unavailable"
            detail = f"This graph needs a Workbench host that supports it: {plan.reason}."
            support = "unsupported_graph"
        elif str(workflow.prompt or "").strip():
            readiness, detail, support = "ready", "", "prompt_workflow"
        else:
            readiness, detail, support = (
                "unavailable",
                "Add a runnable graph or prompt in Workbench.",
                "empty",
            )
        row = workflow.to_dict()
        row["capability"] = capability_descriptor(
            kind="workflow",
            name=workflow.name or workflow.id,
            readiness=readiness,
            detail=detail,
            action_label=f"Run {workflow.name or 'Workflow'}",
            support=support,
        )
        return row

    def _chain_payload(self, chain: Any) -> dict[str, Any]:
        missing = [
            rid for rid in chain.steps if self._db.recipes.get(str(rid)) is None
        ]
        ready = bool(chain.steps) and not missing
        detail = ""
        if not chain.steps:
            detail = "Add at least one Agent to this linear Sequence."
        elif missing:
            detail = "Missing Agents: " + ", ".join(map(str, missing))
        row = chain.to_dict()
        row["capability"] = capability_descriptor(
            kind="sequence",
            name=chain.name or chain.id,
            readiness="ready" if ready else "unavailable",
            detail=detail,
            action_label=f"Run {chain.name or 'Sequence'}",
            support="linear_compatibility",
        )
        return row
