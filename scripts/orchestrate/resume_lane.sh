#!/usr/bin/env bash
# resume_lane.sh <wave> <stem> <lane> <followup-file> [round]
# A follow-up round to the SAME Codex session of a lane (it keeps its context), in its worktree.
# Report: $ORCH/<wave>/out/<stem>/last-r<round>.md.
set -uo pipefail
. "$(dirname "$0")/_env.sh"
WAVE="$1"; STEM="$2"; LANE="$3"; FOLLOW="$4"; R="${5:-2}"
WT="$(lane_tree "$LANE")"; OUT="$ORCH/$WAVE/out/$STEM"
ID=$(head -1 "$OUT/events.jsonl" | python3 -c "import sys,json; print(json.loads(sys.stdin.readline())['thread_id'])")
cd "$WT" || exit 2
"$CODEX" exec resume "$ID" -m "$MODEL" --dangerously-bypass-approvals-and-sandbox \
  -c "model_reasoning_effort=\"$EFFORT\"" --json -o "$OUT/last-r$R.md" - < "$FOLLOW" \
  > "$OUT/events-r$R.jsonl" 2> "$OUT/stderr-r$R.log"
RC=$?
echo "LANE $LANE round $R exit $RC"; head -60 "$OUT/last-r$R.md" 2>/dev/null; tail -3 "$OUT/stderr-r$R.log"
exit $RC
