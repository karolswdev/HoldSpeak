# PARKED 2026-11-09 (door/own-choice-park-waist): their methods are parked: no product caller once the engine door chose on its own.
# Moved from tests/unit/test_engines_route_plans.py; its helpers are still there.

from tests.unit.test_engines_route_plans import *  # noqa: F401,F403


def test_legacy_adapter_is_pure_and_never_projects_locator_or_endpoint(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO profiles
               (id,name,kind,model_file,base_url,model,node,context_limit,requires_key,created_at,last_modified,deleted)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,0)""",
            ("legacy-cloud", "Legacy", "openAICompatible", "/private/model.gguf", "https://secret.example/v1", "legacy-model", "", 16384, 1, "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"),
        )
    original_exists = Path.exists
    monkeypatch.setattr(Path, "exists", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("scan")))
    service = InferenceRoutePlanService(db)
    try:
        route = service.freeze_legacy_one_leg_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="legacy-freeze",
            capability_id="ask.answer",
            legacy_profile_id="legacy-cloud",
        )
    finally:
        monkeypatch.setattr(Path, "exists", original_exists)
    encoded = json.dumps(route)
    assert "secret.example" not in encoded
    assert "/private/" not in encoded
    assert "secret_slot" not in encoded
    assert service.get_route_plan(OWNER, route["id"]) == route


def test_legacy_adapter_refuses_unproved_structured_capability_before_writes(db: Database) -> None:
    with db._connection() as conn:
        conn.execute("INSERT INTO profiles(id,name,kind,model_file,model,context_limit,created_at,last_modified) VALUES (?,?,?,?,?,?,?,?)", ("legacy-local", "Old", "onDevice", "/missing/private.gguf", "old", 32768, "2026-08-21T00:00:00Z", "2026-08-21T00:00:00Z"))
    service = InferenceRoutePlanService(db)
    with pytest.raises(Exception) as refused:
        service.freeze_legacy_one_leg_plan(
            ROUTE_PLANNING_AUTHORITY,
            command_id="legacy-illegal",
            capability_id="thought.interview",
            legacy_profile_id="legacy-local",
        )
    assert getattr(refused.value, "code", "") == "no_compatible_assignment"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plan_commands").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0] == 0


def test_one_shot_hashes_private_material_and_attempt_ordinal_is_not_minted(db: Database) -> None:
    _ready_route(db)
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='ready'")
    evidence_entries = [
        {
            "route_leg_ordinal": ordinal,
            "eligibility": "executable",
            "reason_code": None,
            "admitted_request_id": f"admitted-{ordinal}",
            "admitted_request_sha256": _digest({"prompt": f"private prompt {ordinal}"}),
            "context_plan_sha256": _digest({"tokens": ordinal * 10}),
            "serialized_request_sha256": _digest(f"private serialization {ordinal}"),
        }
        for ordinal in (1, 2)
    ]
    service = _evidence_service(db, entries=evidence_entries, reference="one-shot-source")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="oneshot-1",
        route_request={"capability_id": "ask.answer"},
        operation_id="operation-1",
        planning_reference="one-shot-source",
    )
    encoded = json.dumps(result)
    assert "owner note body" not in encoded
    assert "private prompt" not in encoded
    assert "private serialization" not in encoded
    evidence = service.route_leg_evidence(
        ROUTE_PLANNING_AUTHORITY,
        operation_plan_id=result["operation_request_plan"]["id"],
        route_leg_ordinal=2,
    )
    assert evidence["route_leg_ordinal"] == 2
    assert "physical_attempt_ordinal" not in evidence
    replay = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="oneshot-1",
        route_request={"capability_id": "ask.answer"},
        operation_id="operation-1",
        planning_reference="one-shot-source",
    )
    assert replay == result
    without_provider = InferenceRoutePlanService(Database(db.db_path))
    with pytest.raises(ServiceError) as unavailable:
        without_provider.get_operation_request_plan(
            ROUTE_PLANNING_AUTHORITY, result["operation_request_plan"]["id"]
        )
    assert unavailable.value.code == "inference_operation_evidence_provider_missing"
    restarted = _evidence_service(
        Database(db.db_path), entries=evidence_entries, reference="one-shot-source"
    )
    assert restarted.get_operation_request_plan(
        ROUTE_PLANNING_AUTHORITY, result["operation_request_plan"]["id"]
    ) == result["operation_request_plan"]


def test_recomputed_operation_and_normalized_leg_forgery_refuses(db: Database) -> None:
    _ready_route(db, profiles=("quick",))
    entries = [{
        "route_leg_ordinal": 1, "eligibility": "known_preflight_unavailable",
        "reason_code": "binding_not_ready",
    }]
    service = _evidence_service(db, entries=entries, reference="forgery-source")
    # Make the real binding observation unavailable so the original plan is lawful.
    with db._connection() as conn:
        conn.execute("UPDATE model_profile_readiness_observations SET state='unavailable'")
    result = service.freeze_one_shot(
        ROUTE_PLANNING_AUTHORITY,
        command_id="forgery-shot",
        route_request={"capability_id": "ask.answer"},
        operation_id="forgery-operation",
        planning_reference="forgery-source",
    )
    with db._connection() as conn:
        operation_plan_id = result["operation_request_plan"]["id"]
        row = conn.execute("SELECT payload_json FROM inference_operation_route_request_plans WHERE id=?", (operation_plan_id,)).fetchone()
        material = json.loads(str(row["payload_json"]))
        material["entries"][0] = {
            "route_leg_ordinal": 1, "eligibility": "executable", "reason_code": None,
            "admitted_request_id": "forged", "admitted_request_sha256": _digest("a"),
            "context_plan_sha256": _digest("b"), "serialized_request_sha256": _digest("c"),
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        conn.execute("UPDATE inference_operation_route_request_plans SET payload_json=?,sha256=? WHERE id=?", (encoded, _digest(material), operation_plan_id))
        forged = material["entries"][0]
        conn.execute("""UPDATE inference_operation_route_request_plan_entries SET eligibility='executable',reason_code=NULL,admitted_request_id=?,admitted_request_sha256=?,context_plan_sha256=?,serialized_request_sha256=? WHERE operation_plan_id=?""", (forged["admitted_request_id"], forged["admitted_request_sha256"], forged["context_plan_sha256"], forged["serialized_request_sha256"], operation_plan_id))
    with pytest.raises(ConflictError):
        service.route_leg_evidence(ROUTE_PLANNING_AUTHORITY, operation_plan_id=operation_plan_id, route_leg_ordinal=1)


