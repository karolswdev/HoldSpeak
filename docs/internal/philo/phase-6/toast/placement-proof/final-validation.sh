set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright
uv run --extra dev pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo_architecture.py > docs/internal/philo/phase-6/toast/placement-proof/final-python-collect.txt 2>&1
uv run --extra dev pytest -q tests/unit/test_philo_graph_atlas.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo_architecture.py > docs/internal/philo/phase-6/toast/placement-proof/final-python-run.txt 2>&1
tail -4 docs/internal/philo/phase-6/toast/placement-proof/final-python-collect.txt
tail -8 docs/internal/philo/phase-6/toast/placement-proof/final-python-run.txt
python3 scripts/generate_capability_docs.py > .tmp/philo603/generate-caps.txt
python3 scripts/check_doc_coverage.py > .tmp/philo603/generate-coverage.txt
python3 scripts/philo_graph_reference.py > .tmp/philo603/generate-graph.txt
python3 scripts/philo_boundary_census.py > .tmp/philo603/generate-boundary.txt
python3 scripts/generate_capability_docs.py --check > docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt
python3 scripts/check_doc_coverage.py --check >> docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt
python3 scripts/philo_graph_reference.py --check > .tmp/philo603/graph-check.txt
python3 scripts/philo_api_reference.py --check >> docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt
python3 scripts/philo_boundary_census.py --check >> docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt
python3 - <<'PY'
from pathlib import Path
p=Path('docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt')
p.write_text(p.read_text()+'philo_graph_reference.py --check: exit 0 (all graph rows checked; full console in .tmp/philo603/graph-check.txt)\n')
PY
cat docs/internal/philo/phase-6/toast/placement-proof/generated-checks.txt
git diff --check
