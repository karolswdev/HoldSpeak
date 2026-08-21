"""HS-130-06 — Ask tells the truth: the target id selects the placement and a
`model` override may only name what the resolved target advertises. Ask never
silently hops to another destination by model name, and `list_models` no longer
dedupes across destinations."""
from __future__ import annotations

import asyncio

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "owner")
from holdspeak.services.ask_service import AskService
from holdspeak.services.errors import ServiceError, ValidationError


class _FakeIntel:
    active_provider = "openai_compatible"

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        return "ok"


@pytest.fixture
def rig(tmp_path, monkeypatch):
    db = Database(tmp_path / "ask_retarget.db")
    # A private-LAN destination (boundary: private_network) advertising model-a.
    db.profiles.upsert(profile_id="prof_a", name="Alpha", kind="openAICompatible",
                       base_url="http://192.168.1.50:8080", model="model-a", requires_key=False)
    # An external-service destination (boundary: cloud) advertising model-b.
    db.profiles.upsert(profile_id="prof_b", name="Beta", kind="openAICompatible",
                       base_url="https://api.example.com/v1", model="model-b", requires_key=False)
    # A second private endpoint serving the SAME model name as prof_a.
    db.profiles.upsert(profile_id="prof_c", name="Gamma", kind="openAICompatible",
                       base_url="http://192.168.1.51:8080", model="model-a", requires_key=False)
    # The admitted runner loads engines from the frozen deployment revision.
    # Targeting is the behavior here, so its runner seam supplies a test engine.
    broker = _configure(db)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda revision, **_kw: _FakeIntel())
    return AskService(db, hub_model=lambda: "", broker=broker)


def _ask(service, **kw):
    return asyncio.run(service.ask(OWNER, "summarize", **kw))


def test_explicit_target_runs_on_that_target(rig) -> None:
    payload = _ask(rig, inference_target_id="prof_a", model="model-a")
    assert payload["profile_id"] == "prof_a"
    assert payload["inference_target"]["id"] == "prof_a"
    assert payload["egress"]["scope"] == "private_network"


def test_no_model_override_stays_on_resolved_target(rig) -> None:
    payload = _ask(rig, inference_target_id="prof_b")
    assert payload["profile_id"] == "prof_b"
    assert payload["egress"]["scope"] == "cloud"


def test_mismatched_model_refuses_and_names_target(rig) -> None:
    # OLD behaviour: model-b != prof_a's model → scan all profiles, silently
    # rebind to prof_b, and run on a DIFFERENT egress boundary (cloud) than the
    # caller's chosen prof_a (private_network). NEW: refuse, never hop.
    with pytest.raises(ValidationError) as exc:
        _ask(rig, inference_target_id="prof_a", model="model-b")
    msg = str(exc.value)
    assert "Alpha" in msg and "model-a" in msg and "model-b" in msg
    assert getattr(exc.value, "code", "") == "model_not_advertised"


def test_silent_hop_never_returns_the_other_destination(rig) -> None:
    # Concrete proof the run never crosses to prof_b: a payload for prof_b is
    # impossible; the call raises instead of returning another destination's id.
    with pytest.raises(ValidationError):
        _ask(rig, inference_target_id="prof_a", model="model-b")


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


def test_list_models_does_not_dedupe_across_destinations(rig) -> None:
    rows = rig.list_models(OWNER)
    ids = {r["id"] for r in rows}
    assert {"prof_a", "prof_b", "prof_c"} <= ids
    # prof_a and prof_c serve the SAME model name yet BOTH appear, distinct by id.
    same_name = [r for r in rows if r["name"] == "model-a"]
    assert {r["id"] for r in same_name} == {"prof_a", "prof_c"}


def test_hub_row_carries_its_id(tmp_path, monkeypatch) -> None:
    # Listing destinations builds no engine at all — HS-131-13 removed the
    # vestigial `build_intel_for_target` patch this test used to carry (the
    # factory is gone, and listing never reached it in the first place).
    db = Database(tmp_path / "ask_hub.db")
    service = AskService(db, hub_model=lambda: "hub-model")
    rows = service.list_models(OWNER)
    hub = [r for r in rows if r["source"] == "hub"]
    assert len(hub) == 1 and hub[0]["id"] == "this_machine"
