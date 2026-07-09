# HSM-27-01 — The steering client parity

- **Status:** done
- **Shipped:** 2026-07-08 — the Swift client speaks the full Phase-89/90 wire; `swift test` 519/0. Evidence: [evidence-story-01.md](./evidence-story-01.md).
- **Depends on:** Phase 89/90 (the hub routes), HSM-26-03 (the client base)

## Problem

The iPad's steering client stopped at Phase 87's five verbs. The web
desk gained keys, panes, nodes, kill, spawn, rename, and cross-machine
routing. The client must reach all of it before any surface can.

## What shipped

`apple/Sources/Providers/Desktop/HTTPDesktopClient+Steering.swift`:

- `coderKeys(key:keys:node:)` — full key control; `SteerKey.named` /
  `.literal` (`.interrupt`, arrows, `.escape` shorthands); a named key is
  a bare string, a literal is `{literal}`; refusal is DATA (a 409
  SteerResult, revoking re-offers ARM).
- `steeringPanes()` → `[PaneInfo]`; `steeringNodes()` → `[String]`.
- `killCoder(key:scope:)` → `CoderKillResult` (killed or a typed refusal;
  local only, like the web).
- `spawnSession(name:command:)` / `renameSession(target:name:)` →
  `FactoryResult` (spawned returns `paneKey`, ready to attach; bad_name
  is DATA).
- A `node` param on `coderPeek`/`armCoder`/`steerCoder`/`coderKeys` that
  routes through the relay (`api/coders/relay/{node}/{verb}`, the key in
  the BODY) — the web's `verbEndpoint` mirrored.

## Acceptance criteria

- [x] Every new verb round-trips over a URLProtocol stub, incl. the
      refusal-as-data paths and the relay key-in-body
      (`SteeringClientTests`, 16).
- [x] `PaneInfo` decodes the `/panes` shape (snake_case via the shared
      decoder, the `CoderArmResult` precedent — no clashing CodingKeys).
- [x] `swift test` green (519/0); the package builds.
