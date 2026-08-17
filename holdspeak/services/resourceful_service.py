"""Intrinsic resourceful-when-idle control loop.

This service turns negative space into one bounded, causally scoped Workbench
item. It never asks a model to invent work: typed candidate providers must find
an eligible source revision first.
"""
from __future__ import annotations

import hashlib
import inspect
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.services.workbench_service import WorkbenchService


ItemRunner = Callable[
    [Principal, str, str, dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]
]

SUPPORTED_ROUTINES = {"loose_ideas", "failed_work"}
DEFAULT_IDLE_AFTER_MINUTES = 30
DEFAULT_COOLDOWN_HOURS = 6
DEFAULT_NIGHTLY_TARGET = 2
DEFAULT_NIGHT_ONLY = True
DEFAULT_NIGHT_START_HOUR = 22
DEFAULT_NIGHT_END_HOUR = 7
DEFAULT_ROUTINES = ["loose_ideas", "failed_work"]


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _night_key(now: datetime, start: int, end: int) -> str | None:
    hour = now.hour
    if start < end:
        if not start <= hour < end:
            return None
        return now.date().isoformat()
    if hour >= start:
        return now.date().isoformat()
    if hour < end:
        return (now.date() - timedelta(days=1)).isoformat()
    return None


class ResourcefulService:
    def __init__(self, db: Any, *, item_runner: ItemRunner | None = None) -> None:
        self._db = db
        self._repo = db.resourceful_policies
        self._ledger = ServiceEventLedger(db)
        self._item_runner = item_runner

    @staticmethod
    def _owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_principal_required",
                "Resourceful routines run as OWNER in v1",
                context={"status": 403},
            )

    def get_policy(self, principal: Principal, workbench_id: str) -> dict[str, Any]:
        self._owner(principal)
        if self._db.workbenches.get(workbench_id) is None:
            raise NotFound("workbench", workbench_id)
        policy = self._repo.get(workbench_id)
        return policy or {
            "workbench_id": workbench_id,
            "enabled": False,
            "idle_after_minutes": DEFAULT_IDLE_AFTER_MINUTES,
            "cooldown_hours": DEFAULT_COOLDOWN_HOURS,
            "nightly_target": DEFAULT_NIGHTLY_TARGET,
            "night_only": DEFAULT_NIGHT_ONLY,
            "night_start_hour": DEFAULT_NIGHT_START_HOUR,
            "night_end_hour": DEFAULT_NIGHT_END_HOUR,
            "routines": list(DEFAULT_ROUTINES),
            "idle_since": None,
            "idle_epoch": 0,
            "last_checked_at": None,
            "last_fired_at": None,
            "night_key": "",
            "nightly_count": 0,
            "last_outcome": "",
            "last_error": None,
        }

    def configure_policy(
        self,
        principal: Principal,
        workbench_id: str,
        *,
        enabled: bool,
        idle_after_minutes: int = DEFAULT_IDLE_AFTER_MINUTES,
        cooldown_hours: int = DEFAULT_COOLDOWN_HOURS,
        nightly_target: int = DEFAULT_NIGHTLY_TARGET,
        night_only: bool = DEFAULT_NIGHT_ONLY,
        night_start_hour: int = DEFAULT_NIGHT_START_HOUR,
        night_end_hour: int = DEFAULT_NIGHT_END_HOUR,
        routines: list[str] | None = None,
    ) -> dict[str, Any]:
        self._owner(principal)
        workbench = self._db.workbenches.get(workbench_id)
        if workbench is None:
            raise NotFound("workbench", workbench_id)
        if enabled and not workbench.recipe_id:
            raise ValidationError("Bind an agent before enabling resourceful routines")
        if not 1 <= int(idle_after_minutes) <= 1440:
            raise ValidationError("idle_after_minutes must be between 1 and 1440")
        if not 1 <= int(cooldown_hours) <= 168:
            raise ValidationError("cooldown_hours must be between 1 and 168")
        if not 1 <= int(nightly_target) <= 8:
            raise ValidationError("nightly_target must be between 1 and 8")
        if not 0 <= int(night_start_hour) <= 23 or not 0 <= int(night_end_hour) <= 23:
            raise ValidationError("night window hours must be between 0 and 23")
        selected = list(dict.fromkeys(routines or DEFAULT_ROUTINES))
        unsupported = sorted(set(selected) - SUPPORTED_ROUTINES)
        if unsupported:
            raise ValidationError(f"Unsupported resourceful routines: {', '.join(unsupported)}")
        return self._repo.upsert(
            workbench_id=workbench_id,
            enabled=enabled,
            idle_after_minutes=idle_after_minutes,
            cooldown_hours=cooldown_hours,
            nightly_target=nightly_target,
            night_only=night_only,
            night_start_hour=night_start_hour,
            night_end_hour=night_end_hour,
            routines=selected,
        )

    def history(self, principal: Principal, workbench_id: str) -> list[dict[str, Any]]:
        self._owner(principal)
        return self._repo.list_dispatches(workbench_id)

    def _has_actionable_work(self, workbench_id: str) -> bool:
        with self._db._connection() as conn:
            item = conn.execute(
                """SELECT 1 FROM workbench_items
                   WHERE workbench_id=? AND status IN ('pending','claimed') LIMIT 1""",
                (workbench_id,),
            ).fetchone()
            run = conn.execute(
                """SELECT 1 FROM workbench_runs
                   WHERE workbench_id=? AND status='running' LIMIT 1""",
                (workbench_id,),
            ).fetchone()
        return item is not None or run is not None

    def _loose_idea(self, workbench_id: str) -> dict[str, Any] | None:
        directory = self._db.directories.find_by_normalized_name("Loose Ideas")
        if directory is None:
            return None
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT n.id,n.title,n.body_markdown,n.last_modified
                   FROM directory_memberships m
                   JOIN notes n ON m.primitive_id=('note:' || n.id)
                   WHERE m.directory_id=? AND m.deleted=0 AND n.deleted=0
                   ORDER BY n.last_modified ASC,n.id ASC""",
                (directory.id,),
            ).fetchall()
        for row in rows:
            key = f'note:{row["id"]}:{row["last_modified"]}'
            if self._repo.was_dispatched(workbench_id, key):
                continue
            title = str(row["title"] or "Untitled loose idea")
            return {
                "candidate_key": key,
                "routine": "loose_ideas",
                "source_ref": f'note:{row["id"]}',
                "source_revision": str(row["last_modified"]),
                "title": f"Develop loose idea: {title}",
                "body": (
                    "Develop this loose idea into a concise, evidence-grounded proposal. "
                    "Clarify the opportunity, likely value, unknowns, and one practical next step. "
                    "Do not mutate or publish the source note; return a reviewable result.\n\n"
                    f"Source idea:\n{str(row['body_markdown'] or '')[:4000]}"
                ),
            }
        return None

    def _failed_work(self, workbench_id: str) -> dict[str, Any] | None:
        with self._db._connection() as conn:
            rows = conn.execute(
                """SELECT id,title,result,last_modified FROM workbench_items
                   WHERE status='failed' AND workbench_id != ?
                   ORDER BY last_modified ASC,id ASC LIMIT 100""",
                (workbench_id,),
            ).fetchall()
        for row in rows:
            key = f'workbench-item:{row["id"]}:{row["last_modified"]}'
            if self._repo.was_dispatched(workbench_id, key):
                continue
            title = str(row["title"] or row["id"])
            return {
                "candidate_key": key,
                "routine": "failed_work",
                "source_ref": f'workbench-item:{row["id"]}',
                "source_revision": str(row["last_modified"]),
                "title": f"Prepare recovery plan: {title}",
                "body": (
                    "Diagnose this failed Workbench item and prepare a bounded recovery plan. "
                    "Do not retry external effects. Identify the likely failure, evidence, and "
                    f"safest next action.\n\nPrevious result:\n{str(row['result'] or '')[:4000]}"
                ),
            }
        return None

    def _candidate(self, policy: dict[str, Any]) -> dict[str, Any] | None:
        providers = {
            "loose_ideas": self._loose_idea,
            "failed_work": self._failed_work,
        }
        for routine in policy["routines"]:
            candidate = providers[routine](policy["workbench_id"])
            if candidate is not None:
                return candidate
        return None

    async def _run_item(
        self,
        principal: Principal,
        workbench_id: str,
        item_id: str,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        if self._item_runner is not None:
            result = self._item_runner(principal, workbench_id, item_id, event)
            return await result if inspect.isawaitable(result) else result
        return await WorkbenchService(self._db).run_item(
            principal,
            workbench_id,
            item_id,
            request_id=f'resourceful:{event["id"]}',
            source_event={
                "event_id": event["id"],
                "correlation_id": event.get("correlation_id", ""),
                "causation_id": event["id"],
            },
            deadline_seconds=600,
        )

    async def tick(
        self, principal: Principal, *, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        self._owner(principal)
        current = now or datetime.now().astimezone()
        outcomes: list[dict[str, Any]] = []
        for initial in self._repo.list_enabled():
            workbench_id = initial["workbench_id"]
            candidate: dict[str, Any] | None = None
            item: dict[str, Any] | None = None
            try:
                if self._has_actionable_work(workbench_id):
                    self._repo.mark_busy(workbench_id)
                    outcomes.append({"workbench_id": workbench_id, "status": "busy"})
                    continue
                policy = initial
                if not policy.get("idle_since"):
                    policy = self._repo.begin_idle(workbench_id, idle_since=_iso(current))
                    self._ledger.append(
                        principal,
                        event_type="workbench.became_idle",
                        producer="ResourcefulService",
                        subject_ref=f"workbench:{workbench_id}",
                        source_revision=f'idle-epoch:{policy["idle_epoch"]}',
                        facts={"idle_since": policy["idle_since"], "idle_epoch": policy["idle_epoch"]},
                        refs=[f"workbench:{workbench_id}"],
                    )
                    outcomes.append({"workbench_id": workbench_id, "status": "idle_started"})
                    continue
                idle_since = _parse(policy["idle_since"])
                if idle_since is None or current - idle_since < timedelta(
                    minutes=policy["idle_after_minutes"]
                ):
                    outcomes.append({"workbench_id": workbench_id, "status": "warming"})
                    continue
                night_key = _night_key(
                    current, policy["night_start_hour"], policy["night_end_hour"]
                )
                if policy["night_only"] and night_key is None:
                    outcomes.append({"workbench_id": workbench_id, "status": "awaiting_night"})
                    continue
                effective_key = night_key or current.date().isoformat()
                nightly_count = policy["nightly_count"] if policy["night_key"] == effective_key else 0
                if nightly_count >= policy["nightly_target"]:
                    outcomes.append({"workbench_id": workbench_id, "status": "nightly_target_met"})
                    continue
                last_fired = _parse(policy.get("last_fired_at"))
                if last_fired and current - last_fired < timedelta(hours=policy["cooldown_hours"]):
                    outcomes.append({"workbench_id": workbench_id, "status": "cooldown"})
                    continue
                last_checked = _parse(policy.get("last_checked_at"))
                if (
                    policy.get("last_outcome") == "no_candidate"
                    and last_checked
                    and current - last_checked < timedelta(hours=1)
                ):
                    outcomes.append({"workbench_id": workbench_id, "status": "no_candidate_cooldown"})
                    continue
                candidate = self._candidate(policy)
                if candidate is None:
                    self._repo.mark_checked(
                        workbench_id,
                        at=_iso(current),
                        night_key=effective_key,
                        outcome="no_candidate",
                    )
                    outcomes.append({"workbench_id": workbench_id, "status": "no_candidate"})
                    continue
                event = self._ledger.append(
                    principal,
                    event_type="workbench.resourceful_opportunity_found",
                    producer="ResourcefulService",
                    subject_ref=f"workbench:{workbench_id}",
                    source_revision=candidate["candidate_key"],
                    facts={
                        "entity_title": candidate["title"],
                        "routine": candidate["routine"],
                        "candidate_key": candidate["candidate_key"],
                        "source_ref": candidate["source_ref"],
                        "idle_epoch": policy["idle_epoch"],
                    },
                    refs=[f"workbench:{workbench_id}", candidate["source_ref"]],
                    causation_id=f'idle-epoch:{policy["idle_epoch"]}',
                )
                item_id = "wbi_resourceful_" + hashlib.sha256(
                    f'{workbench_id}:{candidate["candidate_key"]}'.encode()
                ).hexdigest()[:20]
                item = WorkbenchService(self._db).add_item(
                    principal,
                    workbench_id,
                    id=item_id,
                    title=candidate["title"],
                    body=candidate["body"],
                    grounding={"refs": [candidate["source_ref"]]},
                    context={
                        "resourceful": True,
                        "event_id": event["id"],
                        "candidate_key": candidate["candidate_key"],
                        "routine": candidate["routine"],
                    },
                )
                self._repo.record_dispatch(
                    workbench_id=workbench_id,
                    candidate_key=candidate["candidate_key"],
                    routine=candidate["routine"],
                    source_ref=candidate["source_ref"],
                    event_id=event["id"],
                    item_id=item["id"],
                )
                self._repo.mark_checked(
                    workbench_id,
                    at=_iso(current),
                    night_key=effective_key,
                    outcome="admitted",
                    fired=True,
                )
                run = await self._run_item(principal, workbench_id, item["id"], event)
                operation_id = str(run.get("parent_operation_id") or "") or None
                receipt_id = str(run.get("receipt_id") or run.get("parent_receipt_id") or "") or None
                outcome = str(run.get("terminal_disposition") or "succeeded")
                if run.get("error"):
                    outcome = "failed"
                self._repo.complete_dispatch(
                    workbench_id,
                    candidate["candidate_key"],
                    outcome=outcome,
                    operation_id=operation_id,
                    receipt_id=receipt_id,
                )
                outcomes.append(
                    {
                        "workbench_id": workbench_id,
                        "status": "completed" if outcome == "succeeded" else outcome,
                        "item_id": item["id"],
                        "event_id": event["id"],
                        "candidate_key": candidate["candidate_key"],
                    }
                )
            except Exception as exc:
                if item is not None:
                    admitted = self._db.workbench_items.get(item["id"])
                    if admitted is not None and admitted.status in {"pending", "claimed"}:
                        WorkbenchService(self._db).update_item(
                            principal,
                            workbench_id,
                            item["id"],
                            status="failed",
                            result=f"Resourceful execution failed: {exc}",
                            completed_at=_iso(current),
                        )
                if candidate is not None and self._repo.was_dispatched(
                    workbench_id, candidate["candidate_key"]
                ):
                    self._repo.complete_dispatch(
                        workbench_id,
                        candidate["candidate_key"],
                        outcome="failed",
                    )
                key = _night_key(current, initial["night_start_hour"], initial["night_end_hour"])
                self._repo.mark_checked(
                    workbench_id,
                    at=_iso(current),
                    night_key=key or current.date().isoformat(),
                    outcome="failed",
                    error=str(exc),
                )
                outcomes.append({"workbench_id": workbench_id, "status": "failed", "error": str(exc)})
        return outcomes


__all__ = [
    "ResourcefulService",
    "SUPPORTED_ROUTINES",
    "DEFAULT_IDLE_AFTER_MINUTES",
    "DEFAULT_COOLDOWN_HOURS",
    "DEFAULT_NIGHTLY_TARGET",
    "DEFAULT_NIGHT_ONLY",
    "DEFAULT_NIGHT_START_HOUR",
    "DEFAULT_NIGHT_END_HOUR",
    "DEFAULT_ROUTINES",
]
