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
})

# One owner per mutable family.  The value is deliberately a story, not a
# module: implementation work may move files without creating rival authority.
MUTABLE_FAMILY_OWNERS = {
    "ProfileRecord mutable destination fields": "143-03",
    "Deployment head selected by a future profile binding": "143-03",
    "Thoughts and Ask default/request pointer": "143-07",
    "Writing and dictation runtime pointer": "143-07",
    "Meeting intelligence pointer and provider placement": "143-08",
    "Recipe and agent default pointer": "143-10",
    "Workbench execution pointer": "143-10",
    "Workbench voice-resolver pointer": "143-10",
    "Recipe, Sequence, and Workflow request placement override": "143-10",
    "Kernel `inference.run` requested target selector": "143-10",
    "Decision and delivery request placement override": "143-08",
    "Rails observer background pointer": "143-08",
    "Cadence background global resolver": "143-08",
    "V1 profile and workbench sync payload": "143-11",
    "Settings Thoughts and writing legacy pointer writers": "143-07",
    "Settings meeting and background legacy pointer writers": "143-08",
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
    "holdspeak/inference_targets.py:551:resolve_placement",
    "holdspeak/inference_targets.py:497:resolve_inference_target",
    "holdspeak/inference_targets.py:591:resolve_thought_placement",
    "holdspeak/intel/providers.py:666:resolve_meeting_placement",
}

ROUTING_RESOLVER_REFERENCES = {
    "holdspeak/deployment_revisions.py:205:import:resolve_inference_target",
    "holdspeak/deployment_revisions.py:214:ref:resolve_inference_target",
    "holdspeak/inference_targets.py:602:ref:resolve_placement",
    "holdspeak/inference_targets.py:585:ref:resolve_inference_target",
    "holdspeak/kernel/inference.py:9:import:resolve_inference_target",
    "holdspeak/kernel/inference.py:103:ref:resolve_inference_target",
    "holdspeak/services/inference_setup_service.py:23:import:resolve_inference_target",
    "holdspeak/services/inference_setup_service.py:184:ref:resolve_inference_target",
    "holdspeak/services/profile_service.py:131:import:resolve_inference_target",
    "holdspeak/services/profile_service.py:132:ref:resolve_inference_target",
    "holdspeak/services/model_profile_service.py:682:import:resolve_inference_target",
    "holdspeak/services/model_profile_service.py:689:ref:resolve_inference_target",
    "holdspeak/intel/__init__.py:60:import:resolve_meeting_placement",
    "holdspeak/intel/providers.py:193:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:235:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:337:ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py:864:ref:resolve_meeting_placement",
    "holdspeak/kernel/inference_invoke.py:10:import:resolve_deployment_revision",
    "holdspeak/kernel/inference_invoke.py:92:ref:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py:13:import:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py:491:ref:resolve_deployment_revision",
    "holdspeak/kernel/projection_stager.py:133:import:resolve_workbench_deployment_revision",
    "holdspeak/kernel/projection_stager.py:134:ref:resolve_workbench_deployment_revision",
    "holdspeak/meeting_session/intel_plan.py:185:import:resolve_placement",
    "holdspeak/meeting_session/intel_plan.py:186:import:resolve_meeting_placement",
    "holdspeak/meeting_session/intel_plan.py:192:ref:resolve_meeting_placement",
    "holdspeak/meeting_session/intel_plan.py:194:ref:resolve_placement",
    "holdspeak/rails_observer.py:249:import:resolve_placement",
    "holdspeak/rails_observer.py:255:ref:resolve_placement",
    "holdspeak/services/ask_service.py:146:import:resolve_placement",
    "holdspeak/services/ask_service.py:147:ref:resolve_placement",
    "holdspeak/services/cadence_service.py:222:import:resolve_placement",
    "holdspeak/services/cadence_service.py:226:ref:resolve_placement",
    "holdspeak/services/decision_lifecycle_service.py:67:import:resolve_placement",
    "holdspeak/services/decision_lifecycle_service.py:71:ref:resolve_placement",
    "holdspeak/services/recipe_service.py:130:import:resolve_placement",
    "holdspeak/services/recipe_service.py:131:ref:resolve_placement",
    "holdspeak/services/recipe_service.py:173:import:resolve_placement",
    "holdspeak/services/recipe_service.py:174:ref:resolve_placement",
    "holdspeak/services/refinement_application_service.py:63:import:resolve_placement",
    "holdspeak/services/refinement_application_service.py:64:ref:resolve_placement",
    "holdspeak/services/refinement_application_service.py:70:import:resolve_thought_placement",
    "holdspeak/services/refinement_application_service.py:71:ref:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py:222:import:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py:223:ref:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py:609:import:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py:615:ref:resolve_thought_placement",
    "holdspeak/services/schedule_delegation.py:9:import:resolve_placement",
    "holdspeak/services/schedule_delegation.py:18:ref:resolve_placement",
    "holdspeak/services/sequence_workflow_service.py:31:import:resolve_placement",
    "holdspeak/services/sequence_workflow_service.py:33:ref:resolve_placement",
    "holdspeak/services/settings_service.py:68:import:resolve_meeting_placement",
    "holdspeak/services/settings_service.py:76:ref:resolve_meeting_placement",
    "holdspeak/services/workbench_runner.py:30:import:resolve_placement",
    "holdspeak/services/workbench_runner.py:31:ref:resolve_placement",
    "holdspeak/services/workbench_service.py:167:import:resolve_placement",
    "holdspeak/services/workbench_service.py:171:ref:resolve_placement",
    "holdspeak/services/workbench_service.py:378:import:resolve_placement",
    "holdspeak/services/workbench_service.py:379:ref:resolve_placement",
    "holdspeak/speech_session/plan.py:452:import:resolve_placement",
    "holdspeak/speech_session/plan.py:461:ref:resolve_placement",
    "holdspeak/speech_session/plan.py:611:import:resolve_placement",
    "holdspeak/speech_session/plan.py:620:ref:resolve_placement",
    "holdspeak/web/routes/delivery_prs.py:234:import:resolve_placement",
    "holdspeak/web/routes/delivery_prs.py:241:ref:resolve_placement",
}

ROUTING_POINTER_ATTRIBUTES = {
    "holdspeak/config/core.py:135:intel_profile_id",
    "holdspeak/config/core.py:158:intel_profile_id",
    "holdspeak/config/integrations.py:22:inference_target_id",
    "holdspeak/config/integrations.py:23:inference_target_id",
    "holdspeak/config/meeting.py:143:intel_profile_id",
    "holdspeak/config/meeting.py:144:intel_profile_id",
    "holdspeak/db/models/__init__.py:1095:resolver_profile_id",
    "holdspeak/db/models/workbench.py:139:resolver_profile_id",
    "holdspeak/services/inference_setup_service.py:603:inference_target_id",
    "holdspeak/services/inference_setup_service.py:604:inference_target_id",
    "holdspeak/services/inference_setup_service.py:608:intel_profile_id",
    "holdspeak/services/inference_setup_service.py:181:inference_target_id",
    "holdspeak/services/settings_service.py:567:intel_profile_id",
    "holdspeak/services/settings_service.py:816:inference_target_id",
    "holdspeak/services/workbench_service.py:376:resolver_profile_id",
    "holdspeak/services/workbench_service.py:379:resolver_profile_id",
    "holdspeak/services/workbench_service.py:401:resolver_profile_id",
    "holdspeak/services/workbench_service.py:422:resolver_profile_id",
    "holdspeak/services/workbench_service.py:471:resolver_profile_id",
    "holdspeak/kernel/inference.py:103:requested_target_id",
    "holdspeak/kernel/inference.py:147:requested_target_id",
}

# `profile_id` is deliberately not treated as a synonym for routing.  This
# exhaustive classification makes every production read visible while keeping
# receipts, DTOs, readiness, and unrelated records out of the assignment lane.
PROFILE_ID_CLASSIFICATIONS = {
    **{site: "mutable assignment pointer" for site in {
        "holdspeak/config/core.py:138:profile_id", "holdspeak/config/core.py:169:profile_id",
        "holdspeak/config/integrations.py:101:profile_id", "holdspeak/config/model.py:80:profile_id",
        "holdspeak/db/models/__init__.py:1094:profile_id", "holdspeak/db/models/workbench.py:138:profile_id",
        "holdspeak/meeting_session/intel_plan.py:193:profile_id", "holdspeak/plugins/dictation/assembly.py:318:profile_id",
        "holdspeak/services/recipe_service.py:131:profile_id", "holdspeak/services/recipe_service.py:141:profile_id",
        "holdspeak/services/recipe_service.py:146:profile_id", "holdspeak/services/recipe_service.py:174:profile_id",
        "holdspeak/services/recipe_service.py:178:profile_id", "holdspeak/services/schedule_delegation.py:18:profile_id",
        "holdspeak/services/sequence_workflow_service.py:129:profile_id", "holdspeak/services/settings_service.py:717:profile_id",
        "holdspeak/services/settings_service.py:789:profile_id", "holdspeak/services/workbench_runner.py:31:profile_id",
        "holdspeak/services/workbench_service.py:172:profile_id", "holdspeak/services/workbench_service.py:470:profile_id",
        "holdspeak/web_server.py:1138:profile_id", "holdspeak/services/sync_service.py:647:profile_id",
        "holdspeak/services/sync_service.py:662:profile_id",
    }},
    **{site: "display" for site in {
        "holdspeak/commands/doctor.py:488:profile_id", "holdspeak/commands/doctor.py:787:profile_id",
        "holdspeak/commands/doctor.py:795:profile_id", "holdspeak/commands/doctor.py:809:profile_id",
        "holdspeak/commands/doctor.py:934:profile_id",
        "holdspeak/db/models/__init__.py:656:profile_id", "holdspeak/inference_targets.py:162:profile_id",
        "holdspeak/services/ask_service.py:157:profile_id",
        "holdspeak/services/inference_setup_service.py:607:profile_id", "holdspeak/services/settings_service.py:99:profile_id",
        "holdspeak/setup_status.py:151:profile_id",
        "holdspeak/services/model_profile_service.py:224:profile_id",
        "holdspeak/services/model_profile_service.py:263:profile_id",
    }},
    **{site: "immutable evidence" for site in {
        "holdspeak/services/model_profile_service.py:1191:profile_id",
        "holdspeak/services/inference_assignment_service.py:1383:profile_id",
    }},
    **{site: "credential/provider identity" for site in {
        "holdspeak/intel/providers.py:687:profile_id", "holdspeak/intel/providers.py:694:profile_id",
        "holdspeak/intel/providers.py:703:profile_id", "holdspeak/setup_runtime.py:198:profile_id",
        "holdspeak/trust_destinations.py:59:profile_id",
    }},
}


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
        "holdspeak/meeting_session/intel_plan.py:freeze_meeting_intel_plan": "holdspeak/meeting_session/intel_plan.py",
        "holdspeak/speech_session/plan.py:DictationSessionPlanResolver": "holdspeak/speech_session/plan.py",
        "holdspeak/deployment_revisions.py:resolve_workbench_deployment_revision": "holdspeak/deployment_revisions.py",
        "holdspeak/services/schedule_delegation.py:_terms": "holdspeak/services/schedule_delegation.py",
        "holdspeak/services/sequence_workflow_service.py:SequenceWorkflowService._target": "holdspeak/services/sequence_workflow_service.py",
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
    assert len(PROFILE_ID_CLASSIFICATIONS) == 43
    assert sum(value == "mutable assignment pointer" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 23
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


def test_legacy_assignment_writers_are_delete_work_and_acquisition_is_availability_only() -> None:
    census = _text(CENSUS)
    rows = _inventory_rows(census)
    assert rows["Legacy config endpoint migration"] == ("legacy-delete", "143-03")
    assert rows["Old dictation auto-placement fallback labels"] == ("legacy-delete", "143-07")
    assert rows["Old meeting auto-placement fallback labels"] == ("legacy-delete", "143-08")
    acquisition = _text("holdspeak/services/inference_acquisition_service.py")
    assert "config.thoughts.inference_target_id = None" not in acquisition
    assert "config.meeting.intel_realtime_model =" not in acquisition
    assert '"availability": "model_library"' in acquisition
    seed = _text("holdspeak/db/seed.py")
    assert "config.meeting.intel_profile_id = profile_id" not in seed
    assert "config.dictation.runtime.profile_id = profile_id" not in seed
