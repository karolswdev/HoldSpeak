"""PHILO-9-02 round three: Codex Astra r2 on 7119cfd9, each reproduction ported as a fence.

The reproductions (``/tmp/holdspeak-counsel-684-r2-*.py``) run the real hub on
an isolated HOME; each is red on an export of ``7119cfd9`` and green after.
Muad'Dib's rulings:

A. ONE replay store: story 01's ``project_commands.result_json``; the domain
   write, the recorded answer and the terminal receipt commit in ONE
   transaction, so a failure anywhere rolls back all three.
B. A self-closing write (the steward policy) answers a replay from that
   record, never from the policy as it is now; HTTP forwards ``command_id``.
C. An approved-but-unclaimed child settles (with its receipt) before its
   expired parent.
D. A scheduled model draft's ``inference.invoke`` is admitted through the
   REAL inference runner, as the child of the draft effect.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    import holdspeak.workbench_conductor as conductor

    conductor.set_scheduler_services(None, None)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _broker(hub: Hub) -> Any:
    from holdspeak.kernel.runtime import _configure

    return _configure(hub.db)


@pytest.fixture
def clock(hub: Hub):
    broker = _broker(hub)
    real = broker._clock
    yield broker
    broker._clock = real


def _rows(hub: Hub, sql: str, *args: Any) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(sql, args)]


# ── A. one replay store; one transaction ─────────────────────────────────


def test_a_there_is_one_replay_store(hub: Hub) -> None:
    """The r1 second store is gone; a Room write's answer lives in project_commands only."""
    tables = {r["name"] for r in _rows(hub, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "project_operation_results" not in tables, "the same replay body is stored in two tables"
    pid = hub.client.post("/api/projects", json={"name": "Two stores"}).json()["project"]["id"]
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    is_error, first = hub.mcp("project.resource.add", {"project_id": pid, "resource_ref": f"note:{note}",
                                                       "command_id": "one-store"})
    assert is_error is False, first
    assert len(_rows(hub, "SELECT id FROM project_commands WHERE id='one-store'")) == 1
    assert hub.mcp("project.resource.add", {"project_id": pid, "resource_ref": f"note:{note}",
                                            "command_id": "one-store"}) == (False, first)


def _inject(monkeypatch: pytest.MonkeyPatch, hub: Hub, point: str) -> tuple[Any, str, Any]:
    """A failure inside the publication's terminal transaction, at *point*.

    ``answer``: after the answer is written (at 7119cfd9 that seam was
    ``_store_result``, counsel's injection point; here ``_record_answer``).
    ``receipt``: the terminal transition itself (the in-transaction step here;
    the separate terminal transaction at 7119cfd9).
    """
    from holdspeak.kernel import journal_atomic
    from holdspeak.services import project_kernel

    if point == "answer":
        module = project_kernel
        seam = "_record_answer" if hasattr(project_kernel, "_record_answer") else "_store_result"
    else:
        module = journal_atomic
        seam = "transition_and_receipt_in" if hasattr(journal_atomic, "transition_and_receipt_in") \
            else "transition_and_receipt"
    real = getattr(module, seam)
    store = _broker(hub).store
    fired: list[bool] = []

    def publishing(args: tuple[Any, ...]) -> bool:
        ids = [a for a in args if isinstance(a, str) and a.startswith("op_")]
        return bool(ids) and (store.operation(ids[0]) or {}).get("name") == "project.publish_update"

    def broken(*args: Any, **kwargs: Any) -> Any:
        if seam == "_store_result":
            def fail(conn: Any) -> None:
                real(*args)(conn)
                raise RuntimeError("injected: the terminal transaction fails after the answer is written")
            return fail
        if seam == "_record_answer":
            real(*args, **kwargs)
            raise RuntimeError("injected: the terminal transaction fails after the answer is written")
        if not fired and publishing(args):
            fired.append(True)
            raise RuntimeError("injected: the terminal transition fails")
        return real(*args, **kwargs)

    return module, seam, (real, broken)


@pytest.mark.parametrize("point", ["answer", "receipt"])
@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_a_a_failure_in_the_terminal_transaction_rolls_back_the_publication(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, transport: str, point: str,
) -> None:
    """Counsel's rollback probe: nothing is published; the retry succeeds once with the original answer."""
    pid = hub.client.post("/api/projects", json={"name": "Rollback replay"}).json()["project"]["id"]
    uid = hub.client.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    module, seam, (real, broken) = _inject(monkeypatch, hub, point)

    def publish() -> tuple[int, Any]:
        if transport == "http":
            resp = hub.client.post(f"/api/updates/{uid}/publish", json={"command_id": "crash-publish"})
            return resp.status_code, resp.json()
        is_error, body = hub.mcp("project.publish_update", {"update_id": uid, "command_id": "crash-publish"})
        return (409 if is_error else 200), body

    monkeypatch.setattr(module, seam, broken)
    failed_status, _failed = publish()
    monkeypatch.setattr(module, seam, real)
    assert failed_status != 200
    assert hub.db.project_updates.get_update(uid)["lifecycle"] == "draft", "the publication committed without its answer"
    assert _rows(hub, "SELECT id FROM project_commands WHERE id='crash-publish'") == []
    [operation] = _rows(hub, "SELECT operation_id, state FROM kernel_operations WHERE name='project.publish_update'")
    assert _broker(hub).store.receipt(operation["operation_id"]) is None
    status, retry = publish()
    assert status == 200, f"publication replay lost the committed answer after terminal rollback: {retry}"
    assert hub.db.project_updates.get_update(uid)["lifecycle"] == "published"
    status, again = publish()
    assert status == 200 and again == retry, "the retry answered a different body"
    assert retry["operation_id"] == operation["operation_id"]


# ── B. a self-closing write answers its own record ───────────────────────


def test_b_a_policy_retry_answers_its_own_terms_over_mcp(hub: Hub) -> None:
    pid = hub.client.post("/api/projects", json={"name": "Policy replay"}).json()["project"]["id"]

    def put(key: str, kinds: list[str]) -> Any:
        return hub.mcp("project.configure_steward", {"project_id": pid, "eligible_effect_kinds": kinds,
                                                     "command_id": key})

    first, _changed, retry = put("a", ["draft_update"]), put("b", []), put("a", ["draft_update"])
    assert first[1]["operation_id"] == retry[1]["operation_id"]
    assert first == retry, "same operation returns changed policy with original receipt"


def test_b_a_policy_retry_answers_its_own_terms_over_http(hub: Hub) -> None:
    pid = hub.client.post("/api/projects", json={"name": "Policy replay"}).json()["project"]["id"]
    url = f"/api/projects/{pid}/steward/policy"
    first = hub.client.put(url, json={"eligible_effect_kinds": ["draft_update"], "command_id": "policy-a"})
    hub.client.put(url, json={"eligible_effect_kinds": [], "command_id": "policy-b"})
    again = hub.client.put(url, json={"eligible_effect_kinds": ["draft_update"], "command_id": "policy-a"})
    assert first.status_code == again.status_code == 200, again.text
    assert again.json()["operation_id"] == first.json()["operation_id"], "the HTTP route dropped command_id"
    assert again.json() == first.json(), "policy replay changed its original answer"


# ── C. an approved, unclaimed child settles before its parent ────────────


def test_c_an_unclaimed_child_is_settled_before_its_expired_parent(
    hub: Hub, clock: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    svc, broker = hub.root.project_steward_service, clock
    now = [time.time()]
    broker._clock = lambda: now[0]
    pid = hub.client.post("/api/projects", json={"name": "Unclaimed descendant"}).json()["project"]["id"]
    hub.client.put(f"/api/projects/{pid}/steward/policy", json={"eligible_effect_kinds": ["draft_update"]})
    act = svc._phase_act

    def near(*args: Any, **kwargs: Any) -> Any:
        now[0] += 3590  # the child is approved ten seconds before its parent's deadline
        return act(*args, **kwargs)

    monkeypatch.setattr(svc, "_phase_act", near)
    entered, release = threading.Event(), threading.Event()
    claim, held_op = broker.claim, []

    def held(principal: Any, native_id: str = "") -> Any:
        rows = _rows(hub, "SELECT operation_id, name FROM kernel_operations WHERE native_id=?", native_id)
        if rows and rows[0]["name"] == "project.steward.effect":
            held_op.append(rows[0]["operation_id"])
            entered.set()
            release.wait(20)
        return claim(principal, native_id)

    monkeypatch.setattr(broker, "claim", held)
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={}).json()
    assert entered.wait(10)
    parent = broker.store.operation(started["operation_id"])
    child = broker.store.operation(held_op[0])
    assert child["state"] == "awaiting_execution"
    assert child["warrant"]["expires_at"] <= parent["warrant"]["execution_expires_at"], "the claim outlives the parent"
    now[0] = parent["warrant"]["execution_expires_at"] + 0.5
    reaped = [r["operation_id"] for r in broker.reap_expired()["reaped"]]
    after = broker.store.operation(child["operation_id"])
    release.set()
    time.sleep(0.4)
    assert after["state"] in {"refused", "indeterminate"}, "parent terminal while approved child has no receipt"
    assert broker.store.receipt(child["operation_id"]) is not None
    assert reaped.index(child["operation_id"]) < reaped.index(parent["operation_id"]), reaped


# ── D. the scheduled model draft through the REAL inference runner ───────


def test_d_a_scheduled_model_draft_is_admitted_as_the_effects_child(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Counsel's probe: a producer-minted deployment, the real InferenceRunner, the provider boundary reached."""
    import holdspeak.services.project_update_service as update_module
    from holdspeak.deployment_revisions import capture_deployment_revision
    from holdspeak.inference_targets import resolve_inference_target
    from holdspeak.kernel.inference_runner import InferenceRunner
    from holdspeak.principals import Principal, PrincipalKind

    broker = _broker(hub)
    svc = hub.root.project_steward_service
    updates = svc._update_service
    hub.db.profiles.upsert(profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf")
    revision = capture_deployment_revision(hub.db, resolve_inference_target(hub.db, "local"))
    monkeypatch.setattr(update_module, "_resolve_for_capability", lambda *_a, **_k: (revision.id, "assignment", "local"))
    engines: list[bool] = []

    def engine(*_a: Any, **_k: Any) -> Any:
        engines.append(True)
        raise RuntimeError("the provider boundary (no model on an isolated HOME)")

    monkeypatch.setattr(broker, "inference_runner", InferenceRunner(broker, hub.db, engine_factory=engine))
    monkeypatch.setattr(updates, "_broker", broker)
    draft = updates.draft_update
    monkeypatch.setattr(updates, "draft_update", lambda principal, project_id, **_k: draft(
        principal, project_id, generator="model"))
    pid = hub.client.post("/api/projects", json={"name": "Scheduled model child"}).json()["project"]["id"]
    hub.client.put(f"/api/projects/{pid}/steward/policy",
                   json={"unattended_enabled": True, "eligible_effect_kinds": ["draft_update"]})
    answer = svc.start_scheduled(Principal(PrincipalKind.SCHEDULER, "local-steward-conductor"), pid, "probe")
    deadline = time.monotonic() + 20
    while broker.store.receipt(answer["operation_id"]) is None and time.monotonic() < deadline:
        time.sleep(0.05)
    ops = _rows(hub, "SELECT operation_id, name, parent_operation_id, principal_kind FROM kernel_operations "
                     "WHERE name IN ('inference.invoke', 'project.steward.effect')")
    effects = {o["operation_id"] for o in ops if o["name"] == "project.steward.effect"
               and o["parent_operation_id"] == answer["operation_id"]}
    invocations = [o for o in ops if o["name"] == "inference.invoke"]
    assert engines, f"scheduler child was refused before reaching the provider boundary: {ops}"
    assert invocations and all(o["parent_operation_id"] in effects for o in invocations), (invocations, effects)
    assert {o["principal_kind"] for o in invocations} == {"scheduler"}
    assert all(broker.store.receipt(o["operation_id"]) is not None for o in invocations)


# ── Codex Astra r3: a sent nudge answers BOTH receipts ───────────────────


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_r3_a_sent_nudge_answers_the_comment_receipt_and_the_kernel_receipt(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, transport: str,
) -> None:
    """Counsel's probe: the real send_nudge and connector, a canned `gh pr comment` answer at the process edge."""
    import json
    import subprocess

    from test_philo5_the_loop_r2 import _nudge_step

    def runner(argv: list[str], **_kwargs: Any) -> Any:
        return subprocess.CompletedProcess(argv, 0, "https://github.com/example/payments/pull/7#c1\n", "")

    monkeypatch.setattr(hub.root.project_steward_service, "_subprocess_runner", runner)
    step_id = _nudge_step(hub)
    if transport == "http":
        resp = hub.client.post(f"/api/nudges/{step_id}/send", json={"text": "Please review"})
        assert resp.status_code == 200, resp.text
        answer = resp.json()
    else:
        is_error, answer = hub.mcp("nudge.send", {"step_id": step_id, "text": "Please review"})
        assert is_error is False, answer
    stored = json.loads(hub.db.steward_steps.get_step(step_id)["receipt_json"])
    comment = answer.get("comment_receipt") or {}
    assert comment.get("comment_url") == stored["comment_url"] == "https://github.com/example/payments/pull/7#c1", \
        f"comment receipt is overwritten: {answer}"
    assert comment.get("reviewer_login") == stored["reviewer_login"] and comment.get("timestamp") == stored["timestamp"]
    kernel = answer["receipt"]
    assert kernel == _broker(hub).store.receipt(answer["operation_id"]), "the kernel receipt is not the operation's"
