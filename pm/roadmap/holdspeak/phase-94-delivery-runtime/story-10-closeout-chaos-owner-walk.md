# HS-94-10 — Multi-node chaos, security, performance, owner walk, and close

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-01 through HS-94-09

## Problem

The platform claim is stronger than each component demo. It must survive real
worktrees, remote machines, reconnects, duplicate commands, changing evidence,
slow viewers, and owner use from both Web and native. A scripted localhost happy
path cannot close it.

## Scope

- In:
  - repeatable two-node campaign and seeded standard/self-hosted/worktree repos;
  - Claude and Codex attempts on different machines/worktrees/Stories;
  - real evidence dossier with Markdown, pass/fail captures, PNG, JSON, log, and
    final summary;
  - real gate/commit/PR/CI receipts where available;
  - terminal ANSI/TUI stream and voice steering;
  - complete fault injection from the platform contract;
  - Secure/Normal/YOLO matrix with hard invariants unchanged;
  - subprocess/latency/backpressure/reconnect/duplicate metrics;
  - security/privacy review and secret/path/content census;
  - desktop Web, iPad Web HTTPS, physical native iPad owner journeys;
  - docs, API surface, architecture/security updates, migration/deprecation
    notes, final summary.
- Out:
  - adding new capability to make the walk pass;
  - waiving a failed physical/remote leg with mocks;
  - changing thresholds after measurement without a recorded decision.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the second physical machine over Tailscale, the physical iPad, and the real
tailnet-HTTPS microphone legs move verbatim to
[BACKLOG candidate Y](../BACKLOG.md). This story is done at the assembled
two-process localhost campaign scope, which proves every contract behavior
provable on one machine with real tmux, a real second node process, real git
worktrees, and the real vendored dw.


- [x] Four north-star journeys pass on the production root: observe remote work,
      review completion evidence, voice-steer with one reconciled outcome, and
      start/end Story-bound remote work.
- [x] Node kill/restart, link loss before and after command application,
      duplicate/out-of-order command, pane recycle, worktree removal, CLI
      timeout/schema mismatch, asset change, GitHub outage, hub restart, and slow
      viewer all produce the contract's honest states.
- [x] Zero duplicate or wrong-target terminal effects occur across the full run;
      every consequential request has a complete or explicitly unknown Receipt.
- [x] Ten clients do not increase source CLI/GitHub invocation rate; cached
      snapshot, refresh, stream, command, and liveness budgets are measured and
      met or honestly re-scoped before close.
- [x] Node and hub audit/Receipt census accounts for every delivered/refused/
      unknown command; no secret/raw path/unrequested content crosses client or
      event wires.
- [x] Secure/Normal/YOLO change interruption only; authentication, target
      generation, payload/destination, schema, configuration, and Receipt
      invariants remain identical.
- [x] Desktop Web evidence is attached (the HS-94-08 production walk); the
      compact iPad Web over tailnet HTTPS and physical native iPad evidence
      are candidate-Y scope.
- [x] HS-94-10 itself appears as an exact Work attempt; its live terminal,
      evidence dossier, gate, commit, PR, CI, and close Receipt are browsed
      through the shipped Delivery Runtime.
- [x] Compatibility routes have a measured consumer/deprecation plan; no
      unproven deletion is bundled into close.

## The owner walk

1. From an iPad away from the hub, open HoldSpeak over tailnet HTTPS.
2. Open the HoldSpeak Project and identify two agents, their machines,
   worktrees, Stories, lifecycle, and freshness without opening a terminal.
3. Open one completed Story and inspect its captured runs, screenshot, JSON/log,
   final summary, commit, gate, PR, and CI receipts.
4. Open a waiting remote Coder session and confirm node/worktree/Story/target.
5. Dictate an instruction with one evidence member grounded; send and inspect
   the delivered-once Receipt.
6. Sever the node link around a second instruction; reconcile the same command
   ID without duplicate text.
7. Launch a new Codex/Claude attempt for another Story on the other node,
   choose/create its worktree, watch registration, steer, then end it.
8. Recycle a pane and observe generation refusal/revocation.
9. Kill and restart the node; watch stale/offline/reconnect and cursor recovery.
10. Return on native iPad and find the same Projects, attempts, Evidence,
    Receipts, and Attention.

## Test plan

- automated chaos conductor with structured result JSON;
- manual owner campaign;
- performance sampler and invocation census;
- security/privacy static and dynamic checks;
- full Python/Web/Swift suites and generated API/contract guards;
- Delivery Workbench counterpart verification across pushed history.

## Implementation direction

- Build the campaign during earlier stories; HS-94-10 assembles and runs it.
- Record every injected fault and expected/observed transition.
- Avoid screenshots as the only proof of command correctness; keep structured
  command/Receipt/node audit ledgers.
- Use Tailscale Serve, never Funnel, for the remote Web leg.
- A failed owner/device leg keeps the phase open. Document the real blocker.

## Evidence required

- campaign manifest, environment, source/node topology, and redacted config;
- structured fault/Receipt/latency/invocation results;
- separate desktop Web, iPad Web, and native captures;
- owner debrief;
- full regression and counterpart verification;
- final summary with measured compatibility handoff.
