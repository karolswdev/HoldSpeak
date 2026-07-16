# HS-94-10 progress record — Multi-node chaos, security, performance, close

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the assembled two-process localhost campaign
scope; the second physical machine, physical iPad, and real tailnet-HTTPS
microphone are BACKLOG candidate Y.

## What was proven

`scripts/phase94_delivery_campaign.py` stands up a real uvicorn hub serving
the exact six delivery routers on the same shared spine web_server.py wires,
isolated to a temp HOME/registry/DB/ledger, with a REAL second OS process as
the node (`python -m holdspeak.commands.node_serve serve`), real tmux panes,
real git worktrees, and the real vendored dw. The only stub is the launcher
exec.

- **Four north-star journeys** pass over real HTTP: observe remote work
  (node hello/heartbeat → live in the snapshot with an attached attempt),
  browse historical evidence (real dw manifest + a manifest-bound asset
  fetch with ETag = member sha256), steer a live coder (terminal.text
  through the envelope → delivered receipt, marker in the real pane exactly
  once, duplicate command_id returns the same receipt), launch a
  story-bound agent (worktree.create + spawn + target + one launch attempt).
- **Fault matrix** matches the contract's honest states: node kill before
  apply → not_executed; kill after claim → unknown → indeterminate_after_
  node_reset on epoch mismatch; recycled pane → generation_mismatch refused
  and revoked; expiry → command_expired; out-of-order → sequence_conflict;
  source failure → stale with last-known-good retained; link loss + resume →
  contiguous cursor, no dup, no gap.
- **Zero duplicate/wrong-target** effects across the run.
- **Poll economy**: 10 concurrent snapshot clients = 3 dw invocations, same
  as 1 (single-flight measured).
- **Audit/privacy census** (`scripts/phase94_audit_census.py`): 13/13
  commands accounted; 0 secret/token/path/content leaks across 33 client
  wire bodies, 18 hub DB rows, and 11 node ledger receipts.
- **Posture invariance**: Secure/Normal/YOLO change only the authority basis
  (interruption); authentication, target binding, generation, schema, audit,
  and per-payload sha binding are identical.
- **Self-attempt**: HS-94-10 registered itself as an exact manual attempt on
  the holdspeak source with a live target and a delivered receipt, appearing
  exactly-once in the read model — the story proving itself through the
  runtime.
- **Compat census** (measured, nothing deleted): /api/missioncontrol/* has 7
  authored callers, /api/coders/* has 14; both stay until parity shows zero
  callers.

No product code was edited and no real product bug was found; the two
initial red legs were campaign test-logic corrections recorded in the
report.

## Verification

Campaign exit 0 (every leg PASS), census PASS, the bounded pytest wrapper
8 passed, `tests/unit -k delivery` 237 passed with no regression. The
machine-readable report and log are in evidence/hs-94-10/.
Captured at close in [evidence-story-10](./evidence-story-10.md).

## Candidate-Y residue

The second physical machine over Tailscale (real transport, clock skew,
latency budgets), the physical iPad native + iPad Safari tailnet-HTTPS
microphone legs, and the owner walk on all three surfaces.
