"""HSEGHS001HS104-143-02 — canonical capability/retry registry contract."""
from __future__ import annotations

import json
from dataclasses import replace
from io import StringIO
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.inference_capabilities import (
    CapabilityRequirements,
    ConfusableInferenceCapability,
    DuplicateInferenceCapability,
    InferenceCapabilityDefinition,
    InferenceCapabilityRegistry,
    InferenceCapabilityRegistryError,
    InferenceRetryPolicyDefinition,
    OperationContract,
    PluginCapabilityError,
    RetryPolicyReferenceError,
    SchemaDriftInferenceCapability,
    UnknownInferenceCapability,
    builtin_capability_definitions,
    builtin_retry_policy_definitions,
    compose_inference_capability_registry,
    installed_meeting_plugin_capability_definitions,
    process_inference_capability_registry,
)
from holdspeak.mcp import resources
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.inference_capability_service import InferenceCapabilityApplicationService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.setup import build_setup_router

OWNER = Principal(PrincipalKind.OWNER, "owner")
AGENT = Principal(PrincipalKind.AGENT, "agent")
MODEL_TURN = Principal(PrincipalKind.SERVICE, "model-turn")


def _registry() -> InferenceCapabilityRegistry:
    return compose_inference_capability_registry()


def _walk(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key) for key in value] + [item for child in value.values() for item in _walk(child)]
    if isinstance(value, list):
        return [item for child in value for item in _walk(child)]
    return [str(value)]


def test_registry_is_deterministic_across_registration_order_and_restart() -> None:
    capabilities = builtin_capability_definitions() + installed_meeting_plugin_capability_definitions()
    policies = builtin_retry_policy_definitions(capabilities)
    first = InferenceCapabilityRegistry.compose(capabilities=capabilities, retry_policies=policies)
    reversed_order = InferenceCapabilityRegistry.compose(
        capabilities=tuple(reversed(capabilities)), retry_policies=tuple(reversed(policies))
    )
    restarted = _registry()

    assert first.registry_sha256 == reversed_order.registry_sha256 == restarted.registry_sha256
    assert first.capability_ids == reversed_order.capability_ids == restarted.capability_ids
    assert first.retry_policy_ids == reversed_order.retry_policy_ids == restarted.retry_policy_ids
    assert first.capability_projection("ask.answer") == restarted.capability_projection("ask.answer")


def test_registry_covers_every_story01_censused_semantic_capability() -> None:
    from tests.unit.test_phase143_inference_capability_census import (
        EXPLICIT_ROUTE_GROUPS,
        PRODUCT_RUNNER_ENTRANCES,
        SEMANTIC_HELPER_CALLERS,
        SWIFT_PHYSICAL_LEAVES,
    )

    registry = _registry()
    censused = {
        route.capability_id
        for route, _sites in EXPLICIT_ROUTE_GROUPS
    }
    censused.update(route.capability_id for route in PRODUCT_RUNNER_ENTRANCES.values())
    censused.update(route.capability_id for route in SEMANTIC_HELPER_CALLERS.values())
    censused.update(route.capability_id for route in SWIFT_PHYSICAL_LEAVES.values())
    # Dynamic Meeting/Speech/Mesh rows carry an exact frozen capability at
    # admission, rather than being an invented broad registry key.
    censused = {value for value in censused if not value.startswith("dynamic:")}

    assert censused <= set(registry.capability_ids)
    assert {
        "thought.interview",
        "ask.answer",
        "agent.plan",
        "agent.code",
        "sequence.step",
        "workflow.node",
        "project_doc.suggest_update",
        "speech.target_classify",
        "internal.semantic_dispatch",
    } <= set(registry.capability_ids)
    assert registry.require("speech.preload").owner_visibility == "internal"
    assert registry.require("apple.workbench.workflow").owner_visibility == "future"


def test_unknown_capability_refuses_before_any_profile_or_runner_access() -> None:
    called = False

    def profile_resolver() -> object:
        nonlocal called
        called = True
        return object()

    with pytest.raises(UnknownInferenceCapability):
        _registry().require_before_profile_resolution("not.a.real.capability", profile_resolver)
    assert called is False


def test_duplicate_confusable_schema_drift_and_bad_retry_references_refuse_composition() -> None:
    capabilities = builtin_capability_definitions()
    policies = builtin_retry_policy_definitions(capabilities)
    with pytest.raises(DuplicateInferenceCapability):
        InferenceCapabilityRegistry.compose(capabilities=capabilities + (capabilities[0],), retry_policies=policies)

    confusable = replace(capabilities[0], id="thought-interview", schema_sha256="")
    with pytest.raises(ConfusableInferenceCapability):
        InferenceCapabilityRegistry.compose(capabilities=capabilities + (confusable,), retry_policies=policies)

    drifted = replace(capabilities[0])
    object.__setattr__(drifted, "schema_sha256", "sha256:" + "0" * 64)
    with pytest.raises(SchemaDriftInferenceCapability):
        InferenceCapabilityRegistry.compose(capabilities=(drifted,) + capabilities[1:], retry_policies=policies)

    missing_policy = replace(
        capabilities[0],
        permitted_retry_policy_ids=("retry.missing",),
        default_retry_policy_id="retry.missing",
        schema_sha256="",
    )
    with pytest.raises(RetryPolicyReferenceError):
        InferenceCapabilityRegistry.compose(capabilities=(missing_policy,) + capabilities[1:], retry_policies=policies)


def test_group_identity_is_closed_against_label_drift_and_confusables() -> None:
    capabilities = builtin_capability_definitions()
    policies = builtin_retry_policy_definitions(capabilities)
    conflicting_label = replace(
        capabilities[1],
        group_id=capabilities[0].group_id,
        group_label="A conflicting group label",
        schema_sha256="",
    )
    with pytest.raises(SchemaDriftInferenceCapability):
        # A claimed schema hash must bind the actual closed result contract.
        replace(capabilities[0], output_schema_sha256="sha256:" + "0" * 64)
    with pytest.raises(InferenceCapabilityRegistryError, match="conflicting labels"):
        InferenceCapabilityRegistry.compose(
            capabilities=(capabilities[0], conflicting_label) + capabilities[2:],
            retry_policies=policies,
        )
    confusable_group = replace(
        capabilities[1], group_id="thoughts-notes", group_label="Writing & dictation", schema_sha256=""
    )
    with pytest.raises(ConfusableInferenceCapability):
        InferenceCapabilityRegistry.compose(
            capabilities=(capabilities[0], confusable_group) + capabilities[2:],
            retry_policies=policies,
        )


def test_plugin_capabilities_need_a_bounded_exact_definition_revision() -> None:
    base = _registry().require("meeting.live_analysis")
    plugin = replace(
        base,
        id="meeting.plugin.action_items",
        label="Meeting action items",
        operation_contract=OperationContract("meeting.plugin.action_items", 1, "plugin_definition"),
        plugin_id="action_items",
        plugin_definition_revision="2026.08.21",
        source_module="holdspeak.meeting_plugins.action_items",
        schema_sha256="",
    )
    registry = compose_inference_capability_registry(plugin_capabilities=(plugin,))
    assert registry.require("meeting.plugin.action_items").plugin_definition_revision == "2026.08.21"

    with pytest.raises(PluginCapabilityError):
        replace(plugin, plugin_definition_revision="*", schema_sha256="")
    with pytest.raises(PluginCapabilityError):
        compose_inference_capability_registry(plugin_capabilities=(base,))


def test_definition_and_policy_hashes_bind_canonical_content() -> None:
    capability = _registry().require("agent.tool_turn")
    policy = _registry().retry_policy(capability.default_retry_policy_id)
    assert capability.schema_sha256.startswith("sha256:")
    assert policy.sha256.startswith("sha256:")
    assert capability.schema_sha256 != replace(
        capability, label="A distinct label", schema_sha256=""
    ).schema_sha256
    assert policy.sha256 != replace(policy, deadline_ms=policy.deadline_ms + 1, sha256="").sha256


def test_result_contract_hashes_are_exact_and_only_shared_by_identical_schemas() -> None:
    definitions = builtin_capability_definitions()
    thought = next(definition for definition in definitions if definition.id == "thought.interview")
    assert thought.output_kind == "question_or_synthesis"
    assert thought.output_schema_sha256 != next(
        definition.output_schema_sha256 for definition in definitions if definition.id == "ask.answer"
    )
    live = next(definition for definition in definitions if definition.id == "meeting.live_analysis")
    deferred = next(definition for definition in definitions if definition.id == "meeting.deferred_analysis")
    assert live.output_schema_sha256 == deferred.output_schema_sha256
    assert live.output_schema_sha256 != thought.output_schema_sha256


@pytest.mark.parametrize(
    "nested_item",
    (
        {"type": "object"},
        {
            "type": "object",
            "additionalProperties": True,
            "properties": {"task": {"type": "string"}},
            "required": ["task"],
        },
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {"task": {"type": "string"}},
            "required": ["unknown"],
        },
    ),
)
def test_closed_result_schema_refuses_open_or_drifting_nested_object_contracts(
    nested_item: dict[str, Any],
) -> None:
    capability = _registry().require("meeting.live_analysis")
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"rows": {"type": "array", "items": nested_item}},
        "required": ["rows"],
    }
    with pytest.raises(InferenceCapabilityRegistryError):
        replace(capability, output_schema=schema, output_schema_sha256="", schema_sha256="")


def test_registered_schemas_validate_real_ask_and_meeting_plugin_outputs() -> None:
    registry = _registry()
    ask_result = {"output": "The answer."}
    registry.require("ask.answer").validate_result(ask_result)
    # Grounding is application projection metadata, not provider output.  The
    # capability contract deliberately rejects it at the Runner boundary.
    with pytest.raises(InferenceCapabilityRegistryError, match="unregistered fields"):
        registry.require("ask.answer").validate_result({**ask_result, "invented": True})

    from holdspeak.plugins.builtin import _BUILTIN_PLUGIN_DEFS, _REAL_PLUGINS
    from holdspeak.plugins.project_detector import ProjectDetectorPlugin

    # Every installed real plugin's honest no-transcript result is staged as
    # its dict unchanged; the registry accepts precisely those real shapes.
    for plugin_id, _kind in _BUILTIN_PLUGIN_DEFS:
        output = _REAL_PLUGINS[plugin_id]().run({})
        registry.require(f"meeting.plugin.{plugin_id}").validate_result(output)
    detector = ProjectDetectorPlugin()
    registry.require("meeting.plugin.project_detector").validate_result(detector.run({}))

    from holdspeak.plugins.builtin.requirements_extractor import RequirementsExtractorPlugin

    requirements = RequirementsExtractorPlugin()
    requirements._call_intel = lambda _messages, _context: '{"requirements":[{"text":"Ship it","type":"functional"}]}'  # type: ignore[method-assign]
    registered = requirements.run({"transcript": "Ship it"})
    registry.require("meeting.plugin.requirements_extractor").validate_result(registered)
    with pytest.raises(InferenceCapabilityRegistryError, match="unregistered fields"):
        registry.require("meeting.plugin.requirements_extractor").validate_result(
            {**registered, "unregistered": "drift"}
        )


def test_text_capabilities_bind_the_actual_canonical_prompt_adapter_result() -> None:
    from holdspeak.kernel.prompt_adapter import CanonicalPromptAdapter

    class Engine:
        active_provider = "local"
        active_model = "Qwen"

        @staticmethod
        def run_prompt(**_kwargs: Any) -> str:
            return "A real adapter result"

    result = CanonicalPromptAdapter().dispatch(Engine(), {"system_prompt": "s", "user_prompt": "u"}, SimpleNamespace())
    _registry().require("agent.code").validate_result(result)


def test_ask_service_normalizes_rails_echo_to_the_closed_result_contract() -> None:
    from holdspeak.grounding import GroundingBlock
    from holdspeak.services.ask_service import AskService

    ask = object.__new__(AskService)
    ask._db = SimpleNamespace()
    ask._rails_hydrator = lambda _refs, _principal: (
        [GroundingBlock("rails:story", "HS-88-01", "Story", "hs/hs", "body")], []
    )
    rails = [{"repo": "hs", "project": "hs", "kind": "story", "id": "HS-88-01"}]
    _material, echo = ask._grounding(OWNER, {"rails": rails}, "What now?")
    assert echo is not None and echo["rails"] == rails
    with pytest.raises(Exception, match="repo, project, kind, and id"):
        ask._grounding(OWNER, {"rails": [{"repo": "hs", "kind": "story", "id": "HS-88-01"}]}, "What now?")


def test_owner_projection_is_closed_and_has_no_implementation_paths_or_secrets() -> None:
    projection = _registry().owner_projection()
    rows = _walk(projection)
    assert "source_module" not in rows
    assert "model_path" not in rows
    assert "secret" not in " ".join(rows).lower()
    assert all("/Users/" not in value and "\\Users\\" not in value for value in rows)
    ids = {
        row["id"]
        for group in projection["groups"]
        for row in group["capabilities"]
    }
    assert "speech.preload" not in ids
    assert "apple.local_completion" not in ids
    assert {"thought.interview", "agent.tool_turn", "background.rails_summary"} <= ids
    tool_turn = next(
        row
        for group in projection["groups"]
        for row in group["capabilities"]
        if row["id"] == "agent.tool_turn"
    )
    assert tool_turn["requirements"]["structured_tools"] is True
    assert tool_turn["retry"]["default_policy"]["tool_call_budget"] == 8


def test_owner_http_and_mcp_share_the_same_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    service = InferenceCapabilityApplicationService(_registry())
    app = FastAPI()
    current_principal = {"value": OWNER}

    @app.middleware("http")
    async def principal(request: Request, call_next: Any) -> Any:
        request.state.principal = current_principal["value"]
        return await call_next(request)

    app.include_router(
        build_setup_router(
            WebContext(
                get_state=lambda: {},
                setup_service=SimpleNamespace(),
                inference_setup_service=SimpleNamespace(),
                inference_capability_service=service,
            )
        )
    )
    http = TestClient(app).get("/api/inference/capabilities")
    assert http.status_code == 200
    expected = service.get_capabilities(OWNER)
    assert http.json() == {"capabilities": expected}
    current_principal["value"] = AGENT
    assert TestClient(app).get("/api/inference/capabilities").status_code == 403
    current_principal["value"] = MODEL_TURN
    assert TestClient(app).get("/api/inference/capabilities").status_code == 403

    fake_broker = SimpleNamespace(inference_capability_service=service)
    monkeypatch.setattr(resources, "get_database", lambda: object())
    import holdspeak.kernel.runtime as runtime

    monkeypatch.setattr(runtime, "_configure", lambda _db: fake_broker)
    mcp = resources.read_resource("holdspeak://inference/capabilities", OWNER)
    assert json.loads(mcp["contents"][0]["text"]) == {"capabilities": expected}
    current_principal["value"] = OWNER
    detail_http = TestClient(app).get("/api/inference/capabilities/agent.tool_turn")
    assert detail_http.status_code == 200
    monkeypatch.setattr(resources, "process_inference_capability_registry", lambda: service.registry)
    detail_mcp = resources.read_resource("holdspeak://inference/capabilities/agent.tool_turn", OWNER)
    assert json.loads(detail_mcp["contents"][0]["text"]) == detail_http.json()
    assert all(row["uri"] != "holdspeak://inference/capabilities" for row in resources.list_resources(AGENT)["resources"])
    assert all("inference/capabilities" not in row["uriTemplate"] for row in resources.list_resources(AGENT)["resourceTemplates"])


def test_owner_projection_refuses_agent_model_turn_and_none_before_registry_or_db_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ExplodingRegistry:
        def owner_projection(self) -> dict[str, Any]:
            raise AssertionError("registry must not be read for a non-owner")

    service = InferenceCapabilityApplicationService(ExplodingRegistry())  # type: ignore[arg-type]
    for principal in (AGENT, MODEL_TURN, None):
        with pytest.raises(ServiceError) as error:
            service.get_capabilities(principal)  # type: ignore[arg-type]
        assert error.value.code == "inference_capability_owner_required"

    monkeypatch.setattr(resources, "get_database", lambda: (_ for _ in ()).throw(AssertionError("no db")))
    for principal in (AGENT, MODEL_TURN):
        with pytest.raises(ServiceError) as error:
            resources.read_resource("holdspeak://inference/capabilities", principal)
        assert error.value.code == "inference_capability_owner_required"
    with pytest.raises(ServiceError) as error:
        resources.read_resource("holdspeak://inference/capabilities", None)
    assert error.value.code == "mcp_resource_principal_required"


def test_composition_places_one_frozen_registry_on_the_broker(tmp_path: Any) -> None:
    from holdspeak.db import Database
    from holdspeak.kernel.runtime import _configure

    broker = _configure(Database(tmp_path / "capabilities.db"))
    assert broker.inference_capability_registry.registry_sha256 == _registry().registry_sha256
    assert broker.inference_capability_service.registry is broker.inference_capability_registry


def test_retry_policy_rejects_unknown_capability_before_registry_can_start() -> None:
    policy = InferenceRetryPolicyDefinition(
        id="retry.invalid",
        revision=1,
        permitted_capability_ids=("not.a.capability",),
        per_entry_attempts=1,
        total_physical_attempts=1,
        deadline_ms=1,
        retryable_dispositions=(),
        fallback_dispositions=(),
    )
    capability = InferenceCapabilityDefinition(
        id="test.capability",
        revision=1,
        label="Test capability",
        group_id="test",
        group_label="Test",
        description="A bounded test definition.",
        operation_contract=OperationContract("test.capability", 1, "admitted_service"),
        input_modalities=("text",),
        output_kind="text",
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        },
        output_schema_sha256="",
        context_support="bounded",
        requires=CapabilityRequirements(),
        allowed_boundaries=("local",),
        permitted_retry_policy_ids=("retry.invalid",),
        default_retry_policy_id="retry.invalid",
        fallback_dispositions=(),
        owner_visibility="owner",
        source_module="holdspeak.tests",
    )
    with pytest.raises(RetryPolicyReferenceError):
        InferenceCapabilityRegistry.compose(capabilities=(capability,), retry_policies=(policy,))


def test_process_registry_is_one_frozen_composition_and_installed_plugins_are_bound() -> None:
    first = process_inference_capability_registry()
    assert process_inference_capability_registry() is first
    from holdspeak.plugins.builtin import _BUILTIN_PLUGIN_DEFS
    from holdspeak.plugins.project_detector import ProjectDetectorPlugin

    expected_ids = {f"meeting.plugin.{identifier}" for identifier, _kind in _BUILTIN_PLUGIN_DEFS}
    detector = ProjectDetectorPlugin()
    expected_ids.add(f"meeting.plugin.{detector.id}")
    assert expected_ids <= set(first.capability_ids)
    assert first.require(f"meeting.plugin.{detector.id}").plugin_definition_revision == detector.version


def test_mcp_sidecar_composes_capability_registry_before_initialize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak import inference_capabilities
    from holdspeak.mcp import server

    def fail_composition() -> InferenceCapabilityRegistry:
        raise RuntimeError("registry composition failed")

    monkeypatch.setattr(inference_capabilities, "process_inference_capability_registry", fail_composition)
    with pytest.raises(RuntimeError, match="registry composition failed"):
        server.serve(StringIO('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n'), StringIO())
