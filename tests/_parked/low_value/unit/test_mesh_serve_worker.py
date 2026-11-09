# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mesh_serve_worker.py to restore.

# ruff: noqa


# --- test_cli_wiring_parses: P4: runs 'mesh --help' in a subprocess and asserts the help text contains the word serve
def test_cli_wiring_parses() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "holdspeak.main", "mesh", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0
    assert "serve" in proc.stdout
