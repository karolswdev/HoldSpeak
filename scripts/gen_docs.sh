#!/usr/bin/env bash
# Write every generated document. One command; run it from any directory.
#
# Three outputs are not in git (owner ruling 2026-10-03), because they hold
# line numbers, test lists and input hashes that conflict on every merge:
#   docs/generated/api-reference.json
#   docs/generated/boundary-candidates.json
#   docs/generated/graph.json
# The other outputs stay in git; commit them when they change.
set -euo pipefail
cd "$(dirname "$0")/.."

run() { echo "+ $*"; "$@"; }

# The generators that import the product run with an isolated HOME, so the
# owner's config and database stay out of the output.
real_uv_cache="$(uv cache dir)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
product() { echo "+ uv run python $*"; HOME="$scratch" UV_CACHE_DIR="$real_uv_cache" uv run python "$@"; }

product scripts/gen_api_surface.py
product scripts/philo_openapi_reference.py
product scripts/gen_operations_json.py
product scripts/gen_mcp_sidecar_doc.py
# Standard library only.
run python3 scripts/philo_repository_census.py
run python3 scripts/philo_api_reference.py
run python3 scripts/philo_boundary_census.py
run python3 scripts/philo_doctor_reference.py
run python3 scripts/philo_config_reference.py
run python3 scripts/philo_graph_reference.py
run python3 scripts/generate_capability_docs.py
run python3 scripts/check_doc_coverage.py
