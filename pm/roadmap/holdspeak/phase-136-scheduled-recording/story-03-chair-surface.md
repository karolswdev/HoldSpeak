# HS-136-03 — The Chair surface

- **Project:** holdspeak
- **Phase:** 136
- **Status:** done
- **Depends on:** HS-136-02
- **Unblocks:** HS-136-04
- **Owner:** unassigned

## Problem

Scheduling has no home on the Chair. The owner must be able to create a
schedule in-world, see upcoming scheduled recordings, and — when one
fires — see the countdown and be able to cancel it. Per the house laws:
no modals (edit in world), a voice mic on every input, honest labels.

## Scope

### In

- **Create control.** An in-world schedule-creation control reached
  from the capture hero (`web/src/desk/chair/hero/CaptureHero.tsx`) or
  the Meetings lane — a title, a date/time or recurrence, and a
  duration (default 60), posting through HS-136-02. No modal (Article /
  house law): it opens in an existing pullout or a real DeskWindow. A
  speak-to-fill mic on the title field (house law).
- **The list.** Scheduled recordings surface in the existing Meetings
  lane (`web/src/desk/chair/lanes/MeetingsLane.tsx:79-121`) as entries
  with a `SCHEDULED` badge (beside the existing `REC`/`SAVED` badges,
  ~line 106) and their next-fire time; sorted after live, before
  archived. No new lane — the four-lane order is counsel-ruled
  (`web/src/desk/chair/laneContract.ts:26-31`).
- **The arming countdown.** When the spine broadcasts a countdown
  event, the capture hero shows "Recording starts in Ns — tap to
  cancel" with a live counter and a cancel that calls HS-136-02's
  cancel-armed. Handle the started / stopped / refused / missed events
  too, so the hero and Meetings lane stay honest (a refusal or miss
  shows as such, never as a phantom success). Wire through the
  recording store (`web/src/desk/store/recordingSlice.ts`).
- **Honest labels** (Article VI): the create control names that the
  recording will start on its own; the countdown names the cancel.

### Out

- Backend behavior (HS-136-01/02).
- Sound design for the countdown (reuse the existing sfx palette if a
  tick already fits; no new sounds this phase).

## Acceptance criteria

- [ ] A schedule can be created in-world with no modal; the title field
  has a working speak-to-fill mic (test + shot).
- [ ] Scheduled recordings render in the Meetings lane with a SCHEDULED
  badge and a next-fire time (test + shot).
- [ ] A broadcast countdown renders on the hero with a live counter and
  a working cancel; started/stopped/refused/missed each render
  honestly (tests).
- [ ] Screenshot walk at 1440 and 393 against the live hub: create
  control, the lane entry, and the countdown state, no console errors,
  no overflow (per the screenshot-walk rule).

## Test plan

- `cd web && npx vitest run` — the schedule form, the Meetings-lane
  entry, and the countdown/hero suites.
- Live Playwright shots (1440 + 393) folded into the evidence.
