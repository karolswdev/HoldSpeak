# HS-87-01 — Attach: the session pull-out with the live pane view

- **Project:** holdspeak
- **Phase:** 87
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-87-02
- **Owner:** unassigned

## Problem

The desk knows a session exists (registry pin, awaiting flag, last
assistant text) but cannot show WHAT the session is doing. The phone
can (`/live`, `/peek` upstream). Attach means: click a session
anywhere it appears (conveyor pin, coder board) and read the real
pane, live, in place. Read-only — this story issues no grants and
sends no keystrokes.

## Scope

- In: `holdspeak/coder_steering.py` (new) — `peek_pane(pane, *,
  lines, last_hash, runner)`; `GET /api/coders/{key}/peek` on the
  coders router; the SessionPullout desk component (a `Pullout.tsx`
  sibling) with a monospace live view, staleness chip, and honest
  absence states; a 1–2 s poll ONLY while the pull-out is open;
  `scope:"coder"` frames on awaiting-response transitions.
- Out: arming, composing, sending (02/03); classify verbs (05); any
  registry write.

## Acceptance criteria

- [ ] Opening a live session's pull-out shows the pane's real last N
      lines; new agent output appears within ~2 s without reload.
- [ ] `peek` with an up-to-date `last_hash` answers `not_modified`
      (no body); tests pin the hash gate.
- [ ] Dead pane / missing tmux / stale registry entry render as
      typed states in the pull-out (`pane gone`, `tmux absent`,
      `stale`), never an empty black box or a 500.
- [ ] Closing the pull-out stops the poll (asserted: no `/peek` hits
      after close in a route-hit recorder test).
- [ ] Full suite green (read from the output file), desk tests
      green, api-surface regenerated.

## Test plan

- Unit: `tests/unit/test_coder_steering.py` (fake runner: capture
  output, hash gate, ANSI stripping, caps) +
  `tests/unit/test_web_routes_coders_peek.py`.
- Integration: a live peek against a real tmux session captured in
  evidence.
- Manual / device: open the pull-out on THIS session while it works.

## Implementation direction

- **Capture:** `tmux capture-pane -p -e -t <pane> -S -200`; resolve
  the pane target from the registry record (`tmux_session`/`window`/
  `pane` fields — see `fromWireMcSession` for the shapes). Strip
  ANSI/OSC with one compiled regex (`\x1b\[[0-9;?]*[a-zA-Z]` plus
  OSC `\x1b\].*?\x07`); cap 64 KB. Return
  `{status:"live", hash, lines:[…]}`.
- **Hash gate:** sha256 of the stripped text; equality with
  `last_hash` → `{status:"not_modified"}`. This is what makes a 1 s
  poll cheap enough to be boring.
- **Module shape:** mirror `missioncontrol_bridge.py` exactly —
  injectable `runner`, typed statuses, `shutil.which("tmux")` guard,
  timeouts. Route wraps in `asyncio.to_thread` (the Phase-85 rule).
- **Frames:** the registry watcher (`agent_context/`) already
  detects awaiting transitions for the HUD; broadcast
  `{state:"ready", scope:"coder", capability:{kind:"coder",
  id:<key>, name:<agent>}}` there — do NOT invent a second watcher.
- **UI:** state slice `web/src/desk/steering.ts` (zustand, wire→view
  normalizers, POLL only-while-open via a `refCount`); component
  `SessionPullout.tsx` reusing the `Pullout` frame; body is a `<pre>`
  in `--font-mono` 11px (the evidence-panel styling from Phase 86 is
  the visual kin). Entry points: the conveyor `SessionPin` and the
  coder board both call one `openSession(key)`.
- **Honesty:** the staleness chip derives from the registry's
  `updated_at` vs now (the 30-minute upstream TTL); stale sessions
  render dimmed with the chip, exactly like the conveyor pins do.
