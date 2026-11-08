"""HS-200-17: the prepared-recipe catalog on MCP (contract C5).

Three read-only tools over :mod:`holdspeak.services.recipe_catalog`.  They
are deliberately namespaced ``practice_recipe.*``: ``recipe.*`` has meant
*Agent* (a user-authored saved prompt) on this wire since HS-116, and C5's
prepared recipes are the other thing entirely.

Ruling R17-3: discoverability rides this existing registry.  None of these
names is added to ``thread_tools.CHAT_PALETTE`` — the ordinary Thread
palette does not widen for this story; they are classified as
``evidence_read`` in ``thread_tools._TOOL_CLASSES`` so the fail-closed
classification census (``tests/unit/test_thread_tool_gate.py``) stays green
and the gate can still resolve a call the model makes under a narrowing
mode.

Ruling R17-2: the one database handle comes from the composition root via
``db_or``; nothing under ``holdspeak/mcp/`` opens a bare handle of its own.
``practice_recipe.compile`` reads the REAL coverage of the named Project so
its typed gaps describe this installation rather than a guess.
"""
from __future__ import annotations

from typing import Any

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services import recipe_catalog as catalog

TOOLS: list[dict[str, Any]] = [
    {
        "name": "practice_recipe.list",
        "description": (
            "List the prepared recipe catalog: the three versioned descriptors "
            "(meeting preparation, decision and commitment review, weekly Project "
            "update) with their input schema, source requirements, output, "
            "execution owner, effects, supported triggers, limits and acceptance "
            "criteria. Not the Agent catalogue -- that is recipe.list."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "practice_recipe.get",
        "description": (
            "Read one prepared recipe descriptor by id "
            "(preparation_brief | decision_review | weekly_update)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "string",
                    "description": "Prepared recipe id.",
                },
            },
            "required": ["recipe_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "practice_recipe.compile",
        "description": (
            "Compile a configuration plan for one prepared recipe against a "
            "Project: binds the qualified execution refs, the source scope and its "
            "observed coverage, the route policy, the limits and the acceptance "
            "criteria, and returns a typed gap for every missing adapter, "
            "unavailable prerequisite, stale descriptor version and unsupported "
            "trigger. Writes nothing and runs nothing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "string",
                    "description": "Prepared recipe id.",
                },
                "project_id": {
                    "type": "string",
                    "description": "The Project the plan is scoped to.",
                },
                "trigger": {
                    "type": "string",
                    "enum": list(catalog.TRIGGERS),
                    "description": (
                        "Which firing this plan is for. The same descriptor and "
                        "version serves both."
                    ),
                },
                "version": {
                    "type": "integer",
                    "minimum": 1,
                    "description": (
                        "The descriptor version the caller believes it is "
                        "configuring. A disagreement returns a stale_descriptor gap."
                    ),
                },
                "inputs": {
                    "type": "object",
                    "description": "Additional recipe inputs beyond project_id.",
                },
            },
            "required": ["recipe_id", "project_id"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call. Raises LookupError for unowned names."""
    if name == "practice_recipe.list":
        return catalog.catalog_payload()

    if name == "practice_recipe.get":
        descriptor = catalog.get_descriptor(str(arguments.get("recipe_id") or ""))
        return descriptor.to_dict()

    if name == "practice_recipe.compile":
        db = db_or(get_database)
        obs = observer_or(get_observer)
        # R17-2: the hub's live ProjectService when there is one; the
        # coverage read goes through the Room projection, which is what the
        # C4 producer consumes (R17-9).
        from holdspeak.services.project_service import ProjectService

        projects = runtime_service(
            "project_service", lambda: ProjectService(db, observer=obs)
        )
        recipe_id = str(arguments.get("recipe_id") or "")
        project_id = str(arguments.get("project_id") or "")
        supplied = arguments.get("inputs")
        inputs: dict[str, Any] = dict(supplied) if isinstance(supplied, dict) else {}
        inputs.setdefault("project_id", project_id)
        version = arguments.get("version")
        plan = catalog.compile_recipe(
            recipe_id,
            version=int(version) if version is not None else None,
            trigger=str(arguments.get("trigger") or catalog.TRIGGER_MANUAL),
            inputs=inputs,
            coverage=catalog.observed_coverage(projects, principal, project_id),
        )
        return plan.to_dict()

    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
