"""HS-143-01 — executable census of owner route controls and recovery semantics.

This is intentionally a *static* fence.  Phase 143 has not consolidated these
authorities yet, so letting a new helper select a model, or letting a browser
invent a fallback, would make the migration inventory stale before the new
controller exists.  A new production selector/recovery helper therefore needs a
literal classification here and a row in the reviewed census artifact.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "holdspeak"
WEB = REPO / "web" / "src"
APPLE = REPO / "apple" / "Sources"
ARTIFACT = REPO / "pm/roadmap/holdspeak/phase-143-intelligence-router/assets/generated-surface-fallback-census.md"

# A key is deliberately file + private scope, rather than a family-wide glob:
# each new private decision is a new authority until a reviewer says otherwise.
# The value is (classification, one Phase 143 owner story).
BACKEND_PRIVATE_DECISIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("holdspeak/commands/doctor.py", "_check_runtime_profiles"): ("readiness audit; no route selection", "143-03"),
    ("holdspeak/delivery/factory_launch.py", "_valid_profile"): ("agent delivery validation", "143-10"),
    ("holdspeak/desktop_presence.py", "_select_presence_renderer"): ("non-inference false positive", "143-01"),
    ("holdspeak/dictation_telemetry.py", "_fallback_category"): ("lexical/degraded telemetry, never model fallback", "143-07"),
    ("holdspeak/inference_targets.py", "_profile_key_present"): ("profile credential readiness", "143-03"),
    ("holdspeak/intel/engine.py", "_compatibility_retry"): ("provider dialect attempt; separate admitted physical child", "143-06"),
    ("holdspeak/intel/engine.py", "_response_format_compatibility_retry"): ("provider dialect attempt (structured output); separate admitted physical child", "151-01"),
    ("holdspeak/intel/engine.py", "_resolved_model_path"): ("immutable local artifact read", "143-03"),
    ("holdspeak/intel/providers.py", "_lookup_profile_record"): ("legacy profile lookup", "143-03"),
    ("holdspeak/intel/providers.py", "_apply_runtime_profile"): ("legacy profile-shaped runtime construction", "143-03"),
    ("holdspeak/intel/providers.py", "_profile_engine"): ("profile engine factory behind admitted context", "143-03"),
    ("holdspeak/intel_queue.py", "_compute_retry_delay_seconds"): ("deferred scheduling backoff", "143-08"),
    ("holdspeak/intel_queue.py", "_retry_or_fail_job"): ("deferred scheduling retry; new job, not route fallback", "143-08"),
    ("holdspeak/kernel/inference_runner.py", "_cancelled_before_retry"): ("same-leg physical-attempt cancellation fence", "143-06"),
    ("holdspeak/kernel/projection_stager.py", "_retry_stage"): ("projection adoption for dialect child", "143-06"),
    ("holdspeak/plugins/dictation/assembly.py", "_frozen_local_target"): ("frozen dictation target", "143-07"),
    ("holdspeak/plugins/dictation/builtin/project_rewriter.py", "_selected_activity_context"): ("non-route input selection", "143-01"),
    ("holdspeak/plugins/dictation/builtin/project_rewriter.py", "_target_directive"): ("deterministic dictation directive", "143-07"),
    ("holdspeak/plugins/dictation/runtime_mlx.py", "_resolve_generator_factory"): ("dictation runtime factory", "143-07"),
    ("holdspeak/services/inference_acquisition_service.py", "_route_revision"): ("setup preview revision; not assignment authority", "143-12"),
    ("holdspeak/services/model_library_service.py", "_ensure_private_target"): ("library-owned private provider adapter; never assignment selection", "143-12"),
    ("holdspeak/services/model_library_service.py", "_ensure_profile"): ("canonical profile composition for library availability", "143-12"),
    ("holdspeak/services/model_library_service.py", "_profile_body"): ("library profile material builder; no assignment authority", "143-12"),
    ("holdspeak/services/model_library_service.py", "_profile_id"): ("library profile identity parser", "143-12"),
    ("holdspeak/services/model_library_service.py", "_profile_matches"): ("library profile replay comparison", "143-12"),
    ("holdspeak/services/model_library_service.py", "_profile_row"): ("server-owned library availability projection", "143-12"),
    ("holdspeak/services/model_library_service.py", "_target_matches"): ("private provider adapter comparison", "143-12"),
    ("holdspeak/web/routes/primitives/profiles.py", "_library_private_target"): ("retired legacy target side-door refusal", "143-12"),
    ("holdspeak/db/reconcile.py", "_backfill_chat_route_assignments"): ("additive data backfill; no route selection", "150-02"),
    ("holdspeak/services/inference_assignment_service.py", "_resolve"): ("canonical sparse assignment resolver", "143-04"),
    ("holdspeak/services/inference_adoption_service.py", "_validate_parentless_local_preload_route"): ("closed parentless speech preload cross-bind", "143-08"),
    ("holdspeak/services/thread_practice.py", "_resolve_deployment_revision"): ("capability assignment resolver for chat.guardrail/chat.compact deployment revision lookup", "153-03"),
    ("holdspeak/services/project_update_service.py", "_resolve_for_capability"): ("capability assignment resolver for project.update_draft deployment revision lookup", "162-03"),
    ("holdspeak/services/project_steward_service.py", "_apply_effect_with_retry"): ("bounded steward effect retry within one run; STW-008 policy bounds, stop-checked between attempts, never route selection", "163-07"),
    ("holdspeak/speech_session/session.py", "_routed_session_validation_plan"): ("inert validation/history carrier for fully-adopted sessions; no route selection", "143-08"),
    ("holdspeak/services/inference_route_plan_service.py", "_insert_route"): ("canonical immutable route-plan persistence", "143-05"),
    ("holdspeak/services/inference_route_plan_service.py", "_resolve_entries"): ("canonical frozen route-leg resolver", "143-05"),
    ("holdspeak/services/inference_route_plan_service.py", "_route_from_row"): ("canonical route-plan evidence reconstruction", "143-05"),
    ("holdspeak/services/inference_route_plan_service.py", "_validate_route_material"): ("canonical closed route-plan validator", "143-05"),
    ("holdspeak/services/inference_fallback_controller.py", "_route_execution_receipt"): ("immutable route execution receipt reconstruction", "143-06"),
    ("holdspeak/services/ask_service.py", "_routed_projection"): ("controller-winner application projection", "143-07"),
    ("holdspeak/services/inference_setup_service.py", "_thought_target"): ("legacy Thoughts selector", "143-07"),
    ("holdspeak/services/inference_setup_service.py", "_safe_target"): ("setup readiness selector", "143-12"),
    ("holdspeak/services/meeting_intel_service.py", "_retry"): ("explicit owner recovery request", "143-08"),
    ("holdspeak/services/profile_key_service.py", "_profile"): ("credential owner lookup", "143-03"),
    ("holdspeak/services/model_profile_service.py", "_profile_id"): ("canonical Profile identity parser", "143-03"),
    ("holdspeak/services/model_profile_service.py", "_profile_payload"): ("canonical Profile payload builder", "143-03"),
    ("holdspeak/services/model_profile_service.py", "_profile_projection"): ("canonical Profile owner projection", "143-03"),
    ("holdspeak/services/model_profile_service.py", "_route_plan_dependencies"): ("exact Profile assignment dependency lookup", "143-03"),
    ("holdspeak/services/profile_service.py", "_target_fields"): ("profile transport-neutral mutation", "143-03"),
    ("holdspeak/services/recipe_service.py", "_refuse_missing_legacy_profile"): ("post-cutover dangling legacy selection refusal fence", "143-10"),
    ("holdspeak/services/recipe_service.py", "_reject_retired_selector"): ("legacy selector refusal fence", "143-10"),
    ("holdspeak/services/recipe_service.py", "_route_summary"): ("canonical frozen route summary projection", "143-10"),
    ("holdspeak/services/recipe_service.py", "_refuse_post_marker_profile_pointer"): ("post-marker retired pointer refusal fence", "143-11"),
    ("holdspeak/services/sequence_workflow_service.py", "_freeze_parent_routes"): ("canonical parent route-freeze façade", "143-10"),
    ("holdspeak/services/sequence_workflow_service.py", "_reject_retired_selector"): ("legacy selector refusal fence", "143-10"),
    ("holdspeak/services/sequence_workflow_service.py", "_route_placement"): ("frozen route placement projection", "143-10"),
    ("holdspeak/services/sequence_workflow_service.py", "_route_target"): ("frozen route egress projection", "143-10"),
    ("holdspeak/services/support.py", "_norm_run_target"): ("workflow placement normalization", "143-10"),
    ("holdspeak/services/workbench_runner.py", "_route_target"): ("frozen route egress projection", "143-10"),
    ("holdspeak/services/front_door_service.py", "_collect_profile_from_done_item"): ("front-door plan profile identity extraction from receipt; not assignment authority", "156-04"),
    ("holdspeak/services/front_door_service.py", "_resolve_group_assignments"): ("front-door plan assignment composition from completed provisioning items", "156-04"),
    ("holdspeak/services/front_door_service.py", "_select_preset_for_tier"): ("front-door catalog preset selection for pack recommendation; not assignment authority", "156-04"),
    ("holdspeak/speaker_intel.py", "_get_fallback_speaker"): ("speaker identity fallback, not inference", "143-01"),
    ("holdspeak/target_profile.py", "_build_model_target_prompt"): ("model-assisted target prompt", "143-07"),
    ("holdspeak/target_profile.py", "_profile"): ("legacy target-profile lookup", "143-07"),
}

# Every production browser module which reads/writes a routing pointer is known.
# Types and transport projections are included so a new UI cannot hide a selector
# behind a wire helper or a "display-only" component.
WEB_ROUTING_SURFACES: dict[str, tuple[str, str]] = {
    "web/src/desk/api.ts": ("display-transport", "143-11"),
    "web/src/desk/ask.ts": ("inference-route", "143-07"),
    "web/src/desk/components/DeliveryBoard.tsx": ("unrelated", "143-01"),
    "web/src/desk/components/Pullout.tsx": ("display-transport", "143-11"),
    "web/src/desk/deliveryFactory.ts": ("unrelated", "143-01"),
    "web/src/desk/detail-types.ts": ("display-transport", "143-11"),
    "web/src/desk/infoContract.ts": ("display-transport", "143-10"),
    "web/src/desk/store/types.ts": ("display-transport", "143-11"),
    "web/src/lib/primitives.ts": ("display-transport", "143-11"),
    "web/src/pages/cores/SettingsCore.tsx": ("inference-route", "143-13"),
    "web/src/pages/cores/AssignmentEditor.tsx": ("inference-route", "143-13"),
    "web/src/pages/cores/AssignmentModelChooser.tsx": ("inference-route", "143-13"),
    "web/src/pages/cores/assignmentExperience.ts": ("inference-route", "143-13"),
    "web/src/pages/cores/core-types.ts": ("display-transport", "143-11"),
    "web/src/pages/cores/ModelLibraryCore.tsx": ("display-transport", "143-12"),
    "web/src/pages/cores/TopologyMapView.tsx": ("display-transport", "156-04"),
    "web/src/features/project-room/ProjectRoomCore.tsx": ("display-transport", "169-07"),
    "web/src/features/concierge/api.ts": ("display-transport", "170-03"),
    "web/src/pages/cores/dictation/SpeakFace.tsx": ("display-transport", "170-04"),
    "web/src/pages/cores/modelLibrary.ts": ("display-transport", "143-12"),
}

POINTER_TOKENS = ("inference_target_id", "intel_profile_id", "profile_id", "resolver_profile_id")
CAMEL_POINTER_TOKENS = ("inferenceTargetId", "intelProfileId", "profileId", "resolverProfileId")
RUNS_ON_PICKER_SURFACE = re.compile(
    r"(?:import\s*\{\s*RunsOnPicker\s*\}|export\s+function\s+RunsOnPicker)"
)
# HS-151-06: later phases lawfully add classified decisions — the owner
# is any phase-story id (originally 143-only).
STORY_RE = re.compile(r"^\d{2,3}-\d{2}$")

# Story 06 retired every client-owned Swift retry/fallback execution site. The
# scanner remains as a zero-regression fence: legacy wire strings may survive in
# enum raw values, but no execution switch or retry-bound read may reappear.
SWIFT_POLICY_SITES: dict[str, tuple[str, str]] = {}


def _private_decisions() -> set[tuple[str, str]]:
    """Return every current private routing/recovery-shaped backend helper."""
    found: set[tuple[str, str]] = set()
    selector_words = ("resolve", "select", "route", "placement", "profile", "target")
    route_evidence = (*POINTER_TOKENS, "deployment_revision", "resolve_placement", "InferenceRunner", "provider", "model")
    for path in sorted(BACKEND.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("_"):
                continue
            body = ast.get_source_segment(source, node) or ""
            name = node.name.lower()
            is_recovery = "fallback" in name or "retry" in name
            is_selector = any(word in name for word in selector_words) and any(token in body for token in route_evidence)
            if is_recovery or is_selector:
                found.add((path.relative_to(REPO).as_posix(), node.name))
    return found


def _web_routing_surfaces() -> set[str]:
    """Return exact route consumers, including picker imports and camel selectors."""
    found: set[str] = set()
    for path in sorted(WEB.rglob("*")):
        if path.suffix not in {".ts", ".tsx"} or ".test." in path.name or "/__tests__/" in path.as_posix():
            continue
        source = path.read_text(encoding="utf-8")
        if (
            any(token in source for token in (*POINTER_TOKENS, *CAMEL_POINTER_TOKENS))
            or RUNS_ON_PICKER_SURFACE.search(source)
        ):
            found.add(path.relative_to(REPO).as_posix())
    return found


def _swift_policy_sites(sources: dict[str, str] | None = None) -> set[str]:
    """Return every current Swift retry/fallback policy branch and loop."""
    sources = sources or {
        path.relative_to(REPO).as_posix(): path.read_text(encoding="utf-8")
        for path in APPLE.rglob("*.swift")
    }
    found: set[str] = set()
    for relative, source in sorted(sources.items()):
        for line_no, line in enumerate(source.splitlines(), start=1):
            marker = ""
            if "case .fallbackOnDevice:" in line:
                marker = "fallbackOnDevice"
            elif "case .retryThenQueue:" in line:
                marker = "retryThenQueue"
            elif "policy.maxRetries" in line:
                marker = "boundedRetry"
            if marker:
                found.add(f"{relative}:{line_no}:{marker}")
    return found


def test_private_backend_route_and_recovery_decisions_are_classified() -> None:
    """A new private selector/retry/fallback helper fails closed until reviewed."""
    found = _private_decisions()
    assert found == set(BACKEND_PRIVATE_DECISIONS), (
        "Unclassified private route/recovery decision(s): "
        f"{sorted(found - set(BACKEND_PRIVATE_DECISIONS))}; stale classifications: "
        f"{sorted(set(BACKEND_PRIVATE_DECISIONS) - found)}"
    )
    assert all(STORY_RE.fullmatch(owner) for _, owner in BACKEND_PRIVATE_DECISIONS.values())


def test_web_route_pointer_controls_are_classified_and_single_owned() -> None:
    """A new browser routing consumer cannot appear outside the reviewed census."""
    found = _web_routing_surfaces()
    assert found == set(WEB_ROUTING_SURFACES), (
        "Unclassified web route consumer(s): "
        f"{sorted(found - set(WEB_ROUTING_SURFACES))}; stale classifications: "
        f"{sorted(set(WEB_ROUTING_SURFACES) - found)}"
    )
    assert all(
        classification in {"inference-route", "display-transport", "unrelated"}
        and STORY_RE.fullmatch(owner)
        for classification, owner in WEB_ROUTING_SURFACES.values()
    )


def test_story143_workflow_aliases_decode_once_and_no_adopter_reopens_fake_fallback() -> None:
    """The old wire words survive only at the boundary, never as execution law."""
    support = (REPO / "holdspeak/services/support.py").read_text(encoding="utf-8")
    workflow = (REPO / "holdspeak/services/sequence_workflow_service.py").read_text(encoding="utf-8")
    assert '"fallbackOnDevice": "carry"' in support
    assert '"retryThenQueue": "hold"' in support
    assert "fallbackOnDevice" not in workflow
    assert "retryThenQueue" not in workflow
    assert "fell_back" not in workflow
    for relative in (
        "holdspeak/services/recipe_service.py",
        "holdspeak/services/workbench_runner.py",
        "holdspeak/services/workbench_service.py",
        "holdspeak/services/sequence_workflow_service.py",
    ):
        source = (REPO / relative).read_text(encoding="utf-8")
        assert "def _target(" not in source and "def _invoke(" not in source, relative


def test_census_artifact_covers_every_guarded_surface_and_recovery_kind() -> None:
    text = ARTIFACT.read_text(encoding="utf-8")
    for required in (
        "true model-route fallback",
        "scheduling retry",
        "lexical degradation",
        "explicit owner retry",
        "provider dialect attempt",
        "Python fake workflow label",
        "Swift dormant/client fallback",
        "response_format",
        "silent-audio",
        "Storage-delivery retry",
        "fallbackOnDevice",
        "retryThenQueue",
        "exactly one Phase 143 story",
    ):
        assert required in text
    for path, _scope in BACKEND_PRIVATE_DECISIONS:
        assert path in text, f"census artifact omits guarded backend surface {path}"
    for path in WEB_ROUTING_SURFACES:
        assert path in text, f"census artifact omits guarded web surface {path}"


def test_swift_retry_and_fallback_policy_sites_are_exact_and_fail_closed() -> None:
    live = _swift_policy_sites()
    assert live == set(SWIFT_POLICY_SITES), (
        f"unclassified Swift policy sites={sorted(live - set(SWIFT_POLICY_SITES))}; "
        f"stale={sorted(set(SWIFT_POLICY_SITES) - live)}"
    )
    assert all(STORY_RE.fullmatch(owner) for _, owner in SWIFT_POLICY_SITES.values())

    mutated = _swift_policy_sites({
        "apple/Sources/RuntimeCore/Workbench/RogueRunner.swift": """
case .fallbackOnDevice:
case .retryThenQueue:
let tries = policy.maxRetries
""",
    })
    assert mutated == {
        "apple/Sources/RuntimeCore/Workbench/RogueRunner.swift:2:fallbackOnDevice",
        "apple/Sources/RuntimeCore/Workbench/RogueRunner.swift:3:retryThenQueue",
        "apple/Sources/RuntimeCore/Workbench/RogueRunner.swift:4:boundedRetry",
    }
    assert not mutated <= set(SWIFT_POLICY_SITES)
