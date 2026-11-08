"""Parked 2026-11-08: the prepared-recipe (practice recipe) catalog routes.

Programs are the one engine for work that runs. These three read-only routes
lived inside ``build_automations_router`` (holdspeak/web/routes/automations.py)
and had no web caller. Kept verbatim; not mounted, not imported.
"""
# ruff: noqa
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from holdspeak.services._parked import recipe_catalog


def mount_practice_recipe_routes(router: APIRouter, ctx: Any, principal: Any) -> None:
    """The body as it stood inside ``build_automations_router``."""
    # ── HS-200-17: the prepared-recipe catalog (contract C5) ──────────
    #
    # Read-only discovery over ``holdspeak.services.recipe_catalog``.  It
    # lives on this existing automations surface, and NOT under
    # ``/api/recipes/...``: that prefix already belongs to the Agent
    # primitive (``primitives/recipes.py``), whose ``/api/recipes/{recipe_id}``
    # would shadow any sibling path added there.  Ruling R17-4: no new face
    # is introduced -- these are JSON reads for the Web app and the MCP
    # sidecar, not a screen.

    def _project_service() -> Any:
        """PHILO-9-01: the ProjectService the Room's declared operations are bound to."""
        from ... import operations

        # A partially wired context (a route test) reads its Room through the
        # automations service's own database, as the route did before.
        return operations.for_context(ctx, "project_service", bare_db=service._db).target("project.get")

    @router.get("/automations/practice-recipes")
    def list_practice_recipes() -> Any:
        return JSONResponse(recipe_catalog.catalog_payload())

    @router.get("/automations/practice-recipes/{recipe_id}")
    def get_practice_recipe(recipe_id: str) -> Any:
        try:
            return JSONResponse(recipe_catalog.get_descriptor(recipe_id).to_dict())
        except recipe_catalog.UnknownRecipe as exc:
            return JSONResponse(
                {"error": str(exc), "code": "unknown_recipe"}, status_code=404
            )

    @router.get("/automations/practice-recipes/{recipe_id}/plan")
    def compile_practice_recipe(
        request: Request,
        recipe_id: str,
        project_id: str = Query("", description="The Project the plan is scoped to."),
        trigger: str = Query(recipe_catalog.TRIGGER_MANUAL),
        version: int | None = Query(None, ge=1),
        purpose: str = Query("", description="Preparation purpose, when the recipe takes one."),
    ) -> Any:
        """Compile a plan. A read: it writes nothing and runs nothing."""
        try:
            inputs: dict[str, Any] = {"project_id": project_id}
            if purpose:
                inputs["purpose"] = purpose
            plan = recipe_catalog.compile_recipe(
                recipe_id,
                version=version,
                trigger=trigger,
                inputs=inputs,
                coverage=recipe_catalog.observed_coverage(
                    _project_service(), principal(request), project_id
                ),
            )
            return JSONResponse(plan.to_dict())
        except recipe_catalog.UnknownRecipe as exc:
            return JSONResponse(
                {"error": str(exc), "code": "unknown_recipe"}, status_code=404
            )
        except recipe_catalog.CatalogError as exc:
            # A broken descriptor is a typed answer, not a 500 (counsel P2-3).
            return JSONResponse(
                {"error": str(exc), "code": "catalog_error"}, status_code=500
            )

