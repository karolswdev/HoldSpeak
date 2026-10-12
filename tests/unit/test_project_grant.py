"""PHILO-9-07: the project grant's lifecycle, fenced through the REAL kernel (A3, A7).

The steward beat (``docs/internal/philo/phase-9/steward-beat/README.md``,
section 7: A3 and A7) asks for Phase 7's interleaving matrix with the project
dimension. Every fence drives the real broker (``kernel/runtime._configure``
with an injected clock), the real Room codec, the real journal and the real
grant table over an isolated database; the grant is minted only by the real
``project.delegation.grant`` operation (``services/project_delegation.py``).
The operation under test is the agent's ``project.run_steward`` admission,
stepped by hand: submit -> approve -> claim -> receipt.

* frozen at admission: the grant id and its terms hash (the expiry inside);
* revoke, expiry and a re-grant between admission and approval, between
  approval and the claim, and after the claim's check (this one lands once;
  the next is refused, never under G2 for the older operation);
* the codes in Phase 7's order; one LIVE grant per (agent, project);
* a grant on another project or to another agent authorises nothing;
* every refusal leaves its receipt; nothing waits.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel import project as rooms
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import project_delegation, project_kernel
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
AGENT = Principal(PrincipalKind.AGENT, "agent-a")
AGENT_B = Principal(PrincipalKind.AGENT, "agent-b")
NODE = Principal(PrincipalKind.NODE, rooms.PROJECT_EXECUTOR)


class Rig:
    def __init__(self, database: Database, broker: Any, now: list[float]) -> None:
        self.db, self.broker, self.now = database, broker, now
        projects = ProjectService(database)
        made = [projects.create_project(OWNER, name=name) for name in ("Payments ledger cutover", "Hiring loop")]
        self.pid, self.pid_b = [str((m.get("project") or m)["id"]) for m in made]

    def grant(self, identity: str = "agent-a", pid: str | None = None, **body: Any) -> dict[str, Any]:
        return project_delegation.grant(OWNER, identity, pid or self.pid, body, database=self.db)

    def revoke(self, identity: str = "agent-a", pid: str | None = None) -> dict[str, Any]:
        return project_delegation.revoke(OWNER, identity, pid or self.pid, database=self.db)

    def row(self, grant_id: str) -> dict[str, Any]:
        with self.db._connection() as conn:
            return dict(conn.execute("SELECT * FROM kernel_project_delegations WHERE id=?", (grant_id,)).fetchone())

    def submit(self, principal: Principal = AGENT, pid: str | None = None) -> dict[str, Any]:
        native_id = str(uuid.uuid4())
        payload = {"project_id": pid or self.pid}
        raw = project_kernel._raw("project.run_steward", native_id, f"project.run_steward:{native_id}",
                                  f"project:{pid or self.pid}", payload, "")
        with rooms.project_path():
            handle = self.broker.submit(raw, principal)
        handle["native_id"] = native_id
        return handle

    def decide(self, handle: dict[str, Any], principal: Principal = AGENT) -> dict[str, Any]:
        with rooms.project_path():
            return self.broker.decide(handle["operation_id"], "approve", int(handle["revision"]), principal)

    def claim(self, handle: dict[str, Any]) -> dict[str, Any]:
        with rooms.project_path():
            return self.broker.claim(NODE, handle["native_id"])

    def execute(self, handle: dict[str, Any]) -> dict[str, Any]:
        return self.broker.receipt(handle["operation_id"], "succeeded", f"project:{self.pid}", NODE)

    def operation(self, operation_id: str) -> dict[str, Any]:
        return self.broker.store.operation(operation_id)

    def receipt(self, operation_id: str) -> dict[str, Any] | None:
        return self.broker.store.receipt(operation_id)

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


def test_an_agents_run_under_its_grant_names_the_grant_and_the_terms_carry_the_project(rig: Rig) -> None:
    g1 = rig.grant()
    handle = rig.submit()
    rig.decide(handle)
    assert rig.claim(handle)["operations"]
    receipt = rig.execute(handle)
    assert receipt["state"] == "succeeded"
    assert receipt["authority_basis"] == f"project-delegation:{g1['grant_id']}:{_sha(g1, rig)}"
    assert (receipt["delegator_kind"], receipt["delegator_identity"]) == ("owner", "owner-session")
    row = rig.row(g1["grant_id"])
    assert (row["agent_identity"], row["project_id"], row["state"]) == ("agent-a", rig.pid, "LIVE")
    assert sorted(__import__("json").loads(row["operations_json"])) == sorted(rooms.PROJECT_GRANT_OPERATIONS)
    assert row["grant_operation_id"] == g1["operation_id"]


def test_the_expiry_and_the_project_are_inside_the_hash(rig: Rig) -> None:
    terms = rooms.terms_for("agent-a", rig.pid)
    assert rooms.terms_sha256(terms, 2_000.0) != rooms.terms_sha256(terms, None)
    assert rooms.terms_sha256(terms, None) != rooms.terms_sha256(rooms.terms_for("agent-a", rig.pid_b), None)
    g1 = rig.grant(expires_at=2_000.0)
    assert _sha(g1, rig) == rooms.terms_sha256(terms, 2_000.0)


def test_a_regrant_before_approval_never_approves_the_older_operation(rig: Rig) -> None:
    g1 = rig.grant()
    handle = rig.submit()
    g2 = rig.grant()
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.reason == "project_delegation_revoked"
    assert refused.value.receipt["authority_basis"].split(":", 2)[1] == g1["grant_id"]
    assert g2["grant_id"] not in rig.operation(handle["operation_id"])["authority_basis"]
    assert rig.row(g1["grant_id"])["revocation_reason"] == "reapproved" and rig.waiting() == 0


@pytest.mark.parametrize("change, code", [
    ("revoke", "project_delegation_revoked"), ("expire", "project_delegation_expired"),
])
def test_a_change_between_admission_and_approval_refuses_the_approval(rig: Rig, change: str, code: str) -> None:
    g1 = rig.grant(expires_at=1_050.0 if change == "expire" else None)
    handle = rig.submit()
    if change == "revoke":
        rig.revoke()
    else:
        rig.now[0] = 1_100.0
    with pytest.raises(KernelRefused) as refused:
        rig.decide(handle)
    assert refused.value.reason == code
    assert rig.operation(handle["operation_id"])["state"] == "refused"
    assert rig.receipt(handle["operation_id"])["outcome"] == code and rig.waiting() == 0
    if change == "expire":
        assert rig.row(g1["grant_id"])["state"] == "EXPIRED", "an authoritative check persists the expiry"


@pytest.mark.parametrize("change, code", [
    ("revoke", "project_delegation_revoked"), ("expire", "project_delegation_expired"),
    ("regrant", "project_delegation_revoked"),
])
def test_a_change_between_approval_and_the_claim_refuses_the_claim(rig: Rig, change: str, code: str) -> None:
    rig.grant(expires_at=1_010.0 if change == "expire" else None)
    handle = rig.submit()
    rig.decide(handle)
    if change == "revoke":
        rig.revoke()
    elif change == "expire":
        rig.now[0] = 1_020.0
    else:
        rig.grant()
    claimed = rig.claim(handle)
    assert claimed["operations"] == [] and claimed["refusal"]["outcome"] == code
    assert rig.operation(handle["operation_id"])["state"] == "refused"


@pytest.mark.parametrize("change, next_code", [
    ("revoke", "project_delegation_revoked"), ("expire", "project_delegation_expired"), ("regrant", ""),
])
def test_a_change_after_the_claims_check_lets_this_one_land_once_and_refuses_the_next(
    rig: Rig, change: str, next_code: str,
) -> None:
    g1 = rig.grant(expires_at=1_050.0 if change == "expire" else None)
    handle = rig.submit()
    rig.decide(handle)
    assert rig.claim(handle)["operations"]
    g2: dict[str, Any] = {}
    if change == "revoke":
        rig.revoke()
    elif change == "expire":
        rig.now[0] = 1_060.0
    else:
        g2 = rig.grant()
    receipt = rig.execute(handle)
    assert receipt["state"] == "succeeded" and receipt["authority_basis"].split(":", 2)[1] == g1["grant_id"]
    later = rig.submit()
    if next_code:
        assert rig.receipt(later["operation_id"])["outcome"] == next_code
    else:  # the next valid call runs under G2
        assert rig.operation(later["operation_id"])["authority_basis"].split(":", 2)[1] == g2["grant_id"]


def test_the_admission_codes_follow_the_history_in_phase_7s_order(rig: Rig) -> None:
    never = rig.submit()
    assert rig.receipt(never["operation_id"])["outcome"] == "project_delegation_required"
    rig.grant()
    rig.revoke()
    stopped = rig.submit()
    assert rig.receipt(stopped["operation_id"])["outcome"] == "project_delegation_revoked"
    rig.grant(expires_at=1_010.0)
    rig.now[0] = 1_020.0
    lapsed = rig.submit()
    assert rig.receipt(lapsed["operation_id"])["outcome"] == "project_delegation_expired"
    assert rig.waiting() == 0


def test_a_grant_on_another_project_or_to_another_agent_authorises_nothing_here(rig: Rig) -> None:
    rig.grant(pid=rig.pid_b)
    rig.grant(identity="agent-b")
    handle = rig.submit()
    assert handle["state"] == "refused"
    assert rig.receipt(handle["operation_id"])["outcome"] == "project_delegation_required"
    # A B-grant never approves an A operation.
    other = rig.submit(AGENT_B, rig.pid_b)
    assert rig.receipt(other["operation_id"])["outcome"] == "project_delegation_required"


def test_one_live_grant_per_agent_and_project(rig: Rig) -> None:
    rig.grant()
    rig.grant()
    rig.grant(pid=rig.pid_b)
    with rig.db._connection() as conn:
        live = conn.execute("SELECT agent_identity, project_id FROM kernel_project_delegations WHERE state='LIVE' "
                            "ORDER BY project_id").fetchall()
        assert sorted(tuple(r) for r in live) == sorted([("agent-a", rig.pid), ("agent-a", rig.pid_b)])
        with pytest.raises(Exception):
            conn.execute("UPDATE kernel_project_delegations SET state='LIVE' WHERE project_id=?", (rig.pid,))


def test_the_projection_says_what_the_kernel_would_answer(rig: Rig) -> None:
    """The chip is ALLOWED iff the kernel admits (Phase 7 F15, per project)."""
    views = lambda: project_delegation.views(["agent-a"], database=rig.db, now=rig.now[0])["by_identity"]["agent-a"]  # noqa: E731
    assert views() == []
    rig.grant(expires_at=1_050.0)
    assert [v["state"] for v in views()] == ["LIVE"] and rig.submit()["state"] != "refused"
    rig.now[0] = 1_060.0
    assert [v["state"] for v in views()] == ["EXPIRED"]
    assert rig.receipt(rig.submit()["operation_id"])["outcome"] == "project_delegation_expired"


# ── merged from tests/unit/test_philo9_project_grant_restart.py (fast diet, by service) ────────

"""PHILO-9-07 A7: a LIVE project grant survives a REAL hub restart and a credential reissue.

A hub is a PROCESS here (Phase 7's F13 rig, ``test_philo7_grant_restart.py``):
the credential store is a module singleton, so only a new process is a real
restart. The fence boots the real ``MeetingWebServer`` in a child process over
an isolated HOME, grants G1 on one project through the real route, kills the
process (SIGKILL), boots a NEW process on the same database, issues a new
PROJECT credential for the same identity through the real Settings route, and
publishes a draft over ``/api/mcp`` under G1.

Conductor R2 (credentials persist, hashed): a restart keeps exactly the
same access. The first credential is still live after the restart and still
names G1, so G1 is no orphan; the reissue replaces that credential (the old
token is refused) and the new one names G1. Before R2 the first credential
died with the process and G1 showed as an orphan: that was the in-memory
accident, not the ruling.

Red on main: the grant route is a 404, and the agent's publish succeeds with
no operation and no receipt.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo7_grant_restart import AGENT_ID, HubProcess  # noqa: E402


@pytest.mark.timeout(300)
def test_a_live_project_grant_survives_a_real_restart_and_a_reissue(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    first = HubProcess(home)
    try:
        status, project = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        assert status in (200, 201), project
        pid = project["project"]["id"]
        status, update = first.call("POST", f"/api/projects/{pid}/updates/draft", {})
        update_id = update["update"]["id"]
        status, granted = first.call("PUT", f"/api/settings/remote/delegations/{AGENT_ID}/projects/{pid}", {})
        assert status == 200, granted
        g1 = granted["grant_id"]
        old_token = first.credential()
    finally:
        first.kill()

    second = HubProcess(home)
    try:
        # Conductor R2: the old credential lives through the restart, the same
        # access and no more: it still names G1, so there is no orphan.
        assert second.call("PUT", "/api/settings/remote", {"enabled": True})[0] == 200
        ledger = second.call("GET", "/api/settings/remote")[1]
        assert ledger["project_delegations"] == []
        [old] = ledger["credentials"]
        assert old["palette"] == "DESK"
        assert [(g["project_id"], g["state"], g["grant_id"]) for g in old["project_delegations"]] == [(pid, "LIVE", g1)]
        # A new credential for the same identity: the grant is its own again.
        status, issued = second.call("POST", "/api/settings/remote/credentials",
                                     {"identity": AGENT_ID, "palette": "PROJECT"})
        assert status == 200, issued
        is_error, published = second.tool(issued["token"], "project.publish_update", {"update_id": update_id})
        assert is_error is False, published
        status, receipt = second.call("GET", f"/api/kernel/read?refs=operation:{published['operation_id']}&view=receipt")
        assert status == 200, receipt
        assert receipt["objects"][0]["receipt"]["authority_basis"].split(":", 2)[1] == g1
        ledger = second.call("GET", "/api/settings/remote")[1]
        assert ledger["project_delegations"] == []
        [cred] = ledger["credentials"]
        assert [(g["project_id"], g["state"], g["grant_id"]) for g in cred["project_delegations"]] == [(pid, "LIVE", g1)]
        assert cred["palette"] == "PROJECT" and cred["id"] != old["id"]
        # The reissue replaced the old credential: its token is refused.
        assert second.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                           token=old_token)[0] == 401
    finally:
        second.kill()


# ── merged from tests/unit/test_philo9_project_grant_face_rule.py (fast diet, by service) ────────

"""PHILO-9-07: the face's palette rule matches the palettes the hub resolves.

The ratified canvas settles it as a correctness rule: a grant's controls show
only where the credential's ISSUED palette holds the tools that grant covers.
The face declares the two palette lists (``web/src/pages/cores/SettingsCore.tsx``
``PROJECT_GRANT_PALETTES``, ``DESK_GRANT_PALETTES``); this fence derives them
from ``holdspeak.mcp.palettes.resolve_palette`` so a palette change cannot
leave a grant's verb on a credential that cannot use it, or hide it from one
that can.
"""

import re
from pathlib import Path

from holdspeak.kernel.desk import DESK_GRANT_OPERATIONS
from holdspeak.kernel.project import PROJECT_GRANT_OPERATIONS
from holdspeak.mcp.palettes import PALETTE_NAMES, resolve_palette

SOURCE = Path(__file__).resolve().parents[2] / "web" / "src" / "pages" / "cores" / "SettingsCore.tsx"


def _declared(name: str) -> list[str]:
    match = re.search(rf"export const {name} = \[([^\]]*)\] as const;", SOURCE.read_text(encoding="utf-8"))
    assert match, f"{name} is not declared by the face"
    return re.findall(r'"([A-Z]+)"', match.group(1))


#: The desk family the desk grant covers (the canvas: desk.*, zone.*, decision.*, note.*, kb.*).
DESK_FAMILY = ("desk.", "zone.", "decision.", "note.", "kb.")


def test_the_project_palettes_are_exactly_those_holding_the_bound() -> None:
    holding = [p for p in PALETTE_NAMES if set(PROJECT_GRANT_OPERATIONS) <= resolve_palette(p)]
    assert _declared("PROJECT_GRANT_PALETTES") == holding


def test_the_desk_palettes_are_exactly_those_holding_the_desk_writes() -> None:
    holding = [p for p in PALETTE_NAMES if any(t.startswith(DESK_FAMILY) for t in resolve_palette(p))]
    assert _declared("DESK_GRANT_PALETTES") == holding
    assert {name.split(".")[0] + "." for name in DESK_GRANT_OPERATIONS} <= set(DESK_FAMILY)
