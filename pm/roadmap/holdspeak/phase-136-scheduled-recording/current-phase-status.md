# Phase 136 — Scheduled Recording

**Status:** chartered (0/4).

**Last updated:** 2026-08-17.

## Owner mandate

From the Dashboard Door reflection (2026-08-17): the Chair should let
the owner **schedule a recording** — set a time (one-shot or recurring)
at which HoldSpeak starts capturing a meeting on its own, and stops it
on its own. Chosen as a focused standalone build ("a good use of our
time") ahead of a full Dashboard Door or Narrow Shell charter — those
stay deferred. Zero corporate access needed (this is HoldSpeak's own
capture, not the blocked external calendar).

## The scoping evidence (and the honest contradiction)

A read-only opus-worker scoped this against the live code and stopped
twice with two **contradictory** verdicts (headless auto-start
possible / not possible). They were reconciled by the orchestrator:
both passes agreed on the **mechanics**, disagreeing only on **canon
policy**. The reconciled facts:

- **Capture runs on the HUB, not the browser.** `MeetingRecorder`
  (`holdspeak/meeting_recorder.py:22,300+`) opens the local mic via
  `sounddevice`/PortAudio on the machine running the hub process. The
  browser only sends `POST /api/meeting/start`
  (`web/src/desk/store/recordingSlice.ts:46`). **Therefore the hub can
  start a capture with no browser present** — a scheduled, headless
  start is technically real.
- **The one seam is `_start_meeting()`**
  (`holdspeak/runtime/meeting_glue.py:186-313`) — it already accepts a
  `principal`, claims the audio floor (IV.3), and admits the session
  through the kernel (line 441). A SCHEDULER principal follows the same
  path the Workbench Conductor already uses
  (`holdspeak/workbench_conductor.py:562`).
- **The schedule pattern already exists.** `WorkbenchConductor`
  (`workbench_conductor.py:505-568`) is a 60s tick reading cron
  (`_cron_is_due`, lines 117-157) under bounded delegation
  (`holdspeak/services/schedule_delegation.py:32-77`). And
  `ActivityMeetingCandidateService`
  (`holdspeak/services/activity_meeting_candidate_service.py:11-62`)
  already stores `starts_at`/`title`/`status` with a `start` verb — the
  scheduled-recording row has a home that already exists.

## Settled design (owner-ruled — implement, don't relitigate)

All four decisions are the owner's, ruled 2026-08-17:

1. **Auto-start via a visible countdown, tap-to-cancel.** At the set
   time the hub *arms*: it broadcasts a countdown ("Recording starts in
   10s — tap to cancel") and starts a hub-authoritative timer. If no
   cancel arrives within the window, capture starts on its own. This
   fires without a required tap (auto-start) yet keeps the mic owner
   **visible at the moment of truth** (Article IV.3) — so nothing in
   the Constitution is amended. The countdown is a courtesy to a
   watching browser; the **hub** owns the timer, so a closed browser
   never blocks the fire.
2. **One-shot and recurring from one control.** A schedule carries a
   cron expression; a one-shot is a schedule that disables itself after
   it fires. One picker, both modes.
3. **Auto-stop by duration, default 60 minutes, editable.** Every
   schedule carries a max duration and the hub stops the capture when
   it elapses. No unattended recording runs unbounded.
4. **Honest missed-schedule receipt.** If the fire time arrives and the
   hub is down, or the mic floor is held (voice typing / another
   capture), the schedule does not silently skip — it leaves a
   named missed/refused receipt (Articles VI.1, V.2).

## The state machine (the invariant-carrying core)

A firing scheduler is invariant-carrying; workers implement against
this spec, not around it. A scheduled recording moves:

`idle → (tick sees due) → arming → (countdown elapses uncancelled) →
recording → (duration elapses OR manual stop) → stopped`

with these branches:
- `arming → cancelled` (a cancel arrives in the countdown window) → no
  capture, an armed-cancelled receipt; recurring computes next fire,
  one-shot disables.
- `arming/recording refused` (mic floor held per IV.3) → a named
  refusal receipt; recurring computes next fire, one-shot disables.
- `due but hub was down` (detected on next start / catch-up window) →
  a missed receipt; never a silent skip.

**Invariants (each gets a test):**
- **I1 — single fire.** A due schedule fires exactly once per due
  instant; the 60s tick never double-fires (guard on `last_fired_at` /
  a fired-instant marker).
- **I2 — recurring advances.** After any terminal outcome (recorded,
  cancelled, refused, missed) a recurring schedule computes the next
  fire strictly in the future; a one-shot flips `enabled=false`.
- **I3 — hub-authoritative countdown.** The fire does not depend on a
  browser being connected; a cancel is only honored inside the window.
- **I4 — mic authority (IV.3).** A fire never steals a held mic floor;
  it refuses with a receipt naming the current owner.
- **I5 — bounded delegation.** Enabling a schedule records the owner's
  approval of its exact terms (time, cadence, duration); each fire is
  admitted through the kernel and leaves a receipt; a terms edit
  re-approves.
- **I6 — auto-stop.** A recording started by a schedule stops at
  `duration_minutes`, even with no client attached.

## Canon this phase is measured against

`docs/internal/CONSTITUTION.md` — supreme canon. In scope here:
- **IV.3** one mic authority, owner always visible → the countdown.
- **V.1** acting is armed → the deliberate schedule is the arming
  gesture (the owner's Phase-107 clarification: "the deliberate setting
  is the confirming human act"); the countdown is its visible fire.
- **V.2 / XI.1-4** every attempt leaves a receipt; consequential ops
  are kernel-admitted under an authenticated principal and bounded
  delegation.
- **VI.1** no fallback that hides a failure → the missed/refused
  receipt.
- **III.1** nothing leaves the machine by default → capture stays
  local; no new egress.

## Stories

1. **HS-136-01 — The scheduled-capture spine.** DB rows + the hub
   conductor (arm → countdown → start → auto-stop), the SCHEDULER
   principal through `_start_meeting`, all six invariants with tests.
2. **HS-136-02 — The schedule verb (API + MCP).** CRUD + cancel-armed
   routes and MCP tools (the owner's "drive it independently with MCP"
   value), bounded-delegation receipt on enable.
3. **HS-136-03 — The Chair surface.** In-world schedule-creation
   control (no modal; voice mic on its fields), SCHEDULED entries in
   the Meetings lane with next-fire time, the arming countdown on the
   capture hero; screenshot walk both widths.
4. **HS-136-04 — Docs, walk, close.** ENTRY-point docs (USER_GUIDE,
   SECURITY, ARCHITECTURE), the live metal walk proving a real
   scheduled recording fires, auto-stops, and leaves receipts (incl.
   the refusal and missed paths), a reusable harness in `scripts/`,
   the counsel, and the final summary.

## Out of scope

- The external corporate calendar connector (blocked by Conditional
  Access; ships later as an empty slot per the arc ruling).
- Scheduled dictation (meeting capture only this phase).
- The full Dashboard Door (TODO kanban, deep dashboard) and the Narrow
  Shell — both deferred.

## Where we are

Chartered. HS-136-01 is next.
