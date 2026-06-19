# HSM-10-04 — Continuity closeout (Gate 6)

- **Project:** holdspeak-mobile
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HSM-10-01, HSM-10-02, HSM-10-03
- **Owner:** unassigned

## Problem

The charter's Track K gate (program Gate 6) is cross-device continuity. This is
the proof on real hardware: capture on one device, see it on another, edit it, and
have the edit round-trip — the thing that makes mobile and desktop one ecosystem
rather than two apps.

## Scope

- **In:** a real-device continuity demonstration — capture a meeting on the phone,
  sync it to the desktop/homelab over Tailscale, confirm it appears intact;
  edit/approve on one side and confirm the change round-trips to the other; the
  recorded walkthrough as evidence.
- **Out:** building any of the sync machinery (HSM-10-01..03). Hardening the sync
  under stress (Phase 11 may add an offline/airplane sync scenario). UI work
  beyond what surfaces sync (Phases 8–9).

## Acceptance criteria

- [ ] A meeting captured on a real iPhone/iPad appears intact on the desktop (or
      another device) after sync, schema-valid on arrival.
- [ ] An edit/approval made on one device round-trips to the other.
- [ ] **Track K gate / Gate 6 — cross-device continuity** is demonstrated on real
      devices over a real Tailscale network, evidenced by a walkthrough.
- [ ] No data is lost in the round-trip (the HSM-10-03 conflict policy holds on
      real devices, not just in unit tests).

## Test plan

- Manual / device: the capture→sync→appear→edit→round-trip walkthrough across two
  real devices over Tailscale, captured as gate evidence.
- Unit: the idempotency/conflict suite (HSM-10-03) runs in CI as the fast guard.

## Notes / open questions

- This closes Phase 10; on pass write `evidence-story-04.md` + `final-summary.md`.
- If the desktop receiver isn't ready, this gate is blocked on the `holdspeak`
  roadmap side — record the dependency rather than faking the round-trip.
