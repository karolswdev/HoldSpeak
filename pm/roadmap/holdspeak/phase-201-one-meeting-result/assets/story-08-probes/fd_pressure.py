"""Run the real interrupted-send test with valid descriptors above select's ceiling."""
import os
import sys

import pytest

opened = []
try:
    for _ in range(1050):
        opened.append(os.open(os.devnull, os.O_RDONLY))
    print(f"descriptor pressure: {len(opened)} open; highest={max(opened)}", flush=True)
    result = pytest.main([
        "-q", "-s",
        "tests/integration/test_process_input_real_hub.py::test_real_sigkill_mid_send_reconciles_indeterminate_by_command_id",
    ])
finally:
    for descriptor in opened:
        os.close(descriptor)
sys.exit(result)
