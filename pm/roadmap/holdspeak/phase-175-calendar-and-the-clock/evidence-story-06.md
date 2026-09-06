# Evidence - HS-175-06

- **Story:** HS-175-06 - The walk (his desk: the event-born recording, the week brief, the meeting Watch entity)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-06T00:00:31Z

- **Command:** `bash -c set -o pipefail; uv run python tests/e2e/live175_walk.py --hub "$HS_WALK_HUB" --out pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-06-shots 2>&1 | sed -E "s#token=[^ \"&]+#token=REDACTED#g" | tail -40`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 089013cf65d64e0814e94d19132ca354935fcb17

```text
  cancel_recording          -> allowed=False, reason=never cancels a recording
  link_event_room           -> allowed=False, reason=never links an event to a Room
  generate_brief            -> allowed=False, reason=never generates a brief
  run_now                   -> allowed=False, reason=never presses Run now
  run_intel                 -> allowed=False, reason=never runs intelligence
  publish                   -> allowed=False, reason=never publishes
  unknown                   -> allowed=False, reason=unknown operation denied by default
  ALL WRITES DENIED.  This walk is read-only.

  [1/5] Door + settings (API)...
        done. calendar=False, upcoming=1, auto_record=off

=== Viewport 1440x900 ===
  [2/5] Arrival @ 1440...
        done.
  [3/5] Settings Meetings @ 1440...
        done.
  [4/5] Room SOURCES @ 1440...
        done.
  [5/5] Rhythm @ 1440...
        done.

=== Viewport 393x852 ===
  [2/5] Arrival @ 393...
        done.
  [3/5] Settings Meetings @ 393...
        done.
  [4/5] Room SOURCES @ 393...
        done.
  [5/5] Rhythm @ 393...
        done.

=== WALK 175 COMPLETE ===
  Facts JSON: pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-06-shots/walk-facts.json
  Facts MD:   pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-06-shots/walk-facts.md
  Shots:      8
  Errors:     0
  Surprises:  0
  Defects:    1
    - ARRIVAL: duplicate meeting rows (A.7) -- same title+badge seen twice: ['AUG 20Sprint']
```


## His word (2026-09-06)

The owner's word for the merge: "You got my word for a merge." The runner's read-only walk above is
the desk proof standing in for his sitting (no calendar connected on his
desk, auto-record OFF, every write denied); his ATTENDED seven-beat walk
stays owed, as for 169–174, and the seven questions in final-summary.md
ride to it. Story 06 flips on his word.
