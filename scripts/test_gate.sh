#!/bin/sh
# The full-suite gate, fast: two lanes whose combined failure names equal the
# serial suite's (certified against a same-tree serial baseline, 2026-08-10).
#
# Lane 1 (parallel, ~3 min): everything except the serial tail, under plain
#   xdist `load`. Timeouts use the SIGNAL method only: SIGALRM fires in the
#   worker's main thread and names the hung test without killing the worker —
#   the thread method kills the whole process ("node down") and cascades into
#   xdist scheduler crashes. A hang can never silently eat an hour.
# Lane 2 (serial tail, ~13 min): tests/e2e + tests/uat + the named files.
#   These boot real browsers, hub subprocesses on fixed ports, local HTTP
#   loops, the physical LAN box, or timing-sensitive threads — each measured
#   parallel-unsafe (worker crashes clustered in e2e; the named files flaked
#   only under contention). test_metal stays excluded everywhere (hangs
#   without a mic). De-flaking the named files so they can rejoin lane 1 is
#   remediation-phase work.
#
# Run under an isolated HOME to keep tests off the real ~/.holdspeak:
#   HOME=$(mktemp -d) sh scripts/test_gate.sh
set -u

status=0
uv run pytest -q -n auto --dist load \
    --timeout=180 --timeout-method=signal \
    --ignore tests/e2e --ignore tests/uat \
    --ignore tests/unit/test_webhook_post_actuator.py \
    --ignore tests/unit/test_gated_connector.py \
    --ignore tests/integration/test_web_companion_slack.py \
    --ignore tests/unit/test_device_recording_tick.py \
    --ignore tests/unit/test_intel_cloud.py \
    -p no:cacheprovider "$@" || status=1
uv run pytest -q \
    --timeout=300 --timeout-method=signal \
    tests/e2e tests/uat \
    tests/unit/test_webhook_post_actuator.py \
    tests/unit/test_gated_connector.py \
    tests/integration/test_web_companion_slack.py \
    tests/unit/test_device_recording_tick.py \
    tests/unit/test_intel_cloud.py \
    --deselect tests/e2e/test_metal.py \
    -p no:cacheprovider "$@" || status=1
exit $status
