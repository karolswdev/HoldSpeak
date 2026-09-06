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
            "current": {...}  # HS-166-03: the current entity snapshot
        },
    }

A condition leaf has ``field``, ``comparison``, and optionally ``value``.
The matcher resolves ``field`` against each transition's
``facts.changed`` dict -- if the field key is present in ``changed``,
the leaf comparisons apply to the change tuple ``[old, new]``.

For comparisons that do not reference ``changed``:
- ``exists``/``missing`` check whether the field key is present in
  the transition's facts.changed.
- ``equals``/``not_equals``/``in``/``not_in`` compare the NEW value
  (index 1 of the change pair, or the raw value if not a pair).

Snapshot-level comparisons (HS-166-03):
- ``entered_state`` is an alias for ``changed_to`` on the field;
  matchable on transitions whose ``changed`` carries the field.
- ``due_within_days``, ``overdue``, ``inactive_for``, ``older_than``,
  ``newer_than`` read from ``facts.current[field]`` (the current
  entity snapshot) when the field is absent from ``changed``.
  These are provider-agnostic and operate on ISO date/datetime strings.

Convention: follows watch_validation.py (pure, package-root).

HS-164-03 trace: this is the minimal honest matcher for the condition
shapes the 159/161 templates actually emit.
HS-166-03 trace: six comparisons graduate -- entered_state,
due_within_days, overdue, inactive_for, older_than, newer_than.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_factory() -> datetime:
    """Overridable clock for testing."""
    return datetime.now(timezone.utc)


# Module-level clock -- tests monkeypatch this.
_clock = _now_factory


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


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO date or datetime string to a tz-aware datetime."""
    if not value:
        return None
    s = str(value).strip()
    try:
        parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        # Try date-only
        try:
            parsed = datetime.strptime(s[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_duration_days(value: Any) -> float | None:
    """Parse a duration value: integer (days) or string like '7d'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if s.endswith("d"):
        try:
            return float(s[:-1])
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _compare_against_transition(
    field: str,
    comparison: str,
    value: Any,
    transition: dict[str, Any],
) -> bool:
    """Evaluate one comparison leaf against one transition.

    Two resolution paths for the field value:
    1. Change-level: field is in ``facts.changed`` -- the comparison
       applies to the change pair [old, new].
    2. Snapshot-level: field is NOT in ``changed`` but IS in
       ``facts.current`` -- snapshot-level comparisons (older_than,
       newer_than, due_within_days, overdue, inactive_for) read the
       current entity's field value.  Change-level comparisons
       (changed, changed_to, changed_from) require the field in
       ``changed`` and return False when it is absent.
    """
    facts = transition.get("facts", {})
    changed = facts.get("changed", {})
    current = facts.get("current", {})

    # ── Snapshot-level comparisons (read current entity) ───────────
    # These do NOT require the field in changed.  They inspect the
    # entity's current state.  If the field IS in changed, they use
    # the new value from the change pair; otherwise they read from
    # current.

    if comparison == "entered_state":
        # Alias for changed_to: the field MUST be in changed.
        if field not in changed:
            return False
        change_val = changed[field]
        if isinstance(change_val, list) and len(change_val) == 2:
            return change_val[1] == value
        return change_val == value

    if comparison in ("older_than", "newer_than", "due_within_days",
                      "overdue", "inactive_for"):
        # Resolve the field value: prefer changed (new), fall back to current.
        if field in changed:
            change_val = changed[field]
            if isinstance(change_val, list) and len(change_val) == 2:
                field_val = change_val[1]
            else:
                field_val = change_val
        elif field in current:
            field_val = current[field]
        else:
            return False

        now = _clock()

        if comparison == "overdue":
            # due_at field < today AND no resolution
            dt = _parse_iso(field_val)
            if dt is None:
                return False
            resolution = current.get("resolution", "")
            if resolution:
                return False
            return dt < now

        days = _parse_duration_days(value)
        if days is None:
            return False

        dt = _parse_iso(field_val)
        if dt is None:
            return False

        if comparison == "older_than":
            from datetime import timedelta
            cutoff = now - timedelta(days=days)
            return dt < cutoff
        elif comparison == "newer_than":
            from datetime import timedelta
            cutoff = now - timedelta(days=days)
            return dt > cutoff
        elif comparison == "due_within_days":
            # due_at is within N days from now (upcoming or already past)
            from datetime import timedelta
            deadline = now + timedelta(days=days)
            return dt <= deadline
        elif comparison == "inactive_for":
            from datetime import timedelta
            cutoff = now - timedelta(days=days)
            return dt < cutoff

        return False

    # ── Change-level comparisons (require field in changed) ────────

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

    # Unknown comparison: never match.
    return False
