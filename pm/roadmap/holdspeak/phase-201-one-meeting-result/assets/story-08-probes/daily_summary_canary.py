"""Reject forced proposal/plugin-call states with the actual daily-walk assertions."""
import ast
from pathlib import Path
from types import SimpleNamespace

source = Path("tests/e2e/test_phase200_daily_loop.py")
tree = ast.parse(source.read_text())
method = next(node for node in ast.walk(tree)
              if isinstance(node, ast.FunctionDef)
              and node.name == "test_a_project_carries_work_across_two_working_days")
checks = []
for node in ast.walk(method):
    if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
        continue
    comparison = node.test
    if len(comparison.ops) != 1 or not isinstance(comparison.ops[0], ast.Eq):
        continue
    if not isinstance(comparison.comparators[0], ast.List) or comparison.comparators[0].elts:
        continue
    left = comparison.left
    if (isinstance(left, ast.Attribute) and isinstance(left.value, ast.Name)
            and left.value.id == "engine" and left.attr == "plugin_calls"):
        checks.append(node)
    elif (isinstance(left, ast.Subscript) and isinstance(left.value, ast.Name)
            and left.value.id == "review" and isinstance(left.slice, ast.Constant)
            and left.slice.value == "proposals"):
        checks.append(node)
assert len(checks) == 2, "Both actual current-law empty-state assertions must exist"
code = compile(ast.Module(body=checks, type_ignores=[]), str(source), "exec")
print("Actual assertion lines:", [node.lineno for node in checks])
for label, calls, proposals, reject in [
    ("summary-only", [], [], False),
    ("forced plugin call", ["canary plugin call"], [], True),
    ("forced proposal", [], [{"id": "canary-proposal"}], True),
]:
    try:
        exec(code, {"engine": SimpleNamespace(plugin_calls=calls),
                    "review": {"proposals": proposals}})
    except AssertionError as error:
        if not reject:
            raise
        print(f"PASS {label}: actual assertion rejected {error}")
    else:
        assert not reject, f"CANARY FAILED: {label} was accepted"
        print(f"PASS {label}: actual assertions accept the current law")
