# HSM-21-01 — The one egress contract

- **Project:** holdspeak-mobile
- **Phase:** 21
- **Status:** done — see [`evidence-story-01.md`](./evidence-story-01.md). `EgressScope` in
  Contracts (test-locked grammar + honest tint split), `DeskPrimitive.egress` (protocol
  requirement; connector=.cloud, coder session=.mixed), every surface consuming it — the
  hard-coded pull-out capsule, the mesh text, and both shell chips are gone. Sim-proven
  three ways (connector Cloud, local-note control, the shell's amber mixed chip).
- **Depends on:** the 18/19 surfaces (they carry the drift this story kills); the canon
  rule [[feedback_no_privacy_novels]] (one badge: local / local+cloud / cloud+target).
- **Unblocks:** every current and future iPad surface inherits an honest badge; 21-02's
  guard can then hold the line.
- **Owner:** unassigned

## Problem

Three parallel, hand-built egress treatments disagree with reality:

1. `DioPullout` hard-codes `lock.fill / "On device"` for every primitive
   (`DeskDioramaStage.swift:1321-1324`) — connector primitives (Slack/GitHub/Webhook)
   wear "On device" though their whole purpose is cloud egress.
2. `CompanionMesh` hand-builds `"ON-DEVICE · " + label` text (`CompanionMesh.swift:748`).
3. Tonight's shell chips: `egressChip("Local + \(host)")` renders a mixed posture green
   (`CompanionShellApp.swift:970`); `cloudChip` re-implements the badge (`:607`).

`EgressBadge.Scope` has no `.mixed` case, and `DeskPrimitive` carries no egress at all —
the honest hub-run badge exists only as a one-off `@State` (`printedEgress`, `:2895`).

## The design

1. **`EgressScope` in Contracts** (pure, UI-free): `local`, `mixed(target)`,
   `cloud(target)`; carries `label` ("On device" / "Local + \(target)" /
   "Cloud · \(target)"), `symbolName` (lock / house-arrow / arrow-up-forward), and a
   `tint` key (ok / warn / warn) so every app renders the same grammar with its own
   chrome. Unit-tested in ContractsTests.
2. **`DeskPrimitive.egress`** — protocol default `.local`; `ConnectorPrimitive`
   overrides to `.cloud(name)`; hub-run/`RunsOn`-Mac surfaces resolve `.mixed("your
   desktop")`. `DioPullout` renders `EgressBadge(scope: prim.egress)`; `EgressBadge`
   consumes `EgressScope` (chrome unchanged, adds the mixed band).
3. **The mesh + shell converge:** `CompanionMesh`'s hand-built text and both shell chips
   render from `EgressScope` — the dictate-to-desktop chip becomes
   `.mixed(host)` (amber, honest), the slack approve keeps `.cloud("slack")`.

## Scope

- **In:** the Contracts type + tests; `DeskPrimitive.egress` + overrides; DioPullout /
  EgressBadge / CompanionMesh / shell chips consuming it; sim proof (a connector pullout
  wearing Cloud, the dictate chip amber).
- **Out:** web badges (already scope-driven since Phase 62); per-record persisted scopes
  (the chip-that-refuses-to-lie moment is Vision backlog, not this story).

## Test plan

- `swift test` (new `EgressScopeTests` in ContractsTests; existing suites green).
- Sim proofs: a connector primitive's pullout wearing `Cloud · slack`; the shell dictate
  receipt wearing the amber `Local + <host>` chip.
