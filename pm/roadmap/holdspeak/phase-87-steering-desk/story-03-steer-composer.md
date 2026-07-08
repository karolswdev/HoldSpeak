# HS-87-03 — Steer: the voice-first composer, delivered and audited

- **Project:** holdspeak
- **Phase:** 87
- **Status:** done
- **Depends on:** HS-87-02
- **Unblocks:** HS-87-04, HS-87-05
- **Owner:** unassigned

## Problem

An armed session should take a reply the way the desk takes
everything: spoken first, typed if you like, delivered with the
craft that keeps a TUI agent's input intact — and every delivery
remembered. This is the one story that sends keystrokes; everything
it sends passes ONE chokepoint.

## Scope

- In: `coder_steering.deliver(key, text, *, submit)` — the
  chokepoint: `require_grant(key)` → resolve pane → ownership
  re-check → `tmux_transport.send_text_to_pane` → audit row;
  `POST /api/coders/{key}/steer`; the composer in the session
  pull-out (desk composer + `MicButton`, submit and no-submit
  sends); the audit trail (`db` table `steering_audit`: ts, key,
  agent, pane_id, text sha256 + first 120 chars, grounding refs,
  outcome) + `GET /api/coders/steering/audit`; refusal states
  rendered in place (unarmed → the ARM affordance, not an error).
- Out: grounding (04 — but `deliver` accepts the final composed text,
  so 04 changes composition, not delivery); classify (05); any
  parallel send path (the old `/api/coders/select` spoken-answer flow
  must route THROUGH `deliver` or be explicitly documented as the
  legacy voice path — decide in-story, record the decision).

## Acceptance criteria

- [ ] An unarmed `POST /steer` is refused with the typed reason; the
      UI shows the ARM affordance instead of a toast-shaped apology.
- [ ] An armed steer lands in the real pane exactly as composed
      (literal text; multi-line intact; Enter its own keystroke);
      captured live against a real session.
- [ ] The pane-recycled crown case: kill/recreate the pane mid-grant,
      steer → refused, grant revoked, desk shows disarmed — live
      capture.
- [ ] Every delivered steer has an audit row (who/when/session/
      pane_id/hash/refs/outcome); refused steers audit too, with the
      refusal reason.
- [ ] Voice: hold-to-talk fills the composer via the existing
      transcribe route (no new audio path).
- [ ] Full suite green (read from the file); api-surface regen.

## Test plan

- Unit: chokepoint tests (refusals, audit rows, submit modes) with
  injected runner + fake transport; route tests.
- Integration: the live steer + the crown case, captured.
- Manual / device: speak a steer to a real waiting session.

## Implementation direction

- **One chokepoint, enforced by shape:** `deliver` is the only
  caller of `send_text_to_pane` for steering; add a unit test that
  greps the route modules for `send_text_to_pane` imports and pins
  the allowed call sites (the desk-locks style of mechanical rule).
- **Reuse the send craft:** `send_text_to_pane` already does
  literal-mode sends and Enter-as-its-own-keystroke; do NOT
  reimplement; if a settle delay is missing for long pastes, add it
  THERE (one craft, both callers). Re-read upstream absorb items
  8/21 ("TUI send craft") before touching.
- **Audit:** a small repository on the existing `db` container
  pattern (see `db/actuators.py` for the shape); never store full
  steer text — hash + head is the privacy-respecting receipt; the
  grounding refs list mirrors `RunProvenance`'s shape.
- **Composer:** the desk composer already exists for the
  answer-by-voice flow (`companion-desk.js` / the desk store's coder
  answer path) — lift it into the pull-out rather than building a
  second one; `MicButton` gives voice; keep the no-submit toggle
  visible (a `⏎` chip that can be un-lit).
- **Legacy path decision:** `/api/coders/select`'s spoken-answer
  delivery predates arming. Options: (a) route it through `deliver`
  with an implicit grant question — NO; (b) keep it as-is but
  documented as the voice-answer flow that TYPES ONLY WHEN A CODER
  ASKED (its consent story is the agent's own question) — likely
  right; (c) deprecate. Default (b); record in the phase decisions.
