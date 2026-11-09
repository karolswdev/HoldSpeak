"""PARKED 20261108 (Lane S2): cases of ``tests/unit/test_placement_provenance.py`` that drove the item queue.

The item queue is parked (holdspeak/services/_parked/workbench_runner_queue_20261108.py);
an automation's run is a Program of one prompt step. Not collected; they import the
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_placement_provenance import *  # noqa: F401,F403


def test_workbench_run_placement(tmp_path, monkeypatch):
    """Workbench run projects egress only from its frozen parent route."""
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db = Database(tmp_path / "wb_prov.db")

    class FakeIntel:
        active_provider = "test-provider"
        active_model = "test-model"

        def run_prompt(self, **kwargs):
            return "wb-output"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **_: FakeIntel(),
    )
    profile = db.profiles.upsert(
        profile_id="wb_profile",
        name="Profile",
        kind="openAICompatible",
        base_url="http://profile",
        model="model",
    )
    recipe = db.recipes.upsert(
        recipe_id="wb_recipe",
        name="Runner",
        system_prompt="SYS",
        user_template="{input}",
    )
    workbench = db.workbenches.upsert(
        workbench_id="wb_1",
        name="Runner",
        recipe_id=recipe.id,
        profile_id=profile.id,
    )
    db.workbench_items.upsert(
        item_id="item_1",
        workbench_id=workbench.id,
        title="Item 1",
        body="input 1",
    )
    broker = _configure(db)
    result = asyncio.run(
        WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False)
    )
    assert "placement" in result, f"placement missing from workbench run: {sorted(result)}"
    # No service-local source/target decision survives the cutover. The public
    # projection comes from the route frozen with the parent bundle.
    assert result["placement"]["model"] == profile.id
    assert result["placement"]["deployment_revision_id"]
    assert "source" not in result["placement"] and "effective_target_id" not in result["placement"]
    with db._connection() as conn:
        member = conn.execute(
            "SELECT member.route_plan_id FROM inference_parent_route_bundle_members member "
            "JOIN inference_parent_route_bundles bundle ON bundle.id=member.bundle_id "
            "WHERE bundle.parent_operation_id=?", (result["parent_operation_id"],)
        ).fetchone()
        entry = conn.execute(
            "SELECT profile_id,deployment_revision_id FROM inference_route_plan_entries WHERE plan_id=?",
            (member["route_plan_id"],),
        ).fetchone()
    assert member is not None and entry is not None
    assert (entry["profile_id"], entry["deployment_revision_id"]) == (
        f"legacy-{profile.id}", result["placement"]["deployment_revision_id"],
    )


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cadence (LLM-drafted path)
# ---------------------------------------------------------------------------
