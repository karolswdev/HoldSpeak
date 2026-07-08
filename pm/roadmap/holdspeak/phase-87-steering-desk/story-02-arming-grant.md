# HS-87-02 — The arming grant: consent with a countdown

- **Project:** holdspeak
- **Phase:** 87
- **Status:** done
- **Depends on:** HS-87-01
- **Unblocks:** HS-87-03
- **Owner:** unassigned

## Problem

Watching is free; steering must be earned per session, per window of
time, against a pinned pane identity — and the enforcement must live
where the keystrokes leave (the hub), not in the UI. This story
builds the grant model and its desk surface; it still sends nothing
(the send chokepoint lands with 03, refusing everything until then
is fine and right).

## Scope

- In: hub-side grant store in `coder_steering.py` (in-memory:
  `{key: {pane_id, granted_at, expires_at}}`); `POST
  /api/coders/{key}/arm` and `/disarm`; `require_grant(key)` — THE
  chokepoint helper 03 will call before every send (verifies grant
  exists, not expired, and the registry's CURRENT pane still resolves
  to the pinned `pane_id`; any failure revokes and refuses); the desk
  arming affordance in the pull-out (arm → countdown chip → disarm),
  armed state visible on the session pin everywhere it renders.
- Out: sending (03); persistence of grants (fail-closed restart is a
  decision, not a gap); auto-arm anything.

## Acceptance criteria

- [ ] Arming pins the pane identity: the grant records tmux's
      `#{pane_id}` (the `%N` unique id), not the target string.
- [ ] `require_grant`: no grant → refused; expired → refused +
      removed; pane_id mismatch (recycled/retargeted) → refused +
      REVOKED — each a distinct typed reason, all tested.
- [ ] TTL defaults to 15 minutes; the pull-out shows a live
      countdown; disarm is one tap and immediate; expiry flips the
      desk state without a reload (a `scope:"coder"` frame).
- [ ] A hub restart leaves zero grants (test constructs the store
      fresh and asserts emptiness — fail closed).
- [ ] Arming a stale-registry session is refused with the staleness
      named.
- [ ] Full suite green (read from the file); api-surface regen.

## Test plan

- Unit: grant lifecycle property tests (grant/expire/revoke/
  mismatch), route tests for arm/disarm/refusals.
- Integration: arm a real tmux session; kill the pane; assert
  `require_grant` refuses and revokes.
- Manual / device: the countdown chip on the live desk.

## Implementation direction

- **Pane identity:** at arm time run `tmux display-message -p -t
  <target> "#{pane_id}"` (via the same injectable runner) and store
  it. At check time re-run it for the registry's CURRENT target and
  compare. This is the upstream recycled-pane lesson made structural
  ("Prove pane ownership before typing: recycled pane ids refused" —
  their commit d19d8a2/4780b7b lineage).
- **Store:** module-level dict guarded by a `threading.Lock` (route
  calls arrive via to_thread); expose `arm/disarm/require_grant/
  active_grants` as functions, not a class singleton with state
  spread around — one file owns consent.
- **Clock:** `time.monotonic()` for expiry (wall-clock jumps must
  not extend a grant).
- **Frames:** arm/disarm/expiry broadcast the `scope:"coder"` frame
  so every surface (pin, pull-out, HUD) reflects armed state without
  private polling; expiry needs a lazy sweep (check on read + a
  sweep inside `require_grant`) — no background timer thread.
- **UI:** the arm affordance is deliberate but not ceremonial — a
  press-and-hold (~600 ms) on an `ARM` chip (the desk has no modals;
  hold-to-confirm is the desk-grammar consent gesture, same family
  as the record orb). Armed = the chip becomes the countdown
  (`mm:ss`), one tap = disarm. `desk-mc-pin.armed` styling on pins.
- **SECURITY.md:** add the consent-model paragraph in this story
  (arming semantics), since 02 is where the model becomes real.
