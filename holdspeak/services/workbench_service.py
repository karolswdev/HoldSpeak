"""Transport-neutral Workbench operations (HS-122-02)."""
from __future__ import annotations
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import hashlib
import json
import time
import uuid
from typing import Any, Callable

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError


SKILL_BODY_LIMIT = 8192


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class _VoiceResolutionAdapter:
    """Keep raw resolver text inside the frozen typed route contract."""

    connector_id = "inference-provider"

    def __init__(self) -> None:
        from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
        self._inner = CanonicalPromptAdapter()

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: Any) -> dict[str, Any]:
        result = self._inner.dispatch(engine, payload, cancellation)
        return {"reference": str(result.get("output") or ""), "confidence": 1.0}

    def cancel(self) -> str:
        return self._inner.cancel()


def _launch_own(principal: Principal, *refs: str) -> None:
    """Conductor K6: a launch changes only Workbenches it created."""
    from .conductor_launch import require_own

    require_own(principal, *refs)


@observe_service
class WorkbenchService:
    # Route adapters create a short-lived service per request; limiter state is shared.
    _resolve_timestamps: dict[str, float] = {}

    def __init__(
        self,
        db: Database,
        *,
        observer: PipelineObserver | None = None,
        on_changed: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self._db = db
        self._observer = observer or NullObserver()
        # HS-200-45 R4: workbench/item/skill writes bypass PrimitiveService, so
        # this service carries the same ``on_changed`` hook. The hub binds both
        # to one ``desk_changed`` broadcast.
        self._on_changed = on_changed

    def _changed(self, kind: str, obj_id: str, op: str) -> None:
        """Announce a successful write. Never fails the write it reports on."""
        if self._on_changed is None:
            return
        try:
            self._on_changed(kind, obj_id, op)
        except Exception:  # pragma: no cover - a dead socket is not a failed write
            pass

    def _refuse_post_marker_pointer_write(self, principal: Principal, fields: dict[str, Any]) -> None:
        """Retired selectors never create or rewrite assignment authority."""
        retired = sorted({"profile_id", "resolver_profile_id"} & set(fields))
        if not retired:
            return
        from .inference_adoption_service import RECIPE_WORKBENCH_MIGRATION_FAMILY
        from .inference_assignment_service import InferenceAssignmentService

        marker = InferenceAssignmentService(self._db).migration_marker(
            principal, family=RECIPE_WORKBENCH_MIGRATION_FAMILY
        )
        if marker is None:
            return
        raise ValidationError(
            "Legacy Workbench profile selectors are unavailable after assignment migration.",
            code="inference_legacy_selector_retired",
            context={"retired_fields": retired},
        )

    # ── Workbenches ──────────────────────────────────────────────────────

    def list_workbenches(self, principal: Principal) -> list[dict[str, Any]]:
        return [self._wb_payload(wb, principal) for wb in self._db.workbenches.list()]

    def get_workbench(
        self, principal: Principal, workbench_id: str, *, parked: bool = False
    ) -> dict[str, Any]:
        wb = self._require_workbench(workbench_id)
        return self._wb_payload(wb, principal, parked=parked)

    def create_workbench(self, principal: Principal, *, name: str, **fields: Any) -> dict[str, Any]:
        if not name.strip():
            raise ValidationError("Automation name is required")
        self._refuse_post_marker_pointer_write(principal, fields)
        self._clean_automation_fields(fields)
        body = {"name": name, **fields}
        fields = self._wb_fields(body)
        if fields["schedule_enabled"] and principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        supplied = str(body.pop("id", "") or "")
        # Conductor K6 (Astra round 2 on #903): a launch creates only NEW
        # Workbenches; an existing id (live or deleted) is refused before any
        # write, and ownership is recorded only after the insert.
        from .conductor_launch import record_own, require_new

        if supplied:
            require_new(principal, f"workbench:{supplied}",
                        lambda: self._db.workbenches.get(supplied, include_deleted=True) is not None)
        workbench_id = supplied or _new_id("workbench")
        if not fields["schedule_enabled"]:
            wb = self._db.workbenches.upsert(workbench_id=workbench_id, **fields)
            record_own(principal, f"workbench:{wb.id}")
            self._changed("workbench", wb.id, "create")
            return self._wb_payload(wb, principal)
        # The owner's single enable gesture commits its configuration, captured
        # deployment revision, and local delegation as one crash-consistent unit.
        from holdspeak.kernel.runtime import _configure
        _configure(self._db)
        from .schedule_delegation import ScheduleDelegationService
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            wb = self._db.workbenches.upsert_in_transaction(conn, workbench_id=workbench_id, **fields)
            ScheduleDelegationService(self._db).enable_from_owner_in_transaction(principal, wb, conn)
        self._changed("workbench", wb.id, "create")
        return self._wb_payload(wb, principal)

    def update_workbench(
        self, principal: Principal, workbench_id: str, **fields: Any
    ) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        existing = self._require_workbench(workbench_id)
        if principal.kind is PrincipalKind.OWNER:
            from holdspeak.kernel.runtime import _configure
            _configure(self._db).inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        self._refuse_post_marker_pointer_write(principal, fields)
        self._clean_automation_fields(fields)
        proposed = self._wb_fields(fields, existing)
        bound_changed = any(proposed[key] != getattr(existing, key) for key in ("schedule", "schedule_enabled", "recipe_id", "profile_id"))
        enabling = not existing.schedule_enabled and proposed["schedule_enabled"]
        if enabling and principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can enable a schedule", context={"status": 403})
        if bound_changed:
            proposed["schedule_revision"] = existing.schedule_revision + 1
        else:
            proposed["schedule_revision"] = existing.schedule_revision
        if not bound_changed:
            wb = self._db.workbenches.upsert(workbench_id=workbench_id, **proposed)
            self._changed("workbench", wb.id, "update")
            return self._wb_payload(wb, principal)
        # Bound configuration and the authority it invalidates share one lock.
        # A provider is only signalled after the epoch fence has committed.
        from .schedule_delegation import ScheduleDelegationService
        service = ScheduleDelegationService(self._db)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            wb = self._db.workbenches.upsert_in_transaction(conn, workbench_id=workbench_id, **proposed)
            fenced = service.revoke_in_transaction(
                conn, workbench_id,
                "schedule_disabled" if not wb.schedule_enabled else "bound_terms_changed",
            )
            if enabling:
                service.enable_from_owner_in_transaction(principal, wb, conn)
        service.complete_fenced(fenced)
        self._changed("workbench", wb.id, "update")
        return self._wb_payload(wb, principal)

    def delete_workbench(self, principal: Principal, workbench_id: str) -> bool:
        _launch_own(principal, f"workbench:{workbench_id}")
        if self._db.workbench_items.has_active_items(workbench_id):
            raise ConflictError(
                "Cannot delete workbench with active items. Wait for running items to complete."
            )
        if not self._db.workbenches.delete(workbench_id):
            raise NotFound("workbench", workbench_id)
        self._changed("workbench", workbench_id, "delete")
        return True

    # ── Betterment A4: When and With ─────────────────────────────────────

    def set_when(self, principal: Principal, workbench_id: str, when: Any) -> dict[str, Any]:
        """Store one When choice: ``{"kind": "schedule", "every", "time", "day"}``,
        ``{"kind": "event", "event_id", "repository"}`` or ``{"kind": "manual"}``.

        The choice the owner presses is what starts it, and the other starts
        of this automation stop (one When). A schedule is stored as cron and
        turned on; with no engine to freeze yet it is kept, off, and the
        refusal says so."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can change when it runs",
                               context={"status": 403})
        _launch_own(principal, f"workbench:{workbench_id}")
        self._require_workbench(workbench_id)
        if not isinstance(when, dict):
            raise ValidationError("when must be a choice")
        kind = str(when.get("kind") or "")
        from .automation_when import cron_for, event_choices
        from .reaction_service import ReactionService

        reactions = ReactionService(self._db, observer=self._observer, on_changed=self._on_changed)
        own = [r for r in self._db.automations.list_reactions() if r.get("workbench_id") == workbench_id]

        def stop_events(keep: str = "") -> None:
            for reaction in own:
                if reaction["id"] != keep and reaction.get("enabled"):
                    reactions.set_workbench_automation_enabled(
                        principal, workbench_id=workbench_id, reaction_id=reaction["id"], enabled=False)

        if kind == "manual":
            self.update_workbench(principal, workbench_id, schedule=None, schedule_enabled=False)
            stop_events()
            self._db.workbenches.set_when_json(workbench_id, {"kind": "manual"})
        elif kind == "schedule":
            cron = cron_for(when)
            try:
                self.update_workbench(principal, workbench_id, schedule=cron, schedule_enabled=True)
            except ServiceError as exc:
                if exc.code not in {"no_assignment", "no_compatible_assignment", "delegation_stale_work"}:
                    raise
                self.update_workbench(principal, workbench_id, schedule=cron, schedule_enabled=False)
                stop_events()
                self._db.workbenches.set_when_json(workbench_id, {"kind": "schedule"})
                raise ValidationError(
                    "The schedule is saved but off: choose an engine under With, then turn it on.",
                    code="automation_schedule_needs_engine",
                ) from exc
            stop_events()
            self._db.workbenches.set_when_json(workbench_id, {"kind": "schedule"})
        elif kind == "event":
            event_id = str(when.get("event_id") or "")
            choice = next((c for c in event_choices() if c["id"] == event_id), None)
            if choice is None:
                raise ValidationError("Choose one of the events the hub can deliver")
            repository = str(when.get("repository") or "").strip()
            # The same event on the same repository is turned back on, not
            # made again.
            same = next((r for r in own if r.get("event_pattern") == choice["event_pattern"]
                         and ((self._db.automations.get_watch(r["watch_id"]) or {}).get("query") or {})
                         .get("repository") == repository), None) if repository else None
            reaction_id = same["id"] if same else reactions.create_preset_automation(
                principal, workbench_id=workbench_id, preset_id=event_id, repository=repository)["id"]
            # Turning it on reads the source now (the quiet baseline): a
            # source that cannot be read refuses here, before anything else
            # changes.
            reactions.set_workbench_automation_enabled(
                principal, workbench_id=workbench_id, reaction_id=reaction_id, enabled=True)
            stop_events(keep=reaction_id)
            self.update_workbench(principal, workbench_id, schedule=None, schedule_enabled=False)
            self._db.workbenches.set_when_json(workbench_id, {"kind": "event", "reaction_id": reaction_id})
        else:
            raise ValidationError("when.kind must be schedule, event or manual")
        return self.get_workbench(principal, workbench_id)

    def set_engine(self, principal: Principal, workbench_id: str, **fields: Any) -> dict[str, Any]:
        """With: the engine for this automation's runs (the subject assignment
        ``subject:workbench:<id>:capability:workbench.item``) and its optional
        Spend limit per run. A changed engine re-freezes a live schedule
        (``InferenceAssignmentService.set_assignment``), so a scheduled run
        uses it too."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Only the owner can choose the engine",
                               context={"status": 403})
        _launch_own(principal, f"workbench:{workbench_id}")
        self._require_workbench(workbench_id)
        unknown = set(fields) - {"profile_id", "spend_limit_usd"}
        if unknown:
            raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}")
        if "spend_limit_usd" in fields:
            limit = fields["spend_limit_usd"]
            if limit is not None:
                if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not 0 < float(limit) <= 1000:
                    raise ValidationError("The spend limit is a dollar amount above 0 and at most 1000")
                limit = round(float(limit), 2)
            self._db.workbenches.set_spend_limit(workbench_id, limit)
        profile_id = str(fields.get("profile_id") or "").strip()
        if profile_id:
            from holdspeak.kernel.runtime import _configure

            from .inference_assignment_service import InferenceAssignmentService

            _configure(self._db)
            assignments = InferenceAssignmentService(self._db)
            key = f"subject:workbench:{workbench_id}:capability:workbench.item"
            with self._db._connection() as conn:
                expected = assignments._expected_revision(conn, key)
            assignments.set_assignment(principal, {
                "command_id": _new_id("automation-with"),
                "expected_revision": expected,
                "scope": {"kind": "subject", "subject_kind": "workbench",
                          "subject_id": workbench_id, "capability_id": "workbench.item"},
                "entries": [{"profile_id": profile_id}],
            })
        self._changed("workbench", workbench_id, "update")
        return self.get_workbench(principal, workbench_id)

    def refreeze_schedule(self, principal: Principal, workbench_id: str) -> bool:
        """Re-approve a live schedule on the current engine.

        A schedule delegation freezes the route when it is turned on
        (``schedule_delegation._terms``); without this, a scheduled run keeps
        the engine of that moment after he changes With. The old delegation
        is revoked and a new one is frozen in one transaction; an off
        schedule has nothing to re-freeze."""
        if principal.kind is not PrincipalKind.OWNER:
            return False
        wb = self._db.workbenches.get(workbench_id)
        if wb is None or not wb.schedule_enabled or not wb.schedule:
            return False
        from holdspeak.kernel.runtime import _configure

        from .schedule_delegation import ScheduleDelegationService

        _configure(self._db)
        service = ScheduleDelegationService(self._db)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            fenced = service.revoke_in_transaction(conn, workbench_id, "engine_changed")
            service.enable_from_owner_in_transaction(principal, wb, conn)
        service.complete_fenced(fenced)
        return True

    # ── Items ────────────────────────────────────────────────────────────

    def get_item(
        self,
        principal: Principal,
        workbench_id: str,
        item_id: str,
        *,
        include_parked: bool = False,
    ) -> dict[str, Any]:
        return self._require_item(
            workbench_id, item_id, include_parked=include_parked
        ).to_dict()

    def add_item(
        self, principal: Principal, workbench_id: str, *, title: str, **fields: Any
    ) -> dict[str, Any]:
        if not title.strip():
            raise ValidationError("Item title is required")
        _launch_own(principal, f"workbench:{workbench_id}")
        self._require_workbench(workbench_id)
        supplied = str(fields.get("id") or "")
        if supplied:
            # An item id names ONE item anywhere: a launch never re-homes or
            # overwrites an existing one (live or parked).
            from .conductor_launch import require_new

            require_new(principal, f"workbench_item:{supplied}",
                        lambda: self._db.workbench_items.get(supplied, include_parked=True) is not None)
        item = self._db.workbench_items.upsert(
            item_id=supplied or _new_id("wbi"),
            workbench_id=workbench_id,
            title=title,
            body=str(fields.get("body", "")),
            priority=int(fields.get("priority", 3)),
            grounding=fields.get("grounding") or {},
            context=fields.get("context") or {},
        )
        from .conductor_launch import record_own

        record_own(principal, f"workbench_item:{item.id}")
        self._changed("workbench_item", item.id, "create")
        return item.to_dict()

    def update_item(
        self, principal: Principal, workbench_id: str, item_id: str, **fields: Any
    ) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        existing = self._require_item(workbench_id, item_id)

        def pick(key: str, default: Any) -> Any:
            return fields[key] if key in fields else default

        item = self._db.workbench_items.upsert(
            item_id=item_id,
            workbench_id=workbench_id,
            title=str(pick("title", existing.title)),
            body=str(pick("body", existing.body)),
            priority=int(pick("priority", existing.priority)),
            status=str(pick("status", existing.status)),
            grounding=pick("grounding", json.loads(existing.grounding_json or "{}")),
            context=pick("context", json.loads(existing.context_json or "{}")),
            result=pick("result", existing.result),
            result_egress=pick("result_egress", None),
            tokens_consumed=int(pick("tokens_consumed", existing.tokens_consumed)),
            claimed_at=pick("claimed_at", existing.claimed_at),
            completed_at=pick("completed_at", existing.completed_at),
        )
        self._changed("workbench_item", item.id, "update")
        return item.to_dict()

    def delete_item(
        self, principal: Principal, workbench_id: str, item_id: str
    ) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        return self.park_item(principal, workbench_id, item_id)

    def park_item(self, principal: Principal, workbench_id: str, item_id: str) -> dict[str, Any]:
        """Park one item while retaining every result and run link."""
        _launch_own(principal, f"workbench:{workbench_id}")
        self._require_workbench(workbench_id)
        self._require_item(workbench_id, item_id, include_parked=True)
        changed, reason, bad_ids = self._db.workbench_items.park_many(
            workbench_id, [item_id]
        )
        self._raise_transition_error(reason, bad_ids, parked=True)
        item = self._db.workbench_items.get(item_id, include_parked=True)
        if item is None or not changed:
            raise NotFound("item", item_id)
        self._changed("workbench_item", item_id, "park")
        return item.to_dict()

    def park_items(
        self, principal: Principal, workbench_id: str, item_ids: list[str]
    ) -> dict[str, list[str]]:
        """Park a validated set atomically, or leave every item untouched."""
        _launch_own(principal, f"workbench:{workbench_id}")
        ids = self._validate_item_ids(item_ids)
        self._require_workbench(workbench_id)
        changed, reason, bad_ids = self._db.workbench_items.park_many(workbench_id, ids)
        self._raise_transition_error(reason, bad_ids, parked=True)
        for item_id in changed:
            self._changed("workbench_item", item_id, "park")
        return {"parked": changed}

    def restore_item(
        self, principal: Principal, workbench_id: str, item_id: str
    ) -> dict[str, Any]:
        """Restore one parked item without rewriting its contents."""
        _launch_own(principal, f"workbench:{workbench_id}")
        self._require_workbench(workbench_id)
        self._require_item(workbench_id, item_id, include_parked=True)
        changed, reason, bad_ids = self._db.workbench_items.restore_many(
            workbench_id, [item_id]
        )
        self._raise_transition_error(reason, bad_ids, parked=False)
        item = self._db.workbench_items.get(item_id, include_parked=True)
        if item is None or not changed:
            raise NotFound("item", item_id)
        self._changed("workbench_item", item_id, "restore")
        return item.to_dict()

    def restore_items(
        self, principal: Principal, workbench_id: str, item_ids: list[str]
    ) -> dict[str, list[str]]:
        """Restore a validated set atomically, or leave every item untouched."""
        _launch_own(principal, f"workbench:{workbench_id}")
        ids = self._validate_item_ids(item_ids)
        self._require_workbench(workbench_id)
        changed, reason, bad_ids = self._db.workbench_items.restore_many(workbench_id, ids)
        self._raise_transition_error(reason, bad_ids, parked=False)
        for item_id in changed:
            self._changed("workbench_item", item_id, "restore")
        return {"restored": changed}

    def retry_mint(self, principal: Principal, workbench_id: str, item_id: str) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        item = self._require_item(workbench_id, item_id)
        if item.status != "done" or not item.result:
            raise ValidationError("Item is not done or has no result")
        if item.result_artifact_id:
            return {"artifact_id": item.result_artifact_id, "created": False}

        wb = self._require_workbench(workbench_id)
        recipe = self._db.recipes.get(wb.recipe_id) if wb.recipe_id else None
        if recipe is None:
            raise ValidationError("No recipe assigned")
        # Retry is historical projection work: recover the completed item's
        # frozen route evidence instead of resolving today's placement.
        from types import SimpleNamespace
        with self._db._connection() as conn:
            row = conn.execute(
                """SELECT attempt.deployment_revision_id,attempt.boundary,plan.profile_id
                   FROM inference_route_attempts attempt
                   JOIN inference_route_executions execution ON execution.id=attempt.execution_id
                   JOIN inference_operation_route_request_plans operation ON operation.id=execution.operation_plan_id
                   JOIN inference_adoption_route_evidence evidence ON evidence.evidence_ref=operation.admission_evidence_ref
                   JOIN inference_adoption_material_snapshots material ON material.planning_reference=evidence.planning_reference
                   JOIN inference_route_plan_entries plan ON plan.plan_id=operation.route_plan_id
                    AND plan.route_leg_ordinal=attempt.route_leg_ordinal
                   JOIN kernel_operations child ON child.operation_id=attempt.child_operation_id
                  WHERE child.parent_operation_id IN (
                    SELECT parent_operation_id FROM workbench_runs WHERE workbench_id=?
                  )
                    AND json_extract(material.payload_json, '$.item_id')=?
                    AND json_extract(material.payload_json, '$.source_item_operation_id') IS NULL
                  ORDER BY attempt.terminal_at DESC LIMIT 1""",
                (workbench_id, item_id),
            ).fetchone()
        if row is None:
            raise ValidationError("No frozen route evidence found for this Workbench item")
        target = SimpleNamespace(boundary=str(row["boundary"]), model=str(row["profile_id"]).removeprefix("legacy-"))

        run_id = None
        with self._db._connection() as conn:
            existing = conn.execute(
                "SELECT source_run_id FROM artifacts WHERE source_item_id = ? LIMIT 1",
                (item_id,),
            ).fetchone()
            if existing and existing["source_run_id"]:
                run_id = existing["source_run_id"]
        if not run_id:
            runs = self._db.workbench_runs.list_for_workbench(workbench_id, limit=1)
            if not runs:
                raise ValidationError("No runs found for this automation")
            run_id = runs[0].id

        from holdspeak.workbench_conductor import _auto_mint_artifact
        artifact_id = _auto_mint_artifact(
            db=self._db, item=item, recipe=recipe, workbench=wb,
            run_id=run_id, target=target, output=item.result,
        )
        if not artifact_id:
            raise ServiceError("artifact_persist_failed", "Mint failed")
        return {"artifact_id": artifact_id, "created": True}

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool = True,
                  request_id: str | None = None,
                  source_event: dict[str, str] | None = None,
                  item_ids: list[str] | None = None) -> dict[str, Any]:
        """Run the pending queue, or only ``item_ids`` (an item's Re-run).

        An automation with an instruction runs one new occurrence instead, and
        its result goes where ``output_target`` says (Betterment A2)."""
        self._require_workbench(workbench_id)
        from holdspeak.workbench_conductor import run_workbench
        if request_id or source_event or item_ids:
            from holdspeak.kernel.runtime import _service
            from holdspeak.services.workbench_runner import WorkbenchRunner
            result = await WorkbenchRunner(self._db, _service()).run(
                principal, workbench_id, memory_enabled=memory_enabled,
                request_id=request_id, source_event=source_event,
                item_ids=item_ids,
            )
        else:
            result = await run_workbench(workbench_id, principal, memory_enabled=memory_enabled)
        return self._deliver(principal, result)

    async def run_item(
        self,
        principal: Principal,
        workbench_id: str,
        item_id: str,
        *,
        memory_enabled: bool = True,
        request_id: str | None = None,
        source_event: dict[str, str] | None = None,
        deadline_seconds: float = 600,
    ) -> dict[str, Any]:
        """Admit exactly one causal Workbench item, never the pending batch."""
        self._require_item(workbench_id, item_id)
        from holdspeak.kernel.runtime import _service
        from holdspeak.services.workbench_runner import WorkbenchRunner

        result = await WorkbenchRunner(self._db, _service()).run(
            principal,
            workbench_id,
            memory_enabled=memory_enabled,
            request_id=request_id,
            source_event=source_event,
            deadline_seconds=deadline_seconds,
            item_ids=[item_id],
        )
        return self._deliver(principal, result)

    def _deliver(self, principal: Principal, result: Any) -> Any:
        """Send each new occurrence result to its output target (Betterment A2)."""
        if not isinstance(result, dict) or not result.get("run_id"):
            return result
        from .automation_runs import deliver_run

        deliveries = deliver_run(self._db, principal, result)
        if deliveries:
            result = {**result, "deliveries": deliveries}
            self._changed("workbench", str(self._run_workbench_id(result["run_id"]) or ""), "update")
        return result

    def _run_workbench_id(self, run_id: str) -> str | None:
        with self._db._connection() as conn:
            row = conn.execute("SELECT workbench_id FROM workbench_runs WHERE id=?", (run_id,)).fetchone()
        return str(row["workbench_id"]) if row is not None else None

    def open_result(self, principal: Principal, workbench_id: str, artifact_id: str) -> dict[str, Any]:
        """Open one result: a ``new`` result becomes ``read`` (decision 5)."""
        self._require_workbench(workbench_id)
        from .automation_runs import open_result

        opened = open_result(self._db, workbench_id, artifact_id)
        self._changed("workbench", workbench_id, "update")
        return opened

    def cancel_run(self, principal: Principal, parent_operation_id: str) -> str:
        """Cancel exactly the authenticated parent, never a Workbench lookup."""
        from holdspeak.kernel.runtime import _service
        return _service().parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)

    def list_runs(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._db.workbench_runs.list_for_workbench(workbench_id)]

    # ── Templates and skills ─────────────────────────────────────────────

    def list_templates(self, principal: Principal) -> list[dict[str, Any]]:
        """Betterment A7: the starters New automation offers, each with its
        schedule as cron (the face reads it in words, never as cron)."""
        from holdspeak.workbench_templates import list_templates
        from .automation_when import cron_for

        return [{**starter, "schedule": cron_for(starter["when"]) if starter["when"]["kind"] == "schedule" else None}
                for starter in list_templates()]

    def make_from_starter(self, principal: Principal, starter: dict[str, Any]) -> dict[str, Any]:
        """Betterment A7: one automation with the starter's sentence and no
        agent (nothing is copied). A schedule is stored and stays Off: he
        turns it On (a starter is not a recurring-inference approval)."""
        from .automation_when import cron_for

        when = dict(starter["when"])
        made = self.create_workbench(
            principal, name=starter["name"], instruction=starter["instruction"],
            sources=list(starter["sources"]), output_target=starter["output_target"],
            schedule=cron_for(when) if when["kind"] == "schedule" else None, schedule_enabled=False,
        )
        self._db.workbenches.set_when_json(made["id"], {"kind": when["kind"]})
        return self._wb_payload(self._require_workbench(made["id"]), principal)

    def instantiate_template(
        self, principal: Principal, template_id: str, profile_id: str | None = None
    ) -> dict[str, Any]:
        from holdspeak.workbench_templates import get_starter, get_template
        starter = get_starter(template_id)
        template = None if starter is not None else get_template(template_id)
        if starter is None and template is None:
            raise NotFound("template", template_id)
        if profile_id is not None:
            self._refuse_post_marker_pointer_write(
                principal, {"profile_id": profile_id}
            )
        if starter is not None:
            return {"workbench": self.make_from_starter(principal, starter)}
        # A retired template (hidden from New automation): the old path.
        recipe_data = template["recipe"]
        recipe = self._db.recipes.upsert(
            recipe_id=_new_id("recipe"), name=recipe_data.get("name", "Agent"),
            role=recipe_data.get("role", ""), system_prompt=recipe_data.get("system_prompt", ""),
            user_template=recipe_data.get("user_template", ""), profile_id=profile_id or None,
        )
        wb_config = template.get("workbench", {})
        wb = self._db.workbenches.upsert(
            workbench_id=_new_id("workbench"), name=template["name"], recipe_id=recipe.id,
            profile_id=profile_id or None, schedule=wb_config.get("schedule"),
            # Instantiating a template is not recurring-inference approval.
            schedule_enabled=False,
        )
        for starter in template.get("starter_items", []):
            self._db.workbench_items.upsert(
                item_id=_new_id("wbi"), workbench_id=wb.id, title=starter.get("title", ""),
                body=starter.get("body", ""), priority=starter.get("priority", 3),
            )
        skill_names = template.get("skill_names", [])
        if skill_names:
            for skill in self._db.skills.list():
                if skill.title in skill_names:
                    recipe_ids = list(skill.to_dict().get("recipe_ids", []))
                    if recipe.id not in recipe_ids:
                        recipe_ids.append(recipe.id)
                        self._db.skills.upsert(
                            skill_id=skill.id, title=skill.title, body=skill.body,
                            source=skill.source, status=skill.status, recipe_ids=recipe_ids,
                            created_by=skill.created_by,
                        )
        return {"workbench": self._wb_payload(wb, principal), "recipe": recipe.to_dict()}

    def list_skills(
        self, principal: Principal, recipe_id: str | None = None
    ) -> list[dict[str, Any]]:
        skills = [skill.to_dict() for skill in self._db.skills.list()]
        if recipe_id is not None:
            skills = [skill for skill in skills if recipe_id in skill.get("recipe_ids", [])]
        return skills

    def create_skill(self, principal: Principal, *, title: str, body: str, **fields: Any) -> dict[str, Any]:
        if not title.strip():
            raise ValidationError("Skill title is required")
        if len(body) > SKILL_BODY_LIMIT:
            raise ValidationError(
                f"Skill body exceeds {SKILL_BODY_LIMIT:,} byte limit (got {len(body):,})"
            )
        skill = self._db.skills.upsert(
            skill_id=str(fields.get("id") or _new_id("skill")), title=title, body=body,
            source=str(fields.get("source", "owner-authored")),
            status=str(fields.get("status", "active")),
            recipe_ids=list(fields.get("recipe_ids", [])),
            created_by=str(fields.get("created_by", "")),
        )
        self._changed("skill", skill.id, "create")
        return skill.to_dict()

    def update_skill(self, principal: Principal, skill_id: str, **fields: Any) -> dict[str, Any]:
        existing = self._db.skills.get(skill_id)
        if existing is None:
            raise NotFound("skill", skill_id)

        def pick(key: str, default: Any) -> Any:
            return fields[key] if key in fields else default

        skill = self._db.skills.upsert(
            skill_id=skill_id, title=str(pick("title", existing.title)),
            body=str(pick("body", existing.body)), source=str(pick("source", existing.source)),
            status=str(pick("status", existing.status)),
            recipe_ids=list(pick("recipe_ids", existing.to_dict().get("recipe_ids", []))),
            created_by=str(pick("created_by", existing.created_by)),
        )
        self._changed("skill", skill.id, "update")
        return skill.to_dict()

    def delete_skill(self, principal: Principal, skill_id: str) -> bool:
        if not self._db.skills.delete(skill_id):
            raise NotFound("skill", skill_id)
        self._changed("skill", skill_id, "delete")
        return True

    # ── Memory ───────────────────────────────────────────────────────────

    def list_memory(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        from holdspeak.workbench_memory import read_memory
        return read_memory(workbench_id)

    def clear_memory(self, principal: Principal, workbench_id: str) -> bool:
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import clear_memory
        clear_memory(workbench_id)
        return True

    def forget_memory(self, principal: Principal, workbench_id: str, index: int, timestamp: str = "") -> bool:
        """Forget one lesson (Betterment A3); NotFound when it is not there."""
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import forget_memory
        if not forget_memory(workbench_id, index, timestamp):
            raise NotFound("lesson", str(index))
        return True

    def promote_memory(self, principal: Principal, workbench_id: str, index: int) -> dict[str, Any]:
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import read_memory
        entries = read_memory(workbench_id)
        if index < 0 or index >= len(entries):
            raise ValidationError("Invalid memory index")
        wb = self._db.workbenches.get(workbench_id)
        if not wb or not wb.recipe_id:
            raise ValidationError("Automation has no agent")
        entry = entries[index]
        skill = self._db.skills.upsert(
            skill_id=_new_id("skill"), title=f"Learned: {entry.get('content', '')[:60]}",
            body=entry.get("content", ""), source="agent-proposed", status="draft",
            recipe_ids=[wb.recipe_id], created_by=f"memory:{workbench_id}",
        )
        return skill.to_dict()

    # ── Voice resolution ─────────────────────────────────────────────────

    def resolve_voice(
        self, principal: Principal, workbench_id: str, text: str, request_id: str
    ) -> dict[str, Any]:
        now = time.monotonic()
        if now - self._resolve_timestamps.get(workbench_id, 0.0) < 2.0:
            raise ServiceError("resolver_rate_limited", "Wait before retrying", context={"error": "resolver_rate_limited", "detail": "Wait before retrying"})
        self._resolve_timestamps[workbench_id] = now
        if not text.strip():
            raise ValidationError("transcript is required")
        if principal is None or principal.kind is PrincipalKind.NONE:
            raise ServiceError("resolver_principal_required", "Authenticated principal required", context={"error": "resolver_principal_required"})
        wb = self._require_workbench(workbench_id)
        from holdspeak.voice_resolver import ZoneCatalogEntry, _extract_json_from_response, _validate_response, build_resolver_prompt
        zones = [ZoneCatalogEntry(id=z.id, name=z.name, items=0) for z in self._db.directories.list() if not getattr(z, "deleted", False)]
        if not zones:
            return {"refs": [], "egress": {}, "request_id": request_id, "attempts": 0}
        from holdspeak.kernel.runtime import _configure
        from holdspeak.services.inference_parent_route_bundle_service import InferenceParentRouteBundleService
        broker = _configure(self._db) if getattr(self, "_kernel", None) is None else self._kernel
        if principal.kind is PrincipalKind.OWNER:
            broker.inference_adoption_service.migrate_recipe_workbench_subject_assignments(principal)
        deadline = time.time() + 30
        bundle = InferenceParentRouteBundleService(broker, broker.inference_adoption_service).start(
            principal, command_id=f"voice-route-{request_id or uuid.uuid4().hex}", parent_kind="voice_reference_resolve",
            definition_ref=f"workbench:{workbench_id}", definition_revision=str(getattr(wb, "last_modified", "1")),
            input_snapshot={"workbench_id": workbench_id, "transcript_hash": hashlib.sha256(text.encode()).hexdigest()},
            deadline_at=deadline, lifecycle_child_budget=0,
            routes=[{"key": "resolve", "capability_id": "voice.reference_resolve", "invocation_id": f"voice:{request_id or uuid.uuid4().hex}", "subject_kind": "workbench", "subject_id": workbench_id}],
            parent_command_id=request_id or None,
        )
        parent, member = bundle["parent"], bundle["bundle"]["members"][0]
        if parent.replayed:
            receipt = broker.store.receipt(parent.operation_id) or {}
            return {"refs": [], "error": str(receipt.get("outcome") or "resolver_replayed"), "egress": {}, "request_id": request_id, "attempts": 0}
        from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
        route = broker.inference_adoption_service.plans.get_route_plan(ROUTE_PLANNING_AUTHORITY, str(member["route_plan_id"]))
        entry = dict(route["entries"][0])
        egress = {"boundary": str(entry["boundary"]), "model": str(entry["profile_id"]).removeprefix("legacy-")}
        prompt = build_resolver_prompt(zones, text)
        payload = {"system_prompt": "", "user_prompt": prompt, "temperature": 0.1, "max_tokens": 128,
                   "transcript_hash": hashlib.sha256(text.encode()).hexdigest(),
                   "catalog_hash": hashlib.sha256("|".join(f"{z.id}:{z.name}" for z in zones).encode()).hexdigest()}
        operation_id = "voice_reference_" + uuid.uuid4().hex

        def publish(value: Any, reservation: dict[str, Any]) -> str:
            digest = "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
            return broker.projection_stager.stage(str(reservation["child_invocation_id"]), "voice-resolver-attempt", {"output": str(dict(value).get("reference") or "")}, result_sha256=digest, receipt_result_ref=f"inference-result:{reservation['child_invocation_id']}/{digest}").result_ref

        admitted = broker.inference_adoption_service.admit_on_frozen_route(
            principal, command_id=f"{operation_id}:admit", route_plan_id=str(route["id"]), capability_id="voice.reference_resolve",
            operation_id=operation_id, payload=payload, reserved_output_tokens=128, parent_operation_id=parent.operation_id,
        )
        routed = broker.inference_adoption_service.execute(
            principal, execution_id=admitted["execution"]["id"], adapter=_VoiceResolutionAdapter(), publish=publish,
            parent_context=parent.context, planned_node="voice.reference_resolve",
        )
        try:
            receipt = broker.parent_run_controller.close(
                parent.context, "succeeded" if routed["outcome"] == "succeeded" else "failed",
                f"workbench:{workbench_id}", principal=principal,
            )
        except Exception as exc:
            # Cancellation can elect the parent terminal receipt while the
            # controller-owned model attempt is returning. Adopt that durable
            # winner rather than trying to overwrite it with a local close.
            from holdspeak.kernel.model import KernelRefused
            if not isinstance(exc, KernelRefused) or exc.reason != "parent_context_invalid":
                raise
            receipt = broker.store.receipt(parent.operation_id)
            if receipt is None:
                raise
        if routed["outcome"] != "succeeded" or receipt["outcome"] != "succeeded":
            disposition = str(receipt["outcome"]) if receipt["outcome"] != "succeeded" else str(routed["outcome"])
            return {"refs": [], "error": f"resolver_{disposition}", "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}
        raw = str(routed["result"]["reference"])
        parsed = _extract_json_from_response(raw)
        ids = None if parsed is None else _validate_response(parsed, {zone.id for zone in zones})
        if ids is None:
            return {"refs": [], "error": "resolver_parse_failure", "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}
        by_id = {zone.id: zone for zone in zones}
        return {"refs": [{"name": by_id[item].name, "id": item, "ref": f"zone:{item}", "kind": "zone"} for item in ids], "egress": egress, "request_id": request_id, "attempts": len(routed["receipt"]["attempts"]), "route_execution_receipt": routed["receipt"]}

    # ── Internal ─────────────────────────────────────────────────────────

    def _require_workbench(self, workbench_id: str) -> Any:
        wb = self._db.workbenches.get(workbench_id)
        if wb is None:
            raise NotFound("workbench", workbench_id)
        return wb

    def _require_item(
        self, workbench_id: str, item_id: str, *, include_parked: bool = False
    ) -> Any:
        item = self._db.workbench_items.get(item_id, include_parked=include_parked)
        if item is None or item.workbench_id != workbench_id:
            raise NotFound("item", item_id)
        return item

    @staticmethod
    def _validate_item_ids(item_ids: Any) -> list[str]:
        if not isinstance(item_ids, list) or not item_ids:
            raise ValidationError("item_ids must be a non-empty list")
        if any(not isinstance(item_id, str) or not item_id.strip() for item_id in item_ids):
            raise ValidationError("item_ids must contain non-empty strings")
        return list(dict.fromkeys(item_id.strip() for item_id in item_ids))

    @staticmethod
    def _raise_transition_error(
        reason: str | None, bad_ids: list[str], *, parked: bool
    ) -> None:
        if reason is None:
            return
        item_id = bad_ids[0] if bad_ids else ""
        if reason == "missing":
            raise NotFound("item", item_id)
        if reason == "claimed":
            raise ConflictError("Cannot park a claimed item")
        if reason == "already_parked":
            raise ConflictError("Item is already parked")
        if reason == "not_parked":
            raise ConflictError("Item is not parked")
        action = "park" if parked else "restore"
        raise ConflictError(f"Cannot {action} automation item {item_id}")

    def _wb_payload(
        self, wb: Any, principal: Principal, *, parked: bool = False
    ) -> dict[str, Any]:
        payload = wb.to_dict()
        items = self._db.workbench_items.list_for_workbench(wb.id, parked=parked)
        payload["items"] = [item.to_dict() for item in items]
        payload["item_count"] = len(items)
        payload["pending_count"] = sum(
            1 for item in items if item.status == "pending" and not item.parked
        )
        runs = self._db.workbench_runs.list_for_workbench(wb.id, limit=1)
        payload["last_run"] = runs[0].to_dict() if runs else None
        # Betterment A2: the Do text to show (an old automation reads its
        # agent's prompt; nothing is written) and the results, one per run.
        from .automation_runs import effective_instruction, results_of, source_names, sources_of

        shown, source = effective_instruction(self._db, wb)
        payload["instruction_shown"] = shown
        payload["instruction_from"] = source
        payload["results"] = results_of(self._db, wb.id)
        # Betterment A3: the About line names each source (never its ref).
        payload["sources_shown"] = source_names(self._db, sources_of(wb))
        # Betterment A7: a blank a starter could not guess, while it is open.
        from holdspeak.workbench_templates import starter_blanks

        payload["blanks"] = starter_blanks(str(wb.instruction or ""), sources_of(wb))
        # ... and the When line names an event start by its name. Betterment
        # A4: after a When choice, only the start he chose is this
        # automation's start (the others stay stored, off); before A4, all.
        try:
            chosen = json.loads(wb.when_json) if wb.when_json else {}
        except (TypeError, ValueError):
            chosen = {}
        payload.pop("when_json", None)
        payload["when_kind"] = str(chosen.get("kind") or "") or None
        payload["event_starts"] = [
            {"id": str(r.get("id") or ""), "name": str(r.get("name") or ""), "enabled": bool(r.get("enabled")),
             "event_pattern": str(r.get("event_pattern") or "")}
            for r in self._db.automations.list_reactions() if r.get("workbench_id") == wb.id
            and (not chosen or r.get("id") == chosen.get("reaction_id"))
        ]
        # Betterment A4: when the schedule fires next (only while it is on),
        # and the events the When editor can offer.
        from .automation_when import event_choices, next_run_at

        payload["next_run_at"] = next_run_at(wb.schedule, wb.schedule_enabled)
        payload["when_events"] = [{"id": c["id"], "words": c["words"], "needs": c["needs"],
                                   "subject": c["subject"], "event_pattern": c["event_pattern"]}
                                  for c in event_choices()]
        if principal.kind is PrincipalKind.OWNER:
            from .inference_assignment_service import InferenceAssignmentService

            effective = InferenceAssignmentService(self._db).resolve_effective(
                principal,
                capability_id="workbench.item",
                subject_kind="workbench",
                subject_id=wb.id,
            )
            assignment = effective.get("assignment") or {}
            payload["assignment_summary"] = {
                "status": effective["status"],
                "source": effective.get("inherited_from"),
                "chain": [str(entry["label"]) for entry in assignment.get("entries", [])],
                "repair": effective.get("repair"),
                # Betterment A4: the With picker marks the engine in use and
                # shows where its prompt goes.
                "profile_id": str((assignment.get("entries") or [{}])[0].get("profile_id") or "") or None,
                "boundary": str((assignment.get("entries") or [{}])[0].get("boundary") or "") or None,
            }
        return payload

    @staticmethod
    def _wb_fields(body: dict[str, Any], existing: Any = None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "recipe_id": pick("recipe_id", existing.recipe_id if existing else None) or None,
            "profile_id": pick("profile_id", existing.profile_id if existing else None) or None,
            "resolver_profile_id": pick("resolver_profile_id", existing.resolver_profile_id if existing else None) or None,
            "schedule": pick("schedule", existing.schedule if existing else None) or None,
            "schedule_enabled": bool(pick("schedule_enabled", existing.schedule_enabled if existing else False)),
            "schedule_revision": int(pick("schedule_revision", existing.schedule_revision if existing else 1)),
            "item_order": list(pick("item_order", [])),
            "instruction": str(pick("instruction", existing.instruction if existing else "") or ""),
            "sources": list(pick("sources", json.loads(existing.sources_json or "[]") if existing else [])),
            "output_target": str(pick("output_target", existing.output_target if existing else "inbox") or "inbox"),
        }

    def _clean_automation_fields(self, fields: dict[str, Any]) -> None:
        """Validate the instruction, sources and output target in place."""
        from .automation_runs import clean_output_target, clean_sources

        if "instruction" in fields:
            if fields["instruction"] is not None and not isinstance(fields["instruction"], str):
                raise ValidationError("instruction must be text")
            fields["instruction"] = str(fields["instruction"] or "").strip()
        if "sources" in fields:
            fields["sources"] = clean_sources(fields["sources"])
        if "output_target" in fields:
            fields["output_target"] = clean_output_target(self._db, fields["output_target"])
