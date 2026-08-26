"""HS-104-143-01 — fence the routing-authority census to observed production.

This is intentionally a static inventory test.  It does not bless the two
known unsafe seams: they are named blockers until their owning stories replace
them.  Updating a source anchor therefore requires an explicit census review.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CENSUS = REPO / (
    "pm/roadmap/holdspeak/phase-143-intelligence-router/assets/"
    "generated-routing-authority-census.md"
)

CLASSES = frozenset({
    "mutable assignment pointer",
    "immutable evidence",
    "display",
    "credential/provider identity",
    "unrelated",
    "legacy-delete",
    "migration source",
    "refusal fence",
})

# One owner per mutable family.  The value is deliberately a story, not a
# module: implementation work may move files without creating rival authority.
MUTABLE_FAMILY_OWNERS = {
    "ProfileRecord mutable destination fields": "143-03",
    "Deployment head selected by a future profile binding": "143-03",
    "Thoughts and Ask default/request pointer": "143-07",
    "Writing and dictation runtime pointer": "143-07",
    "Cadence background global resolver": "143-08",
    "V1 profile and workbench sync payload": "143-11",
    "Settings Thoughts and writing legacy pointer writers": "143-07",
}

ROUTING_RESOLVER_NAMES = frozenset({
    "resolve_inference_target",
    "resolve_placement",
    "resolve_thought_placement",
    "resolve_meeting_placement",
    "resolve_workbench_deployment_revision",
    "resolve_deployment_revision",
})

# This is deliberately exact: definitions, imports, and use-sites are all
# authority.  A new resolver or a late read cannot silently evade Story 01 by
# looking like a harmless helper in a new module.
ROUTING_RESOLVER_DEFINITIONS = {
    "holdspeak/deployment_revisions.py:202:resolve_workbench_deployment_revision",
    "holdspeak/deployment_revisions.py:224:resolve_deployment_revision",
    "holdspeak/inference_targets.py:550:resolve_placement",
    "holdspeak/inference_targets.py:496:resolve_inference_target",
    "holdspeak/inference_targets.py:590:resolve_thought_placement",
    "holdspeak/intel/providers.py:666:resolve_meeting_placement",
}

ROUTING_RESOLVER_REFERENCES = {
    "holdspeak/deployment_revisions.py:205:import:resolve_inference_target",
    "holdspeak/deployment_revisions.py:214:ref:resolve_inference_target",
    "holdspeak/inference_targets.py:584:ref:resolve_inference_target",
    "holdspeak/inference_targets.py:601:ref:resolve_placement",
    "holdspeak/intel/__init__.py:60:import:resolve_meeting_placement",
    "holdspeak/intel/providers.py:193:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:235:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:337:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:864:ref:resolve_meeting_placement",
    "holdspeak/kernel/inference_invoke.py:10:import:resolve_deployment_revision",
    "holdspeak/kernel/inference_invoke.py:92:ref:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py:13:import:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py:491:ref:resolve_deployment_revision",
    "holdspeak/services/ask_service.py:307:import:resolve_placement",
    "holdspeak/services/ask_service.py:308:ref:resolve_placement",
    "holdspeak/services/inference_setup_service.py:184:ref:resolve_inference_target",
    "holdspeak/services/inference_setup_service.py:23:import:resolve_inference_target",
    "holdspeak/services/model_profile_service.py:683:import:resolve_inference_target",
    "holdspeak/services/model_profile_service.py:690:ref:resolve_inference_target",
    "holdspeak/services/profile_service.py:131:import:resolve_inference_target",
    "holdspeak/services/profile_service.py:132:ref:resolve_inference_target",
    "holdspeak/services/refinement_application_service.py:63:import:resolve_placement",
    "holdspeak/services/refinement_application_service.py:64:ref:resolve_placement",
    "holdspeak/services/refinement_application_service.py:70:import:resolve_thought_placement",
    "holdspeak/services/refinement_application_service.py:71:ref:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py:309:import:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py:310:ref:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py:640:import:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py:681:ref:resolve_thought_placement",
    "holdspeak/services/settings_service.py:68:import:resolve_meeting_placement",
    "holdspeak/services/settings_service.py:76:ref:resolve_meeting_placement",
    "holdspeak/speech_session/plan.py:452:import:resolve_placement",
    "holdspeak/speech_session/plan.py:461:ref:resolve_placement",
    "holdspeak/speech_session/plan.py:629:import:resolve_placement",
    "holdspeak/speech_session/plan.py:638:ref:resolve_placement",
    "holdspeak/speech_session/provider.py:149:import:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py:151:ref:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py:226:import:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py:230:ref:resolve_deployment_revision",
}

ROUTING_POINTER_ATTRIBUTES = {
    "holdspeak/config/core.py:135:intel_profile_id",
    "holdspeak/config/core.py:158:intel_profile_id",
    "holdspeak/config/integrations.py:22:inference_target_id",
    "holdspeak/config/integrations.py:23:inference_target_id",
    "holdspeak/config/meeting.py:143:intel_profile_id",
    "holdspeak/config/meeting.py:144:intel_profile_id",
    "holdspeak/db/models/__init__.py:1122:resolver_profile_id",
    "holdspeak/db/models/workbench.py:139:resolver_profile_id",
    "holdspeak/services/inference_setup_service.py:605:intel_profile_id",
    "holdspeak/services/inference_setup_service.py:610:inference_target_id",
    "holdspeak/services/inference_setup_service.py:611:inference_target_id",
    "holdspeak/services/inference_setup_service.py:615:intel_profile_id",
    "holdspeak/services/inference_setup_service.py:181:inference_target_id",
    "holdspeak/services/settings_service.py:636:intel_profile_id",
    "holdspeak/services/settings_service.py:885:inference_target_id",
    "holdspeak/services/workbench_service.py:565:resolver_profile_id",
}

# `profile_id` is deliberately not treated as a synonym for routing.  This
# exhaustive classification makes every production read visible while keeping
# receipts, DTOs, readiness, and unrelated records out of the assignment lane.
PROFILE_ID_CLASSIFICATIONS = {
    **{site: "mutable assignment pointer" for site in {
        "holdspeak/config/core.py:138:profile_id", "holdspeak/config/core.py:169:profile_id",
        "holdspeak/config/integrations.py:101:profile_id", "holdspeak/config/model.py:80:profile_id",
        "holdspeak/plugins/dictation/assembly.py:321:profile_id",
        "holdspeak/services/settings_service.py:786:profile_id",
        "holdspeak/services/settings_service.py:858:profile_id",
        "holdspeak/services/sync_service.py:682:profile_id",
        "holdspeak/services/sync_service.py:697:profile_id",
    }},
    **{site: "display" for site in {
        "holdspeak/commands/doctor.py:488:profile_id", "holdspeak/commands/doctor.py:787:profile_id",
        "holdspeak/commands/doctor.py:795:profile_id", "holdspeak/commands/doctor.py:809:profile_id",
        "holdspeak/commands/doctor.py:934:profile_id",
        "holdspeak/db/models/__init__.py:683:profile_id", "holdspeak/inference_targets.py:161:profile_id",
        "holdspeak/services/ask_service.py:318:profile_id",
        "holdspeak/services/inference_setup_service.py:614:profile_id", "holdspeak/services/settings_service.py:99:profile_id",
        "holdspeak/setup_status.py:151:profile_id",
        "holdspeak/services/model_profile_service.py:225:profile_id",
        "holdspeak/services/model_profile_service.py:264:profile_id",
    }},
    **{site: "immutable evidence" for site in {
        "holdspeak/services/model_profile_service.py:1196:profile_id",
        "holdspeak/services/inference_assignment_service.py:1656:profile_id",
    }},
    **{site: "migration source" for site in {
        "holdspeak/db/models/__init__.py:1121:profile_id",
        "holdspeak/db/models/workbench.py:138:profile_id",
        "holdspeak/services/recipe_service.py:309:profile_id",
        "holdspeak/services/workbench_service.py:564:profile_id",
    }},
    **{site: "credential/provider identity" for site in {
        "holdspeak/intel/providers.py:687:profile_id", "holdspeak/intel/providers.py:694:profile_id",
        "holdspeak/intel/providers.py:703:profile_id", "holdspeak/setup_runtime.py:198:profile_id",
        "holdspeak/trust_destinations.py:59:profile_id",
    }},
}


# Story 143-10 retired family-local placement selection. These are the product
# modules that may *project* frozen route evidence or translate a legacy write,
# but may never regain a resolver/import, the old `_target`/`_invoke` helpers, or
# a direct Runner entrance. The broad AST census above detects a new resolver in
# any Python module; this narrow exact-empty gate makes the adopter boundary
# reviewable and gives a mutation proof for the actual regression shape.
PLACEMENT_ADOPTER_MODULES = frozenset({
    "holdspeak/services/recipe_service.py",
    "holdspeak/services/workbench_runner.py",
    "holdspeak/services/workbench_service.py",
    "holdspeak/services/sequence_workflow_service.py",
    "holdspeak/services/support.py",
})
RETIRED_ADOPTER_HELPERS = frozenset({"_target", "_invoke"})


def _placement_adopter_forks(root: Path) -> set[str]:
    """Return family-local resolution/dispatch authority in adopted Python legs."""
    found: set[str] = set()
    for relative in PLACEMENT_ADOPTER_MODULES:
        path = root / relative
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in RETIRED_ADOPTER_HELPERS or (
                    node.name.startswith("resolve_")
                    and any(token in node.name for token in ("placement", "inference_target", "deployment"))
                ):
                    found.add(f"{relative}:{node.lineno}:definition:{node.name}")
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in ROUTING_RESOLVER_NAMES or alias.name == "InferenceRunner":
                        found.add(f"{relative}:{node.lineno}:import:{alias.name}")
            elif isinstance(node, ast.Name) and node.id in ROUTING_RESOLVER_NAMES | {"InferenceRunner"}:
                found.add(f"{relative}:{node.lineno}:ref:{node.id}")
            elif isinstance(node, ast.Attribute) and node.attr == "invoke":
                receiver = ast.unparse(node.value)
                if "inference_runner" in receiver or "InferenceRunner" in receiver:
                    found.add(f"{relative}:{node.lineno}:runner-invoke")
    return found


def _text(path: str | Path) -> str:
    return (REPO / path).read_text(encoding="utf-8") if isinstance(path, str) else path.read_text(encoding="utf-8")


def _routing_ast_inventory(root: Path) -> tuple[set[str], set[str], set[str], set[str]]:
    """Return every public routing resolver, reference, and mutable pointer.

    The source root is an argument so the mutation test below proves that this
    guard catches both a new public resolver and a late mutable-pointer read.
    """
    definitions: set[str] = set()
    references: set[str] = set()
    pointers: set[str] = set()
    profile_ids: set[str] = set()
    for path in sorted((root / "holdspeak").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("resolve_") and (
                    "placement" in node.name
                    or "deployment_revision" in node.name
                    or "inference_target" in node.name
                ):
                    definitions.add(f"{relative}:{node.lineno}:{node.name}")
            elif isinstance(node, ast.Name) and node.id in ROUTING_RESOLVER_NAMES:
                references.add(f"{relative}:{node.lineno}:ref:{node.id}")
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in ROUTING_RESOLVER_NAMES:
                        references.add(f"{relative}:{node.lineno}:import:{alias.name}")
            elif isinstance(node, ast.Attribute) and node.attr in {
                "inference_target_id", "intel_profile_id", "resolver_profile_id",
                "requested_target_id",
            }:
                pointers.add(f"{relative}:{node.lineno}:{node.attr}")
            elif isinstance(node, ast.Attribute) and node.attr == "profile_id":
                profile_ids.add(f"{relative}:{node.lineno}:profile_id")
    return definitions, references, pointers, profile_ids


def _inventory_rows(census: str) -> dict[str, tuple[str, str]]:
    section = census.split("## Production site inventory", 1)[1].split("## ", 1)[0]
    rows: dict[str, tuple[str, str]] = {}
    for line in section.splitlines():
        if not line.startswith("|") or "Family" in line or "---" in line:
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        assert len(parts) == 4, f"malformed census row: {line}"
        family, _anchors, classification, owner = parts
        assert classification in CLASSES, f"unknown classification for {family}: {classification}"
        assert family not in rows, f"duplicate census family: {family}"
        rows[family] = (classification, owner)
    return rows


def test_census_inventory_has_one_owner_for_each_mutable_family() -> None:
    rows = _inventory_rows(_text(CENSUS))
    observed = {
        family: owner for family, (classification, owner) in rows.items()
        if classification == "mutable assignment pointer"
    }
    assert observed == MUTABLE_FAMILY_OWNERS
    assert all(re.fullmatch(r"143-\d{2}", owner) for owner in observed.values())


def test_census_anchors_current_routing_resolvers_and_legacy_assignment_writers() -> None:
    census = _text(CENSUS)
    required_anchors = {
        "holdspeak/inference_targets.py:resolve_placement": "holdspeak/inference_targets.py",
        "holdspeak/inference_targets.py:resolve_thought_placement": "holdspeak/inference_targets.py",
        "holdspeak/intel/providers.py:effective_intel_cloud": "holdspeak/intel/providers.py",
        "holdspeak/intel/providers.py:effective_dictation_llm": "holdspeak/intel/providers.py",
        "holdspeak/meeting_session/intel_plan.py:decode_meeting_intel_plan_v1": "holdspeak/meeting_session/intel_plan.py",
        "holdspeak/speech_session/plan.py:DictationSessionPlanResolver": "holdspeak/speech_session/plan.py",
        "holdspeak/deployment_revisions.py:resolve_workbench_deployment_revision": "holdspeak/deployment_revisions.py",
        "holdspeak/services/schedule_delegation.py:_terms": "holdspeak/services/schedule_delegation.py",
        "holdspeak/services/sequence_workflow_service.py:SequenceWorkflowService._freeze_parent_routes": "holdspeak/services/sequence_workflow_service.py",
        "holdspeak/services/decision_lifecycle_service.py:draft_promoted_with_model": "holdspeak/services/decision_lifecycle_service.py",
        "holdspeak/web/routes/delivery_prs.py:api_delivery_pr_draft_review": "holdspeak/web/routes/delivery_prs.py",
        "holdspeak/services/cadence_service.py:_drafted_next_action": "holdspeak/services/cadence_service.py",
        "holdspeak/services/settings_service.py:SettingsService.update_settings": "holdspeak/services/settings_service.py",
        "holdspeak/services/inference_acquisition_service.py:_activate": "holdspeak/services/inference_acquisition_service.py",
    }
    for anchor, path in required_anchors.items():
        assert anchor in census
        symbol = anchor.rsplit(":", 1)[1].rsplit(".", 1)[-1]
        assert symbol in _text(path)


def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
    definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
    assert definitions == ROUTING_RESOLVER_DEFINITIONS
    assert references == ROUTING_RESOLVER_REFERENCES
    assert pointers == ROUTING_POINTER_ATTRIBUTES
    assert profile_ids == set(PROFILE_ID_CLASSIFICATIONS)
    assert set(PROFILE_ID_CLASSIFICATIONS.values()) <= CLASSES
    assert len(PROFILE_ID_CLASSIFICATIONS) == 33
    assert sum(value == "mutable assignment pointer" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 9
    assert sum(value == "migration source" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 4
    assert sum(value == "display" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 13
    assert sum(value == "credential/provider identity" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 5
    assert sum(value == "immutable evidence" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 2


def test_ast_census_rejects_a_new_public_resolver_or_late_pointer_read(tmp_path: Path) -> None:
    """Mutation proof: a new authority cannot arrive without census review."""
    root = tmp_path
    source = root / "holdspeak" / "kernel"
    source.mkdir(parents=True)
    (source / "inference.py").write_text(
        "def resolve_late_inference_target(admission):\n"
        "    return admission.requested_target_id\n"
        "def public_profile(config):\n"
        "    return config.runtime.profile_id\n",
        encoding="utf-8",
    )
    definitions, references, pointers, profile_ids = _routing_ast_inventory(root)
    assert definitions == {"holdspeak/kernel/inference.py:1:resolve_late_inference_target"}
    assert references == set()
    assert pointers == {"holdspeak/kernel/inference.py:2:requested_target_id"}
    assert profile_ids == {"holdspeak/kernel/inference.py:4:profile_id"}
    assert definitions != ROUTING_RESOLVER_DEFINITIONS
    assert pointers != ROUTING_POINTER_ATTRIBUTES


def test_phase143_placement_adopters_have_zero_python_resolution_forks() -> None:
    """All terms originate at the assignment/coordinator seam, never a family."""
    assert _placement_adopter_forks(REPO) == set()
    assignment = _text("holdspeak/services/inference_assignment_service.py")
    coordinator = _text("holdspeak/services/inference_adoption_service.py")
    assert "def resolve_effective(" in assignment
    assert "def admit(" in coordinator and "def freeze_routes(" in coordinator


def test_phase143_placement_adopter_fork_scan_rejects_local_resolver_or_runner(tmp_path: Path) -> None:
    root = tmp_path
    source = root / "holdspeak" / "services"
    source.mkdir(parents=True)
    (source / "recipe_service.py").write_text(
        "from holdspeak.inference_targets import resolve_placement\n"
        "def _target(request):\n"
        "    return resolve_placement(request)\n"
        "def _invoke(broker):\n"
        "    return broker.inference_runner.invoke()\n",
        encoding="utf-8",
    )
    forks = _placement_adopter_forks(root)
    assert forks == {
        "holdspeak/services/recipe_service.py:1:import:resolve_placement",
        "holdspeak/services/recipe_service.py:2:definition:_target",
        "holdspeak/services/recipe_service.py:3:ref:resolve_placement",
        "holdspeak/services/recipe_service.py:4:definition:_invoke",
        "holdspeak/services/recipe_service.py:5:runner-invoke",
    }
    assert forks != _placement_adopter_forks(REPO)


def test_profile_service_owner_gate_is_enforced_before_lookup_or_probe() -> None:
    census = _text(CENSUS)
    source = _text("holdspeak/services/profile_service.py")
    assert "PROFILE_SERVICE_OWNER_ENFORCEMENT_GAP" not in census
    assert "PrincipalKind" in source
    assert "owner_principal_required" in source
    for method in (
        "list_profiles", "get_profile", "create_profile", "update_profile",
        "delete_profile", "list_inference_targets", "probe_inference_target",
        "get_inference_target",
    ):
        body = re.search(rf"    def {method}\(.*?(?=\n    def |\n    @|\Z)", source, re.S)
        assert body is not None, f"missing {method}"
        assert "self._require_owner(principal)" in body.group(0)


def test_path_bearing_profile_sync_seam_is_a_named_blocker_not_an_exception() -> None:
    census = _text(CENSUS)
    source = _text("holdspeak/services/sync_service.py")
    assert "PROFILE_SYNC_PATH_BEARING_SEAM" in census
    profile_merge = re.search(r'"profiles": \([^\n]+\)', source)
    assert profile_merge, "profiles must remain visible to the census until Story 143-11 retires it"
    assert "model_file" in profile_merge.group(0)
    assert "base_url" in profile_merge.group(0)
    assert 'SyncKindSpec("profile", "profiles", "profile.schema.json", True)' in source


def test_phase_f_meeting_execution_surface_has_no_v1_resolver_or_direct_runner() -> None:
    """Phase F leaves C1 bundle reconstruction as the sole Meeting queue executor."""
    sources = {
        path: _text(path)
        for path in (
            "holdspeak/intel_queue.py",
            "holdspeak/meeting_session/intel_plan.py",
            "holdspeak/meeting_session/deferred_admission.py",
            "holdspeak/meeting_session/intel_routed_children.py",
            "holdspeak/meeting_session/transcribe_admission.py",
            "holdspeak/meeting_session/intel_admission.py",
            "holdspeak/services/meeting_deferred_queue_binding.py",
        )
    }
    retired = (
        "InferenceRunner.invoke",
        "inference_runner.invoke",
        "resolve_placement",
        "resolve_meeting_placement",
        "freeze_meeting_intel_plan",
        "class DeferredIntelJob",
        "run_admitted_capability",
        "run_admitted_child",
    )
    for path, source in sources.items():
        assert not any(name in source for name in retired), path
    assert "claim_next_intel_job_bound" in sources["holdspeak/intel_queue.py"]
    assert "BoundDeferredIntelJob.reconstruct" in sources["holdspeak/intel_queue.py"]


def test_legacy_assignment_writers_are_delete_work_and_acquisition_is_availability_only() -> None:
    census = _text(CENSUS)
    rows = _inventory_rows(census)
    assert rows["Legacy config endpoint migration"] == ("legacy-delete", "143-03")
    assert rows["Old dictation auto-placement fallback labels"] == ("legacy-delete", "143-07")
    assert rows["Old meeting auto-placement fallback labels"] == ("immutable evidence", "143-08")
    acquisition = _text("holdspeak/services/inference_acquisition_service.py")
    assert "config.thoughts.inference_target_id = None" not in acquisition
    assert "config.meeting.intel_realtime_model =" not in acquisition
    assert '"availability": "model_library"' in acquisition
    seed = _text("holdspeak/db/seed.py")
    assert "config.meeting.intel_profile_id = profile_id" not in seed
    assert "config.dictation.runtime.profile_id = profile_id" not in seed
