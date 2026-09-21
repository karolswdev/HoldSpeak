# HS-202-02 — the shot walk facts (2026-09-20)

One real hub per run (`scripts/walk_working_desk.py serve`) against an
isolated `HOME=$(mktemp -d)`, Playwright Chromium at 1440x900 and
393x852. The browser context is given NO microphone permission, so no
device is ever opened. Rig: `shoot.py` beside this file; machine data:
`walk-facts.json`.

- console errors: none
- page errors: none
- step errors: none

| What the inventory measured | 1440 | 393 |
|---|---|---|
| dock box (x, width) — was `Overview` at x=1313 in a 393 viewport | 102, 1235 | 0, 393 |
| dock buttons inside the viewport — was 0 of 11 pressable at 393 | 9/9 | 9/9 |
| the Record orb's box — it lives in the dock | x=1290 y=855 | x=338 y=806 |
| menu titles rendered — was 4 at 393, 3 of them unopenable | ['desk', 'object', 'go', 'window'] | ['go'] |
| `New Note` inside Go — job 3's door at phone width | False (it is in the Desk menu) | True |
| ⌘K rows named `Ask AI` / of those, ghosts — was 2 doors, one dead | 1 / 0 | 1 / 0 |
| ⌘K top row for the typed word `Notes` — was `Change places` / `Telegram control` | Start here | A thought I want kept |
| `Write a thought` opens — was the Speak dictation router | Thought window ×1, Speak ×0 | Thought window ×1, Speak ×0 |
| the note editor's keep receipt — was nothing at all | KEPT · 6:50 PM | KEPT · 6:51 PM |
| Desk memory on open — was an empty body | 2 rows, region `Recent on this desk` | 2 rows, region `Recent on this desk` |
| the Server address placeholder — was the owner's LAN address | `http://<host>:<port>/v1` | `http://<host>:<port>/v1` |
| the Speak footer's egress chips — was a hardcoded `THIS DEVICE` | none | none |
| `Assignments` in the settings ledger — was declared and never rendered | present (row 2 after Models) | present |

## What this walk could NOT show

- **The meeting record's route disclosure and `Run summary`.** The
  seeded meeting (`Phase 132 desk review`) carries NO TRANSCRIPT, so
  `wantsRun` is false and both are correctly withheld
  (`pages/cores/history/NeedsYouTable.tsx:51-61`). The refresh contract
  this story changed is fenced instead in
  `web/src/pages/cores/__tests__/meetingRefresh202.test.tsx`.
- **The arrival's `Generate` badge and receipt.** The walk's desk
  already holds a brief, so the arrival renders the brief rows, not the
  `No brief yet` + `Generate` branch. Fenced in
  `web/src/desk/chair/__tests__/briefBadgeReceipt202.test.tsx`.
- **The microphone failure copy.** No microphone is ever opened by this
  rig; `speak-face-*.png` shows the face, and the failure contract is
  fenced in `web/src/lib/dictationRecovery.test.ts`.

## The coordinator's two rulings (2026-09-20), on the real card

Shots: `first-run-1440/393.png` (the card a stranger meets) and
`first-run-mic-refused-1440/393.png` (after the refusal). One hub per
viewport, each with its own `HOME`: the first-run card is a
once-per-desk state, so a shared hub can never show it twice.

| | 1440 | 393 |
|---|---|---|
| the refusal message — was "Dictation did not finish … Retry the capture." | No microphone was found on this device. Your draft remains editable. Connect a microphone, then retry. | No microphone was found on this device. Your draft remains editable. Connect a microphone, then retry. |
| the verbs on the card | Click to retry, Copy, Keep as Note, Check the microphone, Continue later, Skip for now | Click to retry, Copy, Keep as Note, Check the microphone, Continue later, Skip for now |
| HTTP responses >= 400 | none | none |
| console errors / page errors | none / none | same |

`Check the microphone` opens the readiness face
(`configure-setup` → `pages/cores/SetupCore.tsx`), whose sections carry
the doctor's own `_check_microphone()` row 1:1
(`holdspeak/commands/doctor.py:1064` → `holdspeak/setup_status.py:254-260`).

## Astra's counsel round (PR #595) + the coordinator's items 9-10

Every verb PRESSED, on a real isolated hub, at both widths. One hub per
viewport with its own `HOME`; the seeded brief is skipped
(`HOLDSPEAK_WALK_SKIP_BRIEF=1`) so the `No brief yet` + `Generate`
branch exists to press; the transcript arrives through the product's
own `.txt` import door, never the microphone.

| Condition | 1440 | 393 |
|---|---|---|
| counsel 1 — pressing `Check the microphone` opens the DOCTOR, not New Project | setup=1, new-project=0 | setup=1, new-project=0 |
| counsel 2 — `Generate` badged BEFORE | THIS DEVICE | THIS DEVICE |
| counsel 2 — receipted AFTER, surviving the brief that replaces the branch | Brief ready · 3 items · 9:49 PM | Brief ready · 3 items · 9:53 PM |
| counsel 3 — the record re-reads on the product's own return signal, no reload | 1 re-read | 1 re-read |
| counsel 5 — Desk memory on open | 2 rows, `Recent on this desk` | 2 rows, `Recent on this desk` |
| counsel 9 — every dock launcher PRESSED (geometry is not pressability) | 9/9, refused none | 9/9, refused none |
| dock buttons inside the viewport | 9/9 | 9/9 |
| the note editor's keep receipt | KEPT · 9:50 PM | KEPT · 9:53 PM |
| HTTP >= 400 / console / page / step errors | none / none / none / none | same |

`run_verb` stays 0: this hub has no engine, so the route is
`no_assignment` and the disclosure says the reason in the verb's place
(`NeedsYouTable.tsx:51-61`). Designed state, not a gap.

The walk also caught a defect THIS round introduced: opening the doctor
from the cold card and then pressing `Continue later` left the card
spinning forever, because a recovery window was still on glass when
first value handed over. `FirstWords.dismiss` now clears surface
windows before the handoff; the shot that caught it is
`arrival-1440.png` from the failing run.

Shots: `first-run-*`, `first-run-mic-refused-*`,
`first-run-microphone-checked-*`, `arrival-*`, `dock-*`, `go-menu-*`,
`shelf-notes-*`, `write-a-thought-*`, `note-kept-*`, `desk-memory-*`,
`concierge-address-*`, `settings-hub-*`, `generate-before-*`,
`generate-after-*`, `meeting-record-*`, `meeting-record-refreshed-*`,
`speak-face-*` — each at `-1440` and `-393`.
