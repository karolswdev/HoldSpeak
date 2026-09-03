"""Jira Watch templates -- the five SRS SS8.2 recommended templates.

Pure module: DATA + one builder.  No DB, no IO, no side-effects.
Every compiled output MUST pass holdspeak.watch_validation validation
-- that is the definition of "compiles".

The table is CLOSED: adding a template requires a code change + test.
Shape follows github_templates.py (the twin).

SRS traceability
----------------
- SS8.2: five recommended Jira templates
- SS4.1: cadence presets (active_work/normal/daily/weekdays)
- SS7.2: WatchCondition@1 closed operators/comparisons
- SS7.3: WatchAction@1 closed action kinds
- WatchSpec@1: schema, name, intent, provider, subject, trigger, rules, mode
- INT-007/008: live provider inventory, recommendation shape
- PROV-011: scope comes from caller, never invented

Convention: follows refs.py/project_contracts.py/watch_validation.py
(pure, package-root).

HS-166-03 LIVE FINDING (team-managed sites): Done issues carry
resolution:null.  Templates condition completion on status_category
changed_to done, NEVER on resolution appearing.
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

class JiraTemplate(NamedTuple):
    """One row in the closed template table."""
    template_id: str
    name: str
    intent: str
    cadence_preset: str          # key into CADENCE_PRESETS
    rules: list[dict[str, Any]]  # WatchCondition@1/WatchAction@1 trees
    query_defaults: dict[str, Any]  # default query filters


JIRA_TEMPLATES: tuple[JiraTemplate, ...] = (
    JiraTemplate(
        template_id="watch.jira.blockers",
        name="Jira blockers",
        intent="Surface issues that enter a configured blocked state",
        cadence_preset="active_work",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "status", "comparison": "entered_state",
                     "value": "Blocked"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
                {"schema": ACTION_SCHEMA, "kind": "project.steward.run_once"},
            ],
        }],
        query_defaults={
            "blocked_statuses": ["Blocked"],
            "status_categories": ["indeterminate", "new"],
        },
    ),
    JiraTemplate(
        template_id="watch.jira.delivery_flow",
        name="Jira delivery flow",
        intent="Track issue status transitions and completion",
        cadence_preset="normal",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "status", "comparison": "changed"},
                    # LIVE FINDING: team-managed sites carry resolution:null
                    # on Done issues.  Condition on status_category, not
                    # resolution.
                    {"field": "status_category", "comparison": "changed_to",
                     "value": "done"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
    JiraTemplate(
        template_id="watch.jira.due_risk",
        name="Jira due risk",
        intent="Flag issues approaching or past their due date",
        cadence_preset="daily",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "due_at", "comparison": "due_within_days",
                     "value": 7},
                    {"field": "due_at", "comparison": "overdue"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
                {"schema": ACTION_SCHEMA, "kind": "project.steward.run_once"},
            ],
        }],
        query_defaults={
            "due_within_days": 7,
        },
    ),
    JiraTemplate(
        template_id="watch.jira.scope_intake",
        name="Jira scope intake",
        intent="Observe newly discovered issues entering the watch scope",
        cadence_preset="normal",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "entity", "comparison": "changed_to",
                     "value": "new"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
    JiraTemplate(
        template_id="watch.jira.transformation",
        name="Jira transformation",
        intent="Track priority escalations, reassignments, and staleness",
        cadence_preset="daily",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "priority", "comparison": "changed_to",
                     "value": "Highest"},
                    {"field": "priority", "comparison": "changed_to",
                     "value": "High"},
                    {"field": "assignee", "comparison": "changed"},
                    {"field": "updated_at", "comparison": "inactive_for",
                     "value": 14},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={},
    ),
)

_TEMPLATE_BY_ID: dict[str, JiraTemplate] = {
    t.template_id: t for t in JIRA_TEMPLATES
}

TEMPLATE_IDS: frozenset[str] = frozenset(_TEMPLATE_BY_ID.keys())


# ------------------------------------------------------------------
# Compile
# ------------------------------------------------------------------

def compile(
    template_id: str,
    site_scope: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a template + site scope + options into a WatchSpec@1 draft.

    Parameters
    ----------
    template_id : str
        One of the five closed template IDs.
    site_scope : dict
        ``{connection_ref: str, projects: list[str], issue_types: list[str]}``.
        PROV-011: never invented here -- the caller is responsible for
        providing only discovered/validated scope.
    options : dict, optional
        Overrides:
        - ``cadence``: key from CADENCE_PRESETS or a raw trigger dict

    Returns
    -------
    dict
        A complete WatchSpec@1 draft.  Validated before return --
        raises ValueError if the output fails watch_validation.
    """
    if template_id not in _TEMPLATE_BY_ID:
        raise ValueError(
            f"Unknown template {template_id!r}; "
            f"allowed: {sorted(TEMPLATE_IDS)}"
        )

    tmpl = _TEMPLATE_BY_ID[template_id]
    opts = options or {}

    connection_ref = site_scope.get("connection_ref", "")
    projects = site_scope.get("projects", [])
    issue_types = site_scope.get("issue_types", [])

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
    if connection_ref:
        query["connection_ref"] = connection_ref
    if projects:
        query["projects"] = list(projects)
    if issue_types:
        query["issue_types"] = list(issue_types)

    spec: dict[str, Any] = {
        "schema": "WatchSpec@1",
        "name": tmpl.name,
        "intent": tmpl.intent,
        "provider": {
            "id": "jira",
            "transport": "connector_pack",
            "connection_ref": connection_ref,
        },
        "subject": {
            "kind": "issue",
            "scope": {
                "connection_ref": connection_ref,
                "projects": list(projects),
                "issue_types": list(issue_types),
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
