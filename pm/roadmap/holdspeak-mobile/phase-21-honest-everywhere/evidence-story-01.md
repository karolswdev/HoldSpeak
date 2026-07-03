# Evidence — HSM-21-01 — The one egress contract

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-21-01-egress-contract`.

## 1. The contract (`apple/Sources/Contracts/EgressScope.swift`)

`EgressScope` — `local / mixed(target) / cloud(target)` — pure data: `label`
("On device" / "Local + \(target)" / "Cloud · \(target)"), `symbolName`, `tintKey` +
`leavesDevice` (the honest split: anything that leaves the device never wears the local
treatment). Locked by `EgressScopeTests` (labels, symbols, the tint split).

## 2. The primitives carry their posture

- `DeskPrimitive.egress` is a **protocol requirement** with a `.local` default (the same
  dynamic-dispatch rule as `glyph`: extension-only would statically render every
  connector "On device" — the exact bug).
- `ConnectorPrimitive.egress = .cloud(name)` — a connector's whole purpose is egress.
- `AgentSessionPrimitive.egress = .mixed("your desktop")` — a live Mac coding session.
- Everything else inherits `.local` honestly.

## 3. Every surface consumes the one grammar

- `EgressBadge` (desk) now renders `EgressScope` (chrome unchanged; gains the mixed band);
  the four scope-typed call sites (`printedEgress`, act rows, run pickers) migrated.
- **`DioPullout`'s hard-coded "On device" capsule is dead** — the header renders
  `EgressBadge(scope: prim.egress)`.
- The recorder's dictate line ("to your desktop") and `CompanionMesh`'s hand-built
  "ON-DEVICE · local mesh → X" both render from the scope now — mixed postures, amber.
- The Companion shell's two hand-built chips became one `egressChip(_ scope:)`: the
  dictate receipt is `.mixed(host)` (WAS "Local + host" dressed green — tonight's own
  drift, fixed), the slack approve stays `.cloud("slack")`.

## 4. Sim proofs (iPad Air 13-inch M4)

- [`hsm-21-01-connector-cloud-badge.png`](./screenshots/hsm-21-01-connector-cloud-badge.png)
  — the Slack connector's pull-out wearing **Cloud · slack** (amber), via the new
  `HS_DESK_OPEN=connector` seed.
- [`hsm-21-01-local-note-control.png`](./screenshots/hsm-21-01-local-note-control.png)
  — the CONTROL: a local note's pull-out still wears **On device** (green); the default
  posture did not over-rotate.
- [`hsm-21-01-shell-mixed-amber.png`](./screenshots/hsm-21-01-shell-mixed-amber.png)
  — the shell dictate receipt wearing **Local + 192.168.1.13** in the amber
  leaves-device treatment.

## Honest boundaries

- The mesh badge and recorder line are build-verified consumers of the same scope (their
  surfaces need a live mesh/recording to screenshot); the rider (21-05) carries the
  on-glass look.
- Per-record persisted scopes (the Vision's "chip that refuses to lie" moment) stay
  deliberately out — this story is the contract, not the record store.

## Suites

`swift test` **428 passed / 8 skipped / 0 failures** (incl. the new `EgressScopeTests`) ·
companion-shell sim build **BUILD SUCCEEDED** · meeting-capture sim build
**BUILD SUCCEEDED** — all after the change.
