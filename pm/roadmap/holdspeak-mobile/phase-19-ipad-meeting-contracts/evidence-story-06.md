# Evidence — HSM-19-06 — The learning-loop reader (read-first)

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-06-learning-reader`. The read
clients (`journalEntries` / `learningDigest`, commit `8f65657`) gain their surface: the
visible learning loop (HS-48) reaches the iPad, read-only by shape.

## 1. The learning card (`CompanionShellApp.swift`, Dictate tab)

Dictation's afterlife sits beside the teleprompter, not under Meetings:

- **The digest headline** as chips: corrections made, dictations corrected,
  "N similar nudged" (only when `enabled` — the header also states honestly when
  corrections are off on the desktop), journal total. A **Week / All** toggle re-reads
  the digest window.
- **The correction rows** (top 4): kind icon, gist → value, the real per-correction
  reach ("N similar" — the same Jaccard count the live router uses).
- **The journal** (recent 6): final text, source (dictation / dry run), target profile,
  the `corrected` mark, the HS-48-02 inline "learned from N similar" signal when the
  hub sends one, honest ms. `journal.enabled=false` and N=0 each render a quiet one-line
  state, never an error.
- **Read-only by shape:** no correction editing, no delete — the card simply has no
  write affordances (corrections CRUD and on-device journaling stay Phase-9 territory,
  per the story's scope).

## 2. The live-hub proof (real routes, scratch DB + scratch CONFIG)

`holdspeak.config` redirected to a scratch dir BEFORE anything reads it (the owner's
real `~/.config/holdspeak` untouched); real rows through the real repositories
(`db.dictation_journal.record`, `db.dictation_corrections.record_correction`,
`mark_corrected`):

```
1. journal -> enabled=True, count=3, items=3
   - [dry_run]   'Draft the standup summary…'  corrected=False learning=intent->commit_message similar=1
   - [dictation] 'Use Redis with a 1 hour TTL…' corrected=False learning=None      ← honest: no Jaccard reach
   - [dictation] 'Use Redis with a 24 hour TTL.' corrected=True  learning=target->terminal similar=1
2. digest(week) -> enabled=True, totals={corrections_made: 2, dictations_corrected: 1, similar_nudged: 2, journal_count: 3}
3. digest(all)  -> same totals (all activity is inside the week)
```

The connected simulator rendered that live hub (not a seed):
[`hsm-19-06-live-hub-learning.png`](./screenshots/hsm-19-06-live-hub-learning.png) —
the totals chips, both correction rows with their reach, and the journal with the
per-entry source/target/corrected/"learned from 1 similar" marks, under the live
teleprompter.

## Honest boundaries

- The Week/All **tap** rides the 19-07 walk (W3 covers the Dictate surface); both
  windows were read live above and the toggle calls the same `learningDigest(window:)`.
- The digest's by-block/by-target breakdowns are decoded (contract-locked) but only the
  top-line chips and correction rows render — the iPad card is a reader, not the web
  Memory tab.

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** (`LearningClientTests` lock both
verbs' URL + decode) · companion-shell simulator build (iPad Air 13-inch M4)
**BUILD SUCCEEDED** — both after the change.
