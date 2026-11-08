"""Parked 2026-11-08 with the prepared-recipe catalog (holdspeak/services/_parked/recipe_catalog.py).

The three USER_GUIDE claims and their predicates, verbatim from
tests/unit/doc_claims/registry.py. Kept, not collected.
"""
# ruff: noqa

PARKED_CLAIMS = """
    # ── paid by HS-200-17 (the prepared-recipe catalog) ──────────────
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="A descriptor declares a limit only where one is real.",
        sentence=(
            "A descriptor declares a limit only where one is real. Where "
            "the executing service enforces a cap, the descriptor points at "
            "that service's own value and reads it rather than repeating "
            "the number. Where no cap exists, it declares none. The same "
            "rule covers inputs: none of the three offers a setting no step "
            "can act on."
        ),
        predicate=lambda: _prepared_recipes_declare_nothing_unreadable(),
        state="holds",
        truth=(
            "no descriptor carries a literal: limit or an input that no "
            "step binds (recipe_catalog.unreachable_declarations is empty "
            "for all three), and weekly_update declares no limits at all "
            "because ProjectUpdateService enforces no claim cap"
        ),
        story="HS-200-17",
    ),
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="Three prepared procedures ship",
        sentence=(
            "Three prepared procedures ship: meeting preparation, decision "
            "and commitment review, and the weekly project update. Each is a "
            "versioned descriptor in the product tree, bound to the service "
            "that already does the work."
        ),
        predicate=lambda: _prepared_catalog_is_the_declared_three(),
        state="holds",
        truth=(
            "holdspeak/services/recipe_catalog.py holds exactly "
            "preparation_brief, decision_review and weekly_update, and every "
            "execution step of all three imports to a real method on a "
            "service that shipped before HS-200-17"
        ),
        story="HS-200-17",
    ),
    Claim(
        doc="docs/USER_GUIDE.md",
        anchor="**None of the three fires on a schedule yet.**",
        sentence=(
            "None of the three fires on a schedule yet. All three name the "
            "same owner path, the one that really recurs in this product: "
            "a connector watch on its evaluation interval, swept by the "
            "Heartbeat, whose due evaluation mints an effect the steward "
            "drains for that project. No effect kind names one of these "
            "three yet."
        ),
        predicate=lambda: _no_prepared_recipe_has_a_wired_schedule(),
        state="holds",
        truth=(
            "every descriptor's TRIGGER_SCHEDULED binding names the "
            "connector_watches -> run_sweep -> evaluate_due -> "
            "project.steward.run_once -> run_due chain and carries "
            "available=False, so compiling under it yields a "
            "trigger_owner_not_wired gap; CadenceService still exposes no "
            "create/schedule verb and cadence_loops carries no next-fire "
            "column; and no module in that chain imports recipe_catalog. "
            "The day one of them does, this predicate goes False and the "
            "sentence must be corrected in the same commit"
        ),
        story="HS-200-17",
    ),

"""


def _prepared_recipes_declare_nothing_unreadable() -> bool:
    """No invented limit, no orphaned input (HS-200-17 ruling R17-10)."""
    from holdspeak.services import recipe_catalog as catalog

    return all(
        catalog.unreachable_declarations(descriptor) == []
        for descriptor in catalog.list_descriptors()
    )


def _prepared_catalog_is_the_declared_three() -> bool:
    """The catalog holds those three ids and every step really resolves."""
    from holdspeak.services import recipe_catalog as catalog

    if sorted(catalog.CATALOG) != sorted(
        (
            catalog.RECIPE_PREPARATION_BRIEF,
            catalog.RECIPE_DECISION_REVIEW,
            catalog.RECIPE_WEEKLY_UPDATE,
        )
    ):
        return False
    try:
        for descriptor in catalog.list_descriptors():
            for step in descriptor.steps:
                catalog.resolve_step(step)
    except catalog.CatalogError:
        return False
    return True


def _no_prepared_recipe_has_a_wired_schedule() -> bool:
    """True while no descriptor claims an unattended firing it cannot make.

    Also checks the two owners the sentence rules OUT, against the real
    class and the real schema rather than against this file's memory of
    them (HS-200-17 ruling R17-8).
    """
    from holdspeak.db import schema
    from holdspeak.services import recipe_catalog as catalog
    from holdspeak.services.cadence_service import CadenceService

    for descriptor in catalog.list_descriptors():
        binding = descriptor.trigger(catalog.TRIGGER_SCHEDULED)
        if binding is None or binding.available:
            return False
        if binding.owner != catalog.SCHEDULED_TRIGGER_OWNER:
            return False
    for link in (
        "connector_watches", "HeartbeatService.run_sweep",
        "WatchService.evaluate_due", "project.steward.run_once",
        "ProjectStewardService.run_due",
    ):
        if link not in catalog.SCHEDULED_TRIGGER_OWNER:
            return False
    verbs = {name for name in dir(CadenceService) if not name.startswith("_")}
    if verbs & {"create", "create_loop", "schedule", "set_schedule"}:
        return False
    loops = schema.SCHEMA_SQL.split(
        "CREATE TABLE IF NOT EXISTS cadence_loops"
    )[1].split(");")[0]
    if any(
        column in loops
        for column in ("next_evaluation_at", "next_fire_at", "rrule")
    ):
        return False

    # The direct check on the event the sentence actually describes: no
    # module in the recurring chain reaches the prepared-recipe catalog.
    # Without this the predicate only proved the descriptors still SAY
    # available=False, which a builder could forget to flip.
    for relative in (
        "holdspeak/runtime/heartbeat.py",
        "holdspeak/services/heartbeat_service.py",
        "holdspeak/services/watch_service.py",
        "holdspeak/services/project_steward_service.py",
    ):
        if "recipe_catalog" in _read(relative):
            return False
    return True


