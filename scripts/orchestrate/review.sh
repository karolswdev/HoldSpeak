#!/usr/bin/env bash
# review.sh <wave> <name>
# The one review round after a merge on a security surface: a FRESH Codex session (no builder
# context), read-only by its brief, on origin/main in the review worktree.
# Brief: $ORCH/<wave>/out/<name>/brief.md (written by the orchestrator). Verdict: .../last.md.
set -uo pipefail
. "$(dirname "$0")/_env.sh"
OUT="$ORCH/$1/out/$2"; WT="${HS_REVIEW_WT:-$TREES/wt-review}"
[ -f "$OUT/brief.md" ] || { echo "no brief $OUT/brief.md"; exit 2; }
[ -d "$WT" ] || git -C "$ROOT" worktree add -q --detach "$WT" origin/main || exit 2
cd "$WT" && git fetch -q origin && git checkout -q --detach origin/main || exit 3
"$CODEX" exec -m "$MODEL" --dangerously-bypass-approvals-and-sandbox \
  -c "model_reasoning_effort=\"$EFFORT\"" --json -o "$OUT/last.md" - < "$OUT/brief.md" \
  > "$OUT/events.jsonl" 2> "$OUT/stderr.log"
RC=$?
echo "REVIEW $2 on $(git rev-parse --short HEAD) exit $RC"; head -80 "$OUT/last.md" 2>/dev/null
exit $RC
