"""HS-131-06 local schedule delegation policy proofs."""
from __future__ import annotations
import asyncio
import pytest
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.services.schedule_delegation import ScheduleDelegationService

OWNER = Principal(PrincipalKind.OWNER, "schedule-owner")
SCHEDULER = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")
AGENT = Principal(PrincipalKind.AGENT, "agent")


def _rig(tmp_path):
    db=Database(tmp_path / "schedule.db")
    profile=db.profiles.upsert(profile_id="p",name="P",kind="openAICompatible",base_url="http://profile",model="model")
    recipe=db.recipes.upsert(recipe_id="r",name="R",system_prompt="S")
    service=WorkbenchService(db)
    wb=service.create_workbench(OWNER,name="W",recipe_id=recipe.id,profile_id=profile.id,schedule="* * * * *")
    # The hub's start consumes the pointer into the automation's With line
    # (the startup migration); the schedule names that assignment.
    from holdspeak.kernel.runtime import _configure
    _configure(db)
    return db, service, wb["id"]


def _hand_rig(tmp_path):
    db = Database(tmp_path / "hand-schedule.db")
    service = WorkbenchService(db)
    wb = service.create_workbench(
        OWNER,
        name="Hand",
        do_kind="hand_to_agent",
        agent_profile="claude-default",
        review_by="claude",
        instruction="Complete the action.",
        output_target="today",
        schedule="* * * * *",
    )
    return db, service, wb["id"]


def test_owner_enable_creates_local_exact_terms_delegation(tmp_path):
    db, service, wid=_rig(tmp_path)
    service.update_workbench(OWNER,wid,schedule_enabled=True)
    row=ScheduleDelegationService(db).live(wid)
    assert row["delegator_kind"] == "owner"
    assert row["cadence"] == "* * * * *"
    assert row["deployment_revision_id"]
    assert "secret" not in str(row).lower()


def test_regular_run_instruction_edit_keeps_the_existing_schedule(tmp_path):
    db, service, wid = _rig(tmp_path)
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    approved = ScheduleDelegationService(db).live(wid)

    service.update_workbench(OWNER, wid, instruction="Write the revised team update.")

    assert db.workbenches.get(wid).schedule_enabled is True
    assert ScheduleDelegationService(db).live(wid)["id"] == approved["id"]


def test_enable_configuration_rolls_back_when_delegation_mint_fails(tmp_path, monkeypatch):
    db, service, _ = _rig(tmp_path)
    original = ScheduleDelegationService.enable_from_owner_in_transaction

    def fail_mint(*args, **kwargs):
        raise RuntimeError("simulated mint failure")

    monkeypatch.setattr(ScheduleDelegationService, "enable_from_owner_in_transaction", fail_mint)
    with pytest.raises(RuntimeError, match="simulated mint failure"):
        service.create_workbench(OWNER, name="Atomic", recipe_id="r", schedule="* * * * *", schedule_enabled=True)
    assert [wb for wb in db.workbenches.list() if wb.name == "Atomic"] == []
    monkeypatch.setattr(ScheduleDelegationService, "enable_from_owner_in_transaction", original)


@pytest.mark.parametrize("change,reason", [("disabled","delegation_revoked"), ("revoked","delegation_revoked"), ("expired","delegation_expired")])
def test_due_tick_refuses_revoked_or_expired_delegation_before_provider(tmp_path, change, reason):
    db, service, wid=_rig(tmp_path); service.update_workbench(OWNER,wid,schedule_enabled=True)
    if change == "disabled": service.update_workbench(OWNER,wid,schedule_enabled=False)
    elif change == "revoked": ScheduleDelegationService(db).revoke(wid, "test")
    elif change == "expired":
        with db._connection() as conn: conn.execute("UPDATE kernel_schedule_delegations SET expires_at=0 WHERE workbench_id=?",(wid,))
    # The failed due tick is an attempt with a terminal receipt, not merely an
    # exception before the provider layer.
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_service import WorkbenchService
    broker = _configure(db)
    with pytest.raises(ServiceError) as tick:
        asyncio.run(WorkbenchService(db).run_scheduled(SCHEDULER, wid, due_minute=1000))
    assert tick.value.code == reason
    with db._connection() as conn:
        operation_id = conn.execute("SELECT operation_id FROM kernel_receipts ORDER BY created_at DESC LIMIT 1").fetchone()[0]
    receipt = broker.store.receipt(operation_id)
    assert (receipt["state"], receipt["outcome"]) == ("refused", reason)


def test_bound_edit_revokes_and_requires_owner_reenable(tmp_path):
    db, service, wid=_rig(tmp_path); service.update_workbench(OWNER,wid,schedule_enabled=True)
    old=ScheduleDelegationService(db).live(wid)["id"]
    service.update_workbench(OWNER,wid,schedule="0 * * * *")
    assert ScheduleDelegationService(db).live(wid) is None
    with db._connection() as conn:
        state=conn.execute("SELECT state FROM kernel_schedule_delegations WHERE id=?",(old,)).fetchone()[0]
    assert state == "REVOKED"
    service.update_workbench(OWNER,wid,schedule_enabled=False); service.update_workbench(OWNER,wid,schedule_enabled=True)
    assert ScheduleDelegationService(db).live(wid)["id"] != old


@pytest.mark.parametrize(
    "field,value",
    [
        ("agent_profile", "codex-default"),
        ("review_by", "codex"),
        ("instruction", "Complete the action and report."),
        ("sources", ["action:one"]),
        ("output_target", "needs_you"),
    ],
)
def test_hand_binding_edit_fences_live_authority_until_when_reapproval(tmp_path, field, value):
    db, service, wid = _hand_rig(tmp_path)
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    old = ScheduleDelegationService(db).live(wid)["id"]

    service.update_workbench(OWNER, wid, **{field: value})

    edited = db.workbenches.get(wid)
    assert edited.schedule_enabled is False
    assert ScheduleDelegationService(db).live(wid) is None
    with db._connection() as conn:
        state = conn.execute(
            "SELECT state FROM kernel_schedule_delegations WHERE id=?", (old,)
        ).fetchone()["state"]
    assert state == "REVOKED"

    service.update_workbench(OWNER, wid, schedule_enabled=True)
    assert ScheduleDelegationService(db).live(wid)["id"] != old


def test_synced_enabled_schedule_refuses_delegation_missing(tmp_path):
    db, _, wid=_rig(tmp_path)
    with db._connection() as conn: conn.execute("UPDATE workbenches SET schedule_enabled=1 WHERE id=?",(wid,))
    with pytest.raises(ServiceError) as raised: ScheduleDelegationService(db).validate(wid)
    assert raised.value.code == "delegation_missing"


def test_refused_tick_stamps_delegation_provenance_atomically(tmp_path):
    db, service, wid = _rig(tmp_path)
    service.update_workbench(OWNER, wid, schedule_enabled=True)
    delegation = ScheduleDelegationService(db).live(wid)
    ScheduleDelegationService(db).revoke(wid, "owner revoked")
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.workbench_service import WorkbenchService
    broker = _configure(db)
    with pytest.raises(ServiceError) as refused:
        asyncio.run(WorkbenchService(db).run_scheduled(SCHEDULER, wid, due_minute=4321))
    assert refused.value.code == "delegation_revoked"
    with db._connection() as conn:
        operation = dict(conn.execute("SELECT * FROM kernel_operations WHERE state='refused' ORDER BY created_at DESC LIMIT 1").fetchone())
    receipt = broker.store.receipt(operation["operation_id"])
    basis = f"schedule-delegation:{delegation['id']}:{delegation['terms_sha256']}"
    assert (operation["delegator_kind"], operation["delegator_identity"], operation["authority_basis"], operation["target_ref"]) == ("owner", OWNER.identity, basis, f"deployment:{delegation['deployment_revision_id']}")
    assert (receipt["delegator_kind"], receipt["delegator_identity"], receipt["authority_basis"], receipt["target_ref"]) == ("owner", OWNER.identity, basis, f"deployment:{delegation['deployment_revision_id']}")
    # A genuinely missing delegation has no invented provenance.
    clean, _, clean_wid = _rig(tmp_path / "missing")
    with clean._connection() as conn:
        conn.execute("UPDATE workbenches SET schedule_enabled=1 WHERE id=?", (clean_wid,))
    _configure(clean)
    with pytest.raises(ServiceError) as missing_refusal:
        asyncio.run(WorkbenchService(clean).run_scheduled(SCHEDULER, clean_wid, due_minute=4322))
    assert missing_refusal.value.code == "delegation_missing"
    with clean._connection() as conn:
        missing = dict(conn.execute("SELECT * FROM kernel_operations WHERE state='refused' ORDER BY created_at DESC LIMIT 1").fetchone())
    assert (missing["delegator_kind"], missing["delegator_identity"]) == ("", "")


def test_scheduler_or_agent_cannot_mint_or_reactivate_delegation(tmp_path):
    db, service, wid=_rig(tmp_path)
    wb=db.workbenches.get(wid)
    for principal in (SCHEDULER, AGENT):
        with pytest.raises(ServiceError) as raised: ScheduleDelegationService(db).enable_from_owner(principal, wb)
        assert raised.value.code == "owner_principal_required"
