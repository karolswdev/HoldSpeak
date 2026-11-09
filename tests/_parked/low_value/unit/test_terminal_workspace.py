# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_terminal_workspace.py to restore.

# ruff: noqa


# --- test_delivery_service_composes_workspace_with_shared_targets: P7: asserts internal object identity ('workspace.targets is targets')
def test_delivery_service_composes_workspace_with_shared_targets() -> None:
    targets = object()
    service = DeliveryService(None)
    workspace = service.terminal_workspace_service(targets=targets, local_node_id="node-a")
    assert workspace.targets is targets
    assert workspace.local_node_id == "node-a"
