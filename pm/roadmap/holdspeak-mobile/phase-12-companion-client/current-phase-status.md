# Phase 12 — The Companion Client

**Status:** planning (scaffolded 2026-06-20). **Track M — added by owner steer
(2026-06-20), outside the original charter's Tracks A–L.** The iPad stops being a
launch stub and becomes a **first-class companion to the desktop/server you are
already coding against**, without losing one ounce of its own on-device power
(Phases 0–7 stand). Point the iPad at the same server your tmux + hooks session
points at, and it becomes a native window into that runtime: list and start
meetings, see live state, and (Phase 13) answer the coder by voice. Built
**native over the desktop's existing HTTP API** (owner call, 2026-06-20) — the
same endpoints the web portal uses — so the experience is web-app-consistent and
genuinely native, not a WebView shell.

**Last updated:** 2026-06-20 (scaffolded — stories HSM-12-01..04 stubbed from the
owner's companion-client steer. No work started.)

## Why this exists (the gap this closes)

The program was chartered as "the first mobile runtime" — a standalone on-device
app. That work is real and stays. But it left a hole the owner named directly:
there was **no phase for the iPad as a rich client to the desktop coder**. The
only iPad-UI phase (Phase 8) is a PencilKit meeting notebook; the iPad app today
is a Gate-1 launch stub plus a one-off inference demo harness. Nothing let you
point the iPad at your dev machine and drive it. This track closes that — and the
desktop is ready to be driven: it already exposes `/api/meetings`,
`/api/meeting/start|stop`, `/api/runtime/status`, `/api/dictation/*`, and the AI PI
`/api/companion/*` surface. A client mostly consumes what already ships.

## The principle (owner, 2026-06-20): not a dumb terminal

> "It doesn't mean the iPad becomes a dumb terminal device. It can act in that
> capacity, but it should also stand its own ground."

The iPad keeps every on-device capability (capture, Whisper, local inference,
meeting intelligence, MIR). The companion shell **adds** a server-aware face; it
never replaces the local runtime. The unified shell presents both at once — what
runs here and what is happening on the server — so the device is enriched, never
reduced.

## Goal

Build the native SwiftUI Companion Client over a Runtime-Core desktop-client seam:
configure/point the iPad at a desktop or homelab server, browse and start/stop
meetings on that server from the iPad, see live runtime state, and present it all
in a web-app-consistent Signal shell that also surfaces the iPad's own on-device
runtime. The phase passes when the iPad is a first-class companion to a real
desktop on real hardware (the Track M gate), with the on-device runtime provably
still intact. The host stays thin — the client seam lives in the Runtime Core; the
views present it.

## Scope

- **In:** the `IDesktopClient` Runtime-Core seam + pairing/handshake against the
  desktop HTTP API (HSM-12-01); meetings remote control — list / open /
  start / stop / live status over the existing endpoints (HSM-12-02); the unified
  Companion shell (web-app-consistent Signal; on-device runtime + server view in
  one app, the iPad never neutered) (HSM-12-03); the Track M gate device closeout
  (HSM-12-04).
- **Out:** answering the coder / the AI PI loop / remote dictation inject (Phase 13
  — Track N). The PencilKit notebook (Phase 8, untouched). The on-device engines
  themselves (Phases 2–7 — this client presents them, it does not rebuild them).
  Cross-device data sync (Phase 10 — a different mechanism; the client drives the
  live server, sync reconciles stores). A hosted cloud service (this is the user's
  own server over LAN/Tailscale). Hardening (Phase 11).

## Exit criteria (evidence required)

- [ ] An `IDesktopClient` seam exists; the Runtime Core depends on the interface,
      not a concrete transport; the iPad can be pointed at a desktop/homelab server
      (host/port/token over LAN/Tailscale), handshakes against `/health` +
      `/api/runtime/status`, carries an honest egress label, and is offline-tolerant
      (the app never stalls when the server is unreachable) (HSM-12-01).
- [ ] From the iPad you can list the server's meetings, open one, and **start and
      stop a meeting on the desktop**, with live runtime state reflected — all over
      the existing endpoints, driven through the seam (HSM-12-02).
- [ ] The Companion shell is web-app-consistent (Signal language, the portal's
      Meetings / Dictate / Companion navigation) and presents the iPad's **own
      on-device runtime alongside** the server view — the device is not reduced to a
      remote (HSM-12-03).
- [ ] **Track M gate — first-class companion, proven:** on a physical iPad against a
      real desktop, point the iPad at the server, list + start/stop a meeting from
      the iPad, and confirm the on-device runtime still fully works (capture/local
      intelligence not neutered), evidenced by a device walkthrough (HSM-12-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-12-01 | Desktop client seam + pairing | backlog | [story-01](./story-01-desktop-client-seam.md) | — |
| HSM-12-02 | Meetings remote control | backlog | [story-02](./story-02-meetings-remote-control.md) | — |
| HSM-12-03 | The unified Companion shell | backlog | [story-03](./story-03-unified-companion-shell.md) | — |
| HSM-12-04 | Track M gate closeout | backlog | [story-04](./story-04-companion-gate-closeout.md) | — |

## Where we are

Just scaffolded from the owner's 2026-06-20 steer. The foundation (HSM-12-01) is
fully host-testable against a fake desktop and unblocks the rest; meetings remote
control (HSM-12-02) consumes endpoints that already ship; the shell (HSM-12-03) is
where the web-app consistency and the "not a dumb terminal" principle become
visible; the gate (HSM-12-04) needs the unlocked iPad + a reachable desktop. Phase
13 (Answer the Coder) builds the voice-note-into-the-coder payoff on this
foundation. Next: HSM-12-01.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The client stalls the app when the server is unreachable (companion blocks the on-device runtime) | high | The seam is offline-tolerant by construction; on-device features never depend on the server being reachable; the shell shows a clear "server unreachable" state and keeps working locally | An on-device action (capture, local meeting) blocks because the desktop is down — decouple; the companion is additive, never on the local path |
| The iPad is quietly reduced to a remote (the "dumb terminal" failure the owner forbade) | high | HSM-12-03 presents the on-device runtime as a first-class peer of the server view; the gate (HSM-12-04) explicitly re-proves on-device capability | The shell hides or disables on-device meetings/inference when paired — restore them; the device stands its own ground |
| Business logic leaks into SwiftUI views, breaking the charter's layer rule | medium | The client logic lives in the `IDesktopClient` seam + view-models in the Runtime Core; views present only | A view holds HTTP/client state or business logic — pull it into the core |
| The mobile↔desktop API drifts and the client breaks silently | medium | The client speaks the same contracts the web portal does; validate decoded payloads against the Phase-0 schemas where they overlap; pin the endpoints the client depends on | A server response fails to decode/validate — reconcile the contract before shipping |
| Pairing/auth to the desktop is unclear over LAN/Tailscale | medium | Reuse the Phase-10 transport posture (direct to the peer over the user's own network, honest egress); a simple host/port + token handshake, no third-party relay | The client needs a hosted relay or a cloud account to reach the desktop — out of scope; keep it the user's own network |

## Decisions made (this phase)

- 2026-06-20 — **Owner steer:** the iPad must be a first-class companion to the
  desktop server in addition to its standalone on-device runtime — not a dumb
  terminal, not neutered. This adds Track M (this phase) + Track N (Phase 13)
  outside the original charter Tracks A–L; the charter may want an owner-blessed
  amendment to record the new tracks (flagged, not silently rewritten).
- 2026-06-20 — **Owner call:** the client is **native SwiftUI over the desktop's
  existing HTTP API** (the same endpoints the web portal uses), not a WebView
  wrapper — native richness + web-app consistency. New desktop endpoints are added
  only where the existing surface has no equivalent (the remote-dictation inject
  path lands in Phase 13).
- 2026-06-20 — **Owner call:** Phase 8 (the PencilKit notebook) stays the iPad
  flagship as-is; the companion client is this separate, later track, not a
  re-scope of Phase 8.

## Decisions deferred

- Pairing/discovery UX (manual host:port + token vs. Bonjour/Tailscale discovery) —
  trigger: HSM-12-01 — default: manual host:port + token first (simplest, no
  dependency), discovery parked as polish.
- Whether the companion shell and the Phase-8 notebook are one app or two targets —
  trigger: HSM-12-03 — default: one app, the companion as a mode/tab alongside the
  on-device surfaces, so the device is unified, not split.
- How live runtime state reaches the iPad (poll `/api/runtime/status` vs. an
  event/stream transport) — trigger: HSM-12-02 — default: poll first; an
  event/push transport is a later optimization (and is also what Phase 13's
  companion board would benefit from).
