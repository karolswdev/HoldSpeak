# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_doctor_cli_one_list.py to restore.

# ruff: noqa


# --- test_the_real_list_carries_coding_agents_mic_hotkey_and_connectors: P8: inspect.getsource scan for function names
def test_the_real_list_carries_coding_agents_mic_hotkey_and_connectors() -> None:
    import inspect

    source = inspect.getsource(local_doctor.collect_doctor_checks)
    for check in ("_check_coding_agents", "_check_microphone", "_check_hotkey", "_check_connector_packs"):
        assert check in source
