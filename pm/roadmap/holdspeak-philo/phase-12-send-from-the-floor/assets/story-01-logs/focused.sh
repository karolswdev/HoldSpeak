#!/bin/bash
set -uo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
selected=(tests/unit/test_philo11_document_sources.py tests/unit/test_philo12_artifact_source.py tests/unit/test_philo12_artifact_lifecycle.py tests/unit/test_philo12_brief_read.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo10_face_words.py tests/integration/test_philo11_document_rig.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo_census.py)
env HOME="$phase_home" uv run --python 3.13 pytest --collect-only -q "${selected[@]}" > .tmp/philo-12-01/focused-collect.log 2>&1
result=$?
if [ "$result" -ne 0 ]; then cat .tmp/philo-12-01/focused-collect.log; exit "$result"; fi
tail -1 .tmp/philo-12-01/focused-collect.log
env HOME="$phase_home" PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13 pytest -q "${selected[@]}" --basetemp "$phase_home/pytest" 2>&1 | tee .tmp/philo-12-01/focused.log
exit "${PIPESTATUS[0]}"
