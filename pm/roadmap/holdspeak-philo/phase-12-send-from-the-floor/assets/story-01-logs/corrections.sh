#!/bin/bash
set -uo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
selected=(tests/unit/test_api_surface.py tests/unit/test_philo9_atlas.py tests/unit/test_philo10_atlas.py)
env HOME="$phase_home" uv run --python 3.13 pytest --collect-only -q "${selected[@]}" > .tmp/philo-12-01/corrections-collect.log 2>&1
result=$?
if [ "$result" -ne 0 ]; then cat .tmp/philo-12-01/corrections-collect.log; exit "$result"; fi
tail -1 .tmp/philo-12-01/corrections-collect.log
env HOME="$phase_home" uv run --python 3.13 pytest -q "${selected[@]}" --basetemp "$phase_home/pytest" 2>&1 | tee .tmp/philo-12-01/corrections-green.log
exit "${PIPESTATUS[0]}"
