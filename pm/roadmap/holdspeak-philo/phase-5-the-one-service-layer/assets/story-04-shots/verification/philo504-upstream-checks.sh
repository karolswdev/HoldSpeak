#!/bin/zsh
set -eu
set -o pipefail
verification=pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification
scoped=(tests/unit/test_philo5_rig_import_boundary.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_reference.py)
env HOME=$(mktemp -d) uv run pytest --collect-only -q $scoped > "$verification/upstream-counsel-collect.txt"
env HOME=$(mktemp -d) uv run pytest -q $scoped | tee "$verification/upstream-counsel-tests.txt"
