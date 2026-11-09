# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_hub_composition.py to restore.

# ruff: noqa


# --- test_compose_hub_builds_the_same_web_context_field_set: P8: pins a hand-kept field-name list and an import graph; the built-once test checks the shared instances
def test_compose_hub_builds_the_same_web_context_field_set(tmp_path) -> None:
    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime import composition
    from holdspeak.runtime.hub_composition import compose_hub
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    get_database(tmp_path / "hub-composition.db")
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
            host="127.0.0.1",
        )
        hub = compose_hub(server, on_launch_hold=lambda _key: None)
        built = sorted(
            field.name
            for field in dataclasses.fields(WebContext)
            if getattr(hub.web_ctx, field.name) is not None
        )
        assert built == FIELDS_BEFORE_THE_MOVE
        assert composition.installed() is hub.runtime_services
        assert hub.runtime_services.actuator_service is hub.web_ctx.actuator_service
    finally:
        reset_database()


# --- test_importing_the_compositions_does_not_import_the_web_server: P8: pins a hand-kept field-name list and an import graph; the built-once test checks the shared instances
def test_importing_the_compositions_does_not_import_the_web_server() -> None:
    probe = (
        "import sys, holdspeak.runtime.composition, holdspeak.runtime.delivery_composition as d, holdspeak.runtime.hub_composition as c; "
        "assert callable(c.compose_hub) and callable(d.compose_delivery); "
        "assert 'holdspeak.web_server' not in sys.modules, 'web_server imported'"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
