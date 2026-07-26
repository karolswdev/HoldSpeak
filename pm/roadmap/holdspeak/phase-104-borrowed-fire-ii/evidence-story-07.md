# Evidence - HS-104-07

- **Story:** HS-104-07 - Closeout — the walk and the sitting
- **Status:** done
- **Date:** 2026-07-26

## The walk — seven beats, one continuous staged session

World: `uv run python -m uat.stage --recipe seeded-desk-watched-hand`
(the HS-103-05 steering-demo family EXTENDED with the
`gate_surface_live` probe — one recipe family, per the story).
Screenshots in assets/story-07/ (the held card, the deny-reason line,
the post-decision shade, the receipt line on the attempt card at
1440 + 393), all read. The machine beats below are the walk's own
log, verbatim where it matters:

```text
=== BEAT 1: arm the gate (both opt-ins) ===
Gate armed (/Users/karol/.holdspeak/gate.json).
No repos are held yet; the gate stays inert until `holdspeak gate allow --repo <path>`.
Holding Bash for /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/75faa314-0bc0-4119-a02b-ee7c00b7d009/scratchpad/gate-demo.
Master switch: armed
  holds Bash in /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/75faa314-0bc0-4119-a02b-ee7c00b7d009/scratchpad/gate-demo
[PASS] Agent capabilities: 4 adapters declared, 4 consumers, all backed by the ledger
[PASS] Tool-call gate: ARMED, fail-closed: Bash in /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/75faa314-0bc0-4119-a02b-ee7c00b7d009/scratchpad/gate-demo
ledger: claude-code-hooks = {'tool_hooks': 'authoritative', 'session_identity': 'inferred', 'usage_tokens': 'authoritative', 'repo_head': 'unavailable', 'blocking': 'authoritative'}
BEAT 2 approve: is_error False | result: Output:  ``` WALK_APPROVE_MARKER ```
BEAT 3 deny: is_error False | result: The command was blocked — it produced no output. The refusal reason, verbatim:  ``` denied from the desk: walk beat three, use printf not echo ```  So `echo WALK_DENY_MARKER` never ran. The permission layer wants `printf` instead. Want me to run `pri
=== BEAT 4a: expiry denies (ttl 8s) ===
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "the hold expired with no decision: expired: no decision arrived before the hold ran out"}}
=== BEAT 4b: two-process restart mid-hold ===
pre-kill state: held
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "gate armed but the hub stopped answering mid-hold; the call was not run"}}
exit=0
post-restart: invalidated | hub restarted while the proposal was held
=== BEAT 4c: unarmed fast path timed ===
real 0.73
user 0.52
sys 0.14
(re-armed for the remaining beats)
=== BEAT 5: PR receipts ===
status: live | observed: 2026-07-26T19:26:26Z
#380 open    ci=pending  heuristic  agent/hs-104-06-docs
#379 open    ci=pending  none       agent/hs-104-05-session-receipts
#378 merged  ci=passing  none       agent/hs-104-04-pr-receipts
#377 merged  ci=passing  none       agent/hs-104-03-gate-threat-model
#376 merged  ci=passing  none       agent/hs-104-02-tool-call-gate
-- see-diff:
diff on #380: ok spec 2e743d344e2248afc8e13a32e bytes 98345
-- stale beat (network yank):
yanked: stale | gh exited 1 | rows retained: 50
recovered: live | observed: 2026-07-26T19:26:48Z
=== BEAT 6: session receipts ===
-- receipt (no price row):
always: {'held': 0, 'approved': 1, 'denied': 0, 'expired': 0, 'invalidated': 0} elapsed 14.8
reported: {'model': 'claude-opus-5', 'input_tokens': 4, 'output_tokens': 112, 'cache_read_tokens': 40189, 'cache_creation_tokens': 3532}
estimated: ABSENT (no price row)
-- price row added (claude-opus-5):
estimated: {'provenance': 'price table', 'cost_usd': 0.01, 'source': 'price table', 'as_of': '2026-07-26'}
-- price row removed:
estimated present: False
```

Beat-by-beat verdicts:

1. **Arm** — both opt-ins flipped; `doctor` read `ARMED,
   fail-closed` and `4 adapters, 4 consumers, all backed`; the
   ledger served claude-code-hooks with tool_hooks / usage_tokens /
   blocking authoritative.
2. **Hold and approve** — a real `claude -p` session's Bash call
   held; the card rose on the shade (shot); Approve clicked on
   glass; `WALK_APPROVE_MARKER` ran (`is_error: false`).
3. **Hold and deny** — second real session; the desk's in-place
   reason "walk beat three, use printf not echo" reached the agent
   VERBATIM and it proposed printf instead (course-correct visible).
4. **Crown cases** — expiry denied by name (8s TTL); a REAL
   `kill -9` mid-hold denied the polling hook and the restarted hub
   read `invalidated | hub restarted while the proposal was held`
   (two process, never a mock); the unarmed hook: exit 0, no
   output, 0.73s wall including `uv` startup.
5. **PR receipts** — this repo registered through the product's own
   route; real rows with heuristic ("name match only") and
   unattributed labels; a 98,345-byte REAL local diff on #380; a
   REAL Wi-Fi yank → `stale | gh exited 1 | rows retained: 50` →
   the verb recovered `live`.
6. **Session receipts** — the gated session's receipt: always tier
   (1 approved hold, elapsed 14.8s), reported tier (claude-opus-5,
   in 4 / out 112 / cache read 40,189 / cache new 3,532, separate),
   estimate ABSENT with no price row → present with one
   (`≈ $0.01 (price table, 2026-07-26)`) → ABSENT again on
   removal. The attempt-card line screenshotted at both viewports.
7. **The sweep** — `uv run pytest -q --ignore=tests/e2e/test_metal.py`:
   **4241 passed, 37 skipped, exit 0** (23m27s; output read from
   the file per the standing rule). Web: tsc clean, **350 vitest
   passed**, build 0, tokens gate clean. Guards + censuses green
   (the captured run below).

## Bookkeeping

- Parked candidates → BACKLOG.md §AB (observed-archives adapter,
  context gauge, merge actuator, each with its one-line scope).
- BACKLOG.md §AC → the sync-clock drift defect diagnosed while it
  flaked CI during this phase's merges (root cause + fix shape).
- The spec ledger → final-summary.md (spec-complete contracts vs
  named TypeScript-only spec debt).
- Roadmap README pointer + Last updated moved; the phase status
  reads MACHINE SCOPE COMPLETE and flips CLOSED only when the
  owner's sitting verdict lands here.

## The sitting — the verdict

The first pass returned a RIDER, not an acceptance (2026-07-26):
*"I was half-expecting you to pick up the generation of new,
Workbench-like-but-modern assets with pixellab. So I will only
accept once you have done that. Gone are the 'crystals' for KB,
gone are cute-ass bitmojis, in are more Workbench 2.0-but-amazing
icons."* — chartered as HS-104-08 (the HS-103-07 mid-sitting
precedent) and shipped the same evening (evidence-story-08.md).

On the reforged desk, the verdict, verbatim: **"Yup. Better.
Let's close out the phase."** Accepted; the phase closes 8/8.

## Proof

### Captured run — 2026-07-26T19:47:14Z

- **Command:** `uv run pytest -q tests/unit/test_gate_chokepoint.py tests/unit/test_coder_gate.py tests/unit/test_session_receipts.py tests/unit/test_pr_receipts.py tests/unit/test_agent_capabilities.py tests/integration/test_gate_threat_model.py tests/uat/test_recipes_parse.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 56ae0ec0ed93edb6be263e1e38367495aa2fbb69

```text
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 38.59s
```
