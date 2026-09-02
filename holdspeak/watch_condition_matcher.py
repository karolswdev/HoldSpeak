"""Minimal WatchCondition@1 matcher: evaluate a condition tree against transitions.

PURE: no DB, no IO, no side-effects.  Matches the closed condition
vocabulary from watch_validation.py against the transition dicts
produced by diff_snapshots (reaction_service.py).

A transition has::

    {
        "event_type": "github.pr.checks_changed",
        "entity_ref": "123",
        "source_revision": "...",
        "facts": {
            "entity_title": "PR title",
            "url": "...",
            "changed": {"checks": ["failure", "success"]},
        },
    }

A condition leaf has ``field``, ``comparison``, and optionally ``value``.
The matcher resolves ``field`` against each transition's
``facts.changed`` dict — if the field key is present in ``changed``,
the leaf comparisons apply to the change tuple ``[old, new]``.

For comparisons that do not reference ``changed``:
- ``exists``/``missing`` check whether the field key is present in
  the transition's facts.changed.
- ``equals``/``not_equals``/``in``/``not_in`` compare the NEW value
  (index 1 of the change pair, or the raw value if not a pair).

Convention: follows watch_validation.py (pure, package-root).

HS-164-03 trace: this is the minimal honest matcher for the condition
shapes the 159/161 templates actually emit.  Unmatchable conditions
return False with no side-effects.
"""
from __future__ import annotations

from typing import Any


def match_condition(
    condition: dict[str, Any],
    transitions: list[dict[str, Any]],
) -> bool:
    """Evaluate a WatchCondition@1 tree against a list of transitions.

    Returns True if the condition is satisfied by ANY of the transitions.
    An empty transitions list never satisfies any condition.
    """
    if not transitions:
        return False

    if not isinstance(condition, dict):
        return False

    operator = condition.get("operator")
    comparison = condition.get("comparison")

    if operator:
        return _match_logical(condition, transitions)
    elif comparison:
        return _match_leaf(condition, transitions)

    # Malformed node: never match.
    return False


def _match_logical(
    node: dict[str, Any],
    transitions: list[dict[str, Any]],
) -> bool:
    """Evaluate a logical (operator) node."""
    op = node.get("operator", "")
    clauses = node.get("clauses", [])

    if not isinstance(clauses, list) or not clauses:
        return False

    if op == "any":
        return any(
            match_condition(clause, transitions)
            for clause in clauses
        )
    elif op == "all":
        return all(
            match_condition(clause, transitions)
            for clause in clauses
        )
    elif op == "not":
        if len(clauses) != 1:
            return False
        return not match_condition(clauses[0], transitions)

    # Unknown operator: never match.
    return False


def _match_leaf(
    leaf: dict[str, Any],
    transitions: list[dict[str, Any]],
) -> bool:
    """Evaluate a comparison leaf against any transition."""
    field = leaf.get("field", "")
    comparison = leaf.get("comparison", "")
    value = leaf.get("value")

    if not field or not comparison:
        return False

    return any(
        _compare_against_transition(field, comparison, value, t)
        for t in transitions
    )


def _compare_against_transition(
    field: str,
    comparison: str,
    value: Any,
    transition: dict[str, Any],
) -> bool:
    """Evaluate one comparison leaf against one transition."""
    facts = transition.get("facts", {})
    changed = facts.get("changed", {})

    # The field must be present in the changed dict for most comparisons.
    if field not in changed:
        if comparison == "missing":
            return True
        # For "exists", the field must be in changed.
        return False

    change_val = changed[field]

    # change_val is typically [old, new] for field-level changes,
    # or a raw value (e.g. {"entity": "new"} for discovery).
    if isinstance(change_val, list) and len(change_val) == 2:
        old_val, new_val = change_val
    else:
        old_val = None
        new_val = change_val

    if comparison == "exists":
        return True
    elif comparison == "missing":
        return False  # field IS in changed
    elif comparison == "changed":
        # Any change on this field satisfies.
        return True
    elif comparison == "changed_to":
        return new_val == value
    elif comparison == "changed_from":
        return old_val == value
    elif comparison == "equals":
        return new_val == value
    elif comparison == "not_equals":
        return new_val != value
    elif comparison == "in":
        if isinstance(value, list):
            return new_val in value
        return False
    elif comparison == "not_in":
        if isinstance(value, list):
            return new_val not in value
        return True
    elif comparison == "contains":
        if isinstance(new_val, str) and isinstance(value, str):
            return value in new_val
        if isinstance(new_val, list):
            return value in new_val
        return False
    elif comparison == "greater_than":
        try:
            return float(new_val) > float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    elif comparison == "less_than":
        try:
            return float(new_val) < float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    elif comparison == "older_than":
        # Time-based comparison: not matchable against transitions.
        # The "delivery drift" template uses this for entity age, but
        # that is a snapshot-level property (updated_at on the entity),
        # not a transition-level change.  Honestly unmatchable here.
        return False
    elif comparison == "newer_than":
        return False

    # Unknown comparison: never match.
    return False
