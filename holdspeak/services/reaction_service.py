"""Connector Watches -> typed service events -> OWNER-mode Workbench Reactions.

The v1 boundary is deliberately typed: connector packs submit normalized entity
snapshots. HoldSpeak owns comparison, durable signals, and idempotent delivery.
No Reaction scrapes presentation text or executes arbitrary connector output.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.observer import (
    NullObserver,
    PipelineObserver,
    current_correlation_id,
    observe_service,
)
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.services.workbench_service import WorkbenchService


SUPPORTED_QUERIES = {
    "gh": {"pull_requests"},
    "jira": {"issues"},
}
DEFAULT_WATCH_REFRESH_MINUTES = 35


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _clean_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _normalize_entity(connector_id: str, entity: Any) -> dict[str, Any]:
    if not isinstance(entity, dict):
        raise ValidationError("Every snapshot entity must be an object")
    entity_id = str(entity.get("id") or entity.get("number") or entity.get("key") or "").strip()
    if not entity_id:
        raise ValidationError("Every snapshot entity requires id, number, or key")
    common = {
        "id": entity_id,
        "title": str(entity.get("title") or entity.get("summary") or "").strip(),
        "url": str(entity.get("url") or "").strip(),
        "updated_at": str(entity.get("updated_at") or entity.get("updatedAt") or "").strip(),
    }
    if connector_id == "gh":
        common.update({
            "state": str(entity.get("state") or "").lower(),
            "is_draft": bool(entity.get("is_draft", entity.get("isDraft", False))),
            "review_requests": _clean_strings(
                entity.get("review_requests", entity.get("reviewRequests", []))
            ),
            "review_decision": str(
                entity.get("review_decision", entity.get("reviewDecision", "")) or ""
            ).lower(),
            "checks": str(entity.get("checks") or entity.get("ci") or "").lower(),
            "head_sha": str(entity.get("head_sha") or entity.get("headRefOid") or ""),
        })
    elif connector_id == "jira":
        common.update({
            "status": str(entity.get("status") or "").lower(),
            "status_category": str(entity.get("status_category") or "").lower(),
            "assignee": str(entity.get("assignee") or "").strip(),
            "priority": str(entity.get("priority") or "").lower(),
            "resolution": str(entity.get("resolution") or "").lower(),
            "due_at": str(entity.get("due_at") or entity.get("dueDate") or ""),
            "issue_type": str(entity.get("issue_type") or "").strip(),
            "labels": entity.get("labels", []) if isinstance(entity.get("labels"), list) else [],
            "project_key": str(entity.get("project_key") or "").strip(),
            "status_changed_at": str(entity.get("status_changed_at") or "").strip(),
        })
    return common


def normalize_snapshot(connector_id: str, entities: Any) -> dict[str, Any]:
    if not isinstance(entities, list):
        raise ValidationError("entities must be an array")
    normalized = [_normalize_entity(connector_id, entity) for entity in entities]
    by_id = {entity["id"]: entity for entity in normalized}
    if len(by_id) != len(normalized):
        raise ValidationError("snapshot entity ids must be unique")
    return {"schema": 1, "entities": {key: by_id[key] for key in sorted(by_id)}}


def _revision(entity: dict[str, Any]) -> str:
    material = json.dumps(entity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode()).hexdigest()


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _event(event_type: str, before: dict[str, Any],
           after: dict[str, Any], changed: Any) -> dict[str, Any]:
    entity = after or before
    revision = _revision(after or before)
    return {
        "event_type": event_type,
        "entity_ref": entity["id"],
        "source_revision": revision,
        "facts": {"entity_title": entity.get("title", ""), "url": entity.get("url", ""),
                  "changed": changed,
                  # HS-166-03: carry the current entity so snapshot-level
                  # comparisons (due_within_days, overdue, inactive_for,
                  # older_than, newer_than) can read field values.
                  "current": dict(entity)},
    }


def diff_snapshots(connector_id: str, before: dict[str, Any],
                   after: dict[str, Any], *, discovery_event: str = "") -> list[dict[str, Any]]:
    """Produce semantic transitions. Missing rows are not treated as deletion."""
    old = before.get("entities", {}) if isinstance(before, dict) else {}
    new = after.get("entities", {})
    events: list[dict[str, Any]] = []
    for entity_id, current in new.items():
        previous = old.get(entity_id)
        if previous is None:
            kind = discovery_event or (
                "github.pr.opened" if connector_id == "gh" else "jira.issue.discovered"
            )
            events.append(_event(kind, {}, current, {"entity": "new"}))
            continue
        if connector_id == "gh":
            if previous.get("state") != current.get("state"):
                state = current.get("state")
                kind = "github.pr.merged" if state == "merged" else "github.pr.state_changed"
                events.append(_event(kind, previous, current,
                                     {"state": [previous.get("state"), state]}))
            added = sorted(set(current.get("review_requests", [])) - set(previous.get("review_requests", [])))
            if added:
                events.append(_event("github.pr.review_requested", previous, current,
                                     {"reviewers": added}))
            for field, kind in (
                ("review_decision", "github.pr.review_decision_changed"),
                ("checks", "github.pr.checks_changed"),
                ("head_sha", "github.pr.head_changed"),
            ):
                if previous.get(field) != current.get(field):
                    events.append(_event(kind, previous, current,
                                         {field: [previous.get(field), current.get(field)]}))
        else:
            for field, kind in (
                ("assignee", "jira.issue.assigned"),
                ("status", "jira.issue.status_changed"),
                ("status_category", "jira.issue.category_changed"),
                ("priority", "jira.issue.priority_changed"),
                ("due_at", "jira.issue.due_changed"),
            ):
                if previous.get(field) != current.get(field):
                    events.append(_event(kind, previous, current,
                                         {field: [previous.get(field), current.get(field)]}))
            if not previous.get("resolution") and current.get("resolution"):
                events.append(_event("jira.issue.resolved", previous, current,
                                     {"resolution": current.get("resolution")}))
    return events


@observe_service
class ReactionService:
    def __init__(self, db: Any, *, observer: PipelineObserver | None = None,
                 snapshot_fetcher: Any | None = None) -> None:
        self._db = db
        self._repo = db.automations
        self._ledger = ServiceEventLedger(db)
        self._observer = observer or NullObserver()
        self._snapshot_fetcher = snapshot_fetcher

    @staticmethod
    def _owner(principal: Principal) -> None:
        if principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Reactions run as OWNER in v1",
                               context={"status": 403})

    def create_watch(self, principal: Principal, *, connector_id: str, query_kind: str,
                     name: str = "", query: dict[str, Any] | None = None,
                     enabled: bool = True, watch_id: str | None = None) -> dict[str, Any]:
        self._owner(principal)
        connector_id = connector_id.strip().lower()
        if connector_id == "github":
            connector_id = "gh"
        query_kind = query_kind.strip().lower()
        if query_kind not in SUPPORTED_QUERIES.get(connector_id, set()):
            raise ValidationError("Supported Watches are gh/pull_requests and jira/issues")
        return self._repo.create_watch(
            watch_id=watch_id or _id("watch"), connector_id=connector_id,
            query_kind=query_kind, name=name.strip(), query=query or {}, enabled=enabled,
        )

    def list_watches(self, principal: Principal) -> list[dict[str, Any]]:
        return self._repo.list_watches()

    def set_watch_enabled(self, principal: Principal, watch_id: str, enabled: bool) -> dict[str, Any]:
        self._owner(principal)
        if not self._repo.set_watch_enabled(watch_id, enabled):
            raise NotFound("watch", watch_id)
        return self._repo.get_watch(watch_id) or {}

    def preview_watch(self, principal: Principal, watch_id: str,
                      entities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        fetched = self._fetch(principal, watch, entities)
        snapshot = normalize_snapshot(watch["connector_id"], fetched)
        baseline = watch.get("snapshot") or {}
        changes = [] if not baseline else diff_snapshots(
            watch["connector_id"], baseline, snapshot,
            discovery_event=str(watch["query"].get("discovery_event") or ""),
        )
        return {"watch_id": watch_id, "baseline": not bool(baseline),
                "entity_count": len(snapshot["entities"]), "changes": changes,
                "would_project": sum(
                    len(self._repo.matching_reactions(watch_id, change["event_type"]))
                    for change in changes
                )}

    def establish_baseline(self, principal: Principal, watch_id: str) -> dict[str, Any]:
        """Persist the current source state without creating any event.

        Setup deliberately starts from observed *now*. Repeating the operation
        after changing a Watch query replaces the comparison point rather than
        replaying intervening history.
        """
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        try:
            snapshot = normalize_snapshot(
                watch["connector_id"], self._fetch(principal, watch, None),
            )
            self._repo.record_refresh(watch_id, snapshot, [])
        except Exception as exc:
            self._repo.record_refresh_error(watch_id, str(exc))
            raise
        return {
            "watch_id": watch_id,
            "baseline": True,
            "entity_count": len(snapshot["entities"]),
            "events": [],
            "projections": [],
        }

    def _fetch(self, principal: Principal, watch: dict[str, Any],
               entities: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if entities is not None:
            return entities
        if self._snapshot_fetcher is not None:
            return self._snapshot_fetcher(
                principal, connector_id=watch["connector_id"],
                query_kind=watch["query_kind"], query=watch["query"],
            )
        from holdspeak.services.watch_sources import fetch_watch_snapshot
        return fetch_watch_snapshot(
            principal, connector_id=watch["connector_id"],
            query_kind=watch["query_kind"], query=watch["query"],
        )

    async def refresh_watch(self, principal: Principal, watch_id: str,
                            entities: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self._owner(principal)
        watch = self._repo.get_watch(watch_id)
        if not watch:
            raise NotFound("watch", watch_id)
        if not watch["enabled"]:
            raise ValidationError("Watch is disabled")
        try:
            snapshot = normalize_snapshot(
                watch["connector_id"], self._fetch(principal, watch, entities),
            )
            baseline = watch.get("snapshot") or {}
            changes = [] if not baseline else diff_snapshots(
                watch["connector_id"], baseline, snapshot,
                discovery_event=str(watch["query"].get("discovery_event") or ""),
            )
            correlation_id = current_correlation_id()
            events = [self._ledger.envelope(
                principal,
                event_type=change["event_type"],
                producer=f'connector.{watch["connector_id"]}.watch',
                subject_ref=f'{watch["connector_id"]}:{watch["query_kind"]}:{change["entity_ref"]}',
                source_revision=change["source_revision"],
                facts=change["facts"],
                refs=[f"watch:{watch_id}"] + ([change["facts"]["url"]] if change["facts"].get("url") else []),
                correlation_id=correlation_id,
                causation_id=f"watch:{watch_id}",
            ) for change in changes]
            self._repo.record_refresh(watch_id, snapshot, events)
        except Exception as exc:
            self._repo.record_refresh_error(watch_id, str(exc))
            raise
        projections = []
        for event in events:
            projections.extend(await self._project(principal, event))
        return {"watch_id": watch_id, "baseline": not bool(baseline),
                "entity_count": len(snapshot["entities"]), "events": events,
                "projections": projections}

    async def refresh_due_watches(
        self, principal: Principal, *, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Refresh enabled Watches that have reached their durable cadence.

        A failure is recorded by ``refresh_watch`` and isolated to its Watch so
        one unavailable connector cannot starve the remaining automation pump.
        ``updated_at`` advances on both success and failure, providing a
        restart-safe retry fence without an in-memory scheduler ledger.
        """
        self._owner(principal)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        outcomes: list[dict[str, Any]] = []
        # HS-166-03 rider-b: graduated watches (state in active/tested/
        # paused/retired) belong to the WatchService scheduler
        # (evaluate_due), not the legacy ReactionService pump.
        _GRADUATED_STATES = {"active", "tested", "paused", "retired"}
        for watch in self._repo.list_watches():
            if not watch["enabled"]:
                continue
            if watch.get("state", "") in _GRADUATED_STATES:
                continue
            try:
                cadence = int(
                    watch["query"].get(
                        "refresh_interval_minutes", DEFAULT_WATCH_REFRESH_MINUTES
                    )
                )
            except (TypeError, ValueError):
                cadence = DEFAULT_WATCH_REFRESH_MINUTES
            cadence = max(1, min(cadence, 1440))
            last_attempt = _timestamp(watch.get("updated_at"))
            if last_attempt and current - last_attempt < timedelta(minutes=cadence):
                continue
            try:
                result = await self.refresh_watch(principal, watch["id"])
                outcomes.append({
                    "watch_id": watch["id"],
                    "status": "refreshed",
                    "event_count": len(result["events"]),
                    "projection_count": len(result["projections"]),
                })
            except Exception as exc:
                outcomes.append({
                    "watch_id": watch["id"],
                    "status": "failed",
                    "error": str(exc),
                })
        return outcomes

    def list_events(self, principal: Principal, *, event_type: str | None = None,
                    producer: str | None = None,
                    limit: int = 100) -> list[dict[str, Any]]:
        return self._ledger.list(
            principal, event_type=event_type, producer=producer, limit=limit,
        )

    def list_presets(self, principal: Principal) -> list[dict[str, Any]]:
        del principal
        from holdspeak.automation_presets import list_automation_presets
        return list_automation_presets()

    def create_preset_automation(self, principal: Principal, *, workbench_id: str,
                                 preset_id: str, repository: str | None = None) -> dict[str, Any]:
        """Install a disabled Watch + Reaction from a named safe preset."""
        self._owner(principal)
        from holdspeak.automation_presets import get_automation_preset

        preset = get_automation_preset(preset_id)
        if preset is None:
            raise NotFound("automation preset", preset_id)
        query = dict(preset["query"])
        if preset["connector_id"] == "gh":
            repo = str(repository or "").strip()
            if not repo:
                raise ValidationError("GitHub automation presets require repository as owner/name")
            if "/" not in repo or repo.startswith("/") or repo.endswith("/"):
                raise ValidationError("repository must be owner/name")
            query["repository"] = repo
        watch = self.create_watch(
            principal, connector_id=preset["connector_id"], query_kind=preset["query_kind"],
            name=preset["label"], query=query, enabled=False,
        )
        reaction = self.create_reaction(
            principal, watch_id=watch["id"], event_pattern=preset["event_pattern"],
            workbench_id=workbench_id, name=preset["label"],
            title_template=preset["title_template"], auto_run=False, enabled=False,
        )
        return {"id": reaction["id"], "preset_id": preset["id"],
                "watch": watch, "reaction": reaction}

    def create_reaction(self, principal: Principal, *, event_pattern: str,
                        workbench_id: str, name: str = "", watch_id: str | None = None,
                        title_template: str = "{event_type}: {entity_title}",
                        auto_run: bool = False, enabled: bool = False,
                        reaction_id: str | None = None) -> dict[str, Any]:
        self._owner(principal)
        if self._db.workbenches.get(workbench_id) is None:
            raise NotFound("workbench", workbench_id)
        if watch_id and not self._repo.get_watch(watch_id):
            raise NotFound("watch", watch_id)
        pattern = event_pattern.strip()
        if not pattern or ("*" in pattern and not pattern.endswith(".*")):
            raise ValidationError("event_pattern must be exact or a family ending in .*" )
        return self._repo.create_reaction(
            reaction_id=reaction_id or _id("reaction"), name=name.strip(), watch_id=watch_id,
            event_pattern=pattern, workbench_id=workbench_id,
            title_template=title_template, auto_run=auto_run, enabled=enabled,
        )

    def list_reactions(self, principal: Principal) -> list[dict[str, Any]]:
        return self._repo.list_reactions()

    def set_reaction_enabled(self, principal: Principal, reaction_id: str,
                             enabled: bool) -> dict[str, Any]:
        self._owner(principal)
        if not self._repo.set_reaction_enabled(reaction_id, enabled):
            raise NotFound("reaction", reaction_id)
        return self._repo.get_reaction(reaction_id) or {}

    def list_workbench_automations(self, principal: Principal,
                                   workbench_id: str) -> list[dict[str, Any]]:
        self._owner(principal)
        if self._db.workbenches.get(workbench_id) is None:
            raise NotFound("workbench", workbench_id)
        rows = []
        for reaction in self._repo.list_reactions():
            if reaction["workbench_id"] != workbench_id:
                continue
            watch = self._repo.get_watch(reaction["watch_id"]) if reaction.get("watch_id") else None
            rows.append({"id": reaction["id"], "reaction": reaction, "watch": watch})
        return rows

    def _workbench_reaction(self, principal: Principal, workbench_id: str,
                            reaction_id: str) -> dict[str, Any]:
        self._owner(principal)
        reaction = self._repo.get_reaction(reaction_id)
        if not reaction or reaction["workbench_id"] != workbench_id:
            raise NotFound("automation", reaction_id)
        return reaction

    def set_workbench_automation_enabled(self, principal: Principal, *, workbench_id: str,
                                         reaction_id: str, enabled: bool) -> dict[str, Any]:
        """Enable only after a quiet baseline; disable both sides together."""
        reaction = self._workbench_reaction(principal, workbench_id, reaction_id)
        watch_id = reaction.get("watch_id")
        if enabled and watch_id:
            self.establish_baseline(principal, watch_id)
            self.set_watch_enabled(principal, watch_id, True)
        self.set_reaction_enabled(principal, reaction_id, enabled)
        if not enabled and watch_id:
            self.set_watch_enabled(principal, watch_id, False)
        return {"id": reaction_id, "reaction": self._repo.get_reaction(reaction_id),
                "watch": self._repo.get_watch(watch_id) if watch_id else None}

    def test_workbench_automation(self, principal: Principal, *, workbench_id: str,
                                  reaction_id: str) -> dict[str, Any]:
        reaction = self._workbench_reaction(principal, workbench_id, reaction_id)
        if not reaction.get("watch_id"):
            raise ValidationError("This automation has no Watch to test")
        return self.preview_watch(principal, reaction["watch_id"])

    def workbench_automation_history(self, principal: Principal, *, workbench_id: str,
                                     reaction_id: str, limit: int = 100) -> list[dict[str, Any]]:
        self._workbench_reaction(principal, workbench_id, reaction_id)
        return self._repo.list_reaction_projections(reaction_id, limit=limit)

    async def process_pending(self, principal: Principal, *, limit: int = 100) -> list[dict[str, Any]]:
        self._owner(principal)
        results = []
        for event in reversed(self._repo.list_events(limit=limit)):
            results.extend(await self._project(principal, event))
        return results

    async def _project(self, principal: Principal,
                       event: dict[str, Any]) -> list[dict[str, Any]]:
        results = []
        workbenches = WorkbenchService(self._db)
        watch_ref = next((ref for ref in event.get("refs", []) if ref.startswith("watch:")), "")
        watch_id = watch_ref.removeprefix("watch:") or None
        for reaction in self._repo.matching_reactions(watch_id, event["event_type"]):
            if self._repo.has_projection(reaction["id"], event["id"]):
                continue
            item_id = "wbi_reaction_" + hashlib.sha256(
                f'{reaction["id"]}:{event["id"]}'.encode()
            ).hexdigest()[:20]
            facts = event["facts"]
            values = {"signal_type": event["event_type"],
                      "event_type": event["event_type"],
                      "entity_ref": event["subject_ref"],
                      "subject_ref": event["subject_ref"],
                      "entity_title": facts.get("entity_title", "")}
            try:
                try:
                    title = reaction["title_template"].format_map(values)
                except (KeyError, ValueError):
                    title = f'{event["event_type"]}: {facts.get("entity_title", "")}'
                item = workbenches.add_item(
                    principal, reaction["workbench_id"], title=title,
                    id=item_id,
                    body=json.dumps({"event": event}, sort_keys=True, indent=2),
                    grounding={"refs": event.get("refs", [])},
                    context={"reaction_id": reaction["id"], "event_id": event["id"]},
                )
                operation_id = receipt_id = None
                if reaction["auto_run"]:
                    run = await workbenches.run_item(
                        principal, reaction["workbench_id"], item["id"],
                        request_id=f'reaction:{reaction["id"]}:{event["id"]}',
                        source_event={"event_id": event["id"],
                                      "correlation_id": event.get("correlation_id", ""),
                                      "causation_id": event["id"]},
                    )
                    operation_id = str(run.get("parent_operation_id") or "") or None
                    receipt_id = str(run.get("receipt_id") or "") or None
                self._repo.record_projection(
                    reaction["id"], event["id"], item_id=item["id"],
                    operation_id=operation_id, receipt_id=receipt_id,
                )
                results.append({"reaction_id": reaction["id"], "status": "projected",
                                "item_id": item["id"], "operation_id": operation_id,
                                "receipt_id": receipt_id})
            except Exception as exc:
                results.append({"reaction_id": reaction["id"], "status": "projection_failed",
                                "error": str(exc)})
        return results
