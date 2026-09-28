#!/bin/zsh
# The UX-canon ratchet after PHILO-9-04: A1 (raw <button>) 106 -> 105. The
# healing notice must no longer list A1; the ratchet and scan fences pass.
cd ${0:A:h}/../../../../../..
HOME_REAL=$HOME
HOME=$(mktemp -d) UV_CACHE_DIR=$HOME_REAL/.cache/uv \
  uv run --extra test python -m pytest -q -p no:cacheprovider -s \
  tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py \
  tests/unit/test_interior_canon_guard.py tests/unit/test_phase200_canon_guard.py 2>&1 \
  | grep -E "ratchet:|passed|failed|Error"
exit ${pipestatus[1]}
