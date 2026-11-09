"""Transport-neutral Workbench operations (HS-122-02)."""
from __future__ import annotations

from holdspeak.db.models import _json_list
from holdspeak.services.observer import NullObserver, PipelineObserver, observe_service

import json
from typing import Any, Callable

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ServiceError, ValidationError
from holdspeak.ids import new_id as _new_id



def _spend_limit(limit: Any) -> float | None:
    """A Spend limit per run: None (the engine's own) or dollars in (0, 1000]."""
    if limit is None:
        return None
    if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not 0 < float(limit) <= 1000:
        raise ValidationError("The spend limit is a dollar amount above 0 and at most 1000")
    return round(float(limit), 2)


#: Betterment M3: the sentence words an agent uses (DESIGN section 4), and
#: the stored field each content word writes. ``when``, ``with`` and
#: ``spend_limit`` go through set_when and set_engine (the owner's).
SENTENCE_WORDS = frozenset({"do", "about", "when", "with", "put_in", "spend_limit", "review_by"})
#: The Do kinds: ``run`` (make a result), AG14 ``hand_to_agent`` and PG14
#: ``run_program`` (each run makes and starts one Program).
DO_KINDS = ("run", "hand_to_agent", "run_program")
#: The Do kinds that run natively (no inference route of their own).
NATIVE_DO_KINDS = frozenset({"hand_to_agent", "run_program"})
#: PG14: the Program a run_program automation makes.
PROGRAM_FIELDS = ("program_template", "program_control", "program_runs_on", "program_may_call", "program_may_handoff")
#: Only the owner chooses who works and how far it may go alone.
_OWNER_FIELDS = frozenset({"agent_profile", "review_by", "program_control", "program_runs_on",
                           "program_may_call", "program_may_handoff"})
_SENTENCE_CONTENT = {"do": "instruction", "about": "sources", "put_in": "output_target"}


def _launch_own(principal: Principal, *refs: str) -> None:
    """Conductor K6: a launch changes only Workbenches it created."""
    from .conductor_launch import require_own

    require_own(principal, *refs)


@observe_service
class WorkbenchService:
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
        if principal.kind is not PrincipalKind.OWNER and (_OWNER_FIELDS & set(fields)):
            raise ServiceError(
                "owner_principal_required",
                "Only the owner can choose the agent, the reviewer or the control level",
                context={"status": 403},
            )
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
        if principal.kind is not PrincipalKind.OWNER and (_OWNER_FIELDS & set(fields)):
            raise ServiceError(
                "owner_principal_required",
                "Only the owner can choose the agent, the reviewer or the control level",
                context={"status": 403},
            )
        # A scheduled hand is approved for its complete sentence and native
        # binding.  Editing any of those terms fences the old authority and
        # makes the owner approve it again through When.
        from .automation_runs import sources_of

        kinds = {str(getattr(existing, "do_kind", "run") or "run"), str(proposed["do_kind"] or "run")}
        native_hand = bool(NATIVE_DO_KINDS & kinds)
        bound_keys = ("schedule", "schedule_enabled", "recipe_id", "profile_id")
        if native_hand:
            bound_keys += ("do_kind", "agent_profile", "review_by", "instruction", "sources", "output_target",
                           *PROGRAM_FIELDS)

        def stored(key: str) -> Any:
            if key == "sources":
                return sources_of(existing)
            if key == "program_runs_on":
                return _json_list(existing.program_runs_on_json)
            return getattr(existing, key)

        bound_changed = any(proposed[key] != stored(key) for key in bound_keys)
        if native_hand and bound_changed and existing.schedule_enabled and "schedule_enabled" not in fields:
            # A changed binding must be visibly reapproved through When.  Keep
            # the persisted schedule off while its old authority is fenced.
            proposed["schedule_enabled"] = False
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
        from .watch_service import WatchService

        # 2026-11-08: an event start is a watch (WatchService). A legacy
        # Watch + Reaction row runs nothing any more (it needs setting again).
        watches = WatchService(self._db, observer=self._observer)

        def stop_events(keep: str = "") -> None:
            for watch in watches.automation_event_watches(workbench_id):
                if watch["id"] != keep and watch.get("state") in {"active", "tested"}:
                    watches.set_automation_event_enabled(
                        principal, workbench_id=workbench_id, watch_id=watch["id"], enabled=False)

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
                message = "The schedule is saved but off: choose an agent under With, then turn it on."
                kind_now = str(getattr(self._require_workbench(workbench_id), "do_kind", "run") or "run")
                if kind_now == "run_program":
                    message = "The schedule is saved but off: choose a template under Do, then turn it on."
                elif kind_now != "hand_to_agent":
                    message = "The schedule is saved but off: choose an engine under With, then turn it on."
                raise ValidationError(
                    message,
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
            # made again. Turning it on reads the source now (the quiet
            # baseline): a source that cannot be read refuses here, before
            # anything else changes.
            watch_id = watches.start_automation_event(
                principal, workbench_id=workbench_id, preset_id=event_id, repository=repository)["id"]
            stop_events(keep=watch_id)
            self.update_workbench(principal, workbench_id, schedule=None, schedule_enabled=False)
            self._db.workbenches.set_when_json(workbench_id, {"kind": "event", "watch_id": watch_id})
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
        wb = self._require_workbench(workbench_id)
        unknown = set(fields) - {"profile_id", "spend_limit_usd"}
        if unknown:
            raise ValidationError(f"Unknown fields: {', '.join(sorted(unknown))}")
        if str(getattr(wb, "do_kind", "run") or "run") == "hand_to_agent":
            profile_id = str(fields.get("profile_id") or "").strip()
            if profile_id:
                aliases = {
                    "agent-claude": "claude-default", "legacy-agent-claude": "claude-default",
                    "agent-codex": "codex-default", "legacy-agent-codex": "codex-default",
                    "agent-pi": "pi-default", "legacy-agent-pi": "pi-default",
                }
                profile_id = aliases.get(profile_id, profile_id)
                # Route all native binding changes through the normal
                # workbench update seam so a live schedule is fenced and must
                # be re-approved with the new profile.
                self.update_workbench(principal, workbench_id, agent_profile=profile_id)
            if "spend_limit_usd" in fields:
                self._db.workbenches.set_spend_limit(workbench_id, _spend_limit(fields["spend_limit_usd"]))
            self._changed("workbench", workbench_id, "update")
            return self.get_workbench(principal, workbench_id)
        if "spend_limit_usd" in fields:
            self._db.workbenches.set_spend_limit(workbench_id, _spend_limit(fields["spend_limit_usd"]))
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

    # ── Betterment M3: the sentence, for an agent (MCP) ──────────────────

    def create_automation(
        self, principal: Principal, *, name: str, sentence: dict[str, Any], **fields: Any
    ) -> dict[str, Any]:
        """Make one automation from its sentence in one call: Do, About and
        Put it in are written with it; With, Spend limit and When follow
        (each is the owner's: ``set_engine``, ``set_when``). The sentence is
        checked before anything is written."""
        starts = self._check_sentence(sentence)
        content = self._sentence_content(sentence, fields)
        made = self.create_workbench(principal, name=name, **fields, **content)
        return self._apply_starts(principal, str(made["id"]), sentence, starts)

    def ensure_project_update(
        self, principal: Principal, project_id: str, *, audience: str = "manager",
    ) -> dict[str, Any]:
        """Create the project's update automation once, when Write is pressed."""
        from .errors import NotFound

        project = self._db.projects.get_project(project_id)
        if project is None:
            raise NotFound("project", project_id)
        target = f"project_updates:{project_id}"
        live = next((wb for wb in self._db.workbenches.list()
                     if str(wb.output_target or "") == target), None)
        if live is not None:
            return self._wb_payload(live, principal)
        project_name = str(getattr(project, "name", "") or project_id)
        reader = "my team" if str(audience).strip().lower() in {"team", "my team"} else "my manager"
        instruction = (
            f"Write the weekly status update for {project_name} for {reader}. "
            "Read this week's meetings, the project's decisions, what each person owes, "
            "the open risks, and the project's linked source state. Lead with the state "
            "and the one thing I need. Leave out 1:1s and People notes. Cite what you used."
        )
        made = self.create_workbench(
            principal,
            id=f"project-update-{project_id}",
            name=f"{project_name} update",
            instruction=instruction,
            sources=[f"project:{project_id}"],
            output_target=target,
            schedule="0 15 * * 5",
            schedule_enabled=False,
        )
        # The workbench route inherits the global workbench.item assignment.
        # When the project update capability already names an engine, copy its
        # profile into the subject assignment; this is configuration metadata,
        # not a second engine choice.
        profile_id = ""
        try:
            with self._db._connection() as conn:
                entry = conn.execute(
                    """SELECT e.profile_id FROM inference_assignment_heads h
                       JOIN inference_assignments e ON e.assignment_id=h.assignment_id
                         AND e.assignment_revision=h.revision AND e.ordinal=0
                       WHERE h.assignment_key='capability:project.update_draft' AND h.cleared=0""",
                ).fetchone()
            profile_id = str(entry["profile_id"] or "") if entry is not None else ""
        except Exception:
            profile_id = ""
        if profile_id:
            try:
                made = self.set_engine(principal, str(made["id"]), profile_id=profile_id)
            except Exception:
                # A global assignment is still inherited by the runner; an
                # unavailable scoped binding must not block the first Write.
                pass
        return made

    def update_automation(
        self, principal: Principal, workbench_id: str, *, sentence: dict[str, Any], **fields: Any
    ) -> dict[str, Any]:
        """Change the words of an automation's sentence that are given."""
        starts = self._check_sentence(sentence)
        content = self._sentence_content(sentence, fields)
        if fields or content:
            self.update_workbench(principal, workbench_id, **fields, **content)
        else:
            _launch_own(principal, f"workbench:{workbench_id}")
            self._require_workbench(workbench_id)
        return self._apply_starts(principal, workbench_id, sentence, starts)

    @staticmethod
    def _check_sentence(sentence: dict[str, Any]) -> dict[str, Any] | None:
        unknown = set(sentence) - SENTENCE_WORDS
        if unknown:
            raise ValidationError(f"Unknown sentence words: {', '.join(sorted(unknown))}")
        if "with" in sentence and not str(sentence["with"] or "").strip():
            raise ValidationError("with is an installed agent profile id")
        if "do" in sentence:
            do = str(sentence["do"] or "").strip()
            if do not in DO_KINDS and not do:
                raise ValidationError("do must be hand_to_agent, run_program or run")
        if "review_by" in sentence:
            from .agent_review import normalize_review_by

            try:
                normalize_review_by(sentence["review_by"])
            except ServiceError as exc:
                raise ValidationError(str(exc)) from exc
        if "spend_limit" in sentence:
            _spend_limit(sentence["spend_limit"])
        if "when" not in sentence:
            return None
        from .automation_when import choice_from_mcp

        return choice_from_mcp(sentence["when"])

    @staticmethod
    def _sentence_content(sentence: dict[str, Any], fields: dict[str, Any]) -> dict[str, Any]:
        content = {stored: sentence[word] for word, stored in _SENTENCE_CONTENT.items() if word in sentence}
        if "do" in sentence:
            do = str(sentence["do"] or "").strip()
            if do in DO_KINDS:
                content["do_kind"] = do
            if do == "run_program":
                # PG14: the goal is the instruction field, never the kind word.
                content.pop("instruction", None)
                # A hand's source item is the agent's brief.  Keep an
                # explicit Do sentence in its own instruction field so the
                # owner can edit it on the face and scheduled terms can bind
                # it without turning it into an inference assignment.
        if "with" in sentence:
            content["agent_profile"] = str(sentence["with"]).strip()
        if "review_by" in sentence:
            from .agent_review import normalize_review_by

            content["review_by"] = normalize_review_by(sentence["review_by"])
        both = set(content) & set(fields)
        if both:
            raise ValidationError(f"Give each once, as a sentence word or a field: {', '.join(sorted(both))}")
        return content

    def _apply_starts(
        self, principal: Principal, workbench_id: str, sentence: dict[str, Any], when: dict[str, Any] | None,
    ) -> dict[str, Any]:
        engine: dict[str, Any] = {}
        wb = self._require_workbench(workbench_id)
        do_kind = str(getattr(wb, "do_kind", "run") or "run")
        hand_mode = do_kind == "hand_to_agent"
        if "with" in sentence and do_kind == "run_program":
            # PG14: With names the agent the Program runs on.
            self.update_workbench(principal, workbench_id, program_runs_on=[str(sentence["with"]).strip()])
        elif "with" in sentence and not hand_mode:
            engine["profile_id"] = str(sentence["with"]).strip()
        elif "with" in sentence:
            self.update_workbench(principal, workbench_id, agent_profile=str(sentence["with"]).strip())
        if "spend_limit" in sentence:
            engine["spend_limit_usd"] = sentence["spend_limit"]
        if engine:
            self.set_engine(principal, workbench_id, **engine)
        notice = ""
        if when is not None:
            try:
                self.set_when(principal, workbench_id, when)
            except ValidationError as exc:
                # The schedule is kept, off, until an engine is chosen: the
                # automation exists, so say so instead of failing the call.
                if exc.code != "automation_schedule_needs_engine":
                    raise
                notice = exc.detail
        payload = self.get_workbench(principal, workbench_id)
        if notice:
            payload["notice"] = notice
        return payload

    def results(self, principal: Principal, workbench_id: str, *, limit: int = 1) -> dict[str, Any]:
        """The newest results, newest first: the rendered text, what its agent
        looked at, wrote and prepared, the cost and the failure reason (the
        automation window's own read, ``automation_runs.results_of``)."""
        self._require_workbench(workbench_id)
        from .automation_runs import results_of

        bounded = max(1, min(int(limit), 20))
        return {"workbench_id": workbench_id, "results": results_of(self._db, workbench_id, limit=bounded)}

    def cancel_latest_run(self, principal: Principal, workbench_id: str, run_id: str = "") -> dict[str, Any]:
        """Cancel this automation's run that is still running (the newest, or
        ``run_id``). The kernel cancels only a run its caller started."""
        self._require_workbench(workbench_id)
        query = "SELECT id, parent_operation_id FROM workbench_runs WHERE workbench_id=? AND status='running'"
        params: list[Any] = [workbench_id]
        if run_id:
            query += " AND id=?"
            params.append(run_id)
        with self._db._connection() as conn:
            row = conn.execute(query + " ORDER BY started_at DESC LIMIT 1", params).fetchone()
        if row is None or not row["parent_operation_id"]:
            raise ConflictError("Nothing is running for this automation")
        disposition = self.cancel_run(principal, str(row["parent_operation_id"]))
        return {"run_id": str(row["id"]), "disposition": disposition}

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

    async def run(self, principal: Principal, workbench_id: str, *, memory_enabled: bool = True,
                  request_id: str | None = None,
                  source_event: dict[str, str] | None = None,
                  item_ids: list[str] | None = None) -> dict[str, Any]:
        """Run the automation now (Run now, ``workbench.run``, ``automation.run``).

        2026-11-08: an automation with an instruction runs as a Program of
        one prompt step (``automation_runs.run_as_program``); this call waits
        for its answer, which goes where ``output_target`` says. An old queue
        (an agent and no instruction of its own) is refused: it is set up as
        a program. An agent hand and a Program automation run as before
        (their ``item_ids``: a hand's Re-run)."""
        from . import automation_runs

        wb = self._require_workbench(workbench_id)
        native = str(getattr(wb, "do_kind", "run") or "run") in NATIVE_DO_KINDS
        if not native and not item_ids and not source_event:
            if automation_runs.runs_as_program(wb):
                import asyncio

                from . import engine_door
                from .program_prompt import JOB
                from holdspeak.kernel.runtime import _service

                try:  # no engine is a state he repairs: the named refusal, before any Program is made
                    engine_door.engine_for(_service(), JOB, subject=("workbench", str(wb.id)))
                except engine_door.EngineDoorError as exc:
                    raise ServiceError("no_assignment", exc.detail, context={"status": 409}) from None
                ran = await asyncio.to_thread(
                    automation_runs.run_as_program, self._db, principal, wb, wait=True,
                    key=f"request:{request_id}" if request_id else None)
                delivered = automation_runs.program_delivery(self._db, ran["program_id"])
                self._changed("workbench", str(wb.id), "update")
                return {**ran, **({"deliveries": [delivered]} if delivered else {})}
            if automation_runs.effective_instruction(self._db, wb)[1] == "agent":
                raise ServiceError(
                    "set_up_as_program", "Programs run this queue now: set it up as a program.",
                    context={"status": 409})
            return {"error": f"The automation {wb.name} has nothing to do yet: write what it should do."}
        # A hand or a Program automation (the item queue is parked: the
        # runner refuses any other run as set_up_as_program).
        from holdspeak.kernel.runtime import _service
        from holdspeak.services.workbench_runner import WorkbenchRunner

        result = await WorkbenchRunner(self._db, _service()).run(
            principal, workbench_id, memory_enabled=memory_enabled,
            request_id=request_id, source_event=source_event,
            item_ids=item_ids,
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

    def make_one_automation(self, principal: Principal, workbench_id: str) -> dict[str, Any]:
        """Betterment A9: an old queue automation becomes one automation.

        Its agent's prompt (the Do text it already shows) is written as its
        instruction, so each run makes one result. Nothing else changes: its
        agent, skills, lessons, items and their results stay. An automation
        that already has its own instruction is returned as it is."""
        wb = self._require_workbench(workbench_id)
        from .automation_runs import effective_instruction

        shown, source = effective_instruction(self._db, wb)
        if source == "automation":
            return self._wb_payload(wb, principal)
        if not shown:
            raise ValidationError("This automation has no agent prompt to copy")
        return self.update_workbench(principal, workbench_id, instruction=shown)

    def new_results(self, principal: Principal) -> list[dict[str, Any]]:
        """Betterment A6: the automations that hold a NEW result (Today's
        rows and the Automations dock tile's count)."""
        from .automation_runs import new_results

        return new_results(self._db)

    def prepared_for_today(self, principal: Principal) -> dict[str, Any]:
        """Betterment daily D9: ``prepared`` (Today's Prepared block, or None)
        and ``automation`` (the live automation whose Put it in is Today, the
        one Prepare now runs; Morning prep first; or None)."""
        from holdspeak.workbench_templates import MORNING_PREP_ID

        from .automation_runs import prepared_for_today

        prepared = prepared_for_today(self._db, principal)
        live = [wb for wb in self._db.workbenches.list() if str(wb.output_target or "") == "today"]
        live.sort(key=lambda wb: (wb.id != MORNING_PREP_ID, wb.id))
        automation = {"id": live[0].id, "name": str(live[0].name or "Morning prep")} if live else None
        return {"prepared": prepared, "automation": automation}

    def cancel_run(self, principal: Principal, parent_operation_id: str) -> str:
        """Cancel exactly the authenticated parent, never a Workbench lookup."""
        from holdspeak.kernel.runtime import _service
        return _service().parent_run_controller.cancel_by_operation_id(principal, parent_operation_id)

    def list_runs(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        from .automation_runs import program_run_rows

        # 2026-11-08: a run is a Program of one prompt step; earlier runs are workbench_runs rows.
        rows = [r.to_dict() for r in self._db.workbench_runs.list_for_workbench(workbench_id)]
        rows.extend(program_run_rows(self._db, workbench_id))
        return sorted(rows, key=lambda row: str(row.get("started_at") or ""), reverse=True)

    # ── Templates and skills ─────────────────────────────────────────────

    def list_templates(self, principal: Principal) -> list[dict[str, Any]]:
        """Betterment A7: the starters New automation offers, each with its
        schedule as cron (the face reads it in words, never as cron)."""
        from holdspeak.workbench_templates import list_templates
        from .automation_when import cron_for

        return [{**starter, "schedule": cron_for(starter["when"]) if starter["when"]["kind"] == "schedule" else None}
                for starter in list_templates(self._db)]

    def make_from_starter(
        self, principal: Principal, starter: dict[str, Any], *, workbench_id: str = "",
    ) -> dict[str, Any]:
        """Betterment A7: one automation with the starter's sentence and no
        agent (nothing is copied). A schedule is stored and stays Off: he
        turns it On (a starter is not a recurring-inference approval).
        ``workbench_id``: a stable id (Betterment D9, Morning prep)."""
        from .automation_when import cron_for

        when = dict(starter["when"])
        extra = {"id": workbench_id} if workbench_id else {}
        made = self.create_workbench(
            principal, **extra, name=starter["name"], instruction=starter["instruction"],
            sources=list(starter["sources"]), output_target=starter["output_target"],
            do_kind=str(starter.get("do_kind") or "run"),
            agent_profile=str(starter.get("agent_profile") or ""),
            review_by=str(starter.get("review_by") or ""),
            **{key: starter[key] for key in PROGRAM_FIELDS if key in starter},
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
        if starter is not None and starter.get("needs") == "pi_engine":
            # PG14: the Overnight starter runs pi on an engine of the library.
            from holdspeak.workbench_templates import _with_engine, pi_engine

            engine = pi_engine(self._db)
            if not engine:
                raise ValidationError("Add an engine that pi can run on first (Engines).")
            starter = _with_engine(starter, engine)
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

    # ── Memory ───────────────────────────────────────────────────────────

    def list_memory(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        from holdspeak.workbench_memory import read_memory
        return read_memory(workbench_id)

    def forget_memory(self, principal: Principal, workbench_id: str, index: int, timestamp: str = "") -> bool:
        """Forget one lesson (Betterment A3); NotFound when it is not there."""
        _launch_own(principal, f"workbench:{workbench_id}")
        from holdspeak.workbench_memory import forget_memory
        if not forget_memory(workbench_id, index, timestamp):
            raise NotFound("lesson", str(index))
        return True

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
        do_kind = str(getattr(wb, "do_kind", "run") or "run")
        payload["instruction_shown"] = "Hand to an agent" if do_kind == "hand_to_agent" else shown
        if do_kind == "run_program":
            from .automation_program import program_payload

            payload["program"] = program_payload(self._db, wb)
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
        # 2026-11-08: an event start is a watch (WatchService).
        from .watch_service import WatchService

        payload["event_starts"] = [
            {"id": str(w.get("id") or ""), "name": str(w.get("name") or ""),
             "enabled": w.get("state") in {"active", "tested"},
             "event_pattern": str(w.get("event_pattern") or "")}
            for w in WatchService(self._db).automation_event_watches(wb.id)
            if not chosen or w.get("id") == chosen.get("watch_id")
        ]
        # Watch fold 4 (2026-11-08): an event start saved before the fold (a
        # legacy Reaction) runs nothing. No migration: the When line says it
        # must be set again until he saves a When choice.
        payload["when_needs_reset"] = bool(chosen.get("reaction_id")) or (
            not chosen and any(r.get("workbench_id") == wb.id and r.get("enabled")
                               for r in self._db.automations.list_reactions()))
        # Betterment A4: when the schedule fires next (only while it is on),
        # and the events the When editor can offer.
        from .automation_when import event_choices, next_run_at

        payload["next_run_at"] = next_run_at(wb.schedule, wb.schedule_enabled)
        payload["when_events"] = [{"id": c["id"], "words": c["words"], "needs": c["needs"],
                                   "subject": c["subject"], "event_pattern": c["event_pattern"]}
                                  for c in event_choices()]
        if principal.kind is PrincipalKind.OWNER and do_kind == "run_program":
            words = payload["program"]["runs_on_words"]
            payload["assignment_summary"] = {
                "status": "assigned" if payload["program"]["template"] else "no_assignment",
                "source": "program", "chain": [words] if words else [], "profile_id": None,
                "boundary": None,
            }
        elif principal.kind is PrincipalKind.OWNER and do_kind != "hand_to_agent":
            from .inference_assignment_service import InferenceAssignmentService

            effective = InferenceAssignmentService(self._db).resolve_effective(
                principal,
                capability_id="workbench.item",
                subject_kind="workbench",
                subject_id=wb.id,
            )
            assignment = effective.get("assignment") or {}
            # Betterment A10: an agent engine (a CLI) names its vendor, so the
            # egress chip says where the prompt goes and About offers a Folder.
            first = str((assignment.get("entries") or [{}])[0].get("profile_id") or "")
            from ..intel.cli_engine import cli_vendor
            from .automation_runs import cli_endpoint_of

            with self._db._connection() as conn:
                vendor = cli_vendor(cli_endpoint_of(conn, first)) if first else ""
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
            if vendor:
                payload["assignment_summary"]["vendor"] = vendor
        elif principal.kind is PrincipalKind.OWNER:
            profile_id = str(getattr(wb, "agent_profile", "") or "").strip()
            labels = {
                "claude-default": ("Claude Code", "claude"),
                "codex-default": ("Codex CLI", "codex"),
                "pi-default": ("pi", "pi"),
            }
            label, executable = labels.get(profile_id, (profile_id, ""))
            payload["agent_profile_label"] = label
            payload["agent_binding"] = {
                "profile_id": profile_id or None,
                "label": label or None,
                "executable": executable or None,
            }
            payload["assignment_summary"] = {
                "status": "assigned" if profile_id else "no_assignment",
                "source": "native_agent",
                "chain": [label] if label else [],
                "profile_id": profile_id or None,
                "boundary": "same_device" if profile_id else None,
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
            "do_kind": str(pick("do_kind", existing.do_kind if existing else "run") or "run"),
            "agent_profile": str(pick("agent_profile", existing.agent_profile if existing else "") or ""),
            "review_by": str(pick("review_by", existing.review_by if existing else "") or ""),
            "program_template": str(pick("program_template", existing.program_template if existing else "") or ""),
            "program_control": str(pick("program_control", existing.program_control if existing else "") or ""),
            "program_runs_on": list(pick("program_runs_on", _json_list(existing.program_runs_on_json) if existing else []) or []),
            "program_may_call": bool(pick("program_may_call", existing.program_may_call if existing else False)),
            "program_may_handoff": bool(pick("program_may_handoff", existing.program_may_handoff if existing else False)),
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
        if "do_kind" in fields:
            fields["do_kind"] = str(fields["do_kind"] or "run").strip()
            if fields["do_kind"] not in DO_KINDS:
                raise ValidationError("do_kind must be run, hand_to_agent or run_program")
        from .automation_program import clean_program_fields

        clean_program_fields(fields)
        if "agent_profile" in fields:
            fields["agent_profile"] = str(fields["agent_profile"] or "").strip()
        if "review_by" in fields:
            from .agent_review import normalize_review_by

            try:
                fields["review_by"] = normalize_review_by(fields["review_by"])
            except ServiceError as exc:
                raise ValidationError(str(exc)) from exc
