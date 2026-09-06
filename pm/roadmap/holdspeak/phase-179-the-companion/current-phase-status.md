# Phase 179 - The Companion

**Last updated:** 2026-09-05.

> **PARKED behind Phase 200 The Working Practice (2026-09-06, the owner's line in the sand, PR #563). Not deleted; re-chartered on his word when Phase 200's gates say the desk is used daily.**

## Goal

The phone and the iPad as the desk's reach. The standing rule -- "web
DeskOS is the spec; Swift recreates from the finished web spec" -- now
fires: the web spec is finished through 178, and 179 is the Swift
recreation. The companion is LAN-only, no relay (Article III); it reads
the desk through the hub's authenticated API (web_auth.py), discovers
the desktop through the mesh (mesh.py), and receives notifications
through 174's LAN push channel. The companion shows the portfolio
(178), the needs-you count, the Room drill-down, and the brief. It
does not create, edit, or act -- it reads and notifies. The companion
is the iPad app (the dormant HSM track, woken by this phase) and the
phone (a second build target from the same Swift source).

## Status

**PLANNED 0/11.**

**Depends on:** Phase 174 merged (the LAN notification channel and the
remote transport this phase's companion connects through) + the web
spec finished through Phase 178 (the Swift recreation recreates what
is finished).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 07:40. His phone buzzes: "HoldSpeak -- 3 need you across 2
projects." He opens the app: the portfolio with the three Rooms, the
red one first. He taps it: the Room's needs-you rows, the first WHY.
He puts the phone down and knows what to address first. He never
opened the MacBook to learn it.

Census facts from the codebase and memory that this phase pays: the
HSM track is DORMANT (memory: project_hsm_ledger.md); the iPad app
exists under `apple/App/` (DOC_AUDIT_2026-08.md:55) with
`DeskPrimitive.swift`, `DeskHome.swift`, `DeskPhysicsCanvas.swift`,
`Sync.swift` (SYSTEM_PRIMITIVE_COMPONENT_INVENTORY.md:1245-1251); the
Bonjour mesh (mesh.py:1-45) advertises `_holdspeak._tcp` for the
iPad's NWBrowser; the hub serves authenticated HTTP off loopback for
companions (web_auth.py:73-89); 174's LAN companion notifications
story (phase-174-reach/story-09) is CONDITIONAL on this track waking
-- this phase wakes it; the standing rule (memory:
feedback_web_desk_is_the_spec.md) says "hold iPad/HSM; Swift recreates
from the finished web spec."

## Scope

- In:
  - The Swift recreation of the portfolio surface (178) as a read-only
    iOS/iPadOS app. The app shows:
    - The portfolio (Room rows with needs-you count, release-readiness
      indicator, urgency sort).
    - The Room drill-down (needs-you rows, health tokens, the first
      WHY).
    - The Monday brief's portfolio section.
    - The needs-you aggregate count.
  - Discovery: the app browses for `_holdspeak._tcp` via NWBrowser
    (the existing iPad mesh pattern); finds the desktop; authenticates
    with the hub token (web_auth.py).
  - Notifications: the app advertises `_holdspeak-notify._tcp`
    (174's reverse Bonjour pattern); the desktop pushes the needs-you
    count when the edge crosses; iOS handles the local notification.
  - The design on the library before build (canvas at 1440 + 393: the
    iPad frame recreating the web spec's portfolio and Room).
  - His walk on his real phone/iPad on his LAN.
- Out:
  - Write operations from the companion (the companion reads and
    notifies; it does not create, edit, or act).
  - Push notifications via APNs or any hosted relay (LAN only;
    Article III).
  - Android (the standing rule names Swift).
  - The web UI on mobile (the companion is a native app, not a
    responsive web view).
  - New features beyond what the web spec ships through 178 (the
    companion recreates, it does not invent).

## Exit criteria (evidence required)

- [ ] The companion app discovers the desktop via `_holdspeak._tcp`
      and authenticates with the hub token.
- [ ] The portfolio surface renders on the companion with Room rows,
      needs-you count, release-readiness indicator, urgency sort.
- [ ] The Room drill-down shows needs-you rows, health tokens, the
      first WHY.
- [ ] The Monday brief's portfolio section renders on the companion.
- [ ] Notifications arrive on the companion when the needs-you count
      crosses the edge; LAN only; no APNs (Article III).
- [ ] The design on the canvas at 1440 + 393 (the iPad frame) is
      ratified by the owner before the build (Article IX.2).
- [ ] His walk on his real phone/iPad on his LAN; his word
      (Article IX.4).
- [ ] Zero hosted relay; zero egress beyond the LAN (Article III).
- [ ] The companion is read-only (no writes, no acts; Article V).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-179-01 | The design (the companion's faces on the canvas: the iPad frame from the finished web spec) | backlog | [story-01-the-design](./story-01-the-design.md) | -- |
| HS-179-02 | Discovery and authentication (NWBrowser + hub token) | backlog | [story-02-discovery-and-auth](./story-02-discovery-and-auth.md) | -- |
| HS-179-03 | The portfolio on the companion (the Swift recreation of the Projects surface) | backlog | [story-03-the-portfolio](./story-03-the-portfolio.md) | -- |
| HS-179-04 | The Room drill-down (needs-you rows, health tokens, the first WHY) | backlog | [story-04-the-room-drilldown](./story-04-the-room-drilldown.md) | -- |
| HS-179-05 | The brief on the companion (the Monday brief portfolio section) | backlog | [story-05-the-brief](./story-05-the-brief.md) | -- |
| HS-179-06 | LAN notifications (reverse Bonjour push, iOS local notification) | backlog | [story-06-lan-notifications](./story-06-lan-notifications.md) | -- |
| HS-179-07 | The walk (his phone/iPad on his LAN: discovery, the portfolio, a notification) | backlog | [story-07-the-walk](./story-07-the-walk.md) | -- |
| HS-179-08 | The HSM track wake-up (update the dormant Swift sources to the current API contract) | backlog | [story-08-the-hsm-track-wakeup](./story-08-the-hsm-track-wakeup.md) | -- |
| HS-179-09 | The docs (the companion in the architecture; the guide's companion section; SECURITY updated for LAN auth) | backlog | [story-09-the-docs](./story-09-the-docs.md) | -- |
| HS-179-10 | The hygiene lane (items from the dormant HSM track and 174's conditional story) | backlog | [story-10-the-hygiene-lane](./story-10-the-hygiene-lane.md) | -- |
| HS-179-11 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-11-the-close](./story-11-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 174 (the LAN notification channel and the
remote transport) and the web spec finished through Phase 178. The
recon is complete:

**The dormant HSM track:** the iPad app exists under `apple/App/` with
`DeskPrimitive.swift` (15 primitive kinds), `DeskHome.swift`,
`DeskPhysicsCanvas.swift`, and `Sync.swift` (11 sync kinds). These
sources are from before Phase 95 (the Desk OS pivot); they speak the
pre-Constitution API and render the 2.5D diorama world (Phase 71), not
the current Room/Door/Portfolio surface. The recreation is substantial:
the Swift sources need a near-complete rewrite to the current API
contract and the current face canon.

**The Bonjour mesh (mesh.py:1-45):** advertises `_holdspeak._tcp` on
off-loopback binds. The `ServiceInfo` TXT record carries `name`,
`version`, `requiresToken`. The iPad's NWBrowser browses for this
service type. The mesh is discovery only; no notification push exists
(174 story-09 adds that, conditional on this track waking).

**Hub auth (web_auth.py:73-89):** `nonloopback_bind_blocked()` refuses
a non-loopback bind without a configured token. `verify_web_token()`
does constant-time comparison. The companion authenticates with the hub
token in the request header (`X-HoldSpeak-Token`) or query parameter.

**The API the companion reads:** `GET /api/desk/needs-you`
(projects.py:380) for the aggregate; `GET /api/desk/portfolio`
(178 adds this) for the portfolio; `GET /api/projects/{id}/room`
(projects.py:46) for the Room drill-down. All read-only, all behind
auth.

**174 story-09 (LAN companion notifications):** CONDITIONAL on this
track waking. Defines the reverse Bonjour pattern: the companion
advertises `_holdspeak-notify._tcp`, the desktop discovers it, pushes
the needs-you count via HTTP POST. This phase wakes the track,
satisfying 174's condition.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Swift source rewrite scope | High | The recreation is read-only (no writes, no acts); the portfolio and Room drill-down are flat list views, not the 2.5D diorama; the existing DeskPrimitive kinds and Sync contracts inform the new contract; the design story scopes the face first | The rewrite estimate exceeds 2 weeks of build time |
| LAN-only limitation | Medium | The standing rule is clear: LAN only, no relay, no APNs (Article III); the companion is useful on the home/office LAN; the tailnet extends the LAN to the .43 box but the phone is not on the tailnet | The owner says the LAN constraint makes the companion useless |
| iOS notification without APNs | Low | The companion uses iOS local notifications triggered by the LAN push; the phone must be on the LAN to receive them; quiet hours and per-project mute apply | The local notification does not fire when the app is backgrounded (iOS restriction) |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- Whether the companion is iPad-only or universal (iPhone + iPad) --
  decided at design time from the face and the owner's devices.
- Whether the companion shows the full brief or only the portfolio
  section -- decided at design time from the face's information
  density.
- The companion's offline state (no LAN connectivity): does it show a
  cached last-known state or an honest disconnect screen? -- decided
  at design time (Article VI favors the honest disconnect).
