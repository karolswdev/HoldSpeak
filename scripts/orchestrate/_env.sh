# Shared paths for the orchestration scripts (docs/internal/ORCHESTRATION.md). Sourced, never run.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"          # the main checkout
TREES="$(dirname "$ROOT")"                                          # where scripts/lane.sh puts wt-<lane>
ORCH="${HS_ORCH:-$ROOT/.tmp/orchestrate}"                           # briefs, reports, the ledger
CODEX="${HS_CODEX:-codex}"
MODEL="${HS_BUILDER_MODEL:-gpt-6.1-sol}"
EFFORT="${HS_BUILDER_EFFORT:-high}"
lane_tree() { echo "$TREES/wt-$(echo "$1" | tr '/' '-')"; }
