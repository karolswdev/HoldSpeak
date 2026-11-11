#!/usr/bin/env bash
# run_lane.sh <wave> <stem> <lane>
# One Codex builder, one lane, to completion. The brief is <wave>/_common.md + <wave>/<stem>.md
# under $ORCH. The lane's worktree comes from `scripts/lane.sh new <lane>` first.
# Report: $ORCH/<wave>/out/<stem>/last.md. Run it as ONE background command per lane.
set -uo pipefail
. "$(dirname "$0")/_env.sh"
WAVE="$1"; STEM="$2"; LANE="$3"
WT="$(lane_tree "$LANE")"; OUT="$ORCH/$WAVE/out/$STEM"; mkdir -p "$OUT"
[ -d "$WT" ] || { echo "no worktree $WT"; exit 2; }
sed -e "s|__WT__|$WT|g" -e "s|__BRANCH__|$LANE|g" "$ORCH/$WAVE/_common.md" > "$OUT/brief.md"
echo >> "$OUT/brief.md"; cat "$ORCH/$WAVE/$STEM.md" >> "$OUT/brief.md"
date > "$OUT/started"
"$CODEX" exec -m "$MODEL" -C "$WT" --dangerously-bypass-approvals-and-sandbox \
  -c "model_reasoning_effort=\"$EFFORT\"" --json -o "$OUT/last.md" - < "$OUT/brief.md" \
  > "$OUT/events.jsonl" 2> "$OUT/stderr.log"
RC=$?
date > "$OUT/finished"
echo "LANE $LANE exit $RC"
echo "--- last message ---"; head -80 "$OUT/last.md" 2>/dev/null
echo "--- stderr tail ---"; tail -5 "$OUT/stderr.log"
exit $RC
