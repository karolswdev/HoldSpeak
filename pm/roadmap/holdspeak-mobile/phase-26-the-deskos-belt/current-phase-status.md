# Phase 26 — The DeskOS Belt (B4: the belt, steering, and rails travel)

**Status:** in progress (2/5). Contracts foundation first, per the
owner's B4 scoping (2026-07-08); the belt now renders on glass.

**Last updated:** 2026-07-08 (HSM-26-02 done, sim-proven — the delivery
belt renders on the iPad diorama from the `BeltState` contract).

## Goal

B4 of the Delivery Belt RFC: the belt, the steering surfaces (attach,
arm, steer, ground), and the rails (grounding kinds + the ambient
journal) become native surfaces on the DeskOS diorama — rendered from
documented CONTRACTS, not scraped from a web page. Desktop Phases 87
(the Steering Desk) and 88 (the Rails-Aware Desk) shipped the wire
shapes deliberately so the Apple surfaces inherit, never redesign;
this phase writes those shapes down as contracts and renders them on
glass. Owner (2026-07-07, Phase-87 charter): *"they basically act so
natively awesomely, both on the web, but as well as on the iPad and
iPhone, that oh my gosh, don't we just want to keep manipulating it."*

## Scope

- In: the presence-class steering + rails CONTRACTS (schemas +
  conformance fixtures + entity-catalog entries + validator wiring),
  matching the real Phase-87/88 hub routes byte-for-byte (HSM-26-01,
  this session); then the diorama surfaces on those contracts — the
  belt/conveyor, the session pull-out + arm + steer + ground, the
  rails grounding picker + the journal (HSM-26-02/03/04, sim-built);
  the couch walk + docs (HSM-26-05, on a real device).
- Out: any NEW hub capability (the routes exist; this phase RENDERS
  them); autonomous steering (a human is behind every keystroke — the
  Phase-87 consent spine, ported); B3 (the factory) per the RFC.

## Exit criteria (evidence required)

- [ ] The steering + rails presence contracts are documented as
      schemas with conformance fixtures that validate against the REAL
      hub responses (the peek, the grant, the steer, the audit, the
      classify verbs, the rails ref, the journal, the remote-events
      envelope); `validate.py` green incl. a negative check (HSM-26-01).
- [ ] The belt renders on the diorama from `GET /api/missioncontrol/*`
      (HSM-26-02, sim-proven).
- [ ] The session pull-out attaches, arms (hold-to-arm countdown),
      steers (voice-first), and grounds — under the ported consent
      spine (HSM-26-03, sim-proven).
- [ ] Rails objects ground into a steer on glass, and the ambient
      journal renders as an openable primitive (HSM-26-04, sim-proven).
- [ ] The couch walk: the owner steers a real session and journals a
      real flip from the iPad; docs shipped (HSM-26-05, on device).

## Story status

| ID | Story | Status | Story file |
|---|---|---|---|
| HSM-26-01 | The steering + rails presence contracts | **done** (2026-07-08 — 9 schemas + fixtures; validate.py ALL CHECKS PASSED; the real hub responses validate via `test_steering_contracts_fidelity.py`, 8/8; suite 3461) | [story-01](./story-01-steering-rails-contracts.md) |
| HSM-26-02 | The belt on the diorama | **done** (2026-07-08, sim-proven — the belt renders on the iPad diorama from the `BeltState` contract; `swift test` 503/0 + sim BUILD SUCCEEDED + [screenshot](./screenshots/belt-pullout.png); craft polish deferred to the couch walk) | [story-02](./story-02-belt-on-the-diorama.md) |
| HSM-26-03 | Attach, arm, steer, ground on glass | backlog | [story-03](./story-03-steer-on-glass.md) |
| HSM-26-04 | Rails grounding + the journal on glass | backlog | [story-04](./story-04-rails-on-glass.md) |
| HSM-26-05 | The couch walk + docs | backlog | [story-05](./story-05-couch-walk.md) |

## Where we are

The contracts foundation is real (HSM-26-01): the presence-class
steering + rails shapes are written down as 9 JSON-Schema contracts
(`contracts/schemas/`) with conformance fixtures
(`fixtures/steering-and-rails-sample.json`), wired into the mobile
`validate.py` (positive + negative: a steer without text and a
remote-events envelope carrying a file body are both rejected) and
into the desktop suite via `tests/unit/test_steering_contracts_
fidelity.py`, which builds the REAL Phase-87/88 responses (arm,
deliver, the audit entry, the peek envelope, the journal entry, the
remote envelope) and validates them against the schemas — so a route
that drifts from its contract fails in CI, not on glass. The
entity-catalog and serialization-contract carry the presence section.
Both runners green; suite 3461.

HSM-26-02 in flight — the Swift DECODE layer is done (`swift test`
503/0): `apple/Sources/Contracts/MissionControl.swift` carries the
belt-state models AND the presence shapes (peek, grant, steer result,
audit, rails ref, journal entry), mirroring the HSM-26-01 schemas 1:1;
`HTTPDesktopClient+MissionControl.swift` reads `/api/missioncontrol/
state` and `/rails/journal`; `MissionControlTests.swift` decodes the
SAME fixtures the Python validator checks (one source, three runners).
Fixing the Swift models surfaced a real contract bug HSM-26-01 missed:
the audit `ts` was SQLite-naive, not the contract's UTC-Z — the source
(`db/steering.py`) now emits ISO-Z and the fidelity test builds a REAL
db row to catch it.

The belt renders on glass (HSM-26-02, sim-proven):
`apple/App/MeetingCapture/DeskBelt.swift` is `BeltPrimitive`, a
`DeskPrimitive` conformer whose whole UI derives from one declaration;
`DioStage` polls `GET /api/missioncontrol/state` (15 s, read-only) into
`beltState`, appends the belt to `toolMembers` when the desktop names
rails, and an `HS_DESK_BELT` seed drives it offline. The screenshot
shows both live rails with their current phase + stories (status marks,
evidence + next tags), the ⚠ warnings lane, the honest `✕ unavailable`
lane, and the "Local + your desktop" badge — the web conveyor's
information in the diorama's grammar, from the contract. `swift test`
503/0; sim BUILD SUCCEEDED. Two craft refinements (the header truncates;
stories inherit a route-arrow) are deferred to the couch walk
(HSM-26-05), the craft/acceptance exit. Next: HSM-26-03, steer on glass.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The contracts drift from the real hub responses (a schema that no live route emits) | the reason to fixture from real responses | fixtures are captured from the ACTUAL Phase-87/88 routes; validate.py checks them; a desktop api-surface change re-runs the fixtures | a fixture no route produces |
| The iPad redesigns instead of inheriting | the risk B4 exists to avoid | render STRICTLY from the documented shapes; the Swift decoder mirrors the contract coder; no view model invents a field | a Swift shape with no contract row |
| Seeded sim demos passed off as proof | high (owner's standing bar) | the couch walk on a REAL device is the exit; sim work is labeled sim | a "done" walk that never touched a device |

## Decisions made (this phase)

- 2026-07-08 — Contracts foundation first (owner scoping): the
  presence-class steering/rails shapes are written down and validated
  against the real hub responses BEFORE any Swift renders them —
  "inherits, never redesigns" needs the contracts to exist.

## Decisions deferred

- Whether the coder/steering presence stream syncs as a tail event
  stream (the framework's `presence` class) or is polled per-surface —
  trigger: the pull-out's live view on glass — default: poll the
  documented routes, mirror the web desk's poll-only-while-open.
- The journal's sync class (a synced note vs a device-local cache) —
  trigger: the owner wants the journal on two devices — default: read
  it from the hub route, render as a note.
