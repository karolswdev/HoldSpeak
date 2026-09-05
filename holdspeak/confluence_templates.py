"""Confluence Watch templates -- the two V0 templates (HS-174-07).

Pure module: DATA + one builder.  No DB, no IO, no side-effects.
Every compiled output MUST pass holdspeak.watch_validation validation
-- that is the definition of "compiles".

The table is CLOSED: adding a template requires a code change + test.
Shape follows jira_templates.py (the twin).

V0 CONSTRAINT (the critical gap): ``acli confluence`` has no
``page list`` or ``page search`` command.  V0 watches:
- ``watch.confluence.recent_blogs``: blog posts in a space (``blog list``).
- ``watch.confluence.pages_by_id``: pages by known IDs (``page view --id``).

No full-space page sweep.
"""
from __future__ import annotations

from typing import Any, NamedTuple

from holdspeak.watch_validation import (
    ACTION_SCHEMA,
    CONDITION_SCHEMA,
    validate_rules,
)

# Import CADENCE_PRESETS from the canonical source (github_templates.py
# already has them; single source, no third copy).
from holdspeak.github_templates import CADENCE_PRESETS


# ------------------------------------------------------------------
# Template table (closed)
# ------------------------------------------------------------------

class ConfluenceTemplate(NamedTuple):
    """One row in the closed template table."""
    template_id: str
    name: str
    intent: str
    cadence_preset: str          # key into CADENCE_PRESETS
    query_kind: str              # the ConfluenceWatchSource query_kind
    rules: list[dict[str, Any]]  # WatchCondition@1/WatchAction@1 trees
    query_defaults: dict[str, Any]  # default query filters


CONFLUENCE_TEMPLATES: tuple[ConfluenceTemplate, ...] = (
    ConfluenceTemplate(
        template_id="watch.confluence.recent_blogs",
        name="Confluence recent blogs",
        intent="Surface recently updated blog posts in a Confluence space",
        cadence_preset="normal",
        query_kind="recent_blogs",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "title", "comparison": "changed"},
                    {"field": "status", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
    ConfluenceTemplate(
        template_id="watch.confluence.pages_by_id",
        name="Confluence pages by ID",
        intent="Track specific Confluence pages by their known IDs",
        cadence_preset="normal",
        query_kind="pages_by_id",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "title", "comparison": "changed"},
                    {"field": "status", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
)

TEMPLATE_IDS: frozenset[str] = frozenset(t.template_id for t in CONFLUENCE_TEMPLATES)

_TEMPLATE_BY_ID: dict[str, ConfluenceTemplate] = {
    t.template_id: t for t in CONFLUENCE_TEMPLATES
}


def compile(
    template_id: str,
    site_scope: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a Confluence template + site scope into a WatchSpec@1 draft.

    Parameters
    ----------
    template_id : str
        One of the closed template IDs.
    site_scope : dict
        ``{connection_ref: str, space_key: str, space_id: str}``.
        For ``pages_by_id``, also ``page_ids: list[str]``.
    options : dict, optional
        Overrides:
        - ``cadence``: key from CADENCE_PRESETS or a raw trigger dict

    Returns
    -------
    dict
        A complete WatchSpec@1 draft.
    """
    if template_id not in _TEMPLATE_BY_ID:
        raise ValueError(
            f"Unknown template {template_id!r}; "
            f"allowed: {sorted(TEMPLATE_IDS)}"
        )

    tmpl = _TEMPLATE_BY_ID[template_id]
    opts = options or {}

    conn_ref = site_scope.get("connection_ref", "")
    space_key = site_scope.get("space_key", "")
    space_id = site_scope.get("space_id", "")

    # Cadence resolution
    cadence_key = opts.get("cadence", tmpl.cadence_preset)
    if isinstance(cadence_key, str) and cadence_key in CADENCE_PRESETS:
        trigger = dict(CADENCE_PRESETS[cadence_key])
    elif isinstance(cadence_key, dict):
        trigger = dict(cadence_key)
    else:
        trigger = dict(CADENCE_PRESETS[tmpl.cadence_preset])

    # Query filters: template defaults + scope
    query: dict[str, Any] = dict(tmpl.query_defaults)
    if conn_ref:
        query["connection_ref"] = conn_ref
    if space_id:
        query["space_id"] = space_id

    # For pages_by_id, carry the page IDs
    if tmpl.query_kind == "pages_by_id":
        page_ids = site_scope.get("page_ids", [])
        if page_ids:
            query["page_ids"] = list(page_ids)

    spec: dict[str, Any] = {
        "schema": "WatchSpec@1",
        "name": tmpl.name,
        "intent": tmpl.intent,
        "provider": {
            "id": "confluence",
            "transport": "connector_pack",
            "connection_ref": conn_ref,
        },
        "subject": {
            "kind": tmpl.query_kind,
            "scope": {
                "connection_ref": conn_ref,
                "space_key": space_key,
                "space_id": space_id,
            },
            "query": query,
        },
        "trigger": trigger,
        "rules": tmpl.rules,
        "action": tmpl.rules[0]["actions"][0] if tmpl.rules else {},
        "mode": "yolo",
    }

    # Belt: validate the compiled output
    errors = validate_rules(spec.get("rules", []))
    if errors:
        raise ValueError(
            f"Template {template_id} compiled output failed validation: "
            + "; ".join(str(e) for e in errors)
        )

    return spec
