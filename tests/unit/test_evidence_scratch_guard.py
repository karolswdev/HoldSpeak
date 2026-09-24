"""Fence: no test writes into the tracked evidence tree by default.

A test that builds a repo path under ``pm/roadmap`` and also writes files
(screenshot, write_text, json.dump, mkdir, ...) must get that path from
``tests._evidence.evidence_dir``, which writes to ``.tmp/evidence-shots/``
unless ``HOLDSPEAK_EVIDENCE_WRITE=1``. Before this fence, every full run
rewrote ~388 tracked evidence files of closed phases.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests"

# Files that only READ tracked evidence as input. They are not writers.
ALLOWLIST = {
    "tests/unit/test_one_path_census.py": "reads the HS-131-10 findings inventory as input",
    "tests/unit/test_phase143_surface_fallback_census.py": "reads the generated census artifact as input",
    "tests/unit/test_primitive_contract.py": "reads the mobile contract schemas as input",
    "tests/unit/test_coder_gate.py": "reads the gate-proposal schema as input; writes only to tmp_path",
    "tests/unit/test_phase143_routing_authority_census.py": "reads the routing census as input; writes only to tmp_path",
}

WRITE_RE = re.compile(
    r"\.screenshot\(|write_text\(|write_bytes\(|json\.dump|mkdir\(|makedirs\(|shutil\.copy|\.save\("
)


def _div_operands(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _div_operands(node.left) + _div_operands(node.right)
    return [node]


def _is_roadmap_str(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str) and "pm/roadmap" in node.value


def _anchored_lines(tree: ast.Module) -> list[int]:
    """Lines that build a repo path under pm/roadmap outside evidence_dir()."""
    lines = []
    for node in ast.walk(tree):
        is_div = isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
        if is_div and any(_is_roadmap_str(op) for op in _div_operands(node)):
            lines.append(node.lineno)
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
            value = stmt.value
            if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.startswith("pm/roadmap"):
                lines.append(stmt.lineno)
    return sorted(set(lines))


def test_no_test_writes_into_tracked_evidence() -> None:
    offenders = []
    for path in sorted(TESTS.rglob("*.py")):
        rel = path.relative_to(REPO).as_posix()
        if rel in ALLOWLIST:
            continue
        source = path.read_text(encoding="utf-8")
        if "pm/roadmap" not in source or not WRITE_RE.search(source):
            continue
        lines = _anchored_lines(ast.parse(source, filename=rel))
        if lines:
            offenders.append(f"{rel}:{lines[0]}")
    assert not offenders, (
        f"EVIDENCE-WRITE: {len(offenders)} test file(s) build a pm/roadmap path and write files; "
        "use tests._evidence.evidence_dir(\"<rel>\") for the write dir:\n  " + "\n  ".join(offenders)
    )


def test_allowlist_files_exist() -> None:
    missing = [rel for rel in ALLOWLIST if not (REPO / rel).is_file()]
    assert not missing, f"EVIDENCE-WRITE allowlist names missing files: {missing}"
