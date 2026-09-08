"""HS-200-41 (lanes A+B): the durable Room ask — state machine and projection.

Suite ``phase200_task_resume``.  These are the headless state tests; the
restart, the claimed late answer and the orphaned lease are proven against a
real ``/api/ask`` run in ``tests/integration/test_phase200_task_resume.py``.

What is asserted here:

- the row keeps the ratified elements of the posture-6 `UNFINISHED` row —
  purpose, Project, state, why it is stopped, when it was saved;
- ``discarded`` is a STATE and never appears in the Resume projection (B6);
- the projection draws no token for a fact the row does not hold (A.8: an
  absent recipe is absent, not ``RECIPE · NONE``);
- ``stopped_reason`` is stored byte-for-byte as it was handed in (B5);
- the keyset page mirrors ``list_unfinished``'s contract: bounded limit, a
  signed high-water cursor, ``(resume_order DESC, id DESC)``;
- custody says ``here`` on the MACHINE that holds the row and survives a
  restart, and the identity itself never reaches the wire (B7 as corrected by
  F1: a process lease is not a desk, and a face never prints an opaque id).
"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.db.task_resume import HOST_LOST_CODE
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "owner")


@pytest.fixture
def svc(tmp_path: Path) -> tuple[ProjectService, Database, str]:
    db = Database(tmp_path / "holdspeak.db")
    service = ProjectService(db)
    project = service.create_project(OWNER, {"name": "Architecture review"})
    yield service, db, str(project["id"])
    db.close()


def _save(service: ProjectService, project_id: str, purpose: str, **kw):
    return service.save_ask(OWNER, project_id, {"purpose": purpose, **kw})["task"]


# ── the record ───────────────────────────────────────────────────────


def test_a_saved_ask_keeps_the_ratified_elements(svc) -> None:
    service, _db, project_id = svc
    task = _save(
        service, project_id, "the architecture review brief",
        stopped_reason="192.168.1.43 is unreachable",
        stopped_code="target_unavailable",
        state="failed",
    )
    assert task["purpose"] == "the architecture review brief"
    assert task["projectId"] == project_id
    assert task["state"] == "failed"
    assert task["stoppedReason"] == "192.168.1.43 is unreachable"
    assert task["stoppedCode"] == "target_unavailable"
    assert task["savedAt"]
    # The identity is pinned at save, BEFORE anything is dispatched (B3).
    assert task["invocationId"].startswith("ask_")


def test_the_pinned_identity_is_one_askservice_would_accept(svc) -> None:
    """`AskService.ask` validates the id it is handed (alnum + underscore)."""
    service, _db, project_id = svc
    invocation = _save(service, project_id, "one")["invocationId"]
    assert invocation and invocation.replace("_", "").isalnum()


def test_a_purpose_is_required(svc) -> None:
    service, _db, project_id = svc
    with pytest.raises(ValidationError) as caught:
        service.save_ask(OWNER, project_id, {"purpose": "   "})
    assert caught.value.code == "ask_task_purpose_required"


def test_saving_against_an_unknown_project_is_a_not_found(svc) -> None:
    service, _db, _project_id = svc
    with pytest.raises(NotFound):
        service.save_ask(OWNER, "project_nope", {"purpose": "x"})


def test_an_ask_cannot_be_saved_into_a_state_it_cannot_reach(svc) -> None:
    """B8: an ask has no job row, so the record's writers never mint `running`."""
    service, _db, project_id = svc
    for state in ("running", "waiting", "accepted", "discarded"):
        with pytest.raises(ValidationError) as caught:
            service.save_ask(OWNER, project_id, {"purpose": "x", "state": state})
        assert caught.value.code == "ask_task_state_invalid"


def test_the_stopped_reason_is_stored_verbatim(svc) -> None:
    """B5: the target's own words, never a sentence composed on the way past."""
    service, db, project_id = svc
    words = "Ollama at http://127.0.0.1:11434 refused the connection"
    task = _save(service, project_id, "x", state="failed", stopped_reason=words)
    with db._connection() as conn:
        stored = conn.execute(
            "SELECT stopped_reason FROM project_ask_tasks WHERE id=?", (task["id"],)
        ).fetchone()["stopped_reason"]
    assert stored == words


# ── the projection ───────────────────────────────────────────────────


def test_discard_is_a_state_and_leaves_the_projection(svc) -> None:
    """B6: never delete, park. The row survives; the Resume list does not show it."""
    service, db, project_id = svc
    task = _save(service, project_id, "the one he binned")
    assert [item["id"] for item in service.list_unfinished_asks(OWNER)["items"]] == [task["id"]]

    discarded = service.discard_ask(OWNER, task["id"])["task"]
    assert discarded["state"] == "discarded"
    assert discarded["settledAt"]
    assert service.list_unfinished_asks(OWNER)["items"] == []

    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) c FROM project_ask_tasks WHERE id=?", (task["id"],)
        ).fetchone()["c"] == 1


def test_an_accepted_ask_leaves_the_projection_too(svc) -> None:
    service, db, project_id = svc
    task = _save(service, project_id, "answered")
    db.project_ask_tasks.settle(task["id"], state="accepted")
    assert service.list_unfinished_asks(OWNER)["items"] == []


def test_a_failed_ask_stays_in_the_projection(svc) -> None:
    """The ratified row draws a failed ask WITH a Resume verb — it is unfinished."""
    service, _db, project_id = svc
    task = _save(service, project_id, "stopped", state="failed", stopped_reason="no engine")
    items = service.list_unfinished_asks(OWNER)["items"]
    assert [item["id"] for item in items] == [task["id"]]
    assert items[0]["stoppedReason"] == "no engine"


def test_an_absent_recipe_draws_no_key_at_all(svc) -> None:
    """A.8: no counters or tokens of zero. Absent is absent."""
    service, _db, project_id = svc
    bare = _save(service, project_id, "no recipe yet")
    assert "recipeKey" not in bare
    assert "stoppedReason" not in bare
    assert "stoppedCode" not in bare
    assert "settledAt" not in bare

    with_recipe = _save(service, project_id, "with one", recipe_key="review-brief")
    assert with_recipe["recipeKey"] == "review-brief"


def test_custody_survives_a_restart_and_never_leaks_an_id(svc) -> None:
    """B7 as corrected by F1.

    Custody is stamped with a STABLE MACHINE identity, never the process
    lease.  ``RefinementCoordinator.host_id`` is ``refhost_<uuid4>`` minted per
    process, so custody keyed off it flipped to ``elsewhere`` on the same desk
    after every restart — the exact event this story exists for — and the face
    then printed the raw uuid, breaking the ``raw-ids`` rule as well.

    So: the lease a caller passes must not move the verdict, and the identity
    itself must never reach the wire.
    """
    service, _db, project_id = svc
    service.save_ask(
        OWNER, project_id, {"purpose": "held"}, host_id="refhost_a", lease_epoch=3,
    )

    # The SAME desk, whatever process lease is asking — including the next
    # process, which has minted itself a brand new refhost id.
    for lease in ("refhost_a", "refhost_b", ""):
        item = service.list_unfinished_asks(OWNER, host_id=lease)["items"][0]
        assert item["custody"] == "here", lease
        # The verdict crosses the wire; the identity never does.
        assert "custodyHost" not in item
        assert "refhost" not in json.dumps(item)

    # A row stamped by a different machine reads `elsewhere`.
    service._db.project_ask_tasks.create(
        task_id="asktask_elsewhere",
        project_id=project_id,
        invocation_id="ask_elsewhere",
        purpose="saved on the studio mini",
        lens="Project",
        recipe_key="",
        grounding=None,
        state="saved",
        stopped_reason="",
        stopped_code="",
        custody_host_id="some-other-machine",
        custody_lease_epoch=0,
    )
    rows = {i["purpose"]: i for i in service.list_unfinished_asks(OWNER)["items"]}
    assert rows["saved on the studio mini"]["custody"] == "elsewhere"
    assert "custodyHost" not in rows["saved on the studio mini"]


def test_the_custody_identity_is_stable_within_the_machine(svc) -> None:
    """It is derived from the database file, not from a process uuid."""
    from holdspeak.services.project_service import _custody_identity

    first = _custody_identity()
    assert first, "a machine with a database has an identity"
    assert first == _custody_identity()
    # Opaque and short — a digest, never a path and never reversible to one.
    assert re.fullmatch(r"[0-9a-f]{8,64}", first)


def test_the_projection_can_be_scoped_to_one_project(svc) -> None:
    service, _db, project_id = svc
    other = service.create_project(OWNER, {"name": "Second room"})["id"]
    mine = _save(service, project_id, "mine")
    _save(service, str(other), "theirs")
    scoped = service.list_unfinished_asks(OWNER, project_id=project_id)["items"]
    assert [item["id"] for item in scoped] == [mine["id"]]
    assert len(service.list_unfinished_asks(OWNER)["items"]) == 2


# ── paging, mirroring list_unfinished's contract ─────────────────────


@pytest.mark.parametrize("limit", [0, -1, 51, 1000, "20", 2.5, True])
def test_the_limit_is_bounded_one_to_fifty(svc, limit) -> None:
    service, _db, _project_id = svc
    with pytest.raises(ValidationError) as caught:
        service.list_unfinished_asks(OWNER, limit=limit)
    assert caught.value.code == "ask_task_list_limit_invalid"


def test_the_page_is_newest_first_and_keyset_paged(svc) -> None:
    service, _db, project_id = svc
    saved = [_save(service, project_id, f"ask {n}")["id"] for n in range(5)]

    first = service.list_unfinished_asks(OWNER, limit=2)
    assert [item["id"] for item in first["items"]] == saved[::-1][:2]
    assert first["next_cursor"]

    second = service.list_unfinished_asks(OWNER, limit=2, cursor=first["next_cursor"])
    assert [item["id"] for item in second["items"]] == saved[::-1][2:4]

    third = service.list_unfinished_asks(OWNER, limit=2, cursor=second["next_cursor"])
    assert [item["id"] for item in third["items"]] == saved[::-1][4:]
    assert third["next_cursor"] is None


def test_a_row_saved_mid_page_never_shifts_the_page_under_the_reader(svc) -> None:
    """The high-water anchor, the reason `list_unfinished` uses one."""
    service, _db, project_id = svc
    saved = [_save(service, project_id, f"ask {n}")["id"] for n in range(4)]
    first = service.list_unfinished_asks(OWNER, limit=2)
    _save(service, project_id, "arrived while he was reading")
    second = service.list_unfinished_asks(OWNER, limit=2, cursor=first["next_cursor"])
    assert [item["id"] for item in second["items"]] == saved[::-1][2:4]


def test_a_forged_cursor_is_refused(svc) -> None:
    service, _db, _project_id = svc
    for token in ("", "nonsense", "eyJ2IjogMX0.deadbeef"):
        with pytest.raises(ValidationError) as caught:
            service.list_unfinished_asks(OWNER, cursor=token or "x")
        assert caught.value.code == "ask_task_cursor_invalid"


# ── resume, with no transport supplied ───────────────────────────────


def test_resume_without_a_transport_dispatches_nothing_and_hands_back_the_material(svc) -> None:
    service, _db, project_id = svc
    task = _save(service, project_id, "resume me", lens="Project", recipe_key="brief")
    out = asyncio.run(service.resume_ask(OWNER, task["id"]))
    assert out["dispatched"] is False
    assert out["claimed"] is False
    assert out["answer"] is None
    assert out["task"]["purpose"] == "resume me"
    assert out["task"]["invocationId"] == task["invocationId"]
    assert out["task"]["state"] == "saved"


def test_resuming_a_discarded_ask_is_a_conflict(svc) -> None:
    service, _db, project_id = svc
    task = _save(service, project_id, "binned")
    service.discard_ask(OWNER, task["id"])
    with pytest.raises(ConflictError) as caught:
        asyncio.run(service.resume_ask(OWNER, task["id"]))
    assert caught.value.code == "ask_task_discarded"


def test_resuming_an_unknown_ask_is_a_not_found(svc) -> None:
    service, _db, _project_id = svc
    with pytest.raises(NotFound):
        asyncio.run(service.resume_ask(OWNER, "asktask_nope"))


def test_a_second_resume_cannot_take_a_lease_the_first_still_holds(svc) -> None:
    """The service-level half of "a double Resume cannot double-spend"."""
    service, db, project_id = svc
    task = _save(service, project_id, "in flight")
    assert db.project_ask_tasks.claim_dispatch(task["id"], "refhost_a", 1) is True

    async def dispatch(_task):  # pragma: no cover - must never run
        raise AssertionError("the second resume dispatched")

    with pytest.raises(ConflictError) as caught:
        asyncio.run(service.resume_ask(
            OWNER, task["id"], dispatcher=dispatch, host_id="refhost_a", lease_epoch=1,
        ))
    assert caught.value.code == "ask_task_resume_in_flight"


# ── startup recovery ─────────────────────────────────────────────────


def test_an_orphaned_lease_settles_to_failed_with_a_named_reason(svc) -> None:
    service, db, project_id = svc
    task = _save(service, project_id, "the hub died mid-run")
    db.project_ask_tasks.claim_dispatch(task["id"], "refhost_dead", 7)

    settled = service.recover_ask_tasks_on_startup()
    assert settled == [task["id"]]

    row = db.project_ask_tasks.get(task["id"])
    assert row.state == "failed"
    assert row.stopped_code == HOST_LOST_CODE
    # Never a composed sentence on a recovered row (B5).
    assert row.stopped_reason == ""
    assert row.dispatch_host_id == ""
    assert row.settled_at


def test_a_live_lease_is_not_abandonment(svc) -> None:
    """The discipline of `recover_refinements_on_startup`, copied."""
    service, db, project_id = svc
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    epoch = RefinementThoughtService(db).claim_refinement_host(
        "refhost_live", "test", lease_seconds=600,
    )
    task = _save(service, project_id, "still running elsewhere")
    db.project_ask_tasks.claim_dispatch(task["id"], "refhost_live", epoch)

    assert service.recover_ask_tasks_on_startup() == []
    assert db.project_ask_tasks.get(task["id"]).state == "saved"


def test_recovery_leaves_settled_rows_alone(svc) -> None:
    service, db, project_id = svc
    task = _save(service, project_id, "already answered")
    db.project_ask_tasks.claim_dispatch(task["id"], "refhost_dead", 1)
    db.project_ask_tasks.settle(task["id"], state="accepted")
    assert service.recover_ask_tasks_on_startup() == []
    assert db.project_ask_tasks.get(task["id"]).state == "accepted"


# ── the table's own guards ───────────────────────────────────────────


def test_the_invocation_identity_is_unique(svc) -> None:
    _service, db, _project_id = svc
    with db._connection() as conn:
        row = conn.execute("SELECT COUNT(*) c FROM project_ask_tasks").fetchone()
    assert row["c"] == 0
    db.project_ask_tasks.create(
        task_id="asktask_1", project_id=_project_id, invocation_id="ask_same", purpose="a",
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.project_ask_tasks.create(
            task_id="asktask_2", project_id=_project_id, invocation_id="ask_same", purpose="b",
        )


def test_an_invalid_state_is_refused_by_the_check(svc) -> None:
    _service, db, project_id = svc
    db.project_ask_tasks.create(
        task_id="asktask_chk", project_id=project_id,
        invocation_id="ask_chk", purpose="a",
    )
    with pytest.raises(ValueError):
        db.project_ask_tasks.settle("asktask_chk", state="invented")
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE project_ask_tasks SET state='invented' WHERE id=?", ("asktask_chk",),
            )


def test_the_rows_go_with_their_project(svc) -> None:
    """ON DELETE CASCADE: a Room's saved asks are the Room's."""
    _service, db, project_id = svc
    db.project_ask_tasks.create(
        task_id="asktask_cascade", project_id=project_id,
        invocation_id="ask_cascade", purpose="a",
    )
    with db._connection() as conn:
        assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        assert conn.execute(
            "SELECT COUNT(*) c FROM project_ask_tasks"
        ).fetchone()["c"] == 0


# ── the additive law ─────────────────────────────────────────────────


def test_reconcile_adds_the_table_to_a_pre_200_database(tmp_path: Path) -> None:
    """Migrations are additive and the schema self-reconciles (HS-137).

    A database built WITHOUT `project_ask_tasks` gains it — table and both
    indexes — on the next open, with nothing dropped and nothing rebuilt.
    """
    import re

    from holdspeak.db.reconcile import reconcile_schema
    from holdspeak.db.schema import SCHEMA_SQL

    pre200 = re.sub(
        r"CREATE TABLE IF NOT EXISTS project_ask_tasks \(.*?\);\s*"
        r"CREATE INDEX IF NOT EXISTS idx_project_ask_tasks_resume.*?;\s*"
        r"CREATE INDEX IF NOT EXISTS idx_project_ask_tasks_project.*?;",
        "", SCHEMA_SQL, flags=re.S,
    )
    assert "project_ask_tasks" not in pre200

    path = tmp_path / "pre200.db"
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(pre200)
    conn.execute(
        "INSERT INTO projects (id, name) VALUES ('project_legacy', 'Old room')"
    )
    conn.commit()
    assert conn.execute(
        "SELECT COUNT(*) c FROM sqlite_master WHERE name='project_ask_tasks'"
    ).fetchone()["c"] == 0
    conn.close()

    db = Database(path)
    try:
        with db._connection() as live:
            names = {
                str(row["name"])
                for row in live.execute(
                    "SELECT name FROM sqlite_master WHERE name LIKE '%project_ask_tasks%'"
                ).fetchall()
            }
        assert names >= {
            "project_ask_tasks",
            "idx_project_ask_tasks_resume",
            "idx_project_ask_tasks_project",
        }
        # The pre-existing row is untouched, and the new table works over it.
        task = db.project_ask_tasks.create(
            task_id="asktask_legacy", project_id="project_legacy",
            invocation_id="ask_legacy", purpose="carried over",
        )
        assert task.state == "saved"
    finally:
        db.close()


# ── the browser-observed stop (why it is stopped, AC1) ───────────────
#
# `save_ask` writes the row BEFORE dispatch (B3), so the ordinary failure —
# an engine that is not ready, observed by the Room, never by the server —
# had no way back into the record.  These prove the narrow route that closes
# it, and that ruling B5 survives contact with an untrusted caller.


def _unready(monkeypatch, *, state: str = "unavailable", reason: str = "") -> None:
    """Make the hub's live placement report a named refusal."""
    from holdspeak.inference_targets import InferenceTarget, PlacementResolution

    target = InferenceTarget(
        id="this_machine", name="This Mac", kind="this_device",
        boundary="same_device", owner="you", transport="in_process",
        profile_id=None, engine="configured_local_engine", model="",
        context_limit=16_384, readiness_state=state, readiness_reason=reason,
    )
    monkeypatch.setattr(
        "holdspeak.inference_targets.resolve_placement",
        lambda *a, **k: PlacementResolution(
            effective_target_id="this_machine", source="global", target=target,
        ),
    )


def test_a_browser_observed_refusal_records_the_targets_own_words(svc, monkeypatch) -> None:
    service, db, project_id = svc
    _unready(monkeypatch, reason="No model is configured on this Mac")
    task = _save(service, project_id, "the architecture review brief")

    out = service.record_ask_stop(OWNER, task["id"], "inference_target_unavailable")
    assert out["changed"] is True
    assert out["task"]["state"] == "failed"
    # The words came from the server's own target, not from any caller.
    assert out["task"]["stoppedReason"] == "No model is configured on this Mac"
    assert out["task"]["stoppedCode"] == "inference_target_unavailable"

    row = db.project_ask_tasks.get(task["id"])
    assert row.stopped_reason == "No model is configured on this Mac"
    assert row.invocation_id == task["invocationId"]   # identity never touched


def test_a_stopped_ask_is_still_resumable(svc, monkeypatch) -> None:
    """A failed ask is precisely the one he comes back to."""
    service, _db, project_id = svc
    _unready(monkeypatch, reason="No model is configured on this Mac")
    task = _save(service, project_id, "come back to me")
    service.record_ask_stop(OWNER, task["id"], "inference_target_unavailable")

    listed = service.list_unfinished_asks(OWNER)["items"]
    assert [item["id"] for item in listed] == [task["id"]]
    assert listed[0]["stoppedReason"] == "No model is configured on this Mac"

    transport = _CountingTransport()
    out = asyncio.run(service.resume_ask(OWNER, task["id"], dispatcher=transport))
    assert out["dispatched"] is True
    assert transport.calls == [task["invocationId"]]
    assert out["task"]["state"] == "accepted"


class _CountingTransport:
    def __init__(self, answer=None):
        self.calls: list[str] = []
        self.answer = answer or {"output": "ANSWER"}

    async def __call__(self, task):
        self.calls.append(task["invocationId"])
        return self.answer


def test_an_unrecognised_code_stores_the_code_and_no_reason(svc, monkeypatch) -> None:
    """B5: a code the server cannot corroborate quotes nothing at all."""
    service, db, project_id = svc
    _unready(monkeypatch, state="ready", reason="")   # the engine came back
    task = _save(service, project_id, "stale refusal")

    out = service.record_ask_stop(OWNER, task["id"], "inference_target_unavailable")
    assert out["task"]["stoppedCode"] == "inference_target_unavailable"
    assert "stoppedReason" not in out["task"]
    assert db.project_ask_tasks.get(task["id"]).stopped_reason == ""


def test_a_code_the_hub_has_never_heard_of_quotes_nothing(svc, monkeypatch) -> None:
    service, db, project_id = svc
    _unready(monkeypatch, reason="No model is configured on this Mac")
    task = _save(service, project_id, "invented code")
    service.record_ask_stop(OWNER, task["id"], "something_the_client_made_up")
    assert db.project_ask_tasks.get(task["id"]).stopped_reason == ""
    assert db.project_ask_tasks.get(task["id"]).stopped_code == "something_the_client_made_up"


@pytest.mark.parametrize("code", [
    "",
    "   ",
    "192.168.1.43 is unreachable",
    "Destination 'LAN box' is unavailable",
    "Inference_Target_Unavailable",
    "a" * 65,
])
def test_a_sentence_can_never_get_in_through_the_code(svc, code) -> None:
    """The trap this route exists to avoid: untrusted prose in the store."""
    service, _db, project_id = svc
    task = _save(service, project_id, "guarded")
    with pytest.raises(ValidationError) as caught:
        service.record_ask_stop(OWNER, task["id"], code)
    assert caught.value.code == "ask_task_stop_code_invalid"


def test_recording_the_same_stop_twice_changes_nothing(svc, monkeypatch) -> None:
    service, db, project_id = svc
    _unready(monkeypatch, reason="No model is configured on this Mac")
    task = _save(service, project_id, "retry me")

    first = service.record_ask_stop(OWNER, task["id"], "inference_target_unavailable")
    row = db.project_ask_tasks.get(task["id"])

    # A retry, even carrying a different code, is a no-op and never overwrites
    # the reason already quoted onto the row.
    second = service.record_ask_stop(OWNER, task["id"], "inference_target_needs_setup")
    assert second["changed"] is False
    assert second["task"] == first["task"]
    after = db.project_ask_tasks.get(task["id"])
    assert after == row


@pytest.mark.parametrize("state", ["accepted", "discarded"])
def test_the_route_will_not_move_a_row_it_does_not_own(svc, state) -> None:
    service, db, project_id = svc
    task = _save(service, project_id, "settled already")
    db.project_ask_tasks.settle(task["id"], state=state)
    before = db.project_ask_tasks.get(task["id"])

    with pytest.raises(ConflictError) as caught:
        service.record_ask_stop(OWNER, task["id"], "inference_target_unavailable")
    assert caught.value.code == "ask_task_not_stoppable"
    assert db.project_ask_tasks.get(task["id"]) == before


def test_stopping_an_unknown_ask_is_a_not_found(svc) -> None:
    service, _db, _project_id = svc
    with pytest.raises(NotFound):
        service.record_ask_stop(OWNER, "asktask_nope", "inference_target_unavailable")


# ── custody keys on a DURABLE machine identity (F1, corrected) ───────
#
# Custody asks "is this the same DESK?".  `database_identity` digests the
# database's device+inode, which answers "is this the same FILE?" — correct
# for HS-200-02, wrong here, and the reason custody was nondeterministic
# across a restart.  These are the tests that would have caught it.


def _fresh_config(tmp_path: Path, monkeypatch, name: str = "config.json") -> Path:
    """Point the config facade at an isolated file and clear the id cache."""
    from holdspeak.config import core as config_core

    path = tmp_path / name
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", path)
    config_core._machine_ids.pop(str(path), None)
    return path


def test_the_machine_identity_is_minted_once_and_persisted(tmp_path, monkeypatch) -> None:
    from holdspeak.config import core as config_core
    from holdspeak.config import machine_identity

    path = _fresh_config(tmp_path, monkeypatch)
    assert not path.exists()

    minted = machine_identity()
    assert minted
    assert json.loads(path.read_text())["machine_id"] == minted

    # Never regenerated — not in this process, and not in the next one.
    config_core._machine_ids.pop(str(path), None)
    assert machine_identity() == minted
    assert json.loads(path.read_text())["machine_id"] == minted


def test_an_existing_machine_identity_is_never_rewritten(tmp_path, monkeypatch) -> None:
    from holdspeak.config import machine_identity

    path = _fresh_config(tmp_path, monkeypatch)
    path.write_text(json.dumps({"machine_id": "deadbeef", "control_mode": "yolo"}))
    assert machine_identity() == "deadbeef"
    kept = json.loads(path.read_text())
    assert kept["machine_id"] == "deadbeef"
    assert kept["control_mode"] == "yolo"      # nothing else was disturbed


def test_a_settings_save_round_trips_the_machine_identity(tmp_path, monkeypatch) -> None:
    """It is a real Config field, so a settings write cannot drop it."""
    from holdspeak.config import Config, machine_identity

    path = _fresh_config(tmp_path, monkeypatch)
    minted = machine_identity()
    loaded = Config.load()
    assert loaded.machine_id == minted
    loaded.control_mode = "safe"
    loaded.save()
    assert json.loads(path.read_text())["machine_id"] == minted


def test_a_config_that_cannot_be_written_yields_no_identity(tmp_path, monkeypatch) -> None:
    """Identity failure is never load-bearing: no token beats a guess."""
    from holdspeak.config import core as config_core

    blocked = tmp_path / "not-a-dir" / "config.json"
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", blocked)
    config_core._machine_ids.pop(str(blocked), None)
    monkeypatch.setattr(
        Path, "mkdir", lambda *a, **k: (_ for _ in ()).throw(OSError("read-only")),
    )
    from holdspeak.config import machine_identity
    assert machine_identity() == ""


def test_custody_survives_the_database_file_being_recreated(tmp_path, monkeypatch) -> None:
    """THE regression: a new inode at the same path must not move the desk.

    This is exactly what a restore from backup does, and what made custody
    flake. `database_identity` moves here — correctly, for its own question —
    and custody must not.
    """
    import shutil

    from holdspeak.runtime_identity import database_identity
    from holdspeak.services.project_service import _custody_identity

    _fresh_config(tmp_path, monkeypatch)
    db_path = tmp_path / "holdspeak.db"
    db = Database(db_path)
    service = ProjectService(db)
    project_id = str(service.create_project(OWNER, {"name": "Room"})["id"])
    service.save_ask(OWNER, project_id, {"purpose": "held here"})
    before_desk = _custody_identity()
    before_file = database_identity(db_path)
    assert service.list_unfinished_asks(OWNER)["items"][0]["custody"] == "here"
    db.close()

    # Same path, brand-new inode, same rows — a restore.
    backup = tmp_path / "backup.db"
    shutil.copy2(db_path, backup)
    db_path.unlink()
    shutil.copy2(backup, db_path)

    restored = Database(db_path)
    try:
        assert database_identity(db_path) != before_file   # the FILE moved
        assert _custody_identity() == before_desk          # the DESK did not
        row = ProjectService(restored).list_unfinished_asks(OWNER)["items"][0]
        assert row["custody"] == "here"
        assert row["purpose"] == "held here"
    finally:
        restored.close()


def test_a_different_machine_reads_elsewhere(tmp_path, monkeypatch) -> None:
    from holdspeak.config import core as config_core

    _fresh_config(tmp_path, monkeypatch, "desk-a.json")
    db = Database(tmp_path / "holdspeak.db")
    service = ProjectService(db)
    project_id = str(service.create_project(OWNER, {"name": "Room"})["id"])
    service.save_ask(OWNER, project_id, {"purpose": "saved on desk A"})
    assert service.list_unfinished_asks(OWNER)["items"][0]["custody"] == "here"

    # The same database opened on another desk: a different config, a
    # different identity, and the row honestly reads elsewhere.
    other = tmp_path / "desk-b.json"
    monkeypatch.setattr("holdspeak.config.CONFIG_FILE", other)
    config_core._machine_ids.pop(str(other), None)
    try:
        listed = service.list_unfinished_asks(OWNER)["items"][0]
        assert listed["custody"] == "elsewhere"
        # The token itself never rides the wire — only the verdict.
        assert "machine" not in json.dumps(listed).lower()
    finally:
        db.close()


def test_an_unknown_desk_draws_no_custody_at_all(tmp_path, monkeypatch) -> None:
    from holdspeak.services import project_service as module

    _fresh_config(tmp_path, monkeypatch)
    db = Database(tmp_path / "holdspeak.db")
    try:
        monkeypatch.setattr(module, "_custody_identity", lambda: "")
        service = ProjectService(db)
        project_id = str(service.create_project(OWNER, {"name": "Room"})["id"])
        service.save_ask(OWNER, project_id, {"purpose": "no identity"})
        listed = service.list_unfinished_asks(OWNER)["items"][0]
        assert "custody" not in listed
        assert "custodyHost" not in listed
    finally:
        db.close()
