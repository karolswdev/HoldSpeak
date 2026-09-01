# Evidence - HS-159-07

- **Story:** HS-159-07 - The close (gates, suite amendments, final summary)
- **Status:** done
- **Date:** 2026-08-31

## Proof

### Captured run — 2026-09-01T00:28:42Z

- **Command:** `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/cc25f299-2c98-4864-9e8e-a3504d65c608/scratchpad/close-159.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6cffd49f3da8425656e754468648b4f91608eaff

```text
== FULL SUITE (authoritative):
15 failed, 8187 passed, 55 skipped in 1330.79s (0:22:10)
== SWEEP vs main (27 names @ a685c36e):
FAILED tests/e2e/test_hs151_thread_glass.py::test_done_row_has_receipt_id
FAILED tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
FAILED tests/unit/test_device_recording_tick.py::test_sender_exception_does_not_kill_thread
FAILED tests/unit/test_node_link_two_process.py::TestTwoProcessProof::test_live_kill_stale_offline_restart_resume
== FLAKE + ROOT-CAUSE PROOFS (live):
.......                                                                  [100%]
7 passed in 4.80s
== WEB FINALS (recorded):
Suite totals: 1984 passed, 0 failed, 0 skipped
VERDICT: baseline-subset, zero branch-new
```
