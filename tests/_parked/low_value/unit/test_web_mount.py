# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_mount.py to restore.

# ruff: noqa


# --- test_mount_routers_is_the_runtime_mount: P1/P8: 'callable(mount_routers)' and an import-graph rule; no user outcome
def test_mount_routers_is_the_runtime_mount() -> None:
    from holdspeak.runtime.web_mount import mount_routers

    assert callable(mount_routers)


# --- test_web_mount_never_imports_web_server: P1/P8: 'callable(mount_routers)' and an import-graph rule; no user outcome
def test_web_mount_never_imports_web_server() -> None:
    names: set[str] = set()
    for source in (REPO / "holdspeak" / "runtime").glob("web_mount*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
            elif isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
    assert names, "no web_mount module found"
    assert not any(name.endswith("web_server") for name in names), names
