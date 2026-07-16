# HS-94-06 progress record — Terminal stream and idempotent command receipts

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (the tailnet
output-latency budget is BACKLOG candidate Y; every safety behavior is
machine-verified, including on real local tmux).

## What shipped — the safety core

- `holdspeak/delivery/terminal.py`: immutable targets (opaque target_id →
  canonical %N with a generation that bumps on pane-identity change), one
  node-side capture per pane fanned out to N subscribers over a bounded ring
  (200 lines / 64 KB snapshot, 256 deltas / 256 KB ring), a slow subscriber
  getting `resync_required` + a real fresh snapshot (never fabricated bytes),
  and typed absences (target_gone/generation_mismatch/stream_unavailable/
  unauthorized).
- `holdspeak/delivery/commands.py` + `holdspeak/db/delivery_receipts.py`:
  the §8 command envelope (command_schema:1, immutable target, hub-derived
  authority, payload_sha256, expected_sequence) with the mandatory
  processing order implemented exactly — authn/version → existing-receipt
  return for a known command_id → expiry → generation verify (mismatch
  refuses AND revokes the grant) → hard prereqs + ONE policy decision
  (resolved once at the hub, decoded node-side, never re-resolved; test
  counts resolve_policy == 1) → expected_sequence serialization → execute
  through the coder_steering/coder_factory chokepoints → durable dedup
  ledger commit → receipt. A duplicate envelope returns the same receipt
  with one execution; a lost-after-send command reconciles by command_id;
  a node reset that loses the ledger yields indeterminate_after_node_reset.
  The hub DB stores only hash + head (privacy proven by a full-dump sweep).
- `holdspeak/web/routes/delivery_terminal.py`: the five routes, wired into
  the app sharing one NodeLinkState with the node link so hub-issued
  commands reach a remote node through the same authenticated long-poll
  (the node router's command_source is the terminal command service).

## Verification

52 unit tests + 4 real-tmux integration tests (live ANSI delta, envelope →
real pane exactly once + reconcile, YOLO promptless, live recycled-pane
refusal). Steering/factory/coder suites stay green (165); the delivery lane
is 232+; full unit suite 3,179 passed after production wiring; the API
surface regenerated with all 330 routes (a dictation-router include lost to
an earlier concurrent write was restored in the same pass).
Captured at close in [evidence-story-06](./evidence-story-06.md).
