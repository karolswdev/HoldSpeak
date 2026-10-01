#!/bin/bash
set -euo pipefail
phase_home=$(mktemp -d)
trap 'uv run --python 3.13 python -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
run() { env HOME="$phase_home" uv run --python 3.13 python "$@"; }

run -m unittest discover -s tests/unit -p test_docs_navigation.py
run scripts/check_docs.py
run scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md
run scripts/philo_repository_census.py --check
run scripts/philo_api_reference.py --check
run scripts/philo_boundary_census.py --check
run scripts/philo_doctor_reference.py --check
run scripts/philo_config_reference.py --check
run scripts/philo_graph_reference.py --check
run scripts/validate_architecture.py
run scripts/generate_capability_docs.py --check
run scripts/check_doc_coverage.py --check
