"""HS-131-05 admitted Workbench parent registration and fence proofs."""
from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.workbench_memory import read_memory

OWNER = Principal(PrincipalKind.OWNER, "workbench-owner")
OTHER = Principal(PrincipalKind.OWNER, "other-owner")


def _canonical_hash(payload):
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return "sha256:" + hashlib.sha256(material.encode()).hexdigest()


def _setup_runner(tmp_path: Path, monkeypatch, *, item_count: int = 1):
    """Build the production runner; only the admitted provider constructor is fake."""
    db = Database(tmp_path / "workbench.db")
    state = {"calls": [], "entered": Event(), "release": Event(), "block_call": 0}

    class FakeIntel:
        active_provider = "test-provider"
        active_model = "test-model"

        def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
            state["calls"].append({"system_prompt": system_prompt, "user_prompt": user_prompt})
            call = len(state["calls"])
            state["entered"].set()
            if state["block_call"] == call:
                assert state["release"].wait(5), "test provider was never released"
            return f"provider-output-{call}"

    engine = FakeIntel()

    def build_provider(**kwargs):
        state.setdefault("provider_constructions", []).append(kwargs)
        return engine

    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", build_provider)
    token = hashlib.sha256(str(tmp_path).encode()).hexdigest()[:10]
    profile = db.profiles.upsert(
        profile_id=f"profile-{token}", name="Profile", kind="openAICompatible",
        base_url="http://profile", model="model",
    )
    recipe = db.recipes.upsert(
        recipe_id=f"recipe-{token}", name="Runner", system_prompt="SYS", user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id=f"wb-{token}", name="Runner", recipe_id=recipe.id, profile_id=profile.id,
    )
    items = [
        db.workbench_items.upsert(
            item_id=f"item-{ordinal}", workbench_id=workbench.id,
            title=f"Item {ordinal}", body=f"input {ordinal}",
        )
        for ordinal in range(1, item_count + 1)
    ]
    broker = _configure(db)
    real_invoke = broker.inference_runner.invoke

    def observed_invoke(request, *args, **kwargs):
        state.setdefault("requests", []).append(request)
        return real_invoke(request, *args, **kwargs)

    monkeypatch.setattr(broker.inference_runner, "invoke", observed_invoke)
    return db, broker, workbench, items, state


@pytest.fixture
def runner_rig(tmp_path: Path, monkeypatch):
    return _setup_runner(tmp_path, monkeypatch)


def _run(db, broker, workbench_id: str, *, memory_enabled: bool = True):
    from holdspeak.services.workbench_runner import WorkbenchRunner

    return asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench_id, memory_enabled=memory_enabled))


def _run_row(db, run_id: str):
    with db._connection() as conn:
        return dict(conn.execute("SELECT * FROM workbench_runs WHERE id=?", (run_id,)).fetchone())


def _operations(db, parent_id: str):
    with db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM kernel_operations WHERE parent_operation_id=? ORDER BY created_at", (parent_id,)
        )]


def _row(broker, op):
    with broker.database._connection() as conn:
        return dict(conn.execute("SELECT * FROM kernel_parent_runs WHERE operation_id=?", (op,)).fetchone())


def test_manual_attempt_creates_one_authenticated_workbench_parent(runner_rig):
    db, broker, workbench, _, _ = runner_rig
    result = _run(db, broker, workbench.id, memory_enabled=False)
    parent = broker.store.operation(result["parent_operation_id"])
    assert (parent["name"], parent["principal_identity"]) == ("workbench.run", OWNER.identity)
    assert len([row for row in _operations(db, result["parent_operation_id"]) if row["native_id"].startswith("workbench_item_")]) == 1
    with pytest.raises(KernelRefused):
        asyncio.run(__import__("holdspeak.services.workbench_runner", fromlist=["WorkbenchRunner"]).WorkbenchRunner(db, broker).run(UNAUTHENTICATED, workbench.id))
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM workbench_runs").fetchone()[0] == 1


def test_item_scoped_run_never_sweeps_other_pending_work(tmp_path, monkeypatch):
    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch, item_count=2)
    from holdspeak.services.workbench_runner import WorkbenchRunner

    result = asyncio.run(WorkbenchRunner(db, broker).run(
        OWNER, workbench.id, memory_enabled=False, item_ids=[items[1].id],
    ))

    assert result["receipt_id"]
    assert db.workbench_items.get(items[0].id).status == "pending"
    assert db.workbench_items.get(items[1].id).status == "done"
    assert len(state["calls"]) == 1
    with db._connection() as conn:
        row = conn.execute(
            "SELECT input_json FROM kernel_parent_runs WHERE operation_id=?",
            (result["parent_operation_id"],),
        ).fetchone()
    assert '"item_scope":"explicit"' in row["input_json"]


def test_replay_returns_the_original_terminal_attempt_and_receipt(runner_rig):
    db, broker, workbench, _, state = runner_rig
    from holdspeak.services.workbench_runner import WorkbenchRunner

    request_id = "same-workbench-attempt"
    first = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, request_id=request_id))
    with db._connection() as conn:
        before_runs = conn.execute("SELECT count(*) FROM workbench_runs").fetchone()[0]
        before_children = conn.execute("SELECT count(*) FROM kernel_operations WHERE parent_operation_id=?", (first["parent_operation_id"],)).fetchone()[0]
    replay = asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id, request_id=request_id))
    with db._connection() as conn:
        after_runs = conn.execute("SELECT count(*) FROM workbench_runs").fetchone()[0]
        after_children = conn.execute("SELECT count(*) FROM kernel_operations WHERE parent_operation_id=?", (first["parent_operation_id"],)).fetchone()[0]
    assert replay["replayed"] is True
    assert replay["run_id"] == first["run_id"]
    assert replay["receipt_id"] == replay["parent_receipt_id"] == first["receipt_id"]
    assert replay["terminal_disposition"] == "completed"
    assert replay["children"] == first["children"]
    assert (after_runs, after_children, len(state["calls"])) == (before_runs, before_children, 2)


def test_reaction_source_event_is_bound_into_kernel_parent_input(runner_rig):
    db, broker, workbench, _, _ = runner_rig
    from holdspeak.services.workbench_runner import WorkbenchRunner

    source_event = {
        "event_id": "sevt_review_requested",
        "correlation_id": "corr_connector_refresh",
        "causation_id": "sevt_review_requested",
    }
    result = asyncio.run(
        WorkbenchRunner(db, broker).run(
            OWNER, workbench.id, memory_enabled=False,
            request_id="reaction:r1:sevt_review_requested",
            source_event=source_event,
        )
    )
    with db._connection() as conn:
        row = conn.execute(
            "SELECT input_json FROM kernel_parent_runs WHERE operation_id=?",
            (result["parent_operation_id"],),
        ).fetchone()
    assert row is not None
    assert json.loads(row["input_json"])["source_event"] == source_event


def test_each_item_provider_call_has_one_admitted_child_and_receipt(tmp_path, monkeypatch):
    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch, item_count=2)
    result = _run(db, broker, workbench.id, memory_enabled=False)
    children = _operations(db, result["parent_operation_id"])
    assert len(state["calls"]) == len(items) == 2
    assert len(children) == 2
    assert {child["native_id"] for child in children} == {link["invocation_id"] for link in result["children"]}
    assert all(broker.store.receipt(child["operation_id"])["outcome"] == "succeeded" for child in children)


def test_memory_writeback_is_a_distinct_child_linked_to_its_item_child(runner_rig):
    db, broker, workbench, _, state = runner_rig
    result = _run(db, broker, workbench.id)
    item, memory = _operations(db, result["parent_operation_id"])
    request = next(request for request in state["requests"] if request.invocation_id == memory["native_id"])
    observations = read_memory(workbench.id)
    assert item["native_id"].startswith("workbench_item_")
    assert memory["native_id"].startswith("workbench_memory_")
    assert request.definition_origin.contract == "holdspeak.workbench-memory@1"
    assert observations[0]["provenance"] == {
        "operation_id": memory["operation_id"],
        "receipt_id": broker.store.receipt(memory["operation_id"])["receipt_id"],
    }
    assert request.payload["source_item_receipt_id"] == broker.store.receipt(item["operation_id"])["receipt_id"]
    assert request.payload["source_item_operation_id"] == item["operation_id"]


def test_memory_disabled_admits_no_memory_child(runner_rig):
    db, _, workbench, _, state = runner_rig
    broker = _configure(db)  # assert the production per-database broker is reused.
    result = _run(db, broker, workbench.id, memory_enabled=False)
    assert len(state["calls"]) == 1
    assert all(not child["native_id"].startswith("workbench_memory_") for child in _operations(db, result["parent_operation_id"]))
    assert read_memory(workbench.id) == []


def test_item_and_memory_children_freeze_provenance_and_per_child_placement(runner_rig):
    db, broker, workbench, _, state = runner_rig
    state["block_call"] = 1
    from holdspeak.services.workbench_runner import WorkbenchRunner

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(WorkbenchRunner(db, broker).run(OWNER, workbench.id)))
        assert state["entered"].wait(5), "item provider was not reached"
        db.profiles.upsert(
            profile_id=workbench.profile_id, name="Profile after item", kind="openAICompatible",
            base_url="http://profile-after-item", model="model-after-item",
        )
        state["release"].set()
        result = future.result(timeout=10)

    item, memory = _operations(db, result["parent_operation_id"])
    item_request = next(request for request in state["requests"] if request.invocation_id == item["native_id"])
    memory_request = next(request for request in state["requests"] if request.invocation_id == memory["native_id"])
    assert item_request.definition_origin.ref == f"recipe:{workbench.recipe_id}"
    assert item_request.definition_origin.revision == item_request.payload["recipe_revision"]
    assert memory_request.definition_origin.contract == "holdspeak.workbench-memory@1"
    assert item_request.deployment_revision != memory_request.deployment_revision
    assert item_request.payload["deployment_revision"] == item_request.deployment_revision
    assert memory_request.payload["deployment_revision"] == memory_request.deployment_revision
    assert len(state["provider_constructions"]) == 2
    assert state["calls"][0]["user_prompt"].endswith("input 1")
    assert "Your output:\nprovider-output-1" in state["calls"][1]["user_prompt"]


def test_item_memory_artifact_and_attempt_history_are_receipt_gated(runner_rig):
    db, broker, workbench, items, _ = runner_rig
    result = _run(db, broker, workbench.id)
    run = _run_row(db, result["run_id"])
    item, memory = _operations(db, result["parent_operation_id"])
    item_receipt, memory_receipt, parent_receipt = (
        broker.store.receipt(item["operation_id"]), broker.store.receipt(memory["operation_id"]), broker.store.receipt(result["parent_operation_id"])
    )
    with db._connection() as conn:
        artifact = dict(conn.execute("SELECT * FROM artifacts WHERE source_item_id=?", (items[0].id,)).fetchone())
        stages = [dict(row) for row in conn.execute("SELECT * FROM kernel_projection_stages ORDER BY kind").fetchall()]
    assert db.workbench_items.get(items[0].id).result == "provider-output-1"
    assert json.loads(artifact["structured_json"])["receipt_id"] == item_receipt["receipt_id"]
    assert read_memory(workbench.id)[0]["provenance"]["receipt_id"] == memory_receipt["receipt_id"]
    assert (run["status"], run["parent_receipt_id"]) == ("completed", parent_receipt["receipt_id"])
    assert all(stage["state"] == "PUBLISHED" for stage in stages)


def test_cancel_before_item_checkpoint_leaves_no_item_or_memory_write(runner_rig):
    db, broker, workbench, items, state = runner_rig
    state["block_call"] = 1
    result = _cancel_mid_run((db, broker, workbench, items[0], state))
    assert result[-1]["terminal_disposition"] == "cancelled"
    assert db.workbench_items.get(items[0].id).result in (None, "")
    assert read_memory(workbench.id) == []
    with db._connection() as conn:
        assert conn.execute("SELECT count(*) FROM artifacts WHERE source_item_id=?", (items[0].id,)).fetchone()[0] == 0


def test_cancel_after_item_preserves_item_and_fences_memory_late_write(runner_rig):
    db, broker, workbench, items, state = runner_rig
    state["block_call"] = 2
    db, broker, item, run_id, parent_id, result = _cancel_mid_run((db, broker, workbench, items[0], state))
    assert result["terminal_disposition"] == "cancelled"
    assert db.workbench_items.get(item.id).result == "provider-output-1"
    assert read_memory(workbench.id) == []
    assert len(_operations(db, parent_id)) == 2
    assert _run_row(db, run_id)["status"] == "cancelled"


def test_repeated_or_foreign_parent_cancel_cannot_cross_workbenches_or_mutate_receipts(runner_rig):
    db, broker, workbench, items, state = runner_rig
    state["block_call"] = 1
    db, broker, _, _, parent_id, result = _cancel_mid_run((db, broker, workbench, items[0], state), repeat=True)
    receipt = broker.store.receipt(parent_id)
    with pytest.raises(KernelRefused):
        broker.parent_run_controller.cancel_by_operation_id(OTHER, parent_id)
    assert broker.parent_run_controller.cancel_by_operation_id(OWNER, parent_id) == "cancelled"
    assert broker.store.receipt(parent_id) == receipt
    assert result["receipt_id"] == receipt["receipt_id"]


def test_manual_workbench_uses_only_trusted_runner_children():
    # MANUAL execution only: the no-principal scheduled leg
    # (_run_scheduled_workbench_legacy) is HS-131-06's chartered migration.
    root = Path(__file__).parents[2]
    forbidden = {"run_prompt", "build_configured_meeting_intel", "build_meeting_intel_for_profile"}

    def census(tree) -> set[str]:
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        return forbidden & (names | calls)

    runner = root / "holdspeak/services/workbench_runner.py"
    assert not census(ast.parse(runner.read_text())), f"manual Workbench bypass remains in {runner}"

    conductor = ast.parse((root / "holdspeak/workbench_conductor.py").read_text())
    manual = [n for n in ast.walk(conductor)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "run_workbench"]
    assert manual, "manual entry run_workbench must exist"
    assert not census(manual[0]), "manual Workbench bypass remains in run_workbench"


def test_memory_service_contract_hashes_the_exact_submitted_payload(runner_rig):
    db, broker, workbench, _, state = runner_rig
    result = _run(db, broker, workbench.id)
    memory = next(row for row in _operations(db, result["parent_operation_id"]) if row["native_id"].startswith("workbench_memory_"))
    request = next(request for request in state["requests"] if request.invocation_id == memory["native_id"])
    assert request.definition_origin.payload_hash == _canonical_hash(request.payload)
    assert broker.store.receipt(memory["operation_id"])["outcome"] == "succeeded"


def test_workbench_deadline_expiry_fences_new_children_and_late_projections(tmp_path, monkeypatch):
    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch)
    state["block_call"] = 1
    from holdspeak.services.workbench_runner import WorkbenchRunner
    runner = WorkbenchRunner(db, broker)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(lambda: asyncio.run(runner.run(OWNER, workbench.id, deadline_seconds=.5)))
        assert state["entered"].wait(5)
        time.sleep(.7)
        state["release"].set()
        result = future.result(timeout=10)
    assert result["terminal_disposition"] == "cancelled"
    assert db.workbench_items.get(items[0].id).result in (None, "")
    assert read_memory(workbench.id) == []


def _cancel_mid_run(runner_rig, *, repeat: bool = False):
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, broker, workbench, item, state = runner_rig
    runner = WorkbenchRunner(db, broker)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future = executor.submit(lambda: asyncio.run(runner.run(OWNER, workbench.id)))
        assert state["entered"].wait(5), "provider was not reached"
        for _ in range(500):
            if len(state["calls"]) >= max(1, state["block_call"]):
                break
            time.sleep(.01)
        assert len(state["calls"]) >= max(1, state["block_call"]), "blocked provider was not reached"
        with db._connection() as conn:
            run_id, parent_id = conn.execute("SELECT id,parent_operation_id FROM workbench_runs").fetchone()
        cancellation = executor.submit(broker.parent_run_controller.cancel_by_operation_id, OWNER, parent_id)
        for _ in range(100):
            if _row(broker, parent_id)["state"] in {"CANCELLING", "CANCELLED"}:
                break
            time.sleep(.01)
        assert _row(broker, parent_id)["state"] in {"CANCELLING", "CANCELLED"}
        state["release"].set()
        assert cancellation.result(timeout=10) == "cancelled"
        if repeat:
            assert broker.parent_run_controller.cancel_by_operation_id(OWNER, parent_id) == "cancelled"
        result = future.result(timeout=10)
    return db, broker, item, run_id, parent_id, result


def test_cross_request_cancel_adopts_parent_receipt_and_preserves_child_receipt(runner_rig):
    db, broker, workbench, items, state = runner_rig
    state["block_call"] = 1
    db, broker, item, run_id, parent_id, result = _cancel_mid_run((db, broker, workbench, items[0], state))
    receipt = broker.store.receipt(parent_id)
    assert result["terminal_disposition"] == "cancelled"
    assert result["receipt_id"] == receipt["receipt_id"]
    with db._connection() as conn:
        run = dict(conn.execute("SELECT * FROM workbench_runs WHERE id=?", (run_id,)).fetchone())
        child = conn.execute("SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?", (parent_id,)).fetchone()[0]
        artifacts = conn.execute("SELECT count(*) FROM artifacts WHERE source_item_id=?", (item.id,)).fetchone()[0]
    assert (run["status"], run["parent_receipt_id"]) == ("cancelled", receipt["receipt_id"])
    assert json.loads(run["child_links_json"])[0]["receipt_id"] == broker.store.receipt(child)["receipt_id"]
    assert artifacts == 0 and db.workbench_items.get(item.id).result in (None, "")


def test_checkpoint_that_did_not_advance_never_stages_workbench_success_aggregate(runner_rig, monkeypatch):
    from types import SimpleNamespace
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, broker, workbench, _, _ = runner_rig
    runner = WorkbenchRunner(db, broker)
    entered, release = Event(), Event()

    def stale_success(*args, **kwargs):
        entered.set()
        assert release.wait(5), "stale child was never released"
        return SimpleNamespace(outcome="succeeded", error="")

    monkeypatch.setattr(runner, "_invoke", stale_success)
    monkeypatch.setattr(broker.projection_stager, "finalize", lambda invocation_id: {"advanced": False})
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(runner.run(OWNER, workbench.id, memory_enabled=False)))
        assert entered.wait(5)
        with db._connection() as conn:
            run_id, parent_id = conn.execute("SELECT id,parent_operation_id FROM workbench_runs").fetchone()
        assert broker.parent_run_controller.cancel_by_operation_id(OWNER, parent_id) == "cancelled"
        release.set()
        result = future.result(timeout=10)
    with db._connection() as conn:
        aggregate = conn.execute("SELECT count(*) FROM kernel_projection_stages WHERE operation_id=? AND kind='workbench-run-result'", (parent_id,)).fetchone()[0]
    assert result["terminal_disposition"] == "cancelled"
    assert aggregate == 0


def test_cancel_after_parent_result_stage_never_finalizes_completed_history(runner_rig, monkeypatch):
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, broker, workbench, _, _ = runner_rig
    runner = WorkbenchRunner(db, broker)
    staged, release = Event(), Event()
    close = runner._close_or_adopt

    def pause_before_parent_close(parent, outcome, **kwargs):
        if outcome == "succeeded":
            staged.set()
            assert release.wait(5), "parent close was not released"
        return close(parent, outcome, **kwargs)

    monkeypatch.setattr(runner, "_close_or_adopt", pause_before_parent_close)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(runner.run(OWNER, workbench.id)))
        assert staged.wait(5), "workbench result was not staged before parent close"
        with db._connection() as conn:
            run_id, parent_id = conn.execute("SELECT id,parent_operation_id FROM workbench_runs").fetchone()
        assert broker.parent_run_controller.cancel_by_operation_id(OWNER, parent_id) == "cancelled"
        release.set()
        result = future.result(timeout=10)

    parent_receipt = broker.store.receipt(parent_id)
    children = _operations(db, parent_id)
    with db._connection() as conn:
        run = dict(conn.execute("SELECT * FROM workbench_runs WHERE id=?", (run_id,)).fetchone())
        stage = dict(conn.execute("SELECT * FROM kernel_projection_stages WHERE operation_id=? AND kind='workbench-run-result'", (parent_id,)).fetchone())
    assert result["terminal_disposition"] == parent_receipt["outcome"] == "cancelled"
    assert (run["status"], run["parent_receipt_id"], run["completed_at"]) == ("cancelled", parent_receipt["receipt_id"], None)
    assert stage["state"] != "PUBLISHED"
    assert len(children) == 2
    assert all(broker.store.receipt(child["operation_id"])["outcome"] == "succeeded" for child in children)
    assert {link["receipt_id"] for link in json.loads(run["child_links_json"])} == {
        broker.store.receipt(child["operation_id"])["receipt_id"] for child in children
    }


def test_cancellation_before_claim_does_not_strand_item_and_next_run_processes_it(runner_rig, monkeypatch):
    """Cancellation winning between loop validation and claim leaves no claimed orphan."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, broker, workbench, items, _ = runner_rig
    runner = WorkbenchRunner(db, broker)
    original = broker.parent_run_controller.expire_if_due
    fired = False

    def cancel_before_claim(context, principal):
        nonlocal fired
        if not fired:
            fired = True
            broker.parent_run_controller.cancel_by_operation_id(principal, context.operation_id)
            return False
        return original(context, principal)

    monkeypatch.setattr(broker.parent_run_controller, "expire_if_due", cancel_before_claim)
    cancelled = asyncio.run(runner.run(OWNER, workbench.id, memory_enabled=False))
    assert cancelled["terminal_disposition"] == "cancelled"
    assert db.workbench_items.get(items[0].id).status == "pending"
    monkeypatch.setattr(broker.parent_run_controller, "expire_if_due", original)
    completed = _run(db, broker, workbench.id, memory_enabled=False)
    assert completed["receipt_id"]
    assert db.workbench_items.get(items[0].id).status == "done"
