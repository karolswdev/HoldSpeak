#!/bin/zsh
# The web-unit law: the baseline diff (zero branch-new), then vitest's own
# summary with its Errors line (vitest prints "Errors" only when there are any),
# then the web-quality contract CI runs (`npm run check`).
cd ${0:A:h}/../../../../../..
PY=$PWD/.venv/bin/python
HOME_REAL=$HOME
HOME=$(mktemp -d) UV_CACHE_DIR=$HOME_REAL/.cache/uv npm_config_cache=$HOME_REAL/.npm \
  $PY scripts/check_web_baseline.py --run
rc1=$?
(cd web && npx vitest run 2>&1 | grep -E "Test Files|Tests |Errors|Duration")
rc2=${pipestatus[1]}
(cd web && npm run check 2>&1 | grep -E "drift|token gate|Test Files|Tests |Errors|built in|bundle gate|error TS|FAIL")
rc3=${pipestatus[1]}
echo "baseline=$rc1 vitest=$rc2 check=$rc3"
exit $(( rc1 || rc2 || rc3 ))
