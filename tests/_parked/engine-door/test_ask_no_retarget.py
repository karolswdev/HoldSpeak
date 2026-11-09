# PARKED 2026-11-09 (door/thought-dictation-meeting): the Thought runs through the engine door; the placement-based Ask path (a named target, the frozen placement claim, the v1 contract) is gone.
# Moved from tests/unit/test_ask_no_retarget.py; its helpers are still there.

from tests.unit.test_ask_no_retarget import *  # noqa: F401,F403


def test_explicit_target_runs_on_that_target(rig) -> None:
    payload = _ask(rig, inference_target_id="prof_a", model="model-a")
    assert payload["profile_id"] == "prof_a"
    assert payload["inference_target"]["id"] == "prof_a"
    assert payload["egress"]["scope"] == "private_network"


def test_no_model_override_stays_on_resolved_target(rig) -> None:
    payload = _ask(rig, inference_target_id="prof_b")
    assert payload["profile_id"] == "prof_b"
    assert payload["egress"]["scope"] == "cloud"


def test_silent_hop_never_returns_the_other_destination(rig) -> None:
    # model-b is prof_b's model: the run still stays on the chosen prof_a.
    payload = _ask(rig, inference_target_id="prof_a", model="model-b")
    assert payload["profile_id"] == "prof_a"
    assert payload["egress"]["scope"] == "private_network"


def test_frozen_refinement_admission_refuses_same_id_deployment_race(rig) -> None:
    from holdspeak.inference_targets import resolve_placement
    target = resolve_placement(rig._db, invocation="prof_a").target
    claim = {"target_id":target.id,"target_kind":target.kind,"boundary":target.boundary,
             "engine":target.engine,"model":target.model,"readiness":target.readiness_state,
             "reason":target.readiness_reason}
    rig._db.profiles.upsert(profile_id="prof_a", name="Alpha changed", kind="openAICompatible",
                            base_url="https://changed.example/v1", model="model-b", requires_key=False)
    with pytest.raises(ServiceError) as error:
        _ask(rig, inference_target_id="prof_a", frozen_admission_claim=claim)
    assert error.value.code == "refinement_admission_changed"


def test_paired_actual_receipt_and_egress_are_one_exact_fallback_tuple(rig, monkeypatch) -> None:
    from holdspeak.inference_targets import DeploymentIdentity, InferenceTarget
    target = InferenceTarget(
        id="paired_device", name="Paired device", kind="paired_device", boundary="paired_device",
        owner="you", transport="paired_https", profile_id=None, engine="configured_hub_engine",
        model="paired-model", context_limit=16384,
        deployment=DeploymentIdentity(destination_id="paired_device",kind="paired_device",
                                      engine="configured_hub_engine",model="paired-model",node="",
                                      boundary="paired_device"),
    )
    payload = {"lens":"Refine","selected_model":"paired-model","context_ids":[],
               "context_titles":[],"grounding":None,"source_text":""}
    local = rig._ask_projection({"output":"ok","provider":"local"}, payload, target, None)
    assert local["actual_placement"]["boundary"] == "paired_device"
    assert local["egress"] == {"scope":"local"}
    fallback = rig._ask_projection({"output":"ok","provider":"cloud"}, payload, target, None)
    assert fallback["actual_placement"]["boundary"] == "paired_device_then_external_service"
    assert fallback["actual_placement"]["fallback_reason"]
    assert fallback["egress"] == {"scope":"cloud"}
