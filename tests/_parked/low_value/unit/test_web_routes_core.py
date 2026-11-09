# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_routes_core.py to restore.

# ruff: noqa


# --- test_context_module_has_no_route_import_cycle: P8: import-cycle rule on module load; no user outcome
def test_context_module_has_no_route_import_cycle():
    # WebContext must not import any route module (routers import the context,
    # never the reverse) — guards against an import cycle as the package grows.
    #
    # The popped modules are restored afterwards (HS-86-03): leaving the
    # package out of sys.modules meant the next in-test package import
    # rebuilt it EMPTY of submodule attributes, and every later
    # string-path monkeypatch through holdspeak.web.routes.* failed —
    # an order-dependent break that hid for sixty phases.
    import sys

    import holdspeak.web

    saved_context = sys.modules.pop("holdspeak.web.context", None)
    saved_routes = sys.modules.pop("holdspeak.web.routes", None)
    try:
        import holdspeak.web.context  # noqa: F401

        assert "holdspeak.web.routes" not in sys.modules
    finally:
        if saved_context is not None:
            sys.modules["holdspeak.web.context"] = saved_context
            holdspeak.web.context = saved_context
        if saved_routes is not None:
            sys.modules["holdspeak.web.routes"] = saved_routes
            holdspeak.web.routes = saved_routes
