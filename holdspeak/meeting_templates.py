"""Meeting Watch templates -- the V0 linked-meetings template (HS-175-04).

Pure module: DATA + one builder.  No DB, no IO, no side-effects.
Every compiled output MUST pass holdspeak.watch_validation validation
-- that is the definition of "compiles".

The table is CLOSED: adding a template requires a code change + test.
Shape follows confluence_templates.py (the twin).
"""
from __future__ import annotations

from typing import Any, NamedTuple

from holdspeak.watch_validation import (
    ACTION_SCHEMA,
    CONDITION_SCHEMA,
    validate_rules,
)

# Import CADENCE_PRESETS from the canonical source (github_templates.py).
from holdspeak.github_templates import CADENCE_PRESETS


# ------------------------------------------------------------------
# Template table (closed)
# ------------------------------------------------------------------

class MeetingTemplate(NamedTuple):
    """One row in the closed template table."""
    template_id: str
    name: str
    intent: str
    cadence_preset: str          # key into CADENCE_PRESETS
    query_kind: str              # the MeetingWatchSource query_kind
    rules: list[dict[str, Any]]  # WatchCondition@1/WatchAction@1 trees
    query_defaults: dict[str, Any]  # default query filters


MEETING_TEMPLATES: tuple[MeetingTemplate, ...] = (
    MeetingTemplate(
        template_id="watch.meetings.linked",
        name="Linked meetings",
        intent="Surface decisions, commitments, and intel from meetings linked to this Room",
        cadence_preset="normal",
        query_kind="meetings",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "decisions_count", "comparison": "changed"},
                    {"field": "commitments_count", "comparison": "changed"},
                    {"field": "intel_status", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
)

TEMPLATE_IDS: frozenset[str] = frozenset(t.template_id for t in MEETING_TEMPLATES)

_TEMPLATE_BY_ID: dict[str, MeetingTemplate] = {
    t.template_id: t for t in MEETING_TEMPLATES
}


def compile(
    template_id: str,
    project_scope: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a meeting template + project scope into a WatchSpec@1 draft.

    Parameters
    ----------
    template_id : str
        One of the closed template IDs.
    project_scope : dict
        ``{project_id: str}``.
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

    project_id = project_scope.get("project_id", "")

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
    if project_id:
        query["project_id"] = project_id

    spec: dict[str, Any] = {
        "schema": "WatchSpec@1",
        "name": tmpl.name,
        "intent": tmpl.intent,
        "provider": {
            "id": "meeting",
            "transport": "local_db",
        },
        "subject": {
            "kind": "meetings",
            "scope": {
                "project_id": project_id,
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
