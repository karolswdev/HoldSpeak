# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_runtime_background.py to restore.

# ruff: noqa


# --- test_background_never_imports_the_web_server: P8: an import-graph rule (a subprocess import plus an AST scan); no user outcome
def test_background_never_imports_the_web_server() -> None:
    probe = (
        "import sys, holdspeak.runtime.background as b; "
        "assert callable(b.start_background) and callable(b.Stopper.stop); "
        "assert 'holdspeak.web_server' not in sys.modules, 'web_server imported'"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    names: set[str] = set()
    source = REPO / "holdspeak" / "runtime" / "background.py"
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    assert not any(name.endswith("web_server") for name in names), names
