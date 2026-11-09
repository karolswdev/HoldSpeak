"""The Agent recipes' writes on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``automation_operations.py`` is. Each row states one
``RecipeService`` write once: its call, its HTTP method and path, and its MCP
tool schema. ``web/routes/primitives/recipes.py`` produces the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``. The reads and the run stay on the hand-written
``recipe.list`` / ``recipe.get`` / ``recipe.run`` tools.

Each call answers the shape the hand-written route answered (the desk reads it
unchanged) and names a missing recipe in the route's words ("Unknown Agent:
<id>"). The registry announces each write once (kind ``recipe``, the kind the
desk refreshes on). Imported only through ``holdspeak.operations``.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import NotFound

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown Agent recipe", "ValidationError: an Agent needs a name")
_ID = {"type": "string", "minLength": 1}
_FIELDS: dict[str, Any] = {
    "name": {"type": "string", "maxLength": 200},
    "avatar": {"type": "string", "maxLength": 40},
    "role": {"type": "string", "maxLength": 400},
    "system_prompt": {"type": "string", "maxLength": 20000},
    "user_template": {"type": "string", "maxLength": 20000},
    "tools": {"type": "array", "items": {"type": "string"}},
    "kb_id": {"type": ["string", "null"]},
    "profile_id": {"type": ["string", "null"]},
    "manual_context": {"type": "string", "maxLength": 20000},
    "use_zone_context": {"type": "boolean"},
    "kind": {"type": "string", "maxLength": 40},
}


def _named(call: Call) -> Call:
    """The route's words for a missing recipe: ``Unknown Agent: <the path id>``."""

    def run(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        try:
            return call(service, principal, args)
        except NotFound:
            raise NotFound("Agent", str(args.get("recipe_id"))) from None

    return run


def _create(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    fields = dict(args)
    recipe_id = str(fields.pop("id", "") or fields.pop("recipe_id", "") or "") or None
    return {"recipe": service.create_recipe(principal, recipe_id=recipe_id, **fields)}


def _update(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    fields = {key: value for key, value in args.items() if key != "recipe_id"}
    return {"recipe": service.update_recipe(principal, str(args.get("recipe_id")), **fields)}


def _delete(service: Any, principal: Any, args: dict[str, Any]) -> dict[str, Any]:
    service.delete_recipe(principal, str(args.get("recipe_id")))
    return {"success": True}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        status: int = 200) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write", result="the RecipeService answer, in the route's envelope", refusals=_REFUSALS,
        completion="synchronous; one desk_changed frame (kind recipe)",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="recipe_service", method=method,
        call=call, http=http, http_status=status, handler=handler, tool_schema=tool, thread="effect_proposal",
    )


RECIPE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("recipe.create", "create_recipe", ("POST", "/api/recipes"), "api_create_recipe", _create,
        "Make an Agent recipe: its name, role, system prompt, user template, tools and engine (profile_id).",
        properties={"recipe_id": {"type": "string"}, **_FIELDS}, required=("name",), status=201),
    _op("recipe.update", "update_recipe", ("PUT", "/api/recipes/{recipe_id}"), "api_update_recipe",
        _named(_update), "Change an Agent recipe: only the fields given change.", properties=_FIELDS),
    _op("recipe.delete", "delete_recipe", ("DELETE", "/api/recipes/{recipe_id}"), "api_delete_recipe",
        _named(_delete), "Delete an Agent recipe."),
)

__all__ = ["RECIPE_OPERATIONS"]
