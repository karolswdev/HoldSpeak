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
from typing import Any, Callable

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.observer import (
    NullObserver,
    PipelineObserver,
    current_correlation_id,
    observe_service,
)
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.services.snapshot_diff import (
    _timestamp,
    diff_snapshots,
    normalize_snapshot,
)
from holdspeak.services.workbench_service import WorkbenchService


SUPPORTED_QUERIES = {
    "gh": {"pull_requests", "issues"},
    "jira": {"issues"},
}
DEFAULT_WATCH_REFRESH_MINUTES = 35


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@observe_service
class ReactionService:
    def __init__(self, db: Any, *, observer: PipelineObserver | None = None,
                 snapshot_fetcher: Any | None = None,
                 on_changed: Callable[[str, str, str], None] | None = None) -> None:
        self._db = db
        self._repo = db.automations
        self._ledger = ServiceEventLedger(db)
        self._observer = observer or NullObserver()
        self._snapshot_fetcher = snapshot_fetcher
        # HS-200-45 R4: a projection writes workbench items below the
        # composed WorkbenchService. The hub passes its own callback; without
        # one, the composition root's bus is used, and outside a hub there is
        # no bus, so nothing is emitted.
        from holdspeak.runtime.composition import notify_desk_changed
        self._on_changed = on_changed or notify_desk_changed

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
            raise ValidationError("Supported Watches are gh/pull_requests, gh/issues and jira/issues")
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
        if enabled:
            # HS-200-43: enabling arms -- but ONLY a graduated row.
            # `arm_watch` itself refuses a disabled, paused, retired or
            # legacy (state='') watch, so a legacy row stays owned by
            # refresh_due_watches and never crosses into evaluate_due's
            # territory. Disabling writes nothing: `list_due_watches`
            # already filters on `enabled = 1`, so a stale
            # next_evaluation_at on a disabled row is inert.
            from .watch_service import arm_watch
            arm_watch(self._repo, watch_id)
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
        # HS-168 legacy-side watch guard: the repo query excludes
        # paused/retired watches and watches on archived projects at
        # the SQL level (list_enabled_legacy_watches).  The Python
        # _GRADUATED_STATES belt below stays as defense-in-depth.
        _GRADUATED_STATES = {"active", "tested", "paused", "retired"}
        for watch in self._repo.list_enabled_legacy_watches():
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
        workbenches = WorkbenchService(self._db, on_changed=self._on_changed)
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
                target = self._db.workbenches.get(reaction["workbench_id"])
                occurrence = target is not None and bool(str(target.instruction or "").strip())
                if occurrence:
                    # Betterment A2: an automation with an instruction makes one
                    # occurrence about this event (its title, its subject).
                    from .automation_runs import mint_occurrence

                    item = mint_occurrence(
                        self._db, target, item_id=item_id,
                        title=str(facts.get("entity_title") or "").strip() or title, event=event,
                        context={"reaction_id": reaction["id"], "event_id": event["id"]},
                    ).to_dict()
                    workbenches._changed("workbench_item", item["id"], "create")
                else:
                    item = workbenches.add_item(
                        principal, reaction["workbench_id"], title=title,
                        id=item_id,
                        body=json.dumps({"event": event}, sort_keys=True, indent=2),
                        grounding={"refs": event.get("refs", [])},
                        context={"reaction_id": reaction["id"], "event_id": event["id"]},
                    )
                operation_id = receipt_id = None
                # Betterment A4: an occurrence runs at once. "When something
                # happens" is the start he chose; an occurrence that waited
                # for a press would never run (Run now makes a fresh one).
                if reaction["auto_run"] or occurrence:
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
