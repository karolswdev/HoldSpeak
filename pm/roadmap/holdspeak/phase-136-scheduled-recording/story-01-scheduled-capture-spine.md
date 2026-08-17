# HS-136-01 — The scheduled-capture spine

- **Project:** holdspeak
- **Phase:** 136
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-136-02, HS-136-03
- **Owner:** unassigned

## Problem

There is no way to make HoldSpeak start a recording on its own. The
capture path (`_start_meeting`, `holdspeak/runtime/meeting_glue.py:186`)
runs on the hub and needs no browser, but nothing fires it on a
schedule. The Workbench Conductor
(`holdspeak/workbench_conductor.py:505-568`) proves the pattern — a 60s
tick reading cron under bounded delegation — but it runs LLM items, not
a capture.

## Scope

### In

Per the state machine and invariants I1–I6 in the phase status doc:

- **Storage.** A scheduled-recording row: an id, a schedule spec (a
  cron expression; a one-shot is a cron plus a self-disable), a
  `title`, `duration_minutes` (default 60), `enabled`, a `revision`,
  `created_at`, `last_fired_at`, `next_fire_at`. Reuse
  `ActivityMeetingCandidateService`
  (`holdspeak/services/activity_meeting_candidate_service.py:11-62`) /
  `holdspeak/db/activity.py` where it fits; add a discriminator so
  owner-scheduled rows are distinct from calendar-detected candidates.
  A schema bump follows the repo's migration guard convention.
- **The conductor.** A hub tick (modeled on `WorkbenchConductor`, 60s,
  reusing `_cron_is_due` / cron parsing) that drives the state machine:
  `idle → arming → recording → stopped`, with `cancelled`, `refused`,
  and `missed` branches. On due: broadcast a countdown event and start
  a **hub-authoritative** timer (I3); on countdown-elapsed-uncancelled,
  call `_start_meeting(principal=SCHEDULER, config=…)`; schedule an
  auto-stop after `duration_minutes` (I6). Wire it into `WebRuntime`
  the way `CadenceMixin` / the conductor are wired
  (`holdspeak/web_runtime.py`).
- **The principal + admission.** Fire under a SCHEDULER principal
  exactly as `workbench_conductor.py:562` does; the existing kernel
  admission in `_start_meeting` (line 441) and a receipt on every fire,
  refusal, and miss (I5, VI.1, V.2).
- **Mic authority (I4/IV.3).** Before firing, respect the voice floor
  (`voice_session`); if held, refuse with a receipt naming the owner —
  never steal it.
- **Delegation (I5).** Enabling a schedule records approval of its
  exact terms (mirror `ScheduleDelegationService`,
  `holdspeak/services/schedule_delegation.py:32-77`); a terms edit
  bumps the revision and re-approves.

### Out

- API routes and MCP tools (HS-136-02).
- Any web surface (HS-136-03).
- The countdown *UI* — this story emits the countdown/started/stopped/
  refused/missed events; rendering them is HS-136-03.

## Acceptance criteria

- [ ] A due schedule fires exactly once; the tick never double-fires
  (I1, test with a clock fixture across multiple ticks).
- [ ] A recurring schedule advances `next_fire_at` strictly forward
  after every terminal outcome; a one-shot flips `enabled=false`
  (I2, tests for recorded / cancelled / refused / missed).
- [ ] The fire does not require a connected browser; a cancel is
  honored only inside the countdown window (I3, test).
- [ ] A fire while the mic floor is held refuses with a receipt and
  does not start capture (I4, test).
- [ ] Enabling a schedule writes a delegation/approval receipt; each
  fire is kernel-admitted with a receipt (I5, test).
- [ ] A scheduled capture stops at `duration_minutes` with no client
  attached (I6, test).
- [ ] A fire time that passed while the hub was down yields a missed
  receipt, not a silent skip (VI.1, test).

## Test plan

- `uv run pytest -q tests/ -k "scheduled_recording or schedule_capture"`
  — the conductor state-machine + invariant matrix (clock-driven, no
  real audio; `_start_meeting` stubbed at the seam).
- Scoped only; the live-metal proof (real mic actually records +
  auto-stops) rides HS-136-04's walk.
