"""PHILO-7-02: the grant lifecycle, fenced through the REAL kernel (the checked design beat).

Every fence drives the real broker (``kernel/runtime._configure`` with an
injected clock), the real desk codec, the real journal and the real grant
table over an isolated database. The design and its red conditions:
``pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md``
("Fences story 02 must write"). "Mutation red" fences name the deliberate
mutation that turns them red (recorded in
``docs/internal/philo/phase-7/article-xi/red-mutations.txt``).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel import desk
from holdspeak.kernel.desk import DESK_PLACEMENT, desk_path
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import desk_delegation, desk_kernel
from holdspeak.services.primitive_service import PrimitiveService

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
AGENT = Principal(PrincipalKind.AGENT, "agent-a")
AGENT_B = Principal(PrincipalKind.AGENT, "agent-b")
NODE = Principal(PrincipalKind.NODE, desk.DESK_EXECUTOR)


class Rig:
    def __init__(self, database: Database, broker: Any, now: list[float]) -> None:
        self.db, self.broker, self.now = database, broker, now
        self.primitives = PrimitiveService(database)
        self.zone = self.primitives.create_directory(OWNER, name="Zone")["id"]
        self.note = self.primitives.create_note(OWNER, title="n")["id"]

    # -- the grant, through its real operations ---------------------------
    def grant(self, identity: str = "agent-a", **body: Any) -> dict[str, Any]:
        return desk_delegation.grant(OWNER, identity, body, database=self.db)

    def revoke(self, identity: str = "agent-a") -> dict[str, Any]:
        return desk_delegation.revoke(OWNER, identity, database=self.db)

    def row(self, grant_id: str) -> dict[str, Any]:
        with self.db._connection() as conn:
            return dict(conn.execute("SELECT * FROM kernel_desk_delegations WHERE id=?", (grant_id,)).fetchone())

    def rows(self) -> list[dict[str, Any]]:
        with self.db._connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM kernel_desk_delegations ORDER BY created_at, id")]

    # -- one desk write, step by step (the real broker, the real codec) ---
    def submit(self, principal: Principal = AGENT, name: str = "zone.file") -> dict[str, Any]:
        native_id = str(uuid.uuid4())
        args = {"directory_id": self.zone, "primitive_id": f"note:{self.note}"}
        with desk_path():
            handle = self.broker.submit(desk_kernel._raw(name, native_id, f"note:{self.note}", args), principal)
        handle["native_id"] = native_id
        return handle

    def decide(self, handle: dict[str, Any], principal: Principal = AGENT) -> dict[str, Any]:
        return self.broker.decide(handle["operation_id"], "approve", int(handle["revision"]), principal)

    def claim(self, handle: dict[str, Any]) -> dict[str, Any]:
        return self.broker.claim(NODE, handle["native_id"])

    def execute(self, handle: dict[str, Any]) -> dict[str, Any]:
        self.primitives.file_member(AGENT, self.zone, f"note:{self.note}")
        return self.broker.receipt(handle["operation_id"], "succeeded", f"note:{self.note}", NODE)

    def operation(self, operation_id: str) -> dict[str, Any]:
        return self.broker.store.operation(operation_id)

    def receipt(self, operation_id: str) -> dict[str, Any] | None:
        return self.broker.store.receipt(operation_id)

    def filed(self) -> list[str]:
        return [m.primitive_id for m in self.db.directory_memberships.list_for_directory(self.zone)]

    def waiting(self) -> int:
        return len(self.broker.store.operations_in_state("awaiting_decision"))


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Rig:
    import holdspeak.db.core as db_core

    now = [1_000.0]
    database = Database(tmp_path / "grant.db")
    monkeypatch.setattr(db_core, "_db", database)
    broker = _configure(database, clock=lambda: now[0])
    return Rig(database, broker, now)


def _sha(grant: dict[str, Any], rig: Rig) -> str:
    return rig.row(grant["grant_id"])["terms_sha256"]


# ── invariant 1: frozen at admission ─────────────────────────────────────


def test_f1_an_agents_write_under_its_grant_names_the_grant(rig: Rig) -> None:
    g1 = rig.grant()
    handle = rig.submit()
    rig.decide(handle)
    claimed = rig.claim(handle)
    assert claimed["operations"], claimed
    receipt = rig.execute(handle)
    assert receipt["state"] == "succeeded"
    assert receipt["authority_basis"] == f"desk-delegation:{g1['grant_id']}:{_sha(g1, rig)}"
    assert _sha(g1, rig).startswith("sha256:")
    assert (receipt["delegator_kind"], receipt["delegator_identity"]) == ("owner", "owner-session")
    assert (receipt["actor_kind"], receipt["actor_identity"]) == ("agent", "agent-a")


def test_f2_a_regrant_before_approval_never_approves_the_older_operation(rig: Rig) -> None:
    g1 = rig.grant()
    handle = rig.submit()
    g2 = rig.grant()
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.reason == "desk_delegation_revoked"
    receipt = refused.value.receipt
    assert receipt["state"] == "refused" and receipt["authority_basis"].split(":", 2)[1] == g1["grant_id"]
    assert g2["grant_id"] not in rig.operation(handle["operation_id"])["authority_basis"]
    assert rig.filed() == [] and rig.waiting() == 0
    assert rig.row(g1["grant_id"])["revocation_reason"] == "reapproved"


# ── invariant 2: expiry inside the hashed terms ──────────────────────────


def test_f3_the_expiry_is_inside_the_hash_and_the_basis_keeps_its_prefix(rig: Rig) -> None:
    terms = desk.terms_for("agent-a")
    assert desk.terms_sha256(terms, 2_000.0) != desk.terms_sha256(terms, 3_000.0) != desk.terms_sha256(terms, None)
    g1 = rig.grant(expires_at=2_000.0)
    assert _sha(g1, rig) == desk.terms_sha256(terms, 2_000.0)
    handle = rig.submit()
    basis = rig.operation(handle["operation_id"])["authority_basis"]
    kind, grant_id, sha = basis.split(":", 2)
    assert (kind, grant_id, sha) == ("desk-delegation", g1["grant_id"], _sha(g1, rig))
    assert desk.parse_basis(basis) == (g1["grant_id"], _sha(g1, rig))


# ── invariant 3: the interleavings ───────────────────────────────────────


def test_f4_revoke_between_admission_and_approval(rig: Rig) -> None:
    rig.grant()
    handle = rig.submit()
    rig.revoke()
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.reason == "desk_delegation_revoked"
    operation = rig.operation(handle["operation_id"])
    assert operation["state"] == "refused" and rig.receipt(handle["operation_id"])["outcome"] == "desk_delegation_revoked"
    assert rig.filed() == [] and rig.waiting() == 0


def test_f5_expiry_between_admission_and_approval_and_f5b_the_code_stays_expired(rig: Rig) -> None:
    g1 = rig.grant(expires_at=1_050.0)
    handle = rig.submit()
    rig.now[0] = 1_100.0
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.reason == "desk_delegation_expired"
    assert rig.row(g1["grant_id"])["state"] == "EXPIRED"
    assert rig.filed() == [] and rig.waiting() == 0
    # F5b: after EXPIRED is persisted, a new admission and a second frozen check say expired, never revoked.
    again = rig.submit()
    assert again["state"] == "refused" and rig.receipt(again["operation_id"])["outcome"] == "desk_delegation_expired"
    with rig.db._connection() as conn:
        assert desk.by_basis(conn, rig.operation(handle["operation_id"]), rig.now[0]) == "desk_delegation_expired"


def test_f5c_admission_codes_match_the_history(rig: Rig) -> None:
    never = rig.submit()
    assert rig.receipt(never["operation_id"])["outcome"] == "desk_delegation_required"
    rig.grant()
    rig.revoke()
    stopped = rig.submit()
    assert rig.receipt(stopped["operation_id"])["outcome"] == "desk_delegation_revoked"
    rig.grant(expires_at=1_010.0)
    rig.now[0] = 1_020.0
    lapsed = rig.submit()
    assert rig.receipt(lapsed["operation_id"])["outcome"] == "desk_delegation_expired"
    assert rig.waiting() == 0


@pytest.mark.parametrize("change, code", [
    ("revoke", "desk_delegation_revoked"), ("expire", "desk_delegation_expired"), ("regrant", "desk_delegation_revoked"),
])
def test_f6_f7_f8_a_change_between_approval_and_the_claim_refuses_the_claim(rig: Rig, change: str, code: str) -> None:
    rig.grant(expires_at=1_010.0 if change == "expire" else None)
    handle = rig.submit()
    rig.decide(handle)
    if change == "revoke":
        rig.revoke()
    elif change == "expire":
        rig.now[0] = 1_020.0  # past the grant's expiry, inside the warrant's 30 s claim window
    else:
        rig.grant()
    claimed = rig.claim(handle)
    assert claimed["operations"] == [] and claimed["refusal"]["outcome"] == code
    assert rig.operation(handle["operation_id"])["state"] == "refused"
    assert rig.filed() == []


@pytest.mark.parametrize("change, next_code", [
    ("revoke", "desk_delegation_revoked"), ("expire", "desk_delegation_expired"), ("regrant", ""),
])
def test_f9_a_change_after_the_claims_check_lets_this_write_land_once(rig: Rig, change: str, next_code: str) -> None:
    g1 = rig.grant(expires_at=1_050.0 if change == "expire" else None)
    handle = rig.submit()
    rig.decide(handle)
    assert rig.claim(handle)["operations"]
    if change == "revoke":
        rig.revoke()
    elif change == "expire":
        rig.now[0] = 1_060.0
    else:
        g2 = rig.grant()
    receipt = rig.execute(handle)
    assert receipt["state"] == "succeeded" and receipt["authority_basis"].split(":", 2)[1] == g1["grant_id"]
    assert rig.filed() == [f"note:{rig.note}"]
    later = rig.submit()
    if next_code:
        assert rig.receipt(later["operation_id"])["outcome"] == next_code
    else:  # F9c: the next valid write succeeds under G2
        assert rig.operation(later["operation_id"])["authority_basis"].split(":", 2)[1] == g2["grant_id"]


# ── invariant 4: every desk end is atomic; approval is caller- and state-scoped ──


def test_f10_a_refusal_at_approval_ends_refused_with_the_receipt_on_the_error(rig: Rig) -> None:
    rig.grant()
    handle = rig.submit()
    rig.revoke()
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.receipt == rig.receipt(handle["operation_id"])
    assert rig.operation(handle["operation_id"])["state"] == "refused" and rig.waiting() == 0


def test_f10b_a_tool_call_self_decide_still_waits_with_no_receipt(rig: Rig) -> None:
    from tests.unit.test_kernel_broker import _request

    handle = rig.broker.submit(_request("f10b"), AGENT)
    assert handle["state"] == "awaiting_decision"
    with pytest.raises(KernelRefused) as refused:
        rig.broker.decide(handle["operation_id"], "approve", int(handle["revision"]), AGENT)
    assert refused.value.reason == "owner_principal_required_to_decide"
    assert rig.operation(handle["operation_id"])["state"] == "awaiting_decision"
    assert rig.receipt(handle["operation_id"]) is None


def test_f10c_another_agent_can_neither_end_nor_approve_it(rig: Rig) -> None:
    rig.grant("agent-a")
    rig.grant("agent-b")
    handle = rig.submit(AGENT)
    before = rig.operation(handle["operation_id"])
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle, AGENT_B)
    assert refused.value.reason == "owner_principal_required_to_decide" and refused.value.receipt is None
    after = rig.operation(handle["operation_id"])
    assert (after["state"], after["revision"]) == (before["state"], before["revision"])
    assert rig.receipt(handle["operation_id"]) is None


def test_f10d_a_repeated_decide_after_the_end_keeps_the_one_receipt(rig: Rig) -> None:
    rig.grant()
    handle = rig.submit()
    rig.revoke()
    with pytest.raises(KernelRefused):
        rig.decide(handle)
    first = rig.receipt(handle["operation_id"])
    with pytest.raises(KernelRefused) as again:
        rig.decide(handle)
    assert again.value.reason == "owner_principal_required_to_decide" and again.value.receipt is None
    assert rig.receipt(handle["operation_id"]) == first
    with rig.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_receipts WHERE operation_id=?", (handle["operation_id"],)).fetchone()[0] == 1


def test_f10e_a_winner_between_the_state_read_and_the_seam(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    rig.grant()
    handle = rig.submit()
    rig.revoke()
    store = rig.broker.store
    real = store.transition_and_receipt
    fired: list[str] = []

    def winner_first(operation_id: str, revision: int, state: str, outcome: str, *args: Any, **kwargs: Any):
        if not fired and state == "refused":
            fired.append(operation_id)
            # The winner: approve (owner), claim, and a succeeded receipt.
            op = store.operation(operation_id)
            rig.broker.decide(operation_id, "approve", int(op["revision"]), OWNER)
            # The store's own atomic claim (the winner's grant check already
            # passed in its own call; this one only has to finish first).
            assert store.claim_candidate(NODE.identity, handle["native_id"]) is not None
            rig.broker.receipt(operation_id, "succeeded", f"note:{rig.note}", NODE)
        return real(operation_id, revision, state, outcome, *args, **kwargs)

    monkeypatch.setattr(store, "transition_and_receipt", winner_first)
    # decide() reads awaiting_decision, then the winner lands before the strict seam.
    monkeypatch.setattr(rig.broker, "_clock", lambda: rig.now[0])
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert fired and refused.value.reason == "operation_already_terminal"
    assert rig.receipt(handle["operation_id"])["outcome"] == "succeeded"
    events = store.events(0, {"operation_id": handle["operation_id"], "event_type": "operation.refused"})["events"]
    assert events == []


def test_f11_startup_recovery_ends_a_waiting_desk_operation(rig: Rig) -> None:
    rig.grant()
    handle = rig.submit()
    assert rig.operation(handle["operation_id"])["state"] == "awaiting_decision"
    from holdspeak.kernel.desk_broker import recover_on_startup

    assert recover_on_startup(rig.broker) == 1
    assert rig.operation(handle["operation_id"])["state"] == "indeterminate"
    assert rig.receipt(handle["operation_id"])["outcome"] == "hub_restart_during_decision"


def test_f17_one_live_grant_per_identity(rig: Rig) -> None:
    g1 = rig.grant()
    g2 = rig.grant()
    states = [(r["id"], r["state"], r["revocation_reason"]) for r in rig.rows()]
    assert sorted(states) == sorted([(g1["grant_id"], "REVOKED", "reapproved"), (g2["grant_id"], "LIVE", "")])
    with pytest.raises(sqlite3.IntegrityError):
        with rig.db._connection() as conn:
            conn.execute(
                "INSERT INTO kernel_desk_delegations(id,agent_identity,delegator_kind,delegator_identity,operations_json,"
                "terms_sha256,expires_at,state,grant_operation_id,created_at,updated_at) VALUES('x','agent-a','owner','o','[]','s',NULL,'LIVE','op',1,1)"
            )


def test_f18_decision_delete_is_in_the_grant_and_a_stored_set_decides(rig: Rig) -> None:
    g1 = rig.grant()
    handle = rig.submit(AGENT, "decision.delete")
    assert handle["state"] == "awaiting_decision"
    # A stored set WITHOUT the operation refuses it (a later code change never widens an old grant).
    with rig.db._connection() as conn:
        ops = [n for n in json.loads(rig.row(g1["grant_id"])["operations_json"]) if n != "decision.delete"]
        conn.execute("UPDATE kernel_desk_delegations SET operations_json=? WHERE id=?", (json.dumps(ops), g1["grant_id"]))
    refused = rig.submit(AGENT, "decision.delete")
    assert rig.receipt(refused["operation_id"])["outcome"] == "desk_delegation_required"
    assert "decision.delete" in desk.DESK_GRANT_OPERATIONS
    assert not {"delegation.grant", "delegation.revoke"} & desk.DESK_GRANT_OPERATIONS


def test_f19_a_grant_to_another_agent_authorises_nothing_here(rig: Rig) -> None:
    rig.grant("agent-a")
    handle = rig.submit(AGENT_B)
    assert rig.receipt(handle["operation_id"])["outcome"] == "desk_delegation_required"
    assert rig.filed() == [] and rig.waiting() == 0


def test_a_raw_submission_of_a_desk_name_is_refused_with_a_receipt(rig: Rig) -> None:
    """Outside the desk path nothing would ever execute it: refused, never left waiting."""
    rig.grant()
    handle = rig.broker.submit(desk_kernel._raw("zone.file", str(uuid.uuid4()), "note:x", {}), AGENT)
    assert handle["state"] == "refused" and rig.receipt(handle["operation_id"])["outcome"] == "desk_operation_service_required"


# ── F20 / F24: one transaction, one connection ───────────────────────────


def _fault_on_receipt(db: Database) -> None:
    with db._connection() as conn:
        conn.execute("CREATE TRIGGER fault_receipt BEFORE INSERT ON kernel_receipts BEGIN SELECT RAISE(ABORT, 'injected fault'); END")


def _clear_fault(db: Database) -> None:
    with db._connection() as conn:
        conn.execute("DROP TRIGGER fault_receipt")


def _receipt_count(db: Database) -> int:
    with db._connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM kernel_receipts").fetchone()[0]


def _ended_without_receipt(db: Database) -> list[str]:
    with db._connection() as conn:
        return [r[0] for r in conn.execute(
            "SELECT o.operation_id FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id "
            "WHERE o.state IN ('succeeded','failed','refused','cancelled','indeterminate') AND r.operation_id IS NULL"
        )]


def test_f20_t1_an_admission_refusal_is_all_or_nothing(rig: Rig) -> None:
    _fault_on_receipt(rig.db)
    with rig.db._connection() as conn:
        before = conn.execute("SELECT COUNT(*) FROM kernel_operations").fetchone()[0]
    with pytest.raises(sqlite3.DatabaseError):
        rig.submit()  # no grant: the T1 refusal
    with rig.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations").fetchone()[0] == before
    assert _ended_without_receipt(rig.db) == []


@pytest.mark.parametrize("path", ["T3 approval", "T4 reject", "T5 claim", "T6 recovery", "T7 reaper", "T9 grant", "T1 delegation owner-only"])
def test_f20_every_desk_end_is_atomic(rig: Rig, path: str) -> None:
    rig.grant()
    handle = rig.submit()
    if path == "T3 approval":
        rig.revoke()
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            rig.decide(handle)
    elif path == "T4 reject":
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            rig.broker.decide(handle["operation_id"], "reject", int(handle["revision"]), OWNER)
    elif path == "T5 claim":
        rig.decide(handle)
        rig.revoke()
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            rig.claim(handle)
    elif path == "T6 recovery":
        from holdspeak.kernel.desk_broker import recover_on_startup

        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            recover_on_startup(rig.broker)
    elif path == "T7 reaper":
        rig.decide(handle)
        rig.now[0] = 10_000.0
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            rig.broker.reap_expired()
    elif path == "T9 grant":
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            rig.grant("agent-c")
        assert [r for r in rig.rows() if r["agent_identity"] == "agent-c"] == []
    else:
        _fault_on_receipt(rig.db)
        with pytest.raises(sqlite3.DatabaseError):
            desk_delegation.grant(AGENT, "agent-a", {}, database=rig.db)
    assert _ended_without_receipt(rig.db) == [], f"{path}: an ended operation with no receipt"
    _clear_fault(rig.db)


def test_f24_one_connection_per_atomic_write(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    """T1, T4 and T9 run on ONE connection; T4's row carries decision='reject'."""
    from contextlib import contextmanager

    store = rig.broker.store
    depth = [0]
    nested: list[int] = []

    def recorder(real_factory: Any) -> Any:
        @contextmanager
        def recording():
            with real_factory() as conn:
                depth[0] += 1
                if depth[0] > 1:
                    nested.append(id(conn))
                try:
                    yield conn
                finally:
                    depth[0] -= 1
        return recording

    # Every connection the real database hands out, through the journal or
    # any service or store method, is recorded while a write is open.
    monkeypatch.setattr(store, "_connection", recorder(store._connection))
    monkeypatch.setattr(rig.db, "_connection", recorder(rig.db._connection))
    rig.submit(AGENT_B)  # T1 (no grant for agent-b)
    handle = rig.submit(OWNER)
    rig.broker.decide(handle["operation_id"], "reject", int(handle["revision"]), OWNER)  # T4
    grant_handle = rig.grant("agent-d")  # T9
    assert nested == [], "a second connection opened inside an atomic write"
    row = store.operation(handle["operation_id"])
    assert (row["state"], row["decision"]) == ("refused", "reject")
    assert rig.receipt(handle["operation_id"])["outcome"] == "owner_rejected"
    assert rig.row(grant_handle["grant_id"])["state"] == "LIVE"


def test_f21b_a_fault_inside_the_t9_effect_rolls_the_grant_back(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    g1 = rig.grant()
    before = rig.row(g1["grant_id"])
    real = desk.revoke_effect

    def faulty(**kwargs: Any):
        effect = real(**kwargs)

        def run(conn: Any) -> None:
            effect(conn)
            raise RuntimeError("injected fault after the grant write")

        return run

    monkeypatch.setattr(desk, "revoke_effect", faulty)
    with pytest.raises(RuntimeError):
        rig.revoke()
    after = rig.row(g1["grant_id"])
    assert (after["state"], after["updated_at"], after["revocation_reason"]) == ("LIVE", before["updated_at"], "")
    with rig.db._connection() as conn:
        claimed = conn.execute("SELECT operation_id FROM kernel_operations WHERE name='delegation.revoke' AND state='claimed'").fetchall()
    assert len(claimed) == 1 and rig.receipt(claimed[0][0]) is None
    # The reaper returns zero before the deadline; past it, indeterminate with a receipt.
    assert rig.broker.reap_expired()["count"] == 0
    rig.now[0] += 4_000.0
    reaped = rig.broker.reap_expired()["reaped"]
    assert [(r["state"], r["outcome"]) for r in reaped] == [("indeterminate", "execution_liveness_expired")]
    monkeypatch.setattr(desk, "revoke_effect", real)
    rig.revoke()
    assert rig.row(g1["grant_id"])["state"] == "REVOKED"


# ── the chip agrees with the kernel (F15) ────────────────────────────────


def test_f15_the_projection_is_allowed_iff_the_kernel_admits(rig: Rig) -> None:
    def view() -> Any:
        return desk_delegation.views(["agent-a"], database=rig.db)["by_identity"]["agent-a"]

    def admitted() -> bool:
        return rig.submit()["state"] != "refused"

    assert view() is None and not admitted()                       # never granted: no chip
    rig.grant()
    assert view()["state"] == "LIVE" and admitted()                # FILING ALLOWED
    rig.revoke()
    assert view()["state"] == "REVOKED" and not admitted()         # FILING STOPPED
    rig.grant(expires_at=1_030.0)
    assert view()["state"] == "LIVE" and admitted()
    rig.now[0] = 1_040.0                                           # expired by the clock, stored LIVE
    assert view()["state"] == "EXPIRED" and not admitted()
