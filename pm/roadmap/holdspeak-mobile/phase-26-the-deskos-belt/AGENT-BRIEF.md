# AGENT-BRIEF — Phase 26: The DeskOS Belt (B4)

Read this, then the desktop final summaries
(`../../holdspeak/phase-87-steering-desk/final-summary.md`,
`../../holdspeak/phase-88-rails-aware-desk/final-summary.md`), then
`../contracts/THE_PRIMITIVE_FRAMEWORK.md` (the spine every surface
converges on). This phase RENDERS what those desktop phases built; it
adds no hub capability.

## The owner's scoping (2026-07-08)

B4, contracts foundation first. The belt, the steering surfaces, and
the rails travel to the diorama — but "inherits, never redesigns"
requires the wire shapes written down as contracts, which Phases 87/88
shipped but did not document. So HSM-26-01 writes the presence-class
steering/rails contracts (validated against the REAL hub responses)
before any Swift renders them.

## What the hub already emits (the real routes to contract)

All under the desktop hub, shipped and gated (Phases 87/88):

| Shape | Route | Source |
|---|---|---|
| Coder-session peek | `GET /api/coders/{key}/peek` | `coder_steering_routes.py` |
| Arming grant | `POST /api/coders/{key}/arm`, `GET .../steering/grants` | `coder_steering.py` |
| Steer (request + result) | `POST /api/coders/{key}/steer` | `coder_steering_routes.py` |
| Steering audit row | `GET /api/coders/steering/audit` | `db/steering.py` |
| Keep-as-note | `POST /api/coders/{key}/keep-note` | (a note primitive) |
| Rails grounding ref | `grounding.rails: [{repo,project,kind,id}]` | `grounding_rails.py` |
| Rails size | `POST /api/missioncontrol/rails/size` | `missioncontrol.py` |
| Rails journal entry | `GET /api/missioncontrol/rails/journal` | `rails_observer.py` |
| Remote-events envelope | `POST /api/missioncontrol/rails/remote-events` | `rails_observer.py` |

## The contract rules (pinned)

- **Fixtures come from the REAL responses.** Do not hand-author a
  shape the hub does not emit; capture it from the actual route (a
  live call or the route's own test) and pin it as a fixture that
  `validate.py` checks against the schema.
- **snake_case on the wire**, camelCase native — the framework's
  serialization rule; instants are UTC `Z` (validate.py enforces).
- **Presence class.** These are ephemeral live shapes, not durable
  `ChangeSet` primitives — the framework's `presence` sync class. The
  contracts document the WIRE the surface polls/reads, not a synced
  table.
- **The consent spine is part of the contract.** The grant, the
  ownership check, the audit — the steer contract carries them so the
  iPad enforces the same consent the desk does (watch free, steer
  armed, everything audited).

## For the Swift stories (HSM-26-02+)

- Mirror `apple/Sources/Contracts/Coding.swift` (the Phase-0 contract
  coder) for every new decode.
- Sim-build + screenshot is the working proof; the couch walk on a
  REAL device is the exit (seeded sim demos are not proof — the
  owner's standing bar).
- The diorama surface is `DioStage`; the belt/steering/rails are
  pull-outs and cards on it, not new screens.
