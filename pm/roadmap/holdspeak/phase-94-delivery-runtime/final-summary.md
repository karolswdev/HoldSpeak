# Phase 94 — The Delivery Runtime — Final summary

**Closed:** 2026-07-16, all ten stories done at owner-rescoped
machine-verifiable scopes under the owner's standing close directive.
**Continuation:** every second-physical-machine, physical-iPad, and
tailnet-HTTPS criterion is preserved verbatim as scheduled work in
[BACKLOG candidate Y](../BACKLOG.md); nothing was waived silently.

## What this phase shipped

Delivery Workbench-backed projects, story progress, remote/local Coder
sessions, terminals, evidence, and receipts are now one HoldSpeak platform
primitive, observable and operable from the Desk.

- **The counterpart contract and worktree truth (94-01):** the vendored dw
  gained `capabilities`, cursored `events --after` with stable event ids,
  and `evidence manifest`/`asset`; events resolve the journal through the
  git common dir so linked worktrees are no longer silent; self-hosted
  layouts resolve evidence without weakening containment.
- **The source registry and read model (94-02):** a versioned source/
  worktree registry with credential-free fingerprints and opaque salted
  ids, a single-flight collector over dw, and a coherent `delivery_schema:1`
  snapshot whose one revision covers every collection — 10 readers cost one
  dw flight, no path or secret crosses the wire.
- **The node link (94-03):** an outbound authenticated node with rotatable/
  revocable per-node tokens (a browser credential is structurally refused),
  monotonic liveness, allow-listed metadata-only events, and cursor rules
  that cannot duplicate after node state loss — proven by a real
  two-process kill/restart/resume walk, with an embedded local adapter on
  the same code path.
- **Work attempts (94-04):** durable records with compound identity, honest
  states, and a partial unique index forbidding two live exact attempts per
  session; the correlation fixture reproduces the real dw zero-exact
  baseline and proves exact rider-claim attempts on a real linked worktree.
- **Evidence dossiers (94-05):** manifest-bound story/phase dossiers with
  sanitized markdown, parsed pass/fail runs, and a ranged asset proxy whose
  typed refusals (404/413/409 bundle_changed and hash_mismatch/503) never
  leak a path.
- **The terminal stream and command envelope (94-06):** the safety core —
  immutable targets, one capture fanned to N subscribers over a bounded ring
  with honest resync, and the exact §8 processing order (dedup by
  command_id, generation verify with revoke, one hub-resolved policy
  decision, sequence serialization, mirrored receipts,
  indeterminate_after_node_reset) — verified on real tmux.
- **The remote factory and launch (94-07):** node-owned agent profiles with
  fixed executables, and atomic `agent.launch` (worktree.create → spawn →
  target → one attempt → receipt) with typed pre-execution guards and honest
  rollback retention.
- **The Web Desk expression (94-08):** delivery objects inhabit the existing
  Desk through a no-authority read-model store and immutable-target
  terminals; the production walk renders HS-94-08's own Work attempt on the
  Desk.
- **The native contracts (94-09):** Swift v2 Delivery Runtime models with
  tolerant decoding, golden fixtures from the real emitters, provider
  clients, and the remote-disarm node-routing fix.
- **The assembled campaign (94-10):** a two-process localhost campaign
  proving all four north-star journeys, the full fault matrix against the
  contract's honest states, poll economy, a zero-leak audit census, posture
  invariance, and the story registering itself as an exact attempt.

## Honest boundaries

The second physical machine over Tailscale (real transport, clock skew,
latency budgets), the physical iPad native and iPad Safari tailnet-HTTPS
microphone legs, the upstream reusable-processes adoption of the counterpart
contract, and real GitHub PR/CI receipt rows are candidate-Y scope:
scheduled, not claimed. This summary claims the machine-verifiable substance
— every contract behavior provable on one machine with real tmux, a real
second node process, real git worktrees, and the real vendored dw — not the
multi-machine or physical-device verdicts.

## Handoff

The delivery runtime is one spine (registry, collector, node link, command
envelope, receipts) that the Web Desk already inhabits and the Swift
contracts already decode. The candidate-Y program (a second machine, an
iPad, tailnet HTTPS) turns the proven substrate into the full daily
cross-machine experience; the UAT framework (holdspeak-uat) is the natural
conductor for that owner sitting.
