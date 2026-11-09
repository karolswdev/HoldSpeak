# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_grounding_entailment.py to restore.

# ruff: noqa


# --- test_no_network_egress_imports: P8: greps the module's own source for network symbol names
def test_no_network_egress_imports() -> None:
    """The scorer must never introduce network egress — grep its own
    source for anything that could reach the network."""
    import inspect

    import holdspeak.grounding as grounding_module

    src = inspect.getsource(grounding_module)
    banned = ("requests.", "httpx.", "urllib.request", "socket.", "aiohttp.")
    for token in banned:
        assert token not in src, f"unexpected network-capable symbol: {token}"
