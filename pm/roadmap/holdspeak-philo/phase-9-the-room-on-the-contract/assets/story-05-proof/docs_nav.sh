#!/bin/zsh
# The CI "Documentation Navigation" job (.github/workflows/test.yml), plus the
# OpenAPI export check. Codex Astra r1 finding 5: every check's exit code is
# collected; the script exits 1 when ANY check fails (round one echoed rc and
# exited 0 regardless).
cd ${0:A:h}/../../../../../..
failed=0
run() { "$@"; local rc=$?; echo "rc=$rc  $*"; (( rc == 0 )) || failed=$((failed + 1)); }
run python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
run python3 scripts/check_docs.py
run python3 scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md
run python3 scripts/philo_repository_census.py --check
run python3 scripts/philo_api_reference.py --check
run python3 scripts/philo_boundary_census.py --check
run python3 scripts/philo_doctor_reference.py --check
run python3 scripts/philo_config_reference.py --check
run python3 scripts/philo_graph_reference.py --check
run python3 scripts/validate_architecture.py
run python3 scripts/generate_capability_docs.py --check
run python3 scripts/check_doc_coverage.py --check
run .venv/bin/python scripts/philo_openapi_reference.py --check
echo "checks failed: $failed"
exit $(( failed > 0 ))
