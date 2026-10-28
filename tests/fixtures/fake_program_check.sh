#!/bin/sh
# The Programs rig's fake gate: it prints what scripts/quick_check.sh prints
# (the six sections, a result line each, the verdict line), fast and with no
# test run. The engine writes its header and footer around this output.
#   FAKE_CHECK_RED=1     the pytest section is red, the verdict is RED
#   FAKE_CHECK_NO_LOG=1  print nothing (the log then holds only the header)
#   FAKE_CHECK_RED_FILE  red while this file exists (a test removes it for round 2)
[ "${FAKE_CHECK_NO_LOG:-}" = "1" ] && exit 1
red=0
[ "${FAKE_CHECK_RED:-}" = "1" ] && red=1
[ -n "${FAKE_CHECK_RED_FILE:-}" ] && [ -f "$FAKE_CHECK_RED_FILE" ] && red=1
echo "quick_check: 3 changed files against origin/main"
echo "== build"
echo "   build ok"
echo "== vitest related (1 files)"
echo "   Tests  4 passed (4)"
echo "== pytest affected (2 files)"
if [ "$red" = 1 ]; then
  echo "   FAILED tests/unit/test_fake.py::test_red - assert 1 == 2"
  echo "   1 failed, 11 passed in 2.10s"
  echo "   pytest failed (rc=1): RED"
else
  echo "   12 passed in 2.10s"
fi
echo "== desk sweep"
echo "   62 passed in 40.00s"
echo "== canon guards"
echo "   30 passed in 1.00s"
echo "== repo guards"
echo "   210 passed in 9.00s"
if [ "$red" = 1 ]; then echo "QUICK CHECK RED: fix before merging."; exit 1; fi
echo "QUICK CHECK GREEN: merge; the main watcher runs the whole suite."
