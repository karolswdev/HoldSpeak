# PHILO-13-09 — Astra lane report

**DRAFT — UNCHECKED — awaiting Muad'Dib.**

LANE: H-B4, The 1:1 finds its person. Worktree `../wt-philo-13-09-astra`; branch `feat/philo-13-09-astra`; base `5912fcb9474cae7b058838f120a2c216189be89a`.

OUTCOME: the People brief now suggests calendar events by a saved alias, reads the next confirmed calendar link, and includes the report's open meeting actions and projects beside the agenda. A suggestion does not write a link. The existing confirmation route writes it. Parked meetings, completed actions and other owners stay out. Plaintext read failures return 503 instead of an empty success. No face file changed; story 09 remains in-progress for B4-W and counsel.

PROOF:

- [252 collected](assets/story-09-prep/collection.txt), [252 passed through Delivery Workbench](assets/story-09-prep/captured-runs.md), including all three mandatory shared files. [Two real-producer fences failed before the product fix](assets/story-09-prep/red-before.txt). The focused tests use ICS ingestion, meeting persistence, encrypted People storage with a FILE key, and People routes. The five final B4 tests also cover unlinked meeting actions, parked/completed exclusions, an event past 50 earlier events, ownership and 503 failures.
- [Two client tests](assets/story-09-prep/web-prep.txt), [typecheck](assets/story-09-prep/typecheck.txt), [web build](assets/story-09-prep/build.txt), and [all 12 Documentation Navigation commands](assets/story-09-prep/navigation.txt) pass. No full suite ran.
- The actual live protocol case passes against the restarted hub: linked UID/source, owned action/meeting, agenda and project match the minted records. The face case reaches Priya's linked next 1:1 at 1440 and 393 native touch, then correctly fails on the missing owed action in Prep. [Run index](assets/story-09-prep/runs.json), [manifest](assets/story-09-prep/manifest.json), [desktop Prep](assets/story-09-prep/prep-1440-r2/after.png), [phone Prep](assets/story-09-prep/prep-393/after.png). These are run-owned desk/DB observations, not the owner's sitting.

LEDGER: (b, named B4-W handoff) Prep shows the existing agenda and next 1:1 but does not render `open_meeting_actions` or `projects`. Tenets 3 and 7: he still cannot read what Priya owes from Prep. The face failure is retained; it is not called a pass. The first walk was blocked because the fixture's calendar source was not saved and the restarted conductor pruned its event. The fixture now saves its source in the isolated Config; its test runs the real conductor again before asserting the event survives. Both the blocked run and the corrected runs are retained.

AMENDMENTS: H-B4 is the following contract for B4-W and H-C3. `GET /api/people/relationships/{id}/brief` returns `brief.calendar_link_suggestions`, `next_one_on_one` (event object or null), `agenda_items`, `open_meeting_actions` and `projects`. Each action retains `owner`, `meeting_id`, task, due date and meeting context. Relationship detail exposes `next_one_on_one` as the start timestamp and `next_one_on_one_event` as the event object. `readPeoplePrep(id)` in `web/src/desk/people/prepData.ts` maps the brief to `calendarLinkSuggestions`, `nextOneOnOne`, `agenda`, `openMeetingActions` and `projects`; `composePeoplePrep` is pure. B4-W must render these and offer the existing explicit link confirmation. The verification-only `seed_people_prep` rig action mints through real producers and uses a FILE key inside the run HOME. Its HTTP case is named `.protocol`, not `.op`; the canonical operation guard is unchanged. Capability metadata and generated references are refreshed. Isolated run HOMEs were cleaned; Node 22.21.0 was used because local Node 25 cannot load llhttp.

UNKNOWN: Muad'Dib's check, merge, B4-W's final rendering and the owner's sitting. Tuesday: the data is ready; the owner needs B4-W to read Priya's owed action and project on Prep.

## Mechanical rebase for #742

Rebased the H-B4 changes onto `76c361537` (main including #743). Both
metadata additions and both atlas populations survive the merge; generated
references are current. The parent independently ran 156 tests through
Delivery Workbench: [capture](assets/story-09-rebase/captured-runs.md),
[collection](assets/story-09-rebase/collect.txt). This is a mechanical
integration check, not a new full-suite or glass claim.

#742 stays OPEN and unmerged for B4-W. Astra's separate `p13-b4w-check`
returned RATIFY-WITH-CONDITIONS: show failed brief reads with Retry, preserve
date-only deadlines in Denver, and add the declared B4-W atlas coverage.
Muad'Dib owns those conditions. Story 09 remains in-progress.
