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
    "tests/unit/test_philo5_his_words.py": "reads the retained Phase 6 rehearsal run (the Codex events and hub transcript) as input; writes only to tmp_path",
    "tests/unit/test_philo7_file_and_find.py": "reads the retained Phase 5 and Phase 7 rehearsal runs (events, launch setups) as input; every write goes to tmp_path",
    "tests/unit/test_philo10_send_job.py": "reads the retained story-06 send-job run and the tracked real-send ledger as input; every mutation and the second-run refusal write only under tmp_path",
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
        if rel.startswith("tests/_parked/"):
            continue  # parked tests are not collected; they cannot write
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


def _tracked_path(value: ast.AST | None) -> bool:
    """A path expression that spells pm/roadmap or docs/internal (also in
    parts, `"pm" / "roadmap"`), not through evidence_dir()."""
    if value is None:
        return False
    if isinstance(value, ast.Call) and getattr(value.func, "id", "") == "evidence_dir":
        return False
    ops = _div_operands(value)
    # Anchored at the repository (`Path(__file__)...`, the module constant
    # `REPO` / `ROOT`, upper case): a
    # `tmp_path / "pm" / "roadmap"` fixture tree is not the tracked tree.
    root = {n.id for n in ast.walk(ops[0]) if isinstance(n, ast.Name)}
    if not (root & {"__file__"} or any(r.strip("_") in {"REPO", "ROOT", "REPO_ROOT"} for r in root)):
        return False
    parts = "/".join(n.value for n in ops if isinstance(n, ast.Constant) and isinstance(n.value, str))
    return any(t in parts for t in ("pm/roadmap", "docs/internal"))


def _names(node: ast.AST | None) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} if node is not None else set()


WRITE_METHODS = {"mkdir", "write_text", "write_bytes", "touch"}


def _tracked_writes(tree: ast.Module) -> list[int]:
    """PHILO-17 (mainreds3): a name bound to a tracked path (`=` or an
    annotated `X: Path = ...`) outside evidence_dir() that is later WRITTEN
    through: `.mkdir()`, `.write_text()`, `.write_bytes()`, `.touch()`,
    `screenshot(path=...)`, `open(..., "w"|"a")`, `shutil.copy*(..., dst)`.
    A name that is only read (an atlas, a schema) is not a writer."""
    bound: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _tracked_path(node.value):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    bound.setdefault(t.id, node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and _tracked_path(node.value):
            bound.setdefault(node.target.id, node.lineno)
    if not bound:
        return []
    hits: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        used: set[str] = set()
        if isinstance(func, ast.Attribute) and func.attr in WRITE_METHODS:
            used = _names(func.value)
        elif isinstance(func, ast.Attribute) and func.attr == "screenshot":
            used = set().union(*(_names(k.value) for k in node.keywords if k.arg == "path")) if node.keywords else set()
        elif isinstance(func, ast.Name) and func.id == "open" and node.args:
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and any(c in mode.value for c in "wa"):
                used = _names(node.args[0])
        elif isinstance(func, ast.Attribute) and func.attr.startswith("copy") and len(node.args) > 1:
            used = _names(node.args[1])
        for name in used & set(bound):
            hits.add(bound[name])
    return sorted(hits)


def test_no_writes_through_a_tracked_path_outside_evidence_dir() -> None:
    offenders = []
    for path in sorted(TESTS.rglob("*.py")):
        rel = path.relative_to(REPO).as_posix()
        if rel in ALLOWLIST or rel.startswith(("tests/_parked/", "tests/e2e/_parked/")):
            continue
        source = path.read_text(encoding="utf-8")
        if not any(t in source for t in ('"docs"', "docs/internal", '"pm"', "pm/roadmap")):
            continue
        lines = _tracked_writes(ast.parse(source, filename=rel))
        if lines:
            offenders.append(f"{rel}:{lines[0]}")
    assert not offenders, (
        f"EVIDENCE-WRITE: {len(offenders)} test file(s) write through a pm/roadmap or docs/internal path; "
        "use tests._evidence.evidence_dir(\"<rel>\"):\n  " + "\n  ".join(offenders)
    )


# Calibration (Astra r1 on #1087): the three former writers, an evidence_dir
# use, and readers.
CALIBRATION = {
    "philo15_20 (was)": ('SHOTS = Path(__file__).resolve().parents[2] / "docs" / "internal" / "philo" / "phase-15" / "20-shots"\n'
                         'def t(page):\n    page.screenshot(path=str(SHOTS / "a.png"))\n', True),
    "hs143 (was)": ('SHOTS = REPO / "pm" / "roadmap" / "holdspeak" / "x" / "story-12-shots"\n'
                    'def t(page):\n    SHOTS.mkdir(parents=True, exist_ok=True)\n', True),
    "phase16 (was, annotated)": ('SHOTS: Path = Path(__file__).resolve().parents[2] / "docs" / "internal" / "philo" / "phase-16" / "02-shots"\n'
                                 'SHOTS.mkdir(parents=True, exist_ok=True)\n', True),
    "open for write": ('OUT = REPO / "docs/internal/x.json"\nwith open(OUT, "w") as f:\n    f.write("x")\n', True),
    "evidence_dir": ('SHOTS = evidence_dir("docs/internal/philo/phase-15/20-shots")\n'
                     'def t(page):\n    page.screenshot(path=str(SHOTS / "a.png"))\n', False),
    "reader": ('ATLAS = REPO / "docs/internal/philo/graph/atlas.json"\n'
               'data = json.loads(ATLAS.read_text())\nopen(ATLAS).read()\n', False),
}


def test_the_write_fence_is_calibrated() -> None:
    for name, (source, flagged) in CALIBRATION.items():
        assert bool(_tracked_writes(ast.parse(source))) is flagged, name


def test_allowlist_files_exist() -> None:
    missing = [rel for rel in ALLOWLIST if not (REPO / rel).is_file()]
    assert not missing, f"EVIDENCE-WRITE allowlist names missing files: {missing}"
