#!/bin/zsh
# The CI "Documentation Navigation" job, verbatim (.github/workflows/test.yml),
# plus the OpenAPI export check (docs/generated/openapi.json).
cd ${0:A:h}/../../../../../..
set -x
python3 -m unittest discover -s tests/unit -p test_docs_navigation.py; echo "rc=$?"
python3 scripts/check_docs.py; echo "rc=$?"
python3 scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md; echo "rc=$?"
python3 scripts/philo_repository_census.py --check; echo "rc=$?"
python3 scripts/philo_api_reference.py --check; echo "rc=$?"
python3 scripts/philo_boundary_census.py --check; echo "rc=$?"
python3 scripts/philo_doctor_reference.py --check; echo "rc=$?"
python3 scripts/philo_config_reference.py --check; echo "rc=$?"
python3 scripts/philo_graph_reference.py --check; echo "rc=$?"
python3 scripts/validate_architecture.py; echo "rc=$?"
python3 scripts/generate_capability_docs.py --check; echo "rc=$?"
python3 scripts/check_doc_coverage.py --check; echo "rc=$?"
.venv/bin/python scripts/philo_openapi_reference.py --check; echo "rc=$?"
