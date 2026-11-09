#!/usr/bin/env bash
# Write every generated document. One command; run it from any directory.
#
# No output is in git (owner ruling 2026-10-03, extended 2026-11-08): every
# park or move made a committed copy stale, and every PR conflicted on them.
# .gitignore lists them: docs/generated/, docs/api-surface.json,
# docs/API_SURFACE.md, docs/API_REFERENCE.md and docs/MCP_SIDECAR.md (filled
# from scripts/mcp_sidecar_doc.template.md). Tests derive from the live tree.
set -euo pipefail
cd "$(dirname "$0")/.."

run() { echo "+ $*"; "$@"; }

# The generators that import the product run with an isolated HOME, so the
# owner's config and database stay out of the output.
real_uv_cache="$(uv cache dir)"
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
product() { echo "+ uv run python $*"; HOME="$scratch" UV_CACHE_DIR="$real_uv_cache" uv run python "$@"; }

mkdir -p docs/generated  # out of git since 2026-11-08; a fresh tree has no folder
product scripts/gen_api_surface.py
product scripts/philo_openapi_reference.py
product scripts/gen_operations_json.py
product scripts/gen_mcp_sidecar_doc.py
product scripts/operation_parity.py | tail -n +2 > docs/generated/operation-parity.md  # drop the "+" line
# Standard library only.
run python3 scripts/philo_repository_census.py
run python3 scripts/philo_api_reference.py
run python3 scripts/philo_boundary_census.py
run python3 scripts/philo_doctor_reference.py
run python3 scripts/philo_config_reference.py
# The capability docs write docs/generated/components.yaml, which the graph
# reference joins on: generate first, join second.
run python3 scripts/generate_capability_docs.py
run python3 scripts/philo_graph_reference.py
run python3 scripts/check_doc_coverage.py
