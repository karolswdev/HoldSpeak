"""HS-200-17 (phase200_recipe_catalog): three executable recipe contracts.

The state half of the story, proven against the REAL modules the catalog
binds (no doubles: every qualified ref is imported and every limit is read
off the constant the executing service enforces — a transcribed number
proves only that somebody can transcribe, ``reference_lying_test_doubles``).
The real manual runs live in
``tests/integration/test_phase200_recipe_catalog.py``.

Criteria covered here:

- AC1: each recipe declares input schema, source requirements, output,
  execution owner, effects, and supported triggers.
- AC2: compilation binds qualified refs, source scope, route policy, limits
  and acceptance criteria.
- AC3: missing adapters and unavailable prerequisites produce typed gaps,
  in the SHIPPED C4 coverage vocabulary rather than a parallel one.
- AC4: a manual plan and a scheduled plan share one definition and version.
- AC5: the catalog is discoverable on MCP and Web without widening the
  ordinary Thread palette.
"""
from __future__ import annotations

import importlib
import inspect
from dataclasses import replace

import pytest

from holdspeak.services import recipe_catalog as catalog
from holdspeak.services.needs_you_aggregate import COVERAGE_KINDS, COVERAGE_STATES

def _memory_db():
    """A throwaway Database for router assembly only (no rows are read)."""
    import tempfile
    from pathlib import Path

    from holdspeak.db import Database

    return Database(Path(tempfile.mkdtemp()) / "router.db")


ALL_IDS = (
    catalog.RECIPE_PREPARATION_BRIEF,
    catalog.RECIPE_DECISION_REVIEW,
    catalog.RECIPE_WEEKLY_UPDATE,
)


# ── AC1: the three descriptors declare what C5 requires ─────────────────


class TestDescriptorsDeclareTheContract:
    def test_the_catalog_holds_exactly_the_three_c5_recipes(self) -> None:
        assert sorted(catalog.CATALOG) == sorted(ALL_IDS)

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_c5_field_is_declared_and_non_empty(self, recipe_id: str) -> None:
        d = catalog.get_descriptor(recipe_id)
        assert d.version >= 1
        assert d.title.strip()
        assert d.inputs, "input schema"
        assert d.sources, "source requirements"
        assert d.output.strip() and d.output_owner.strip(), "output + its owner"
        assert d.steps, "execution owner"
        assert d.effects, "effects"
        assert d.triggers, "supported triggers"
        assert d.route_policy.strip()
        assert d.acceptance
        # NOT `assert d.limits`. That assertion is what made an invented
        # limit feel required: weekly_update has no cap because
        # ProjectUpdateService enforces none, and declaring one to satisfy
        # a test is the defect (ruling R17-10).

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_required_input_has_a_description_and_no_default(
        self, recipe_id: str
    ) -> None:
        for spec in catalog.get_descriptor(recipe_id).inputs:
            assert spec.description.strip(), spec.name
            assert spec.type in ("string", "integer"), spec.name
            if spec.required:
                assert spec.default is None, (
                    f"{recipe_id}.{spec.name} is required and also carries a "
                    "default; one of those is a lie"
                )

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_source_kinds_are_c4_kinds_or_the_named_route(self, recipe_id: str) -> None:
        """No parallel vocabulary: a source kind is a C4 coverage kind, with
        ``model_route`` the one named non-source prerequisite."""
        for source in catalog.get_descriptor(recipe_id).sources:
            assert source.kind in tuple(COVERAGE_KINDS) + ("model_route",), source.kind
            assert source.supplied_by.strip(), (
                f"{recipe_id}/{source.kind}: a source with no supplier is a "
                "gap nobody can close (R17-5)"
            )

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_both_trigger_kinds_are_declared_exactly_once(self, recipe_id: str) -> None:
        kinds = [t.trigger for t in catalog.get_descriptor(recipe_id).triggers]
        assert sorted(kinds) == sorted(catalog.TRIGGERS)

    def test_trigger_tokens_are_the_watch_evaluation_cores_tokens(self) -> None:
        """AC4's seam: the catalog does not invent a third scheduling word.

        ``WatchService._evaluate_core`` already spells the two firings
        ``manual`` and ``scheduled``; read them off its real call sites.
        """
        source = inspect.getsource(
            importlib.import_module("holdspeak.services.watch_service")
        )
        assert 'trigger_kind="manual"' in source
        assert 'trigger_kind="scheduled"' in source
        assert catalog.TRIGGERS == ("manual", "scheduled")

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_an_unavailable_trigger_names_what_would_supply_it(
        self, recipe_id: str
    ) -> None:
        for binding in catalog.get_descriptor(recipe_id).triggers:
            assert binding.owner.strip()
            assert binding.supplied_by.strip(), (
                f"{recipe_id}/{binding.trigger}: no fake all-clear and no "
                "nameless blocker (R17-5)"
            )


# ── AC2: the refs, the limits and the fields are REAL ───────────────────


class TestBindingIsReal:
    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_qualified_ref_imports_to_a_real_method(self, recipe_id: str) -> None:
        for step in catalog.get_descriptor(recipe_id).steps:
            fn = catalog.resolve_step(step)
            assert callable(fn)
            assert fn.__qualname__ == step.attr_path, step.qualified_ref

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_bound_name_is_a_real_parameter(self, recipe_id: str) -> None:
        for step in catalog.get_descriptor(recipe_id).steps:
            params = inspect.signature(catalog.resolve_step(step)).parameters
            for bound in step.binds:
                assert bound in params, f"{step.qualified_ref} does not take {bound!r}"

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_runtime_field_the_descriptor_names_exists_on_the_root(
        self, recipe_id: str
    ) -> None:
        from holdspeak.runtime.composition import SERVICE_FIELDS

        for step in catalog.get_descriptor(recipe_id).steps:
            assert catalog.runtime_field_is_real(step)
            if step.runtime_field:
                assert step.runtime_field in SERVICE_FIELDS

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_nothing_is_declared_that_no_step_can_read(self, recipe_id: str) -> None:
        """Ruling R17-10: no invented limit, no orphaned input.

        The defect this replaces: ``weekly_update`` carried
        ``max_claims: 40`` bound to no step and enforced by nothing, and
        ``decision_review`` advertised an ``interval_days`` window neither
        of its steps can accept.
        """
        assert catalog.unreachable_declarations(
            catalog.get_descriptor(recipe_id)
        ) == []

    def test_the_fence_sees_an_invented_literal_limit(self) -> None:
        """The exact mutation that slipped through: a literal nothing reads."""
        d = catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE)
        invented = replace(
            d, limits=d.limits + (catalog.Limit("max_claims", "literal:40", "x"),)
        )
        assert catalog.unreachable_declarations(invented) == ["limit 'max_claims'"]

    def test_the_fence_sees_an_input_no_step_binds(self) -> None:
        d = catalog.get_descriptor(catalog.RECIPE_DECISION_REVIEW)
        orphaned = replace(
            d,
            inputs=d.inputs + (
                catalog.InputField("interval_days", "integer", False, "x", default=7),
            ),
        )
        assert catalog.unreachable_declarations(orphaned) == ["input 'interval_days'"]

    def test_a_constant_backed_limit_is_exempt_from_the_binding_rule(self) -> None:
        """It documents a bound the service enforces without being passed."""
        prep = catalog.get_descriptor(catalog.RECIPE_PREPARATION_BRIEF)
        assert [limit.name for limit in prep.limits] == [
            "max_priorities", "max_questions", "max_obligations",
        ]
        assert all(not limit.source.startswith("literal:") for limit in prep.limits)
        assert catalog.unreachable_declarations(prep) == []

    def test_weekly_update_declares_no_cap_because_none_exists(self) -> None:
        """An absent limit is honest; an invented one is not.

        Asserted against the real service: no claim ceiling, no truncation.
        """
        from holdspeak.services import project_update_service as updates

        assert catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE).limits == ()
        caps = [
            name for name in dir(updates)
            if name.isupper() and isinstance(getattr(updates, name), int)
            and not isinstance(getattr(updates, name), bool)
        ]
        assert caps == [], (
            f"{updates.__name__} gained integer constants {caps}; if one is a "
            "claim cap, the descriptor should now bind it"
        )

    def test_limits_are_read_off_the_real_constants_not_transcribed(self) -> None:
        """The preparation caps come from the Outline the service enforces."""
        from holdspeak.services.preparation_brief_service import (
            MAX_OBLIGATIONS,
            MAX_PRIORITIES,
            MAX_QUESTIONS,
        )

        limits = catalog.resolve_limits(
            catalog.get_descriptor(catalog.RECIPE_PREPARATION_BRIEF)
        )
        assert limits == {
            "max_priorities": MAX_PRIORITIES,
            "max_questions": MAX_QUESTIONS,
            "max_obligations": MAX_OBLIGATIONS,
        }

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_every_declared_limit_resolves_to_an_int(self, recipe_id: str) -> None:
        """Whatever is declared must resolve. Declaring nothing is lawful."""
        descriptor = catalog.get_descriptor(recipe_id)
        resolved = catalog.resolve_limits(descriptor)
        assert set(resolved) == {limit.name for limit in descriptor.limits}
        assert all(isinstance(v, int) for v in resolved.values())

    def test_the_review_decision_limit_stays_inside_the_services_own_cap(self) -> None:
        """``list_records`` clamps at 500; a catalog limit above that would be
        a number the service silently ignores."""
        source = inspect.getsource(
            importlib.import_module(
                "holdspeak.services.decision_record_service"
            ).DecisionRecordService.list_records
        )
        assert "min(int(limit), 500)" in source
        limits = catalog.resolve_limits(
            catalog.get_descriptor(catalog.RECIPE_DECISION_REVIEW)
        )
        assert limits["limit"] <= 500

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_a_compiled_plan_carries_every_c5_binding(self, recipe_id: str) -> None:
        d = catalog.get_descriptor(recipe_id)
        plan = catalog.compile_recipe(
            recipe_id,
            inputs={"project_id": "proj_x", "purpose": "cut-over sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        assert plan.recipe_id == recipe_id
        assert plan.recipe_version == d.version
        assert plan.plan_id.startswith("plan_")
        assert plan.revision == 1
        assert [s["qualified_ref"] for s in plan.steps] == [
            s.qualified_ref for s in d.steps
        ]
        assert all(s["bound"] for s in plan.steps)
        assert plan.route_policy == d.route_policy
        assert plan.limits == catalog.resolve_limits(d)
        assert plan.acceptance == list(d.acceptance)
        assert {row["kind"] for row in plan.source_scope} == {
            s.kind for s in d.sources
        }
        assert plan.ready, plan.gaps

    def test_call_arguments_resolve_from_inputs_then_limits(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_DECISION_REVIEW,
            inputs={"project_id": "proj_x"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        assert catalog.call_arguments(plan, "obligations") == {"project_id": "proj_x"}
        assert catalog.call_arguments(plan, "decisions") == {"limit": plan.limits["limit"]}

    def test_the_same_request_compiles_to_the_same_plan_identity(self) -> None:
        """C6 replay: the same payload is the same plan, not a second one."""
        kwargs = dict(
            inputs={"project_id": "proj_x", "purpose": "cut-over sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        a = catalog.compile_recipe(catalog.RECIPE_PREPARATION_BRIEF, **kwargs)
        b = catalog.compile_recipe(catalog.RECIPE_PREPARATION_BRIEF, **kwargs)
        assert a.plan_id == b.plan_id
        c = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            inputs={"project_id": "proj_y", "purpose": "cut-over sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        assert c.plan_id != a.plan_id


# ── AC3: typed gaps, in the shipped vocabulary ──────────────────────────


class TestTypedGaps:
    def test_gap_states_are_c4_coverage_states(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF, inputs={"project_id": "p"}
        )
        assert plan.gaps
        for row in plan.gaps:
            assert row["state"] in COVERAGE_STATES, row
            assert row["kind"] in catalog.GAP_KINDS, row

    def test_every_gap_names_what_is_missing_and_what_supplies_it(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE,
            version=99,
            trigger=catalog.TRIGGER_SCHEDULED,
            inputs={},
        )
        assert plan.gaps
        for row in plan.gaps:
            assert row["missing"].strip(), row
            assert row["supplied_by"].strip(), row

    def test_a_gap_may_not_be_minted_without_a_supplier(self) -> None:
        """R17-5 enforced at the constructor, not by convention."""
        with pytest.raises(catalog.CatalogError):
            catalog.gap(
                kind=catalog.GAP_MISSING_ADAPTER, state="unavailable",
                subject="x", missing="something", supplied_by="   ",
            )

    def test_a_gap_may_not_invent_a_state_outside_c4(self) -> None:
        with pytest.raises(catalog.CatalogError):
            catalog.gap(
                kind=catalog.GAP_MISSING_ADAPTER, state="degraded",
                subject="x", missing="m", supplied_by="s",
            )

    # -- stale descriptor version ------------------------------------

    def test_a_stale_descriptor_version_is_a_typed_gap_not_a_silent_upgrade(
        self,
    ) -> None:
        current = catalog.get_descriptor(catalog.RECIPE_PREPARATION_BRIEF).version
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            version=current + 1,
            inputs={"project_id": "p", "purpose": "sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        stale = [g for g in plan.gaps if g["kind"] == catalog.GAP_STALE_DESCRIPTOR]
        assert len(stale) == 1
        assert stale[0]["state"] == "stale"
        assert str(current) in stale[0]["missing"]
        assert not plan.ready
        # The plan still reports the version the TREE ships, never the one
        # the caller asked for: a saved plan cannot rename the descriptor.
        assert plan.recipe_version == current

    def test_the_matching_version_produces_no_stale_gap(self) -> None:
        current = catalog.get_descriptor(catalog.RECIPE_PREPARATION_BRIEF).version
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            version=current,
            inputs={"project_id": "p", "purpose": "sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        assert [g for g in plan.gaps if g["kind"] == catalog.GAP_STALE_DESCRIPTOR] == []

    # -- missing adapter ---------------------------------------------

    def test_a_missing_adapter_is_a_typed_gap_naming_the_ref(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Swap ONE descriptor's step for a ref that does not exist and
        compile: the plan must report it rather than raise or pretend."""
        broken = replace(
            catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE),
            steps=(
                replace(
                    catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE).steps[0],
                    qualified_ref=(
                        "holdspeak.services.project_update_service:"
                        "ProjectUpdateService.draft_update_via_absent_adapter"
                    ),
                    binds=(),
                ),
            ),
        )
        monkeypatch.setitem(catalog.CATALOG, catalog.RECIPE_WEEKLY_UPDATE, broken)
        plan = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE,
            inputs={"project_id": "p"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        missing = [g for g in plan.gaps if g["kind"] == catalog.GAP_MISSING_ADAPTER]
        assert len(missing) == 1
        assert "draft_update_via_absent_adapter" in missing[0]["subject"]
        assert plan.steps[0]["bound"] is False
        assert not plan.ready

    def test_a_runtime_field_the_root_does_not_carry_is_a_missing_adapter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        d = catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE)
        broken = replace(
            d, steps=(replace(d.steps[0], runtime_field="update_factory_service"),)
        )
        monkeypatch.setitem(catalog.CATALOG, catalog.RECIPE_WEEKLY_UPDATE, broken)
        plan = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE,
            inputs={"project_id": "p"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        missing = [g for g in plan.gaps if g["kind"] == catalog.GAP_MISSING_ADAPTER]
        assert len(missing) == 1
        assert "update_factory_service" in missing[0]["missing"]

    def test_a_broken_ref_raises_rather_than_shipping_quietly(self) -> None:
        """A catalog bug is not an installation fact: resolve_step raises."""
        step = replace(
            catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE).steps[0],
            binds=("not_a_parameter",),
        )
        with pytest.raises(catalog.CatalogError, match="not_a_parameter"):
            catalog.resolve_step(step)

    # -- unsupported trigger -----------------------------------------

    def test_an_unknown_trigger_kind_is_a_typed_gap(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            trigger="on_commit",
            inputs={"project_id": "p", "purpose": "sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        bad = [g for g in plan.gaps if g["kind"] == catalog.GAP_UNSUPPORTED_TRIGGER]
        assert len(bad) == 1
        assert "on_commit" in bad[0]["subject"]
        assert not plan.ready

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_the_scheduled_trigger_is_honestly_unwired_today(
        self, recipe_id: str
    ) -> None:
        """No recipe may claim an unattended firing it cannot produce (C9)."""
        plan = catalog.compile_recipe(
            recipe_id,
            trigger=catalog.TRIGGER_SCHEDULED,
            inputs={"project_id": "p", "purpose": "sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        unwired = [
            g for g in plan.gaps
            if g["reason"] == "trigger_owner_not_wired"
        ]
        assert len(unwired) == 1, plan.gaps
        assert unwired[0]["supplied_by"].strip()
        assert not plan.ready

    # -- unavailable prerequisites -----------------------------------

    def test_an_unobserved_required_source_is_unavailable_never_an_all_clear(
        self,
    ) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_DECISION_REVIEW, inputs={"project_id": "p"}, coverage={}
        )
        project = [r for r in plan.source_scope if r["kind"] == "project"][0]
        assert project["state"] == "unavailable"
        prereq = [
            g for g in plan.gaps
            if g["kind"] == catalog.GAP_UNAVAILABLE_PREREQUISITE
            and g["subject"] == "project"
        ]
        assert len(prereq) == 1
        assert not plan.ready

    def test_a_stale_required_source_keeps_its_own_state_on_the_gap(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE,
            inputs={"project_id": "p"},
            coverage={"project": "stale"},
        )
        prereq = [g for g in plan.gaps if g["subject"] == "project"][0]
        assert prereq["state"] == "stale"

    def test_an_optional_source_never_blocks_the_plan(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_WEEKLY_UPDATE,
            inputs={"project_id": "p"},
            coverage={"project": "available"},
        )
        assert plan.ready, plan.gaps
        watch = [r for r in plan.source_scope if r["kind"] == "watch"][0]
        assert watch["state"] == "unavailable"
        assert watch["required"] is False

    def test_a_coverage_state_outside_c4_is_a_programming_error(self) -> None:
        with pytest.raises(catalog.CatalogError, match="C4 coverage state"):
            catalog.compile_recipe(
                catalog.RECIPE_WEEKLY_UPDATE,
                inputs={"project_id": "p"},
                coverage={"project": "probably_fine"},
            )

    def test_a_missing_required_input_is_a_typed_gap(self) -> None:
        plan = catalog.compile_recipe(
            catalog.RECIPE_PREPARATION_BRIEF,
            inputs={"project_id": "p"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        missing = [g for g in plan.gaps if g["kind"] == catalog.GAP_MISSING_INPUT]
        assert [g["subject"] for g in missing] == ["purpose"]
        assert not plan.ready

    def test_an_unknown_recipe_id_refuses_by_name_with_a_stable_code(
        self,
    ) -> None:
        """Counsel P2-2: over MCP a bare Exception loses its code."""
        from holdspeak.services.errors import ServiceError

        with pytest.raises(catalog.UnknownRecipe, match="weekly_standup") as caught:
            catalog.get_descriptor("weekly_standup")
        assert isinstance(caught.value, ServiceError)
        assert caught.value.code == "unknown_recipe"
        assert caught.value.context["status"] == 404

    def test_a_catalog_error_also_carries_a_stable_code(self) -> None:
        from holdspeak.services.errors import ServiceError

        with pytest.raises(catalog.CatalogError) as caught:
            catalog.gap(
                kind="not_a_kind", state="unavailable", subject="x",
                missing="m", supplied_by="s",
            )
        assert isinstance(caught.value, ServiceError)
        assert caught.value.code == "catalog_error"


# ── AC4: one definition, two triggers ───────────────────────────────────


class TestOneDefinitionTwoTriggers:
    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_manual_and_scheduled_plans_share_definition_version_and_steps(
        self, recipe_id: str
    ) -> None:
        kwargs = dict(
            inputs={"project_id": "proj_x", "purpose": "cut-over sync"},
            coverage={kind: "available" for kind in COVERAGE_KINDS},
        )
        manual = catalog.compile_recipe(
            recipe_id, trigger=catalog.TRIGGER_MANUAL, **kwargs
        )
        scheduled = catalog.compile_recipe(
            recipe_id, trigger=catalog.TRIGGER_SCHEDULED, **kwargs
        )
        assert manual.recipe_id == scheduled.recipe_id
        assert manual.recipe_version == scheduled.recipe_version
        assert [s["qualified_ref"] for s in manual.steps] == [
            s["qualified_ref"] for s in scheduled.steps
        ]
        assert manual.limits == scheduled.limits
        assert manual.acceptance == scheduled.acceptance
        # The same plan reached two ways, not two plans.
        assert manual.plan_id == scheduled.plan_id
        # Only the firing differs.
        assert manual.trigger != scheduled.trigger
        assert manual.trigger_owner != scheduled.trigger_owner

    @pytest.mark.parametrize("recipe_id", ALL_IDS)
    def test_the_scheduled_owner_is_the_one_chain_that_actually_recurs(
        self, recipe_id: str
    ) -> None:
        """Rulings R17-8 and R17-12: a declared trigger owner must be able
        to fire, and it must name the specific adapter, not "the sweep"."""
        binding = catalog.get_descriptor(recipe_id).trigger(catalog.TRIGGER_SCHEDULED)
        assert binding is not None
        assert binding.owner == catalog.SCHEDULED_TRIGGER_OWNER
        for link in (
            "connector_watches", "HeartbeatService.run_sweep",
            "WatchService.evaluate_due", "project.steward.run_once",
            "ProjectStewardService.run_due",
        ):
            assert link in binding.owner, link

    def test_each_recipes_supplied_by_names_the_specific_thing_to_wire(
        self,
    ) -> None:
        """Not "add a sweep step" -- the adapter a future story must add."""
        for recipe_id in ALL_IDS:
            supplied = catalog.get_descriptor(recipe_id).trigger(
                catalog.TRIGGER_SCHEDULED
            ).supplied_by
            assert "HS-200-" in supplied, f"{recipe_id} names no owning story"
            assert (
                "action_kind" in supplied
                or "watch interval" in supplied
                or "project.steward.run_once" in supplied
            ), f"{recipe_id} does not name the adapter to wire: {supplied}"

    def test_the_effect_kind_the_chain_names_is_in_the_real_registry(self) -> None:
        from holdspeak.watch_validation import ACTION_KINDS

        assert "project.steward.run_once" in ACTION_KINDS

    def test_cadence_is_not_a_scheduler_and_no_descriptor_may_claim_it(
        self,
    ) -> None:
        """The finding this fence exists for.

        ``cadence_loops`` is a projection keyed ``(source_type, source_id)``
        with no next-fire column, and ``CadenceService`` has no create
        operation. Asserted against the real schema and the real class, so
        the day cadence DOES gain a schedule this test fails and the ruling
        is revisited deliberately.
        """
        from holdspeak.db import schema
        from holdspeak.services.cadence_service import CadenceService

        table = schema.SCHEMA_SQL.split("CREATE TABLE IF NOT EXISTS cadence_loops")[1]
        table = table.split(");")[0]
        for absent in ("next_evaluation_at", "next_fire_at", "cadence_minutes", "rrule"):
            assert absent not in table, f"cadence_loops now carries {absent}"

        verbs = {
            name for name in dir(CadenceService)
            if not name.startswith("_") and callable(getattr(CadenceService, name))
        }
        assert not (verbs & {"create", "create_loop", "schedule", "set_schedule"}), (
            f"CadenceService gained a scheduling verb: {sorted(verbs)}"
        )
        assert catalog.SCHEDULED_TRIGGER_OWNER != "CadenceService"

    def test_the_steward_is_an_executor_not_a_trigger_owner(self) -> None:
        """``project.steward.trigger`` still answers scheduler_not_wired."""
        family = inspect.getsource(
            importlib.import_module("holdspeak.mcp.families.project")
        )
        assert "scheduler_not_wired" in family
        assert catalog.SCHEDULED_TRIGGER_OWNER != "ProjectStewardService"
        # ...and the steward IS still named as the executor of the update.
        update = catalog.get_descriptor(catalog.RECIPE_WEEKLY_UPDATE)
        assert "Steward" in update.trigger(catalog.TRIGGER_SCHEDULED).supplied_by \
            or "steward" in update.trigger(catalog.TRIGGER_SCHEDULED).supplied_by


# ── AC5: discoverable, without widening the ordinary Thread palette ─────


class TestDiscoverability:
    def test_the_three_catalog_tools_are_registered_on_mcp(self) -> None:
        from holdspeak.mcp.tools import TOOLS

        names = {t["name"] for t in TOOLS}
        assert {
            "practice_recipe.list",
            "practice_recipe.get",
            "practice_recipe.compile",
        } <= names

    def test_the_family_imported_cleanly(self) -> None:
        from holdspeak.mcp.families import DEGRADED_FAMILIES

        assert "practice_recipe" not in DEGRADED_FAMILIES, DEGRADED_FAMILIES

    def test_the_ordinary_thread_palette_did_not_widen(self) -> None:
        """Ruling R17-3, fenced: classified for the gate, absent from the
        palette a chat turn OFFERS the model."""
        from holdspeak.services.thread_tools import CHAT_PALETTE, TOOL_NAMES

        for name in (
            "practice_recipe.list", "practice_recipe.get", "practice_recipe.compile",
        ):
            assert name in TOOL_NAMES, f"{name} must be classified (fail-closed gate)"
            assert name not in CHAT_PALETTE, f"{name} widened the Thread palette"

    def test_the_catalog_tools_are_reads(self) -> None:
        from holdspeak.services.thread_tools import tool_class

        for name in (
            "practice_recipe.list", "practice_recipe.get", "practice_recipe.compile",
        ):
            assert tool_class(name) == "evidence_read"

    def test_the_prepared_catalog_never_collides_with_the_agent_namespace(self) -> None:
        """``recipe.*`` is the Agent primitive and predates this story."""
        from holdspeak.mcp.tools import TOOLS

        agents = {t["name"] for t in TOOLS if t["name"].startswith("recipe.")}
        prepared = {t["name"] for t in TOOLS if t["name"].startswith("practice_recipe.")}
        assert agents and prepared
        assert agents.isdisjoint(prepared)

    def test_the_mcp_family_never_opens_its_own_database(self) -> None:
        """R17-2, re-derived with the shipped AST guard's own rule.

        ``test_phase200_one_composition_root`` sweeps every file under
        ``holdspeak/mcp/``; this narrows the same walk to the new family so
        the failure names it directly.  A ``get_database`` reference is
        lawful only as the fallback ARGUMENT of ``db_or``.
        """
        import ast
        import pathlib

        tree = ast.parse(
            pathlib.Path("holdspeak/mcp/families/practice_recipe.py").read_text(
                encoding="utf-8"
            )
        )
        allowed: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            fname = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if fname in ("db_or", "observer_or"):
                allowed.update(id(arg) for arg in node.args)
        offenders = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else getattr(node.func, "id", "")
            )
            in ("get_database", "get_observer")
            and id(node) not in allowed
        ]
        assert offenders == [], [node.lineno for node in offenders]
        assert any(
            isinstance(node, ast.Call)
            and getattr(node.func, "id", "") == "db_or"
            for node in ast.walk(tree)
        ), "the family must reach the database through the composition root"

    def test_the_web_surface_declares_the_three_catalog_paths(self) -> None:
        """Read off the assembled router, not the source text.

        ``tests/integration/test_phase200_recipe_catalog.py::TestWebWire``
        actually calls them; this only pins the paths so a rename is loud.
        """
        from holdspeak.services.reaction_service import ReactionService
        from holdspeak.web.routes.automations import build_automations_router

        class _Ctx:
            reaction_service = ReactionService(_memory_db())

        paths = {route.path for route in build_automations_router(_Ctx()).routes}
        assert {
            "/api/automations/practice-recipes",
            "/api/automations/practice-recipes/{recipe_id}",
            "/api/automations/practice-recipes/{recipe_id}/plan",
        } <= paths

    def test_the_wire_payload_carries_the_vocabularies_it_uses(self) -> None:
        payload = catalog.catalog_payload()
        assert [r["recipe_id"] for r in payload["recipes"]] == list(ALL_IDS)
        assert payload["coverage_states"] == list(COVERAGE_STATES)
        assert payload["triggers"] == list(catalog.TRIGGERS)
        assert payload["gap_kinds"] == list(catalog.GAP_KINDS)
