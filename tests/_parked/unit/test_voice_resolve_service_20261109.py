"""PARKED 20261109 (lane door/rest-park-waist) from tests/unit/test_voice_resolve.py: WorkbenchService.resolve_voice is parked (no product caller).
Not collected (tests/_parked/conftest.py). Restore with git revert.
"""
from __future__ import annotations
import json
from typing import Any
import pytest
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.voice_resolver import (
    MAX_REFS,
    MAX_TRANSCRIPT_CHARS,
    MAX_ZONES,
    ResolverResult,
    ZoneCatalogEntry,
    _extract_json_from_response,
    _validate_response,
    build_resolver_prompt,
    build_retry_prompt,
    format_zone_catalog,
    resolve_voice_references,
    truncate_transcript,
)


def _admitted_voice_rig(tmp_path):
    db = Database(tmp_path / "voice.db")
    profile = db.profiles.upsert(
        profile_id="resolver", name="Resolver", kind="openAICompatible",
        base_url="http://resolver", model="resolver-model",
    )
    service = WorkbenchService(db)
    workbench = service.create_workbench(
        OWNER, name="Voice", resolver_profile_id=profile.id,
    )
    db.directories.upsert(directory_id="zone-a", name="Alpha")
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    service._kernel = broker
    return db, service, broker, workbench["id"]


def test_service_parse_failure_has_one_controller_owned_attempt(tmp_path):
    db, service, broker, workbench_id = _admitted_voice_rig(tmp_path)

    class FakeIntel:
        calls = 0
        def run_prompt(self, **_):
            self.calls += 1
            return "not json" if self.calls == 1 else '{"zone_ids":["zone-a"]}'

    fake_intel = FakeIntel()
    broker.inference_runner._engine_factory = lambda _revision, **_kw: fake_intel
    observed_ordinals = []
    invoke = broker.inference_runner.invoke
    def record_attempt(request, *args, **kwargs):
        observed_ordinals.append(request.attempt_ordinal)
        return invoke(request, *args, **kwargs)
    broker.inference_runner.invoke = record_attempt
    result = service.resolve_voice(OWNER, workbench_id, "find Alpha", "voice-retry")

    assert result["error"] == "resolver_parse_failure"
    assert result["attempts"] == 1
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='voice_reference_resolve'"
        ).fetchone()[0]
        children = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?",
            (parent,),
        ).fetchall()
    assert len(children) == 1
    assert observed_ordinals == [1]


def test_service_refuses_missing_principal_before_child_admission(tmp_path):
    db, service, _, workbench_id = _admitted_voice_rig(tmp_path)

    with pytest.raises(ServiceError) as refused:
        service.resolve_voice(Principal(PrincipalKind.NONE, ""), workbench_id, "find Alpha", "voice-none")

    assert refused.value.code == "resolver_principal_required"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations").fetchone()[0] == 0


@pytest.mark.parametrize("order", ["parent_closes_first", "signal_first"])
def test_service_deadline_cancellation_returns_timeout_and_closes_parent(tmp_path, monkeypatch, order):
    from tests._cancel_after_return import assert_provider_return_on_record, force_cancel_order

    force_cancel_order(monkeypatch, order)
    db, service, broker, workbench_id = _admitted_voice_rig(tmp_path)

    class CancellingIntel:
        def run_prompt(self, **_):
            with db._connection() as conn:
                parent_id = conn.execute(
                    "SELECT operation_id FROM kernel_parent_runs WHERE kind='voice_reference_resolve'"
                ).fetchone()[0]
            broker.parent_run_controller.cancel_by_operation_id(OWNER, parent_id)
            return '{"zone_ids":["zone-a"]}'

    broker.inference_runner._engine_factory = lambda _revision, **_kw: CancellingIntel()
    result = service.resolve_voice(OWNER, workbench_id, "find Alpha", "voice-cancel")

    assert result["error"] == "resolver_cancelled"
    with db._connection() as conn:
        parent = conn.execute(
            "SELECT operation_id,state FROM kernel_parent_runs WHERE kind='voice_reference_resolve'"
        ).fetchone()
    receipt = broker.store.receipt(parent[0])
    assert parent[1] == "CANCELLED"
    assert receipt is not None and receipt["outcome"] == "cancelled"
    with db._connection() as conn:
        child_id = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE parent_operation_id=? AND name='inference.invoke'",
            (parent[0],),
        ).fetchone()[0]
    # The provider returned in both orders and the receipt says so; with the
    # signal first its result is fenced.
    assert_provider_return_on_record(db, child_id, fenced=order == "signal_first")


