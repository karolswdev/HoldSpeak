"""GitHub Watch templates -- the five SRS SS8.1 recommended templates.

Pure module: DATA + one builder.  No DB, no IO, no side-effects.
Every compiled output MUST pass holdspeak.watch_validation validation
-- that is the definition of "compiles".

The table is CLOSED: adding a template requires a code change + test.
Shape follows the rule-table convention project_delta_service.py
established in Phase 160.

SRS traceability
----------------
- SS8.1: five recommended GitHub templates
- SS4.1: cadence presets (active_work/normal/daily/weekdays)
- SS7.2: WatchCondition@1 closed operators/comparisons
- SS7.3: WatchAction@1 closed action kinds
- WatchSpec@1: schema, name, intent, provider, subject, trigger, rules, mode
- INT-007/008: live provider inventory, recommendation shape
- PROV-011: scope comes from caller, never invented

Convention: follows refs.py/project_contracts.py/watch_validation.py
(pure, package-root).
"""
from __future__ import annotations

from typing import Any, NamedTuple

from holdspeak.watch_validation import (
    ACTION_SCHEMA,
    CONDITION_SCHEMA,
    validate_rules,
)

# Cadence presets duplicated here to avoid circular import with
# project_setup_service.  Values MUST match SRS SS4.1 and the
# canonical presets in project_setup_service.CADENCE_PRESETS.
CADENCE_PRESETS: dict[str, dict[str, object]] = {
    "active_work": {"kind": "poll", "every_minutes": 15},
    "normal": {"kind": "poll", "every_minutes": 35},
    "daily": {"kind": "poll", "every_minutes": 1440},
    "weekdays": {"kind": "poll", "every_minutes": 1440, "weekdays_only": True},
}


# ------------------------------------------------------------------
# Template table (closed)
# ------------------------------------------------------------------

class GitHubTemplate(NamedTuple):
    """One row in the closed template table."""
    template_id: str
    name: str
    intent: str
    cadence_preset: str          # key into CADENCE_PRESETS
    rules: list[dict[str, Any]]  # WatchCondition@1/WatchAction@1 trees
    query_defaults: dict[str, Any]  # default query filters


GITHUB_TEMPLATES: tuple[GitHubTemplate, ...] = (
    GitHubTemplate(
        template_id="watch.github.review_queue",
        name="PR review queue",
        intent="Surface PRs awaiting or receiving review decisions",
        cadence_preset="active_work",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "review_requested", "comparison": "changed"},
                    {"field": "review_decision", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={"state": "open", "base": "main"},
    ),
    GitHubTemplate(
        template_id="watch.github.ci_health",
        name="CI health",
        intent="Detect check failures and recoveries on open PRs",
        cadence_preset="active_work",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "checks", "comparison": "changed_to", "value": "failure"},
                    {"field": "checks", "comparison": "changed_to", "value": "success"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
                {"schema": ACTION_SCHEMA, "kind": "project.steward.run_once"},
            ],
        }],
        query_defaults={"state": "open", "base": "main"},
    ),
    GitHubTemplate(
        template_id="watch.github.merge_flow",
        name="Merge flow",
        intent="Track PR merge and state transitions",
        cadence_preset="normal",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "state", "comparison": "changed"},
                    {"field": "merged", "comparison": "changed_to", "value": True},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={"state": "open", "base": "main"},
    ),
    GitHubTemplate(
        template_id="watch.github.delivery_drift",
        name="Delivery drift",
        intent="Flag open PRs with no activity for a configured duration",
        cadence_preset="daily",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "updated_at", "comparison": "older_than", "value": "7d"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
                {"schema": ACTION_SCHEMA, "kind": "door.add_item"},
            ],
        }],
        query_defaults={"state": "open", "base": "main"},
    ),
    GitHubTemplate(
        template_id="watch.github.release_readiness",
        name="Release readiness",
        intent="Track head changes, check results, and review approval toward merge readiness",
        cadence_preset="active_work",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "head_sha", "comparison": "changed"},
                    {"field": "checks", "comparison": "changed"},
                    {"field": "review_decision", "comparison": "equals", "value": "approved"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
                {"schema": ACTION_SCHEMA, "kind": "project.update.draft"},
            ],
        }],
        query_defaults={"state": "open", "base": "main"},
    ),
    # HS-169-04: CI on the base branch (counsel M1)
    GitHubTemplate(
        template_id="watch.github.branch_ci",
        name="CI",
        intent="Monitor CI status on the base branch",
        cadence_preset="active_work",
        rules=[{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "conclusion", "comparison": "changed"},
                    {"field": "status", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }],
        query_defaults={"base": "main"},
    ),
)

_TEMPLATE_BY_ID: dict[str, GitHubTemplate] = {
    t.template_id: t for t in GITHUB_TEMPLATES
}

TEMPLATE_IDS: frozenset[str] = frozenset(_TEMPLATE_BY_ID.keys())


# ------------------------------------------------------------------
# Compile
# ------------------------------------------------------------------

def compile(
    template_id: str,
    repo_scope: str | list[str],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile a template + repo scope + options into a WatchSpec@1 draft.

    Parameters
    ----------
    template_id : str
        One of the five closed template IDs.
    repo_scope : str or list[str]
        One or more ``owner/repo`` identifiers.  PROV-011: never
        invented here -- the caller is responsible for providing only
        discovered/validated repos.
    options : dict, optional
        Overrides:
        - ``cadence``: key from CADENCE_PRESETS or a raw trigger dict
        - ``base``: base branch filter (default from template)
        - ``state``: PR state filter (default from template)

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

    # Repo scope normalization
    if isinstance(repo_scope, str):
        repositories = [repo_scope]
    else:
        repositories = list(repo_scope)

    if not repositories:
        raise ValueError("repo_scope must contain at least one repository")

    # Cadence resolution
    cadence_key = opts.get("cadence", tmpl.cadence_preset)
    if isinstance(cadence_key, str) and cadence_key in CADENCE_PRESETS:
        trigger = dict(CADENCE_PRESETS[cadence_key])
    elif isinstance(cadence_key, dict):
        trigger = dict(cadence_key)
    else:
        trigger = dict(CADENCE_PRESETS[tmpl.cadence_preset])

    # Query filters: template defaults + overrides
    query: dict[str, Any] = dict(tmpl.query_defaults)
    if "base" in opts:
        query["base"] = opts["base"]
    if "state" in opts:
        query["state"] = opts["state"]

    # HS-169-04: branch_ci uses a different subject kind
    subject_kind = "branch_ci" if template_id == "watch.github.branch_ci" else "pull_request"

    spec: dict[str, Any] = {
        "schema": "WatchSpec@1",
        "name": tmpl.name,
        "intent": tmpl.intent,
        "provider": {
            "id": "github",
            "transport": "connector_pack",
        },
        "subject": {
            "kind": subject_kind,
            "scope": {"repositories": repositories},
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
