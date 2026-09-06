"""WatchCondition@1 and WatchAction@1 closed-schema validation.

This module is PURE: no DB, no IO, no side-effects.  It freezes the
closed declarative trees that WatchService, routes (P3), MCP (P6), and
the evaluator (P5) validate against.

SRS traceability
----------------
- WatchCondition@1 shape: SRS SS7.2 (closed operators/comparisons)
- WatchAction@1 shape: SRS SS7.3 (closed action kinds)
- Refusal of code/prompt strings: SS7.2 "MUST NOT contain Python,
  shell, JavaScript, SQL, or a model prompt" -- enforced by the
  CLOSED schema (unknown keys/operators/comparisons refused as typed
  validation errors, not by scanning for scripts).

Convention: follows refs.py/project_contracts.py (pure, package-root).
"""
from __future__ import annotations

from typing import Any


# ------------------------------------------------------------------
# WatchCondition@1 closed vocabulary
# ------------------------------------------------------------------

CONDITION_SCHEMA = "WatchCondition@1"

LOGICAL_OPERATORS: frozenset[str] = frozenset({"all", "any", "not"})

COMPARISONS: frozenset[str] = frozenset({
    "equals", "not_equals", "in", "not_in", "exists", "missing",
    "changed", "changed_from", "changed_to",
    "greater_than", "less_than", "older_than", "newer_than",
    "contains",
    # HS-166-03: snapshot-level comparisons (read the transition's
    # current entity, not only the changed dict).  Provider-agnostic.
    "entered_state", "due_within_days", "overdue", "inactive_for",
})

# Keys allowed in a logical (operator) node.
_LOGICAL_KEYS: frozenset[str] = frozenset({"schema", "operator", "clauses"})

# Keys allowed in a comparison (leaf) node.
_COMPARISON_KEYS: frozenset[str] = frozenset({
    "schema", "field", "comparison", "value",
})


# ------------------------------------------------------------------
# WatchAction@1 closed vocabulary
# ------------------------------------------------------------------

ACTION_SCHEMA = "WatchAction@1"

ACTION_KINDS: frozenset[str] = frozenset({
    "project.observe",
    "project.propose",
    "project.steward.run_once",
    "project.update.draft",
    "door.add_item",
    "workbench.add_item",
    "workbench.run",
    "cadence.upsert_loop",
})

# Keys allowed in an action node (kind-specific config may extend
# later; V0 accepts only schema + kind).
_ACTION_KEYS: frozenset[str] = frozenset({"schema", "kind"})


# ------------------------------------------------------------------
# Validation results
# ------------------------------------------------------------------

class WatchValidationError:
    """A single typed validation finding."""

    __slots__ = ("path", "message")

    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message

    def __repr__(self) -> str:
        return f"WatchValidationError({self.path!r}, {self.message!r})"

    def __str__(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


# ------------------------------------------------------------------
# Condition validation
# ------------------------------------------------------------------

def validate_condition(
    node: Any,
    *,
    _path: str = "",
    _depth: int = 0,
) -> list[WatchValidationError]:
    """Validate a WatchCondition@1 tree.

    Returns a list of validation errors (empty = valid).  The tree is
    validated recursively; every node must be either a logical node
    (operator + clauses) or a comparison leaf (field + comparison).
    Unknown keys, operators, and comparisons produce typed errors --
    this IS the code/prompt refusal mechanism (the schema is closed).
    """
    errors: list[WatchValidationError] = []

    if _depth > 20:
        errors.append(WatchValidationError(_path, "condition tree exceeds maximum depth"))
        return errors

    if not isinstance(node, dict):
        errors.append(WatchValidationError(_path, "condition must be an object"))
        return errors

    # Schema tag is optional on nested nodes, required at root.
    schema = node.get("schema")
    if _depth == 0 and schema and schema != CONDITION_SCHEMA:
        errors.append(WatchValidationError(
            _path, f"schema must be {CONDITION_SCHEMA!r}, got {schema!r}",
        ))

    has_operator = "operator" in node
    has_comparison = "comparison" in node

    if has_operator and has_comparison:
        errors.append(WatchValidationError(
            _path, "node cannot have both 'operator' and 'comparison'",
        ))
        return errors

    if has_operator:
        # Logical node
        allowed = _LOGICAL_KEYS
        unknown = set(node.keys()) - allowed
        if unknown:
            errors.append(WatchValidationError(
                _path, f"unknown keys in logical node: {sorted(unknown)}",
            ))

        op = node["operator"]
        if op not in LOGICAL_OPERATORS:
            errors.append(WatchValidationError(
                _path, f"unknown operator {op!r}; allowed: {sorted(LOGICAL_OPERATORS)}",
            ))
            return errors

        clauses = node.get("clauses")
        if not isinstance(clauses, list) or len(clauses) == 0:
            errors.append(WatchValidationError(
                _path, "'clauses' must be a non-empty array",
            ))
            return errors

        if op == "not" and len(clauses) != 1:
            errors.append(WatchValidationError(
                _path, "'not' operator requires exactly one clause",
            ))

        for i, clause in enumerate(clauses):
            child_path = f"{_path}.clauses[{i}]" if _path else f"clauses[{i}]"
            errors.extend(validate_condition(
                clause, _path=child_path, _depth=_depth + 1,
            ))

    elif has_comparison:
        # Comparison leaf
        allowed = _COMPARISON_KEYS
        unknown = set(node.keys()) - allowed
        if unknown:
            errors.append(WatchValidationError(
                _path, f"unknown keys in comparison node: {sorted(unknown)}",
            ))

        comp = node["comparison"]
        if comp not in COMPARISONS:
            errors.append(WatchValidationError(
                _path, f"unknown comparison {comp!r}; allowed: {sorted(COMPARISONS)}",
            ))

        field = node.get("field")
        if not isinstance(field, str) or not field.strip():
            errors.append(WatchValidationError(
                _path, "'field' must be a non-empty string",
            ))

        # "value" is required for comparisons that need it.
        # exists/missing/changed do not require a value.
        no_value_comparisons = {"exists", "missing", "changed", "overdue"}
        if comp not in no_value_comparisons and "value" not in node:
            errors.append(WatchValidationError(
                _path, f"comparison {comp!r} requires a 'value'",
            ))
    else:
        errors.append(WatchValidationError(
            _path, "node must have either 'operator' or 'comparison'",
        ))

    return errors


# ------------------------------------------------------------------
# Action validation
# ------------------------------------------------------------------

def validate_action(action: Any, *, _path: str = "") -> list[WatchValidationError]:
    """Validate a WatchAction@1 node.

    Returns a list of validation errors (empty = valid).
    Unknown kinds produce typed errors.
    """
    errors: list[WatchValidationError] = []

    if not isinstance(action, dict):
        errors.append(WatchValidationError(_path, "action must be an object"))
        return errors

    unknown = set(action.keys()) - _ACTION_KEYS
    if unknown:
        errors.append(WatchValidationError(
            _path, f"unknown keys in action: {sorted(unknown)}",
        ))

    schema = action.get("schema")
    if schema and schema != ACTION_SCHEMA:
        errors.append(WatchValidationError(
            _path, f"schema must be {ACTION_SCHEMA!r}, got {schema!r}",
        ))

    kind = action.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        errors.append(WatchValidationError(_path, "'kind' must be a non-empty string"))
    elif kind not in ACTION_KINDS:
        errors.append(WatchValidationError(
            _path, f"unknown action kind {kind!r}; allowed: {sorted(ACTION_KINDS)}",
        ))

    return errors


# ------------------------------------------------------------------
# Rule validation (condition + actions pair)
# ------------------------------------------------------------------

def validate_rule(
    rule: Any,
    *,
    _path: str = "",
) -> list[WatchValidationError]:
    """Validate a single rule dict with 'condition' and 'actions' keys."""
    errors: list[WatchValidationError] = []

    if not isinstance(rule, dict):
        errors.append(WatchValidationError(_path, "rule must be an object"))
        return errors

    condition = rule.get("condition")
    if condition is None:
        errors.append(WatchValidationError(_path, "rule must have a 'condition'"))
    else:
        cond_path = f"{_path}.condition" if _path else "condition"
        errors.extend(validate_condition(condition, _path=cond_path))

    actions = rule.get("actions")
    if not isinstance(actions, list) or len(actions) == 0:
        errors.append(WatchValidationError(
            _path, "'actions' must be a non-empty array",
        ))
    else:
        for i, action in enumerate(actions):
            act_path = f"{_path}.actions[{i}]" if _path else f"actions[{i}]"
            errors.extend(validate_action(action, _path=act_path))

    return errors


def validate_rules(rules: Any) -> list[WatchValidationError]:
    """Validate a list of rule dicts."""
    errors: list[WatchValidationError] = []

    if not isinstance(rules, list):
        errors.append(WatchValidationError("", "rules must be an array"))
        return errors

    for i, rule in enumerate(rules):
        errors.extend(validate_rule(rule, _path=f"rules[{i}]"))

    return errors
