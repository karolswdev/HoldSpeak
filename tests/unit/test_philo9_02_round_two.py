"""PHILO-9-02 round two: Codex Astra's r1 findings on 24576f25, each ported as a fence.

Every reproduction (``/tmp/holdspeak-counsel-684-*.py``) is ported whole: the
same real hub on an isolated HOME, the same interleaving held at the same
product seam, the same assertion. Each is red at 24576f25 (the capture in
``evidence-story-02.md``) and green after.

1. A late worker cannot resurrect a run the reaper ended; the slot frees.
2. A child's deadline never outlives its parent's; descendants are reaped
   first; a child that returns after the reap cannot record success.
3. The trigger's watch evaluation is an admitted child with its leaf receipt.
4. A replay of a start answers only a DURABLE run (never ``run_id: null``).
5. A replay of an admitted write answers the ORIGINAL success and receipt (a
   class: publish over HTTP and MCP).
6. An accepted suggestion's watch says untested and unbaselined.
7. B1: a cached GitHub row keeps the state its last probe stored.
9. The beat's obligations: a model draft under the draft effect names that
   effect as its parent; ``run_once`` is admitted.
"""
from __future__ import annotations

import json
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402
from test_philo9_b1_connections import _boot as _b1_boot  # noqa: E402
from test_philo9_steward_admission import Runner, _door_project, _project, _suggest  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(None, None)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    gh, acli = Runner(), Runner()
    hub = _b1_boot(tmp_path, monkeypatch, gh, acli)
    yield hub, gh, acli
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(None, None)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _broker(hub: Hub) -> Any:
    from holdspeak.kernel.runtime import _configure

    return _configure(hub.db)


@pytest.fixture
def clock(hub: Hub):
    """The hub broker's clock, movable; restored after (the broker is a process singleton)."""
    broker = _broker(hub)
    real = broker._clock
    yield broker
    broker._clock = real


# ── 1. a late worker cannot resurrect a terminal run ─────────────────────


def test_f1_a_late_worker_cannot_resurrect_a_reaped_run(hub: Hub, clock: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    svc, broker = hub.root.project_steward_service, clock
    pid = hub.client.post("/api/projects", json={"name": "Late worker"}).json()["project"]["id"]
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    real = svc._work

    def held(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        release.wait(20)
        try:
            return real(*args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(svc, "_work", held)
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={}).json()
    assert entered.wait(10)
    op = broker.store.operation(started["operation_id"])
    expired = float(op["warrant"]["execution_expires_at"]) + 1
    broker._clock = lambda: expired
    broker.reap_expired()
    assert hub.db.steward_runs.get_run(started["run_id"])["state"] == "interrupted"
    release.set()
    assert finished.wait(10)
    run = hub.db.steward_runs.get_run(started["run_id"])
    assert run["state"] == "interrupted", "expired run was resurrected by late worker"
    assert broker.store.operation(started["operation_id"])["state"] == "indeterminate"
    monkeypatch.setattr(svc, "_work", real)
    broker._clock = time.time
    again = hub.client.post(f"/api/projects/{pid}/steward/runs", json={})
    assert again.status_code == 200, again.text  # the slot is free



@pytest.mark.parametrize("terminal", ["interrupted", "completed", "failed"])
def test_f1_the_run_repository_never_writes_a_terminal_run_back(hub: Hub, terminal: str) -> None:
    """The repository's own guard (the second wall behind the worker's boundary check)."""
    pid = hub.client.post("/api/projects", json={"name": "Guarded write"}).json()["project"]["id"]
    runs = hub.db.steward_runs
    runs.insert_run(run_id=f"pstrun_guard_{terminal}", project_id=pid, requested_by="owner")
    runs.update_run_state(f"pstrun_guard_{terminal}", state="running")
    runs.update_run_state(f"pstrun_guard_{terminal}", state=terminal)
    for late in ("running", "completed", "failed"):
        runs.update_run_state(f"pstrun_guard_{terminal}", state=late, phase="act")
    assert runs.get_run(f"pstrun_guard_{terminal}")["state"] == terminal
    assert runs.get_active_run(pid) is None


# ── 2. a child never outlives its parent ─────────────────────────────────


def test_f2_a_childs_deadline_is_clamped_and_descendants_settle_first(
    hub: Hub, clock: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc, broker = hub.root.project_steward_service, clock
    now = [time.time()]
    broker._clock = lambda: now[0]
    pid = hub.client.post("/api/projects", json={"name": "Expired parent"}).json()["project"]["id"]
    assert hub.client.put(f"/api/projects/{pid}/steward/policy", json={"eligible_effect_kinds": ["draft_update"]}).status_code == 200
    real_act = svc._phase_act

    def act(*args: Any, **kwargs: Any) -> Any:
        now[0] += 10  # the child is approved ten seconds after its parent
        return real_act(*args, **kwargs)

    monkeypatch.setattr(svc, "_phase_act", act)
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    updates = svc._update_service
    real = updates.draft_update

    def held(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        release.wait(20)
        try:
            return real(*args, **kwargs)
        finally:
            finished.set()

    monkeypatch.setattr(updates, "draft_update", held)
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={}).json()
    assert entered.wait(10)
    parent = broker.store.operation(started["operation_id"])
    [child] = [o for o in broker.store.operations_in_state("claimed") if o["parent_operation_id"] == parent["operation_id"]]
    assert child["warrant"]["execution_expires_at"] <= parent["warrant"]["execution_expires_at"], "child outlives its parent"
    now[0] = parent["warrant"]["execution_expires_at"] + 0.5
    reaped = broker.reap_expired()["reaped"]
    order = [r["operation_id"] for r in reaped]
    assert order.index(child["operation_id"]) < order.index(parent["operation_id"]), order
    release.set()
    assert finished.wait(10)
    time.sleep(0.3)
    assert broker.store.operation(child["operation_id"])["state"] == "indeterminate"
    assert broker.store.receipt(child["operation_id"])["outcome"] == "execution_liveness_expired"
    assert broker.store.operation(parent["operation_id"])["state"] == "indeterminate"


# ── 3. the trigger's watch evaluation is an admitted child ───────────────


def test_f3_the_triggers_watch_evaluation_is_an_admitted_child(rig: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime, timedelta

    import holdspeak.services.watch_service as watches
    import holdspeak.workbench_conductor as conductor

    hub, gh, _acli = rig
    _pid, wid = _door_project(hub)
    broker = _broker(hub)

    class Tomorrow(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
            return datetime.now(tz) + timedelta(days=1)

    monkeypatch.setattr(watches, "datetime", Tomorrow)
    with hub.db._connection() as conn:
        before = {r[0] for r in conn.execute("SELECT operation_id FROM kernel_operations")}
    gh.calls.clear()
    conductor.set_scheduler_services(hub.root.watch_service, hub.root.project_steward_service)
    answer = hub.client.post("/api/steward/trigger", json={}).json()
    deadline = time.monotonic() + 20
    while broker.store.receipt(answer["operation_id"]) is None and time.monotonic() < deadline:
        time.sleep(0.05)
    with hub.db._connection() as conn:
        ops = [dict(r) for r in conn.execute("SELECT operation_id, name, state, parent_operation_id FROM kernel_operations")
               if r["operation_id"] not in before]
    assert gh.calls, "the due watch was not read"
    evaluations = [o for o in ops if o["name"] == "project.watch.evaluate" and o["parent_operation_id"] == answer["operation_id"]]
    assert evaluations, "provider evaluation has no admitted child of trigger"
    assert all(o["state"] == "succeeded" and broker.store.receipt(o["operation_id"]) for o in evaluations)


# ── 4. a start's replay answers only a durable run ───────────────────────


def test_f4_a_concurrent_start_replay_answers_the_durable_run(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = hub.root.project_steward_service
    pid = hub.client.post("/api/projects", json={"name": "Replay before insert"}).json()["project"]["id"]
    entered, release = threading.Event(), threading.Event()
    real = svc._freeze

    def held(*args: Any, **kwargs: Any) -> Any:
        entered.set()
        assert release.wait(20)
        return real(*args, **kwargs)

    monkeypatch.setattr(svc, "_freeze", held)
    answers: list[Any] = []
    first = threading.Thread(target=lambda: answers.append(
        hub.client.post(f"/api/projects/{pid}/steward/runs", json={"command_id": "same-start"}).json()))
    first.start()
    assert entered.wait(10)
    replay_box: list[Any] = []
    second = threading.Thread(target=lambda: replay_box.append(
        hub.client.post(f"/api/projects/{pid}/steward/runs", json={"command_id": "same-start"})))
    second.start()
    time.sleep(0.5)
    assert replay_box == [], "the replay answered before the run was durable"
    release.set()
    first.join(20)
    second.join(20)
    replay = replay_box[0]
    assert replay.status_code == 200, replay.text
    assert replay.json()["run_id"] == answers[0]["run_id"], "same-key replay returned before durable run existed"
    assert replay.json()["operation_id"] == answers[0]["operation_id"]


# ── 5. a replay answers the original success (a class) ───────────────────


def test_f5_a_publication_retry_answers_the_original_success_and_receipt(hub: Hub) -> None:
    pid = hub.client.post("/api/projects", json={"name": "Publication retry"}).json()["project"]["id"]
    for transport in ("http", "mcp"):
        uid = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
        payload = {"command_id": f"publish-{transport}"}
        if transport == "http":
            first = hub.client.post(f"/api/updates/{uid}/publish", json=payload)
            again = hub.client.post(f"/api/updates/{uid}/publish", json=payload)
            assert again.status_code == 200, again.text
            first_body, again_body = first.json(), again.json()
        else:
            _e1, first_body = hub.mcp("project.publish_update", {"update_id": uid, **payload})
            is_error, again_body = hub.mcp("project.publish_update", {"update_id": uid, **payload})
            assert is_error is False, again_body
        assert again_body["operation_id"] == first_body["operation_id"]
        assert again_body["receipt"]["receipt_id"] == first_body["receipt"]["receipt_id"]
        assert again_body["update"] == first_body["update"]


@pytest.mark.parametrize("name", ["archive", "link", "resource"])
def test_f5_the_replay_class_covers_the_other_admitted_writes(hub: Hub, name: str) -> None:
    pid = hub.client.post("/api/projects", json={"name": "Replay class"}).json()["project"]["id"]
    if name == "archive":
        args: tuple[str, dict[str, Any]] = ("project.archive", {"project_id": pid, "command_id": "k-archive"})
    elif name == "link":
        with hub.db._connection() as conn:
            conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m-rc', datetime('now'), 'M')")
        args = ("project.link", {"project_id": pid, "meeting_id": "m-rc", "command_id": "k-link"})
    else:
        note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
        args = ("project.resource.add", {"project_id": pid, "resource_ref": f"note:{note}", "command_id": "k-res"})
    _e1, first = hub.mcp(*args)
    is_error, again = hub.mcp(*args)
    assert is_error is False, again
    assert again == first


# ── 6. an accepted suggestion's watch is honestly untested ───────────────


def test_f6_an_accepted_suggestions_watch_is_untested_and_unbaselined(rig: Any) -> None:
    hub, gh, acli = rig
    pid = _project(hub)
    _suggest(hub, pid)
    gh.calls.clear()
    acli.calls.clear()
    resp = hub.client.post(f"/api/projects/{pid}/suggested-sources/example%2Fpayments/add")
    assert resp.status_code == 200, resp.text
    watch = hub.db.automations.list_project_watches(pid)[0]
    assert watch["test_state"] != "passed" or gh.calls, "accepted suggestion declares an untested watch passed"
    assert watch["baseline_state"] != "established", "accepted suggestion declares a baseline nothing took"
    assert gh.calls == [] and acli.calls == []


# ── 7. B1: the cached row keeps its last probe's state ───────────────────


def test_f7_a_cached_github_row_keeps_its_stored_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.core import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.connections_service import ConnectionsService
    from holdspeak.services.github_provider import GitHubProviderAdapter

    owner = Principal(PrincipalKind.OWNER, "test-owner")
    gh = GitHubProviderAdapter(db=Database(tmp_path / "cached.db"), runner=Runner())
    gh.connection_status(owner)
    svc = ConnectionsService(github_adapter=gh)
    before = svc.list_tools(owner)["tools"][0]
    gh._runner = None
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    after = svc.list_tools(owner)["tools"][0]
    assert before["state"] == after["state"] == "connected", "cached GitHub state changed without a probe"
    assert after["last_checked_at"] == before["last_checked_at"]


# ── 9. the beat's obligations ────────────────────────────────────────────


def test_f9_run_once_is_an_admitted_operation_with_its_receipt(hub: Hub) -> None:
    from holdspeak.principals import Principal, PrincipalKind

    pid = hub.client.post("/api/projects", json={"name": "Internal run"}).json()["project"]["id"]
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    run_id = hub.root.project_steward_service.run_once(owner, pid)
    run = hub.db.steward_runs.get_run(run_id)
    assert run["state"] == "completed" and run["operation_id"]
    receipt = _broker(hub).store.receipt(run["operation_id"])
    assert receipt["state"] == "succeeded" and receipt["outcome"] == "completed"


def test_f9_a_model_draft_under_the_draft_effect_names_it_as_parent(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """A real steward run whose draft effect asks for the model: the invocation names the effect."""
    svc = hub.root.project_steward_service
    updates = svc._update_service
    seen: list[str] = []

    class Stop(Exception):
        pass

    def resolve(*_a: Any, **_k: Any) -> Any:
        return "deprev_x", "assign_x", "profile_x"

    class Capture:
        def invoke(self, request: Any, adapter: Any, publish: Any = None) -> Any:
            seen.append(request.parent_operation_id)
            raise Stop("captured")

    import holdspeak.services.project_update_service as update_module

    monkeypatch.setattr(update_module, "_resolve_for_capability", resolve)
    monkeypatch.setattr(updates, "_broker", type("B", (), {"inference_runner": Capture(), "database": hub.db})())
    real_draft = updates.draft_update
    monkeypatch.setattr(updates, "draft_update", lambda principal, project_id, **k: real_draft(
        principal, project_id, generator="model"))
    pid = hub.client.post("/api/projects", json={"name": "Model draft"}).json()["project"]["id"]
    assert hub.client.put(f"/api/projects/{pid}/steward/policy", json={"eligible_effect_kinds": ["draft_update"]}).status_code == 200
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={}).json()
    deadline = time.monotonic() + 20
    while hub.db.steward_runs.get_run(started["run_id"])["state"] not in {"completed", "failed", "interrupted"} \
            and time.monotonic() < deadline:
        time.sleep(0.05)
    effects = [o for o in _broker(hub).store.operations_in_state("succeeded")
               if o["parent_operation_id"] == started["operation_id"] and o["name"] == "project.steward.effect"]
    assert seen and seen[0] and seen[0] in {o["operation_id"] for o in effects}, (seen, effects)
    # Off the steward (a plain draft): no parent.
    seen.clear()
    updates.draft_update  # noqa: B018
    real_draft(Principal_owner(), pid, generator="model")
    assert seen == [""]


def Principal_owner() -> Any:
    from holdspeak.principals import Principal, PrincipalKind

    return Principal(PrincipalKind.OWNER, "owner-session")
