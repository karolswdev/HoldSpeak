# HS-140-02 — The sentence becomes useful

- **Project:** holdspeak
- **Phase:** 140
- **Status:** backlog
- **Depends on:** 140-01
- **Unblocks:** 140-04, 140-05
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

A transcript is not value if the owner cannot confidently use it. Copy and
Keep as Note exist, but completion feedback and the hand-off to the normal
Desk must prove that the sentence went somewhere findable.

## Scope

- **In:** preserve the editable transcript; make Copy report success or an
  actionable clipboard refusal; mint one stable client note ID for the whole
  Keep attempt so response-loss retry upserts rather than duplicates; refresh
  the Desk store and open the created note through the existing pullout/window
  seam; mark success only after a non-empty transcript; retain content-free
  metrics; apply the existing first-value content-key rejection guard to event
  requests as well as start/finish requests.
- **Out:** rich note editing, rewrite/model setup, clipboard history, note
  schema changes, phrase content in first-value telemetry.

## Acceptance criteria

- [ ] A real non-empty transcript remains editable before finishing.
- [ ] Copy writes the edited value and shows visible success/refusal.
- [ ] Keep reuses one stable note ID across repeated clicks/response-loss retry,
  producing exactly one note.
- [ ] After Keep, the Desk store refreshes and the created note opens through
  the existing pullout/window seam; it remains findable after reload.
- [ ] Capture start/release and empty results do not complete the milestone.
- [ ] First-value records contain no transcript, phrase, audio, clipboard
  value, or note body.
- [ ] First-value event requests reject content-bearing keys rather than merely
  ignoring them.

## Test plan

- **Web unit:** edit→Copy receipt, clipboard refusal, stable-ID response-loss
  Keep retry, store refresh, and opened-note hand-off.
- **Python:** transcript-bound milestone, content-bearing event rejection, and
  content-free records.
- **Local browser:** dictate, edit, Copy, Keep, enter normal Chair, open note.

## Notes

“Dictation is ready” is not the final promise. The sentence must be usable.
