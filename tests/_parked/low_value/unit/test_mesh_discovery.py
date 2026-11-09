# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mesh_discovery.py to restore.

# ruff: noqa


# --- test_mesh_module_constant_is_holdspeak_tcp: P1: asserts a module constant equals its own literal
def test_mesh_module_constant_is_holdspeak_tcp():
    # The Bonjour service type the iPad's NWBrowser browses for.
    assert mesh.MESH_SERVICE_TYPE == "_holdspeak._tcp.local."
