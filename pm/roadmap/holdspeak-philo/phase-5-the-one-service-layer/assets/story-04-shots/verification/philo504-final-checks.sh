#!/bin/zsh
set -eu
set -o pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright
export HOLDSPEAK_EVIDENCE_WRITE=1
verification=pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification
python_tests=(tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_pairs.py tests/unit/test_graph_walk_calibration.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_philo5_his_words.py)
env HOME=$(mktemp -d) uv run pytest --collect-only -q $python_tests > "$verification/final-python-collect.txt"
env HOME=$(mktemp -d) uv run pytest -q $python_tests | tee "$verification/final-python-tests.txt"
cd web
env HOME=$(mktemp -d) npx vitest run --maxWorkers=2 src/desk/chair/__tests__/briefReceiptRendered202.test.tsx src/desk/chair/__tests__/briefFreshRead.philo504.test.tsx src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx | tee "../$verification/final-web-tests.txt"
