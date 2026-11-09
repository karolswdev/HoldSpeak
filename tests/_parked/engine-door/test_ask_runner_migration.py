# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; the placement-based Ask path (a named target, the frozen placement claim, the v1 contract) is gone.
# Moved from tests/unit/test_ask_runner_migration.py; its helpers are still there.

from tests.unit.test_ask_runner_migration import *  # noqa: F401,F403


def test_ask_uses_versioned_contract_hash_runner_and_staged_projection(rig):
    db, broker, engine = rig
    service = AskService(db, broker=broker)
    before_artifacts = len(db.plugins.list_run_artifacts())
    result = asyncio.run(service.ask(OWNER, "What changed?", lens="Brief", operation_capability=CLASSIC))
    assert result["output"] == "runner answer"
    assert result["provider"] == "test-provider"
    assert len(engine.calls) == 1
    with db._connection() as conn:
        stage = conn.execute("SELECT * FROM kernel_projection_stages").fetchone()
        ask = conn.execute("SELECT * FROM ask_results").fetchone()
        operation = conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (stage["operation_id"],)).fetchone()
        receipt = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (stage["operation_id"],)).fetchone()
    assert stage["state"] == "PUBLISHED"
    assert receipt["outcome"] == "succeeded"
    assert receipt["result_ref"] == stage["result_ref"]
    assert ask["projection_stage_id"] == stage["stage_id"]
    assert result["invocation_id"] == stage["invocation_id"]
    assert operation["native_id"] == stage["invocation_id"]
    assert ASK_SERVICE_CONTRACT == "holdspeak.ask"
    assert ASK_SERVICE_SCHEMA_VERSION == "1"
    assert ASK_PAYLOAD_SCHEMA_VERSION == 1
    assert len(db.plugins.list_run_artifacts()) == before_artifacts


def test_profile_ask_persists_revision_before_claim_without_preseed(rig, monkeypatch):
    db, broker, engine = rig
    with db._connection() as conn:
        before_revisions = conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0]
    db.profiles.upsert(profile_id="profile", name="Profile", kind="openAICompatible", base_url="http://profile", model="model")
    # Admission, codec authorization, claim, and runner revision lookup all use
    # real database reads; only the final provider adapter is fake.
    #
    # HS-131-13: through `monkeypatch`, not a bare module assignment. The bare
    # form leaked this stub into every LATER test in the process, so any suite
    # that legitimately builds a profile-shaped engine silently received Ask's
    # fake instead — an ordering landmine that only fires in a combined run.
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: engine
    )
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "profile", inference_target_id="profile", operation_capability=CLASSIC))
    assert result["output"] == "runner answer"
    with db._connection() as conn:
        # Startup may lawfully create the migrated local speech deployment;
        # this Ask still creates exactly its own frozen profile revision.
        assert conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0] == before_revisions + 1
        assert conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (result["operation_id"],)).fetchone()[0] == "succeeded"


def test_ask_cancelled_after_provider_return_publishes_and_returns_no_answer(rig, monkeypatch):
    """A direct cancel of the Ask child lands while the provider is in flight.

    The provider then returns. The receipt records the return; the late answer
    is not staged, not published and not returned to the caller.
    """
    from tests._cancel_after_return import (
        SIGNAL_FIRST, assert_provider_return_on_record, cancel_child_in_flight,
        force_cancel_order, invoke_child_operation_id,
    )

    db, broker, engine = rig
    service = AskService(db, broker=broker)
    settled = force_cancel_order(monkeypatch, SIGNAL_FIRST)
    seen: list[str] = []

    def run_prompt(**_kwargs):
        seen.append(cancel_child_in_flight(db, settled, lambda iid: service.cancel(OWNER, iid)))
        return "late answer"

    monkeypatch.setattr(engine, "run_prompt", run_prompt)
    try:
        answer: object = asyncio.run(service.ask(OWNER, "What changed?", lens="Brief", operation_capability=CLASSIC))
    except Exception as exc:  # noqa: BLE001 - the refusal is the answer here
        answer = exc
    assert len(seen) == 1
    assert "late answer" not in repr(answer)
    assert isinstance(answer, Exception), answer
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_projection_stages").fetchone()[0] == 0
    assert_provider_return_on_record(db, invoke_child_operation_id(db, seen[0]), fenced=True)
