# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_terminal_workspace_context.py to restore.

# ruff: noqa


# --- test_default_paths_are_resolved_from_delivery_modules_at_construction: P2/P1: reads back two module paths the test just patched
def test_default_paths_are_resolved_from_delivery_modules_at_construction(monkeypatch, tmp_path) -> None:
    from holdspeak.delivery import factory_launch, registry as delivery_registry

    registry_path = tmp_path / "sources.json"
    launches_path = tmp_path / "launches.json"
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches_path)

    context = TerminalWorkspaceContext()

    assert context.registry_path == registry_path
    assert context.launches_path == launches_path
