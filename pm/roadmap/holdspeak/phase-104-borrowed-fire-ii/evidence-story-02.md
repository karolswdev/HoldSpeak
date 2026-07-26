# Evidence - HS-104-02

- **Story:** HS-104-02 - The tool-call gate — a held hand, not a watched one
- **Status:** done
- **Date:** 2026-07-26

## The live walk — REAL Claude Code sessions, real metal

Staged hub: `uv run python -m uat.stage --recipe seeded-desk` (port
8789). Gate armed on the real machine: `holdspeak gate arm` +
`gate allow --repo <scratch>/gate-demo`. Hook settings passed to a
real `claude -p` process via `--settings` (PreToolUse, matcher Bash,
`holdspeak gate hook`). Every beat below happened against live
processes; the desk decisions were clicked in the real UI via
Playwright and screenshotted (assets/story-02/, read before flip).

1. **Hold and approve.** The session's Bash call
   (`tool_use_id=toolu_016K6Y4V9pkD8joDSueUZKxk` — the hook's
   idempotency key) held; the card rose in the shade's "Needs you"
   (gate-held-desktop-1440.png, gate-held-phone-393.png); Approve
   clicked on glass; the command ran and the agent reported
   `GATE_APPROVE_MARKER-11798` (`is_error: false`).
2. **Hold and deny with reason.** Second real session held
   (`toolu_01HysmGJC6BxpQGsND2Vi8zA`); Deny opened the in-place
   reason line (gate-deny-reason-desktop-1440.png), sent
   "no destructive echoes today, use printf"; the agent's final
   report quoted it VERBATIM ("denied from the desk: no destructive
   echoes today, use printf") and course-corrected by proposing
   `printf` instead. The command never ran.
3. **Unarmed inertness.** Gate off: the hook exited 0 with no
   output, no hub contact, no rows, in 0.585s total (mostly `uv`
   startup).
4. **Fail-closed, hub unreachable.** Armed + hub pointed at a dead
   port: `permissionDecision: deny`, reason "gate armed but hub
   unreachable; the call was not run".
5. **Expiry denies.** TTL 8s, no decision: deny "the hold expired
   with no decision"; the hub audit shows `expired`.
6. **Restart honesty, two-process.** A second dedicated hub (port
   8871) held a proposal; `kill -9` on the REAL process mid-hold →
   the polling hook denied ("the hub stopped answering mid-hold");
   hub restarted → the proposal read `invalidated` with reason "hub
   restarted while the proposal was held", audit row written.
7. **Doctor + ledger read the armed state.**
   `[PASS] Tool-call gate: ARMED, fail-closed: Bash in <repo>` and
   `[PASS] Agent capabilities: 4 adapters declared, 2 consumers,
   all backed by the ledger`.
8. **Audit read-back** (`GET /api/gate/audit`, the staged hub):
   every proposal reached a terminal state — approved / denied
   (reason attached) / expired — with its `proposed` row, sha256 +
   120-char head only, never the full arguments.

Ledger flip in this commit: `claude-code-hooks` `tool_hooks` +
`blocking` → `authoritative`, `session_identity` → `inferred`
(self-reported session_id); both routes pinned through
`require_capability` by the census.

## Proof

### Captured run — 2026-07-26T18:26:29Z

- **Command:** `uv run pytest -q tests/unit/test_coder_gate.py tests/unit/test_gate_chokepoint.py tests/unit/test_agent_capabilities.py tests/unit/test_db.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** df35a2482de48196ba42af4be816874671a2858d

```text
........................................................................ [ 54%]
............................................................             [100%]
132 passed in 6.80s
```
