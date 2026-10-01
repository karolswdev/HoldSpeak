#!/bin/bash
set -uo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
(cd web && npx vitest list src/desk/floorSendBinding.test.ts)
(cd web && npx vitest run src/desk/floorSendBinding.test.ts --reporter=verbose) || exit $?
(cd web && npm run typecheck) || exit $?
env HOME="$phase_home" npm_config_cache=/Users/karol/.npm uv run --python 3.13 python scripts/check_web_baseline.py --run 2>&1 | tee .tmp/philo-12-01/web-baseline.log
exit "${PIPESTATUS[0]}"
