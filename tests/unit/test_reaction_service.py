from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.reaction_service import ReactionService
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.workbench_conductor import WorkbenchConductor


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


def test_watch_baseline_is_quiet_then_emits_and_delivers_idempotently(tmp_path) -> None:
    db = Database(tmp_path / "reactions.db")
    db.workbenches.upsert(workbench_id="wb-review", name="Review queue")
    service = ReactionService(db)
    watch = service.create_watch(
        OWNER, connector_id="github", query_kind="pull_requests",
        query={"repository": "acme/widget"}, watch_id="watch-gh",
    )
    reaction = service.create_reaction(
        OWNER, watch_id=watch["id"], event_pattern="github.pr.*",
        workbench_id="wb-review", reaction_id="reaction-gh", enabled=True,
    )
    assert reaction["enabled"] is True

    baseline = asyncio.run(service.refresh_watch(OWNER, watch["id"], [{
        "number": 17, "title": "Ship it", "url": "https://github.com/acme/widget/pull/17",
        "state": "OPEN", "reviewRequests": [], "checks": "passing", "headRefOid": "a1",
    }]))
    assert baseline["baseline"] is True
    assert baseline["events"] == []

    changed_entities = [{
        "number": 17, "title": "Ship it", "url": "https://github.com/acme/widget/pull/17",
        "state": "MERGED", "reviewRequests": ["karol"], "checks": "failing", "headRefOid": "b2",
    }]
    changed = asyncio.run(service.refresh_watch(OWNER, watch["id"], changed_entities))
    assert {row["event_type"] for row in changed["events"]} == {
        "github.pr.merged", "github.pr.review_requested",
        "github.pr.checks_changed", "github.pr.head_changed",
    }
    assert all(row["status"] == "projected" for row in changed["projections"])
    assert len(db.workbench_items.list_for_workbench("wb-review")) == 4

    repeated = asyncio.run(service.refresh_watch(OWNER, watch["id"], changed_entities))
    assert repeated["events"] == []
    assert repeated["projections"] == []
    assert len(db.workbench_items.list_for_workbench("wb-review")) == 4


def test_jira_signals_are_semantic_and_missing_rows_are_not_deletions(tmp_path) -> None:
    db = Database(tmp_path / "jira-reactions.db")
    service = ReactionService(db)
    watch = service.create_watch(
        OWNER, connector_id="jira", query_kind="issues", watch_id="watch-jira",
        query={"jql": "assignee = currentUser()"},
    )
    asyncio.run(service.refresh_watch(OWNER, watch["id"], [{
        "key": "OPS-7", "summary": "Rotate key", "status": "todo",
        "assignee": "", "priority": "medium", "resolution": "",
    }]))
    changed = asyncio.run(service.refresh_watch(OWNER, watch["id"], [{
        "key": "OPS-7", "summary": "Rotate key", "status": "done",
        "assignee": "karol", "priority": "high", "resolution": "fixed",
    }]))
    assert {row["event_type"] for row in changed["events"]} == {
        "jira.issue.assigned", "jira.issue.status_changed",
        "jira.issue.priority_changed", "jira.issue.resolved",
    }
    disappeared = asyncio.run(service.refresh_watch(OWNER, watch["id"], []))
    assert disappeared["events"] == []


def test_any_service_event_can_feed_a_global_reaction(tmp_path) -> None:
    db = Database(tmp_path / "service-events.db")
    db.workbenches.upsert(workbench_id="wb-decisions", name="Decision follow-through")
    service = ReactionService(db)
    service.create_reaction(
        OWNER, event_pattern="decision.committed", workbench_id="wb-decisions",
        reaction_id="reaction-decision", enabled=True,
    )
    event = ServiceEventLedger(db).append(
        OWNER, event_type="decision.committed", producer="DecisionService",
        subject_ref="decision:42", source_revision="7",
        facts={"entity_title": "Choose the event spine"}, refs=["decision:42"],
    )
    projected = asyncio.run(service.process_pending(OWNER))
    assert projected == [{
        "reaction_id": "reaction-decision", "status": "projected",
        "item_id": projected[0]["item_id"], "operation_id": None, "receipt_id": None,
    }]
    item = db.workbench_items.get(projected[0]["item_id"])
    assert item is not None
    assert event["id"] in item.context_json


def test_auto_run_links_projection_to_kernel_result(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "auto-run.db")
    db.workbenches.upsert(workbench_id="wb-auto", name="Automatic")
    service = ReactionService(db)
    watch = service.create_watch(
        OWNER, connector_id="gh", query_kind="pull_requests", watch_id="watch-auto",
    )
    service.create_reaction(
        OWNER, event_pattern="github.pr.merged", workbench_id="wb-auto",
        watch_id=watch["id"], reaction_id="reaction-auto", enabled=True, auto_run=True,
    )
    captured = {}

    async def fake_run(self, principal, workbench_id, item_id, **kwargs):  # noqa: ANN001
        captured["item_id"] = item_id
        captured.update(kwargs)
        return {"parent_operation_id": "op-auto", "receipt_id": "rcpt-auto"}

    monkeypatch.setattr(WorkbenchService, "run_item", fake_run)
    asyncio.run(service.refresh_watch(OWNER, watch["id"], [{"number": 1, "state": "open"}]))
    changed = asyncio.run(service.refresh_watch(
        OWNER, watch["id"], [{"number": 1, "state": "merged"}],
    ))
    event = changed["events"][0]
    assert captured["request_id"] == f'reaction:reaction-auto:{event["id"]}'
    assert captured["item_id"].startswith("wbi_reaction_")
    assert captured["source_event"]["event_id"] == event["id"]
    with db._connection() as conn:
        projection = conn.execute(
            "SELECT * FROM reaction_event_projections WHERE reaction_id='reaction-auto'"
        ).fetchone()
    assert (projection["operation_id"], projection["receipt_id"]) == ("op-auto", "rcpt-auto")


def test_preview_queries_source_without_advancing_baseline(tmp_path) -> None:
    db = Database(tmp_path / "preview.db")
    calls = []

    def fetcher(principal, **kwargs):  # noqa: ANN001
        calls.append(kwargs)
        return [{"number": 9, "state": "open", "title": "Nine"}]

    service = ReactionService(db, snapshot_fetcher=fetcher)
    watch = service.create_watch(
        OWNER, connector_id="gh", query_kind="pull_requests", watch_id="watch-preview",
        query={"repository": "acme/app"},
    )
    preview = service.preview_watch(OWNER, watch["id"])
    assert preview == {
        "watch_id": "watch-preview", "baseline": True,
        "entity_count": 1, "changes": [], "would_project": 0,
    }
    assert calls[0]["query"] == {"repository": "acme/app"}
    assert db.automations.get_watch(watch["id"])["snapshot"] == {}


def test_due_watch_pump_uses_35_minute_default_and_isolates_failures(tmp_path) -> None:
    db = Database(tmp_path / "watch-pump.db")
    calls = []

    def fetcher(principal, **kwargs):  # noqa: ANN001
        del principal
        calls.append(kwargs["connector_id"])
        if kwargs["connector_id"] == "jira":
            raise ServiceError("connector_unavailable", "Jira is offline")
        return [{"number": 3, "state": "open", "title": "Three"}]

    service = ReactionService(db, snapshot_fetcher=fetcher)
    service.create_watch(
        OWNER, connector_id="gh", query_kind="pull_requests",
        watch_id="watch-healthy", query={"repository": "acme/app"},
    )
    service.create_watch(
        OWNER, connector_id="jira", query_kind="issues",
        watch_id="watch-offline", query={"jql": "assignee=currentUser()"},
    )
    now = datetime.now(timezone.utc)
    old = (now - timedelta(minutes=36)).isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute("UPDATE connector_watches SET updated_at=?", (old,))

    outcomes = asyncio.run(service.refresh_due_watches(OWNER, now=now))

    assert [(row["watch_id"], row["status"]) for row in outcomes] == [
        ("watch-healthy", "refreshed"),
        ("watch-offline", "failed"),
    ]
    assert calls == ["gh", "jira"]
    assert db.automations.get_watch("watch-offline")["last_error"] == "Jira is offline"
    assert asyncio.run(
        service.refresh_due_watches(OWNER, now=now + timedelta(minutes=34))
    ) == []


def test_conductor_pumps_due_watches(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "conductor-watch-pump.db")
    calls = {"refresh": [], "process": []}

    async def pump(self, principal, **kwargs):  # noqa: ANN001
        del self, kwargs
        calls["refresh"].append(principal)
        return [{"watch_id": "watch-1", "status": "refreshed"}]

    async def process(self, principal, **kwargs):  # noqa: ANN001
        del self
        calls["process"].append((principal, kwargs["limit"]))
        return []

    monkeypatch.setattr("holdspeak.db.get_database", lambda: db)
    monkeypatch.setattr(ReactionService, "refresh_due_watches", pump)
    monkeypatch.setattr(ReactionService, "process_pending", process)

    WorkbenchConductor()._tick()

    assert len(calls["refresh"]) == 1
    assert calls["refresh"][0].kind is PrincipalKind.OWNER
    assert calls["process"] == [(calls["refresh"][0], 500)]


def test_reaction_mutations_require_owner(tmp_path) -> None:
    service = ReactionService(Database(tmp_path / "authority.db"))
    agent = Principal(PrincipalKind.AGENT, "agent-1")
    with pytest.raises(ServiceError, match="Reactions run as OWNER"):
        service.create_watch(agent, connector_id="github", query_kind="pull_requests")
