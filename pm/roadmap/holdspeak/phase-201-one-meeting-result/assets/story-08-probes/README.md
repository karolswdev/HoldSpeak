# HS-201-08 replay probes

These copies preserve the temporary probe code named in the red captures.
They run against an isolated HOME. They do not use a microphone.

- `attention_wallclock.py`: set the ambient heartbeat clock to 02:30 UTC. Before the fix, eight tests fail. After the test helper pins its default, they pass; explicit quiet-hours clocks still apply.
- `linux_backend.py`: model a Linux runner with no transcription backend installed. The former implicit-MLX test fails; the repaired test pins the backend preconditions itself.
- `fake_runner_pytest.py`: treat a supplied temporary HOME as the runner account home, then run the selected pytest nodes. The pair named in the evidence creates an installation marker and fails the guard, as the old CI invocation did. Ordinary pytest with a distinct isolated HOME passes; no guard is weakened.
- `ci_summary.py`: fetch the completed original main CI failure names and commit identity. This retrieves evidence; it is not a local Linux test run.

Use the probe directory on PYTHONPATH for `-p attention_wallclock` or `-p linux_backend`. The real event-gated listener regression is now `tests/unit/test_web_server_startup.py`.

- docs_ci.py runs the eleven documentation CI commands with the invoking interpreter. Final proof uses Python 3.12 and records the staged input tree.
- web-check-result.txt retains selected actual output and the raw-log digest from the completed web run; it is not a rerun.

- `fd_pressure.py`: opens 1,050 valid descriptors, runs the real interrupted-send pytest node, and closes all descriptors in finally. It reproduces the old select limit; it does not diagnose descriptor accumulation.
- `weekly_counter_canary.py`: extracts the actual glass-test counter loop and runs it against rendered timestamp and zero-counter cases. This tests the assertion, not product rendering; the real BriefView component tests cover rendering.
- `daily_summary_canary.py`: extracts the two actual summary-only assertions from the daily-loop rig. Empty state passes; a forced plugin-call record or proposal must fail. The real hub/producer and both-width walk remain separate proof.
