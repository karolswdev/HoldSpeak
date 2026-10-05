"""HS-104-143-01 — fence the routing-authority census to observed production.

This is intentionally a static inventory test.  It does not bless the two
known unsafe seams: they are named blockers until their owning stories replace
them.  Updating a source anchor therefore requires an explicit census review.

The anchors are line-free (owner ruling 2026-10-03; ``tests/unit/_line_free.py``):
``path|scope|site``, with ``#2`` for a second same site in one scope.  An edit
above a site no longer turns the census red; a new resolver, reference or
pointer read still does.  Comments below that say "re-anchored" or name a line
are history from the line-pinned form.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from tests.unit import _line_free
from tests.unit._line_free import Record
from tests.unit.test_one_path_census import _scope_index


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
    "holdspeak/deployment_revisions.py|def:resolve_workbench_deployment_revision",
    "holdspeak/deployment_revisions.py|def:resolve_deployment_revision",
    "holdspeak/inference_targets.py|def:resolve_placement",
    "holdspeak/inference_targets.py|def:resolve_inference_target",
    "holdspeak/inference_targets.py|def:resolve_thought_placement",
    "holdspeak/intel/providers.py|def:resolve_meeting_placement",
}

ROUTING_RESOLVER_REFERENCES = {
    "holdspeak/deployment_revisions.py|resolve_workbench_deployment_revision|import:resolve_inference_target",
    "holdspeak/deployment_revisions.py|resolve_workbench_deployment_revision|ref:resolve_inference_target",
    "holdspeak/inference_targets.py|resolve_placement|ref:resolve_inference_target",
    "holdspeak/inference_targets.py|resolve_thought_placement|ref:resolve_placement",
    "holdspeak/intel/__init__.py|<module>|import:resolve_meeting_placement",
    "holdspeak/intel/providers.py|resolve_llm_capability|ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py|_configured_engine|ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py|configured_meeting_deployment|ref:resolve_meeting_placement",
    "holdspeak/intel/providers.py|configured_egress_boundary|ref:resolve_meeting_placement",
    "holdspeak/kernel/inference_invoke.py|<module>|import:resolve_deployment_revision",
    "holdspeak/kernel/inference_invoke.py|InferenceInvokeCodec.authorize|ref:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py|<module>|import:resolve_deployment_revision",
    "holdspeak/kernel/inference_runner.py|InferenceRunner._revision|ref:resolve_deployment_revision",
    "holdspeak/services/ask_service.py|AskService.ask|import:resolve_placement",
    "holdspeak/services/ask_service.py|AskService.ask|ref:resolve_placement",
    "holdspeak/services/inference_setup_service.py|_thought_target|ref:resolve_inference_target",
    "holdspeak/services/inference_setup_service.py|<module>|import:resolve_inference_target",
    "holdspeak/services/model_profile_service.py|ModelProfileService._observe_destination_readiness|import:resolve_inference_target",
    "holdspeak/services/model_profile_service.py|ModelProfileService._observe_destination_readiness|ref:resolve_inference_target",
    "holdspeak/services/profile_service.py|ProfileService.get_inference_target|import:resolve_inference_target",
    "holdspeak/services/profile_service.py|ProfileService.get_inference_target|ref:resolve_inference_target",
    # HS-147-05: the HS-146-07 snapshot resolve_placement fallback entries are
    # RETIRED — the direct dispatch now pre-filters the profile list to
    # vision-capable targets and refuses (no_vision_model_assigned) with zero
    # dispatches when none qualify; resolve_placement no longer appears in
    # calendar_snapshot_service.py. Deliberate deregistration, not drift.
    "holdspeak/services/refinement_application_service.py|RefinementApplicationService.get_workbench|import:resolve_placement",
    "holdspeak/services/refinement_application_service.py|RefinementApplicationService.get_workbench|ref:resolve_placement",
    "holdspeak/services/refinement_application_service.py|RefinementApplicationService.get_workbench|import:resolve_thought_placement",
    "holdspeak/services/refinement_application_service.py|RefinementApplicationService.get_workbench|ref:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py|RefinementCoordinator._admission_claim|import:resolve_thought_placement",
    "holdspeak/services/refinement_coordinator.py|RefinementCoordinator._admission_claim|ref:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py|RefinementThoughtService._validate_current_admission_under_write_fence|import:resolve_thought_placement",
    "holdspeak/services/refinement_thought_service.py|RefinementThoughtService._validate_current_admission_under_write_fence|ref:resolve_thought_placement",
    # HS-201-03: the Meeting service now reads the disclosed frozen route
    # selection; its former legacy resolver import and call were removed. The
    # execution host remains immutable route evidence in deferred_bound.py.
    # HS-172: resolve_meeting_placement in routing_glue, mcp/tools, settings route
    "holdspeak/runtime/routing_glue.py|RoutingGlueMixin._maybe_auto_enqueue_intel|import:resolve_meeting_placement",
    "holdspeak/runtime/routing_glue.py|RoutingGlueMixin._maybe_auto_enqueue_intel|ref:resolve_meeting_placement",
    # HS-201-03: moved down three lines with the added route/receipt transport;
    # re-anchored. PHILO-5-01/02: moved down again with the operation contract
    # (the decision helpers, the loop's new tools and the import intake);
    # re-anchored, the settings.hub read itself unchanged. PHILO-7-01/02: moved
    # down again (985 -> 1148) with the desk operations; re-anchored, same read.
    "holdspeak/mcp/tools.py|_dispatch|import:resolve_meeting_placement",
    "holdspeak/web/routes/system/settings.py|_resolve_meetings_host|import:resolve_meeting_placement",
    "holdspeak/web/routes/system/settings.py|_resolve_meetings_host|ref:resolve_meeting_placement",
    "holdspeak/services/settings_service.py|meeting_placement_summary|import:resolve_meeting_placement",
    "holdspeak/services/settings_service.py|meeting_placement_summary|ref:resolve_meeting_placement",
    "holdspeak/speech_session/plan.py|configured_pipeline_egress_boundary|import:resolve_placement",
    "holdspeak/speech_session/plan.py|configured_pipeline_egress_boundary|ref:resolve_placement",
    "holdspeak/speech_session/plan.py|DictationSessionPlanResolver._provider_legs|import:resolve_placement",
    "holdspeak/speech_session/plan.py|DictationSessionPlanResolver._provider_legs|ref:resolve_placement",
    "holdspeak/speech_session/provider.py|ProviderAdmission.deployment|import:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py|ProviderAdmission.deployment|ref:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py|ProviderAdmission.dispatch_through|import:resolve_deployment_revision",
    "holdspeak/speech_session/provider.py|ProviderAdmission.dispatch_through|ref:resolve_deployment_revision",
    # HS-200-41: resolve_placement inside ``ProjectService._resolve_stop_reason``.
    # A saved ask task stores a bounded refusal CODE; the reason beside it is
    # the destination's own words, so the resolver is read to ask the LIVE
    # placement this hub would use what it says — and nothing is stored when the
    # hub no longer observes the state the code names.  A provenance read, not a
    # rival route decision, but it is a resolver reference and is registered as
    # one rather than allowed to sit outside the census.
    # HS-200-11 (stacked on 12 over 15, 9a8073fc): the same two sites moved down
    # with the additive Room fields (decision `lifecycle`/`successor_id`, the
    # needs-you `watchId`); re-anchored, not re-registered.
    # HS-200-13 (stacked on 14 over 11 over 12 over 15): moved down again with
    # the Room's commitment attention producer (`_room_commitment_items`);
    # re-anchored, the site unchanged.
    # HS-200-16: moved down 34 lines (+40/-6 above it) by the `_count_unit`
    # helper, the proposal row's `meeting_started_at`, and the Room
    # projections carrying each row's `kind`; re-anchored, the site unchanged.
    # The reference count is still 50 and no added line names a resolver.
    "holdspeak/services/project_service.py|ProjectService._resolve_stop_reason|import:resolve_placement",
    "holdspeak/services/project_service.py|ProjectService._resolve_stop_reason|ref:resolve_placement",
    # Pre-existing and previously UNREGISTERED, found by the HS-200-41 sweep and
    # registered here rather than left red: ``_captured_deployment_revision``
    # (project_update_service.py:1034) resolves a profile's target only to
    # freeze its deployment revision through ``capture_deployment_revision``.
    # The file is byte-identical to HEAD c6e6c1e7 — this census never had a row
    # for it, and HS-200-41 did not create the site.
    # HS-200-11 (same stack): moved down with the shared NAME helper's known-name
    # alias rule and `_known_names_for_room`; the site itself is unchanged.
    "holdspeak/services/project_update_service.py|_captured_deployment_revision|import:resolve_inference_target",
    "holdspeak/services/project_update_service.py|_captured_deployment_revision|ref:resolve_inference_target",
}

ROUTING_POINTER_ATTRIBUTES = {
    "holdspeak/config/core.py|migrate_legacy_endpoints|intel_profile_id",
    "holdspeak/config/core.py|migrate_legacy_endpoints|intel_profile_id#2",
    "holdspeak/config/integrations.py|ThoughtsConfig.__post_init__|inference_target_id",
    "holdspeak/config/integrations.py|ThoughtsConfig.__post_init__|inference_target_id#2",
    "holdspeak/config/meeting.py|MeetingConfig.__post_init__|intel_profile_id#2",
    "holdspeak/config/meeting.py|MeetingConfig.__post_init__|intel_profile_id",
    "holdspeak/db/models/__init__.py|WorkbenchRecord.to_dict|resolver_profile_id",
    "holdspeak/services/inference_setup_service.py|InferenceSetupApplicationService.get_inference_setup|intel_profile_id",
    "holdspeak/services/inference_setup_service.py|InferenceSetupApplicationService.get_inference_setup|inference_target_id",
    "holdspeak/services/inference_setup_service.py|InferenceSetupApplicationService.get_inference_setup|inference_target_id#2",
    "holdspeak/services/inference_setup_service.py|InferenceSetupApplicationService.get_inference_setup|intel_profile_id#2",
    "holdspeak/services/inference_setup_service.py|_thought_target|inference_target_id",
    "holdspeak/services/settings_service.py|SettingsService._update|intel_profile_id",
    "holdspeak/services/settings_service.py|SettingsService._update|inference_target_id",
    "holdspeak/services/workbench_service.py|WorkbenchService._wb_fields|resolver_profile_id",
    # HS-172: resolve_meeting_placement pointer reads
    # HS-201-03: mcp/tools.py moved down three lines (see the reference set).
    # PHILO-7-01/02: moved down again (984 -> 1147); re-anchored, same read.
    "holdspeak/mcp/tools.py|_dispatch|intel_profile_id",
    "holdspeak/web/routes/system/settings.py|_resolve_meetings_host|intel_profile_id",
}

# `profile_id` is deliberately not treated as a synonym for routing.  This
# exhaustive classification makes every production read visible while keeping
# receipts, DTOs, readiness, and unrelated records out of the assignment lane.
PROFILE_ID_CLASSIFICATIONS = {
    **{site: "mutable assignment pointer" for site in {
        "holdspeak/config/core.py|migrate_legacy_endpoints|profile_id", "holdspeak/config/core.py|migrate_legacy_endpoints|profile_id#2",
        "holdspeak/config/integrations.py|RailsObserverConfig.__post_init__|profile_id", "holdspeak/config/integrations.py|RailsObserverConfig.__post_init__|profile_id#2", "holdspeak/config/model.py|LLMRuntimeConfig.__post_init__|profile_id", "holdspeak/config/model.py|LLMRuntimeConfig.__post_init__|profile_id#2",
        "holdspeak/plugins/dictation/assembly.py|_try_build_runtime|profile_id",
        "holdspeak/services/settings_service.py|SettingsService._update|profile_id",
        "holdspeak/services/settings_service.py|SettingsService._update|profile_id#2",
        "holdspeak/services/sync_service.py|_merge_primitive_spec|profile_id",
        "holdspeak/services/sync_service.py|_merge_primitive_spec|profile_id#2",
    }},
    **{site: "display" for site in {
        # HS-201: the inactive live-analysis endpoint display was retired.
        "holdspeak/commands/doctor.py|_check_runtime_profiles|profile_id",
        "holdspeak/commands/doctor.py|_check_runtime_profiles|profile_id#2", "holdspeak/commands/doctor.py|_check_runtime_profiles|profile_id#3",
        "holdspeak/commands/doctor.py|_check_dictation_runtime|profile_id",
        "holdspeak/db/models/__init__.py|RecipeRecord.to_dict|profile_id", "holdspeak/inference_targets.py|InferenceTarget.to_dict|profile_id",
        # HS-162-03: front_door.py profile_id reads (display, Phase 156).
        "holdspeak/web/routes/front_door.py|build_front_door_router.get_topology|profile_id",
        "holdspeak/web/routes/front_door.py|build_front_door_router.get_topology|profile_id#2",
        "holdspeak/web/routes/front_door.py|build_front_door_router.get_topology|profile_id#3",
        "holdspeak/services/ask_service.py|AskService.ask|profile_id",
        "holdspeak/services/inference_setup_service.py|InferenceSetupApplicationService.get_inference_setup|profile_id", "holdspeak/services/settings_service.py|meeting_placement_summary|profile_id",
        "holdspeak/setup_status.py|_trust_block|profile_id",
        "holdspeak/services/model_profile_service.py|ModelProfileRevision.to_dict|profile_id",
        "holdspeak/services/model_profile_service.py|ProfileBinding.to_dict|profile_id",
        # HS-172: meetings host resolve display reads (HS-200-13: +2 lines).
        # PHILO-7-01/02: moved down (987 -> 1150); re-anchored, same read.
        "holdspeak/mcp/tools.py|_dispatch|profile_id",
        "holdspeak/web/routes/system/settings.py|_resolve_meetings_host|profile_id",
    }},
    **{site: "immutable evidence" for site in {
        "holdspeak/services/model_profile_service.py|ModelProfileService._revision_from_row|profile_id",
        "holdspeak/services/inference_assignment_service.py|InferenceAssignmentService._compatibility_issues|profile_id",
    }},
    **{site: "migration source" for site in {
        "holdspeak/db/models/__init__.py|WorkbenchRecord.to_dict|profile_id",
        "holdspeak/services/recipe_service.py|RecipeService._recipe_fields|profile_id",
        "holdspeak/services/workbench_service.py|WorkbenchService._wb_fields|profile_id",
    }},
    **{site: "credential/provider identity" for site in {
        "holdspeak/intel/providers.py|resolve_meeting_placement|profile_id", "holdspeak/intel/providers.py|resolve_meeting_placement|profile_id#2",
        "holdspeak/intel/providers.py|resolve_meeting_placement|profile_id#3", "holdspeak/setup_runtime.py|probe_runtime|profile_id",
        "holdspeak/trust_destinations.py|destination_inventory|profile_id",
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
    definitions: list[Record] = []
    references: list[Record] = []
    pointers: list[Record] = []
    profile_ids: list[Record] = []
    for path in sorted((root / "holdspeak").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        scopes = _scope_index(tree)

        def site(node: ast.AST, what: str) -> Record:
            scope = scopes.get(id(node), "<module>")
            return Record(relative, node.lineno, node.col_offset, f"{scope}|{what}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("resolve_") and (
                    "placement" in node.name
                    or "deployment_revision" in node.name
                    or "inference_target" in node.name
                ):
                    # ``_scope_index`` names a def by its own dotted name.
                    definitions.append(Record(
                        relative, node.lineno, node.col_offset,
                        f"def:{scopes.get(id(node), node.name)}",
                    ))
            elif isinstance(node, ast.Name) and node.id in ROUTING_RESOLVER_NAMES:
                references.append(site(node, f"ref:{node.id}"))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in ROUTING_RESOLVER_NAMES:
                        references.append(site(node, f"import:{alias.name}"))
            elif isinstance(node, ast.Attribute) and node.attr in {
                "inference_target_id", "intel_profile_id", "resolver_profile_id",
                "requested_target_id",
            }:
                pointers.append(site(node, node.attr))
            elif isinstance(node, ast.Attribute) and node.attr == "profile_id":
                profile_ids.append(site(node, "profile_id"))
    return (
        set(_line_free.ordinal_keys(definitions)),
        set(_line_free.ordinal_keys(references)),
        set(_line_free.ordinal_keys(pointers)),
        set(_line_free.ordinal_keys(profile_ids)),
    )


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
    # 39 sites: the line-pinned form counted 37, because two ``__post_init__``
    # lines read ``profile_id`` twice and one ``path:line`` key hid the second read.
    # 38 since 2026-10-05: the stale copy holdspeak/db/models/workbench.py was parked.
    assert len(PROFILE_ID_CLASSIFICATIONS) == 38
    assert sum(value == "mutable assignment pointer" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 11
    assert sum(value == "migration source" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 3
    assert sum(value == "display" for value in PROFILE_ID_CLASSIFICATIONS.values()) == 17
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
    assert definitions == {"holdspeak/kernel/inference.py|def:resolve_late_inference_target"}
    assert references == set()
    assert pointers == {
        "holdspeak/kernel/inference.py|resolve_late_inference_target|requested_target_id"
    }
    assert profile_ids == {"holdspeak/kernel/inference.py|public_profile|profile_id"}
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
