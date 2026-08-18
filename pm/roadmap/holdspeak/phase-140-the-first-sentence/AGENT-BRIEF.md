# Phase 140 — The First Sentence

## The promise

A person opening HoldSpeak for the first time can dictate one sentence, edit
it, copy it or keep it, and understand what happened without first learning
HoldSpeak's architecture.

## Owner mandate

> Who the fuck would use a super complex and complicated piece of shit?

The answer is not a dashboard. Phase 140 cancels the proposed Dashboard Door
and makes the product's smallest real value unmistakable. HoldSpeak already
has the path; it is marooned on the empty Floor while the actual front door
opens on a Chair full of competing nouns and actions.

## Tuesday question

Can a tired owner, on a clean install, get one useful sentence out of
HoldSpeak before they have to understand destinations, pipelines, agents,
workbenches, postures, grounding, or the spatial Floor?

The phase closes only when the answer is yes at 1440×900 and 393×900.

## Product cut

During first value, the Chair has one primary action: **Dictate one sentence**.
Secondary lanes, Ask, Floor, setup administration, routing language, and
ambient system state do not compete with it. They are not deleted. The mounted
first-value composition remains available after transcription so the owner can
edit and finish; a finishing action, Continue later, or later reload returns to
the normal Chair.

Success means a non-empty transcript reached the editable field. Launching
capture, granting microphone access, or opening the screen is not success. The
result stays local and editable; Copy and Keep as Note finish the job.

## Existing seams to reuse

- `web/src/desk/components/FirstWords.tsx` already owns capture, editable
  output, Copy, Keep as Note, and recovery copy. Its retained-audio claim is
  currently false because it does not pass the existing `retainScope` option;
  Story 03 must wire and prove that seam.
- `web/src/desk/firstValue.ts`, `holdspeak/services/setup_service.py`, and
  `holdspeak/db/onboarding.py` already provide content-free journey receipts.
- `holdspeak/setup_status.py` already exposes `arrival_required`.
- `web/src/desk/DeskApp.tsx` already chooses the Chair as `/` and knows setup.
- `web/src/desk/chair/ChairHome.tsx` is the convergence point. Do not create
  another welcome route, wizard, dashboard, or control center.

## Non-negotiable laws

- One obvious first action; no carousel, checklist, wizard, or tour.
- No new model, routing, task, calendar, schema, API, or MCP concept.
- No fake success. A transcript must actually arrive.
- No phrase, transcript, or audio content enters first-value telemetry.
- Every visible action works or names a specific in-place recovery.
- Setup appears only when it is the next necessary recovery action.
- The owner's open-throttle ruling remains unchanged; this phase changes
  hierarchy, not security posture.
- Advanced surfaces remain available after first value. Progressive disclosure
  is not capability deletion.

## Story order

1. **One obvious door** — put the existing first-value path on the Chair and
   remove competing first-run chrome.
2. **The sentence becomes useful** — make edit, Copy, and Keep finish with
   truthful, findable results.
3. **Recovery stays here** — permission, model, transcription, and retained-
   audio failures recover without a systems tour.
4. **The quiet return** — restore the normal Chair after success or Continue
   later, with no silent hero actions.
5. **The cold walk** — prove the journey from a fresh HOME at both widths and
   make public entry-point docs teach the same tiny product.

Story 01 lands first and alone. Stories 02 and 03 are serialized because both
change `FirstWords` and its state machine. Story 04 composes them. Story 05 is
serialized closeout and includes the owner's screenshot sitting.

## Explicit exclusions

- Dashboard Door, TODO kanban, calendar/upcoming-meeting aggregation.
- A new onboarding route or duplicated first-value component.
- Automatic cloud enrollment, key collection, or destination selection.
- Normal-Chair restructuring beyond truthful entry and exit.
- CI monitoring. The owner ruled GitHub minutes out as a gate; verification is
  local and bounded.

## Exit bars

- Fresh HOME opens directly on one first-value composition on the Chair.
- The primary verb is visible without scrolling at both target widths.
- One real sentence can be dictated, edited, copied, and kept as a note.
- The kept note is visible from the normal Desk without hunting.
- Every named failure is shown in place with Retry or one exact recovery.
- Continue later and success each restore the normal Chair on reload.
- No first-value event payload can contain dictated content.
- Owner-visible before/after and failure screenshots exist at both widths;
  owner sees them before merge.
