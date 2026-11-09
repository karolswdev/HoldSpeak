"""Story-07 production adopter, composite, and next-run laws."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter
from holdspeak.kernel.provider_signals import ProviderPermanentNoGeneration
from holdspeak.kernel.runtime import _configure
from holdspeak.services.ask_service import _AskAnswerAdapter
from holdspeak.services.inference_adoption_service import (
    ProductionInferenceAdoptionService,
    ProductionRouteEvidence,
)
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.errors import ConflictError
from holdspeak.services.inference_route_plan_service import InferenceRoutePlanService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim
from tests.unit.test_engines_route_plans import _ready_route


def _payload(text: str = "hello") -> dict[str, Any]:
    return {
        "system_prompt": "Be concise.",
        "user_prompt": text,
        "temperature": 0.0,
        "max_tokens": 64,
    }


def test_production_evidence_claims_meeting_and_speech_routes_without_ambiguity(
    tmp_path: Path,
) -> None:
    """The shared provider owns every Phase-B route and rejects a duplicate claim."""
    provider = ProductionRouteEvidence(Database(tmp_path / "meeting-evidence.db")).provider()
    claimed = {capability_id for capability_id, _revision, _sha in provider.capabilities}
    assert {
        "meeting.live_analysis",
        "meeting.bookmark_label",
        "meeting.auto_title",
        "speech.transcribe",
        "speech.preload",
    } <= claimed
    duplicate = replace(provider, id="duplicate-meeting-route-evidence")
    with pytest.raises(ValueError, match="ambiguous route admission evidence provider"):
        InferenceRoutePlanService(
            Database(tmp_path / "ambiguity.db"),
            operation_evidence_providers=(provider, duplicate),
        )


def test_production_evidence_is_bound_to_exact_resolved_legs_and_reconstructs(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "adoption.db")
    _ready_route(db, profiles=("quick", "deep"))
    service = ProductionInferenceAdoptionService(db)
    admitted = service.admit(
        OWNER,
        command_id="admit-ask-one",
        capability_id="ask.answer",
        operation_id="ask-one",
        payload=_payload(),
        reserved_output_tokens=64,
    )
    operation = admitted["operation_request_plan"]
    route = admitted["route_plan"]
    assert [entry["eligibility"] for entry in operation["entries"]] == [
        "executable",
        "executable",
    ]
    with db._connection() as conn:
        evidence = service.evidence._evidence(conn, operation["admission_evidence_ref"])
    assert evidence["route_plan_sha256"] == route["sha256"]
    assert [
        item["serialized_request"]["deployment_revision"]
        for item in evidence["serialized_requests"]
    ] == [entry["deployment_revision_id"] for entry in route["entries"]]
    assert all(
        item["total_tokens"]
        == item["input_tokens"] + item["reserved_output_tokens"]
        for item in evidence["budgets"]
    )


def test_assignment_edit_after_admission_never_retargets_execution(tmp_path: Path) -> None:
    db = Database(tmp_path / "freeze-race.db")
    _ready_route(db, profiles=("quick", "deep"))
    service = ProductionInferenceAdoptionService(db)
    admitted = service.admit(
        OWNER,
        command_id="freeze-before-edit",
        capability_id="ask.answer",
        operation_id="ask-freeze-race",
        payload=_payload(),
    )
    old_ids = [item["deployment_revision_id"] for item in admitted["route_plan"]["entries"]]
    assignment = InferenceAssignmentService(db).resolve_effective(
        OWNER, capability_id="ask.answer"
    )
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "edit-after-freeze",
            "expected_revision": assignment["assignment"]["revision"],
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "deep", "profile_revision": 1}],
        },
    )
    reconstructed = service.plans.get_route_plan(
        OWNER, admitted["route_plan"]["id"]
    )
    assert [item["deployment_revision_id"] for item in reconstructed["entries"]] == old_ids


def test_recomputed_evidence_hash_cannot_change_dispatched_bytes(tmp_path: Path) -> None:
    db = Database(tmp_path / "hostile-evidence.db")
    _ready_route(db, profiles=("quick",))
    service = ProductionInferenceAdoptionService(db)
    admitted = service.admit(
        OWNER, command_id="hostile-admit", capability_id="ask.answer",
        operation_id="hostile-operation", payload=_payload(),
    )
    evidence_ref = admitted["operation_request_plan"]["admission_evidence_ref"]
    with db._connection() as conn:
        row = conn.execute(
            "SELECT evidence_json FROM inference_adoption_route_evidence WHERE evidence_ref=?",
            (evidence_ref,),
        ).fetchone()
        evidence = json.loads(str(row["evidence_json"]))
        evidence["serialized_requests"][0]["serialized_request"]["payload"]["user_prompt"] = "retargeted"
        conn.execute("DROP TRIGGER inference_adoption_route_evidence_no_update")
        conn.execute(
            "UPDATE inference_adoption_route_evidence SET evidence_json=?,evidence_sha256=? WHERE evidence_ref=?",
            (
                json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
                "sha256:" + hashlib.sha256(
                    json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
                ).hexdigest(),
                evidence_ref,
            ),
        )
    with pytest.raises(ConflictError) as refused:
        service.evidence.serialized_request(evidence_ref, 1)
    assert refused.value.code == "inference_adoption_evidence_invalid"
    evidence = json.loads(str(row["evidence_json"]))
    evidence["serialized_requests"][0]["context_plan"]["invented"] = True
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_adoption_route_evidence SET evidence_json=?,evidence_sha256=? WHERE evidence_ref=?",
            (encoded, "sha256:" + hashlib.sha256(encoded.encode()).hexdigest(), evidence_ref),
        )
    with pytest.raises(ConflictError) as nested:
        service.evidence.serialized_request(evidence_ref, 1)
    assert nested.value.code == "inference_adoption_evidence_invalid"
    evidence = json.loads(str(row["evidence_json"]))
    context = evidence["serialized_requests"][0]["context_plan"]
    context["input_tokens"] += 1
    context_sha = "sha256:" + hashlib.sha256(
        json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    evidence["entries"][0]["context_plan_sha256"] = context_sha
    evidence["budgets"][0]["context_plan_sha256"] = context_sha
    evidence["budgets"][0]["input_tokens"] += 1
    evidence["budgets"][0]["total_tokens"] += 1
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    with db._connection() as conn:
        conn.execute(
            "UPDATE inference_adoption_route_evidence SET evidence_json=?,evidence_sha256=? WHERE evidence_ref=?",
            (encoded, "sha256:" + hashlib.sha256(encoded.encode()).hexdigest(), evidence_ref),
        )
    with pytest.raises(ConflictError) as semantic:
        service.evidence.serialized_request(evidence_ref, 1)
    assert semantic.value.code == "inference_adoption_evidence_invalid"


def test_controller_executes_real_fallback_and_receipts_winning_boundary(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "fallback.db")
    _ready_route(db, profiles=("quick", "deep"))
    broker = _configure(db)
    revisions: list[str] = []

    class Engine:
        active_provider = "fixture"
        active_model = "fixture-model"

        def __init__(self, revision: str) -> None:
            self.revision = revision

        def run_prompt(self, **_kwargs: Any) -> str:
            revisions.append(self.revision)
            if len(revisions) == 1:
                raise ProviderPermanentNoGeneration()
            return "fallback won"

    broker.inference_runner._engine_factory = lambda revision, **_kwargs: Engine(revision.id)
    service = broker.inference_adoption_service
    admitted = service.admit(
        OWNER,
        command_id="admit-fallback",
        capability_id="ask.answer",
        operation_id="ask-fallback",
        payload=_payload(),
    )
    result = service.execute(
        OWNER,
        execution_id=admitted["execution"]["id"],
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
    )
    assert result["result"]["output"] == "fallback won"
    assert [item["purpose"] for item in result["receipt"]["attempts"]] == [
        "primary",
        "fallback",
    ]
    assert result["receipt"]["winning_deployment_revision_id"] == revisions[-1]
    assert result["receipt"]["winning_boundary"] == "local"
    replay = service.execute(
        OWNER, execution_id=admitted["execution"]["id"],
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
    )
    assert replay["result"] == result["result"]
    assert replay["winning_reservation"]["id"] == result["winning_reservation"]["attempt_id"]
    forged = {"output": "forged winner"}
    with db._connection() as conn:
        conn.execute("DROP TRIGGER inference_adoption_attempt_results_no_update")
        conn.execute(
            "UPDATE inference_adoption_attempt_results SET result_json=?,result_sha256=? WHERE attempt_id=?",
            (
                json.dumps(forged, sort_keys=True, separators=(",", ":")),
                "sha256:" + hashlib.sha256(
                    json.dumps(forged, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
                result["winning_reservation"]["attempt_id"],
            ),
        )
    with pytest.raises(ConflictError) as cross_bound:
        service.execute(
            OWNER,
            execution_id=admitted["execution"]["id"],
            adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
        )
    assert cross_bound.value.code == "inference_adoption_result_integrity_invalid"


def test_routed_stop_fences_controller_before_signalling_exact_child(tmp_path: Path) -> None:
    db = Database(tmp_path / "stop.db")
    _ready_route(db, profiles=("quick", "deep"))
    broker = _configure(db)
    entered, release = threading.Event(), threading.Event()

    class Adapter:
        connector_id = "fixture"

        @staticmethod
        def dispatch(_engine: Any, _payload: dict[str, Any], cancellation: Any) -> dict[str, str]:
            entered.set()
            while not cancellation.is_set() and not release.wait(0.01):
                pass
            return {"output": "late", "provider": "fixture", "model": "fixture"}

        @staticmethod
        def cancel() -> str:
            release.set()
            return "cancelled"

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    coordinator = broker.inference_adoption_service
    admitted = coordinator.admit(
        OWNER,
        command_id="admit-stop",
        capability_id="ask.answer",
        operation_id="ask-stop",
        payload=_payload(),
    )
    original_cancel = broker.inference_runner.cancel

    def fenced_cancel(invocation_id: str) -> str:
        with db._connection() as conn:
            state = conn.execute(
                "SELECT state FROM inference_route_executions WHERE id=?",
                (admitted["execution"]["id"],),
            ).fetchone()["state"]
        assert str(state) == "stopping"
        return original_cancel(invocation_id)

    broker.inference_runner.cancel = fenced_cancel
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            coordinator.execute,
            OWNER,
            execution_id=admitted["execution"]["id"],
            adapter=Adapter(),
        )
        assert entered.wait(2)
        stopped = coordinator.stop(
            OWNER,
            command_id="stop-route",
            execution_id=admitted["execution"]["id"],
        )
        release.set()
        result = future.result(timeout=3)
    assert stopped["child_signal"] in {"cancelled", "pending"}
    assert result["receipt"]["outcome"] == "cancelled"
    assert len(result["receipt"]["attempts"]) == 1


def test_composite_is_published_only_after_every_operation_freezes(tmp_path: Path) -> None:
    db = Database(tmp_path / "composite.db")
    _ready_route(db, profiles=("quick",))
    service = ProductionInferenceAdoptionService(db)
    with pytest.raises(Exception):
        service.admit_composite(
            OWNER,
            command_id="speech-composite",
            operations=[
                {
                    "capability_id": "ask.answer",
                    "operation_id": "composite-good",
                    "payload": _payload(),
                },
                {
                    "capability_id": "speech.rewrite",
                    "operation_id": "composite-no-assignment",
                    "payload": _payload("rewrite"),
                },
            ],
        )
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_adoption_composites"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_adoption_material_snapshots"
        ).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_executions").fetchone()[0] == 0





def test_material_and_evidence_are_local_only_and_immutable(tmp_path: Path) -> None:
    db = Database(tmp_path / "private.db")
    _ready_route(db, profiles=("quick",))
    service = ProductionInferenceAdoptionService(db)
    admitted = service.admit(
        OWNER,
        command_id="private-adoption",
        capability_id="ask.answer",
        operation_id="private-operation",
        payload=_payload("SECRET MATERIAL"),
    )
    with db._connection() as conn:
        with pytest.raises(Exception):
            conn.execute(
                "UPDATE inference_adoption_material_snapshots SET payload_json='{}'"
            )
        with pytest.raises(Exception):
            conn.execute("DELETE FROM inference_adoption_route_evidence")
        route_payload = conn.execute(
            "SELECT payload_json FROM inference_route_plans WHERE id=?",
            (admitted["route_plan"]["id"],),
        ).fetchone()[0]
    assert "SECRET MATERIAL" not in route_payload


def test_thought_contract_is_the_actual_closed_question_or_synthesis_union() -> None:
    from holdspeak.inference_capabilities import (
        InferenceCapabilityRegistryError,
        process_inference_capability_registry,
    )

    capability = process_inference_capability_registry().require("thought.interview")
    assert capability.revision == 2
    capability.validate_result(
        {"kind": "question", "question": "Who owns this?", "reason": "Clarify ownership."}
    )
    capability.validate_result(
        {"kind": "synthesis", "title": "Plan", "body_markdown": "Ship it.", "tags": ["launch"]}
    )
    with pytest.raises(InferenceCapabilityRegistryError):
        capability.validate_result(
            {"branch": "next_question", "question": "old", "synthesis": None}
        )


def test_config_migration_is_one_way_and_builtin_sentinel_nominates_one_repair(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "migration.db")
    service = ProductionInferenceAdoptionService(db)
    missing = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id=None),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id=None)),
    )
    issue = service.migrate_legacy_config(OWNER, missing)
    assert (issue["reason_code"], issue["repair"]) == (
        "builtin_profile_required", "choose_model_profile",
    )
    assert InferenceAssignmentService(db).migration_marker(
        OWNER, family="thoughts-writing-route-assignments"
    ) is None

    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")))
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    configured = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-v2"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
    )
    first = service.migrate_legacy_config(OWNER, configured)
    configured.thoughts.inference_target_id = "changed-after-marker"
    replay = service.migrate_legacy_config(OWNER, configured)
    assert first["status"] == replay["status"] == "migrated"
    assert replay["legacy_config_read"] is False
    assert replay["source_sha256"] == first["source_sha256"]


def test_config_migration_rolls_back_every_assignment_when_one_is_incompatible(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "migration-atomic.db")
    _profile(
        db,
        "thought-v2",
        claims=("language", _result_claim("thought.interview"), _result_claim("ask.answer")),
    )
    _profile(db, "writing-incompatible", claims=("language",))
    configured = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-v2"),
        dictation=SimpleNamespace(
            runtime=SimpleNamespace(profile_id="writing-incompatible")
        ),
    )
    with pytest.raises(Exception):
        ProductionInferenceAdoptionService(db).migrate_legacy_config(OWNER, configured)
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key LIKE 'capability:%'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations"
        ).fetchone()[0] == 0


def test_ask_post_marker_uses_assignment_controller_and_route_receipt(tmp_path: Path) -> None:
    from holdspeak.services.ask_service import AskService

    db = Database(tmp_path / "routed-ask.db")
    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")))
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    broker = _configure(db)
    broker.inference_adoption_service.migrate_legacy_config(
        OWNER,
        SimpleNamespace(
            thoughts=SimpleNamespace(inference_target_id="thought-v2"),
            dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
        ),
    )

    class Engine:
        active_provider = "fixture"
        active_model = "routed-model"

        def run_prompt(self, **_kwargs: Any) -> str:
            return "routed answer"

    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: Engine()
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "What changed?"))
    assert result["output"] == "routed answer"
    assert result["profile_id"] == "thought-v2"
    # An answer runs through the engine door: one kernel operation is its receipt.
    assert result["route_execution_receipt"]["execution_id"] == result["operation_id"]


def test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "boundary.db")
    _profile(db, "local-primary")
    db.profiles.upsert(
        profile_id="cloud-fallback", name="Cloud fallback",
        kind="openAICompatible", base_url="https://example.invalid/v1",
        model="cloud-model", context_limit=32768,
    )
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    InferenceAssignmentService(db).set_assignment(
        OWNER,
        {
            "command_id": "assign-boundary-chain",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [
                {"profile_id": "local-primary", "profile_revision": 1},
                {"profile_id": "legacy-cloud-fallback", "profile_revision": 1},
            ],
        },
    )
    broker = _configure(db)
    physical: list[str] = []

    class Engine:
        active_provider = "fixture"
        active_model = "fixture-model"

        def __init__(self, boundary: str) -> None:
            self.boundary = boundary

        def run_prompt(self, **_kwargs: Any) -> str:
            physical.append(self.boundary)
            if self.boundary == "same_device":
                raise ProviderPermanentNoGeneration()
            return "cloud won"

    broker.inference_runner._engine_factory = (
        lambda revision, **_kwargs: Engine(str(revision.boundary))
    )
    coordinator = broker.inference_adoption_service
    admitted = coordinator.admit(
        OWNER, command_id="saved-crossing", capability_id="ask.answer",
        operation_id="saved-crossing-operation", payload=_payload(),
    )
    result = coordinator.execute(
        OWNER, execution_id=admitted["execution"]["id"],
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
    )
    assert physical == ["same_device", "external_service"]
    assert [attempt["boundary"] for attempt in result["receipt"]["attempts"]] == [
        "local", "cloud",
    ]
    assert result["receipt"]["winning_boundary"] == "cloud"

    untouched = Database(tmp_path / "unsaved.db")
    _profile(untouched, "local-only")
    untouched.profiles.upsert(
        profile_id="available-but-unsaved-cloud",
        name="Unsaved cloud",
        kind="openAICompatible",
        base_url="https://example.invalid/v1",
        model="cloud-model",
        context_limit=32768,
    )
    with untouched._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    InferenceAssignmentService(untouched).set_assignment(
        OWNER,
        {
            "command_id": "save-local-without-cloud",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "ask.answer"},
            "entries": [{"profile_id": "local-only", "profile_revision": 1}],
        },
    )
    untouched_broker = _configure(untouched)
    calls: list[str] = []

    class LocalFailure:
        active_provider = "fixture"
        active_model = "fixture-model"

        def __init__(self, boundary: str) -> None:
            self.boundary = boundary

        def run_prompt(self, **_kwargs: Any) -> str:
            calls.append(self.boundary)
            raise ProviderPermanentNoGeneration()

    untouched_broker.inference_runner._engine_factory = (
        lambda revision, **_kwargs: LocalFailure(str(revision.boundary))
    )
    unsaved = untouched_broker.inference_adoption_service.admit(
        OWNER,
        command_id="unsaved-cloud-crossing",
        capability_id="ask.answer",
        operation_id="unsaved-operation",
        payload=_payload("private"),
    )
    failed = untouched_broker.inference_adoption_service.execute(
        OWNER,
        execution_id=unsaved["execution"]["id"],
        adapter=_AskAnswerAdapter(CanonicalPromptAdapter()),
    )
    assert calls == ["same_device"]
    assert failed["receipt"]["outcome"] == "failed"
    assert [entry["boundary"] for entry in unsaved["route_plan"]["entries"]] == ["local"]


# ---- Betterment E3: the token law (Q0 follow-up) -----------------------------


def test_the_token_law_counts_about_three_and_a_half_characters_a_token() -> None:
    from holdspeak.services.inference_adoption_service import (
        LEGACY_TOKEN_ACCOUNTING_REVISION,
        TOKEN_ACCOUNTING_REVISION,
        _input_token_upper_bound,
    )

    text = "x" * 7000
    assert TOKEN_ACCOUNTING_REVISION == "chars-per-3.5@2"
    assert _input_token_upper_bound(text) == 2000 + 16
    assert _input_token_upper_bound("x" * 8) == 3 + 16  # rounded up
    # The old law stays for evidence written under it.
    assert _input_token_upper_bound(text, LEGACY_TOKEN_ACCOUNTING_REVISION) == 7000 + 16
    with pytest.raises(ConflictError):
        _input_token_upper_bound(text, "unknown@9")


def test_evidence_is_verified_under_the_law_it_was_written_with() -> None:
    from holdspeak.services.inference_adoption_service import (
        LEGACY_TOKEN_ACCOUNTING_REVISION,
        TOKEN_ACCOUNTING_REVISION,
        _evidence_token_accounting,
    )

    def evidence(revision: Any) -> dict:
        return {"serialized_requests": [{"context_plan": {"token_accounting_revision": revision}}]}

    assert _evidence_token_accounting(evidence(LEGACY_TOKEN_ACCOUNTING_REVISION)) == LEGACY_TOKEN_ACCOUNTING_REVISION
    assert _evidence_token_accounting(evidence(TOKEN_ACCOUNTING_REVISION)) == TOKEN_ACCOUNTING_REVISION
    assert _evidence_token_accounting({"serialized_requests": []}) == TOKEN_ACCOUNTING_REVISION
