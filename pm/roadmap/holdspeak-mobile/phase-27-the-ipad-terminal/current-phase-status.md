# HSM Phase 27 — The iPad Terminal (parity with Phase 89/90)

**Status:** in progress (1/2). The iPad catches up to the web desk's
first-class agent manipulation.

**Last updated:** 2026-07-08.

## Why

Phases 89 and 90 gave the WEB desk first-class terminal manipulation —
any key, any pane, any machine, plus the session lifecycle (spawn/
rename/kill) — with a full on-glass surface. The iPad was left behind:
its steering client had only the original five verbs (peek/arm/disarm/
steer/audit) and no interactive UI at all. This phase closes that gap.

## Scope

- In: the Swift steering CLIENT parity (keys, panes, nodes, kill, spawn,
  rename, and node routing on arm/steer/keys/peek) — verifiable now; the
  interactive terminal SURFACE on the diorama (peek + hold-to-arm + key
  palette + composer + pane picker + factory controls) — device-felt.
- Out: a full PTY emulator (peek stays the hash-gated poll); cross-machine
  factory (local, like the web); launching an agent into a spawned pane.

## Story status

| ID | Story | Status | Story file |
|---|---|---|---|
| HSM-27-01 | The steering client parity | **done** (2026-07-08, `swift test` 519/0, [evidence](./evidence-story-01.md)) | [story-01-client-parity](./story-01-client-parity.md) |
| HSM-27-02 | The terminal surface on the diorama | backlog (device-gated — the couch) | [story-02-terminal-surface](./story-02-terminal-surface.md) |

## Where we are

HSM-27-01 done: `HTTPDesktopClient+Steering.swift` now speaks the full
Phase-89/90 wire — `coderKeys` (named + literal, node-routable),
`steeringPanes`, `steeringNodes`, `killCoder`, `spawnSession`,
`renameSession`, and a `node` param on arm/steer/keys/peek that routes
through the relay (the web's `verbEndpoint` mirrored). New loose result
types (SteerKey, PaneInfo, CoderKillResult, FactoryResult). Every verb
pinned over a URLProtocol stub (`SteeringClientTests`, 16), including the
refusal-as-data paths and the relay key-in-body. `swift test` 519/0.

HSM-27-02 (the interactive surface) is device-felt consent craft — the
hold-to-arm gesture, the key palette taps, the composer, the spawn/kill
controls — proven on the cabled iPad, not a sim screenshot (the owner's
bar). Staged for the couch, mirroring the web desk's SessionPullout.
