# HSM-15-10 — The Connect surface ("Your Computer" / discovery-first pairing)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** in-progress — opened 2026-06-22 (owner: *"Where do I set up the computer and connect
  to? Have you thought about creating a new place for that? a lot of these have got a lot of
  discovery verbs."*). The foundational connection home the mesh was missing.
- **Depends on:** `HTTPDesktopClient`/`DictatePeerStore` (the paired peer), the desktop `holdspeak web`
  LAN bind + `web_auth` token.
- **Owner:** unassigned

## Problem

The whole mesh hangs off one thing — the iPad being paired to your computer — and there is **no place
to do it**. Today: run `holdspeak web` on the LAN, dig the Mac's IP + auth token out of the CLI, and
hand-type host/port/token into a modal buried in the dictation flow. No discovery, no status, no home.
Grounding (2026-06-22): the desktop advertises **nothing** on the network (no Bonjour/zeroconf); auth
is a manual bearer token (`web_auth.py`) + the device PSK (`holdspeak device-psk`).

## The design — discovery-first, a first-class place

- **Desktop advertises** itself via **Bonjour** (`_holdspeak._tcp`, the server name + port) when it
  binds off-loopback, so the iPad can FIND it by name — no IP typing. (New desktop work; behind the
  LAN-bind mode.)
- **The iPad "Your Computer" surface** (a first-class screen, reachable from the home + wherever a
  feature needs pairing): **browses the LAN** (NWBrowser / Bonjour), lists discovered computers by
  name + reachability, tap-to-connect (host/port come from discovery). The **token** arrives via a
  short **pairing code / QR** the desktop shows (not hand-typed). Live status (reachable / asleep),
  and manage / forget peers. The home of the connection every mesh feature reads.
- **Honest + native:** uses the platform's discovery (Bonjour) and a real pairing exchange rather than
  reinventing — the "native conventions" bar. No prose; tight status chips.

## Acceptance criteria

- [ ] **Desktop Bonjour** — `holdspeak web` advertises `_holdspeak._tcp` (name + port) when bound
      off-loopback; verified discoverable on the LAN. A lightweight unauthenticated `GET /api/mesh/info`
      (name, version, requiresToken) so a discovered server identifies itself.
- [ ] **iPad Connect surface** — a first-class "Your Computer" screen that browses Bonjour, lists
      discovered computers (name + reach), tap-to-connect (discovered host/port), and persists the peer
      via `DictatePeerStore`. Simulator-shot (seeded discovery list).
- [ ] **Pairing** — the token arrives via a pairing code / QR shown by the desktop (a desktop pairing
      affordance + an iPad enter/scan), not hand-typed. (v1 may fall back to a manual token field with
      clear guidance if the code exchange is deferred — but discovery of host/port is the bar.)
- [ ] **Status + manage** — reachable / asleep chip; forget/re-pair. Every mesh feature reads this one
      paired peer.

## Build plan

1. **Desktop:** Bonjour advertising (zeroconf) on LAN bind + `GET /api/mesh/info`. Host-tested where
   possible. (Foundational half — built first, non-colliding.)
2. **iPad:** the "Your Computer" Connect surface — Bonjour browse (`NWBrowser`), discovered list,
   tap-to-connect, status, manage; a home entry. Simulator-proven.
3. **Pairing code / QR** the token exchange (desktop shows a code; iPad enters/scans). Can be a second
   slice if the discovery slice ships first.

## Test plan

- Desktop: unit/integration for the advertising toggle + `/api/mesh/info`; manual LAN discovery check.
- iPad: the discovery→connect flow Simulator-shot with a seeded list; a real LAN discover+pair is the
  owner-at-the-iPad proof.

## Notes

- This is the connection HOME the mesh was missing — the owner flagged it after the dictation surface
  shipped pairing-aware but with no place to actually pair. Discovery (Bonjour) is the headline "verb".
- Reuses `DictatePeerStore` (the persisted peer) so dictation / Agent Desk / Queue HUD all benefit at
  once. See [[story-01-dictation-into-your-mac]], [[story-08-the-agent-desk]].
