# Phase 176 — The Speak Loop — final summary

**Closed:** 2026-09-06 (stories 01–05, 07, 08 done; 06 his attended
walk OPEN until his hand). Branch `feat/the-speak-loop` off main
`7a47904e`; draft PR #566; merge on his word.

## The Tuesday it buys

Dictation became a daily tool with a memory. He says a sentence, it
lands wrong (`queue for` where he said `Q4`), he presses `Wrong`, the
FIELD reads `TEXT`, the well holds what the desk heard, he edits it to
what he said, presses `Teach`, and the row receipts `TAUGHT · queue for
→ Q4`. The next dictation carrying the phrase lands right and wears
`APPLIED`; the chip opens to `HEARD queue for · SAID Q4 · TEXT`. The
Journal wing streams every utterance as it is journaled, with the row
he taught from wearing `TAUGHT` and the row a rule fired on wearing
`APPLIED`, filtered by ALL · DICTATION · BROWSER · HOTKEY, searchable,
pageable, its verbs kept. The Learned wing lists what the desk knows
(`TEXT queue for → Q4 · 1 APPLIED · Forget`). Every dictatable text
input on the desk takes his voice through the square click-to-toggle
mic, and the Speak face has one mic authority, Talk.

## The road here

The owner deferred the road itself ("you decide. we push this forward,
or it's phase 200 time"). Ruled PUSH FORWARD; 176 chartered. The
2026-09-05 design draft was re-verified against main (eleven false
claims fixed) and the mic census recomputed (17 sites, not 31). Counsel
BOUNCED the design on one P0: the correction store held routing
corrections only, so the charter's "postgress → PostgreSQL" Tuesday was
impossible on that wire and the teach row 170 shipped was dead for a
typed sentence. Ruled otherwise than counsel proposed: a third
correction kind `text`, applied deterministically at the transcript
seam inside `Pipeline.run`, with the routing kinds as a pick over the
real enum, and one word per meaning (LEARNED the wing, TAUGHT the
receipt, APPLIED the chip). Counsel's re-read ratified with five
conditions (N1–N5), paid. Seventeen boards at 1440 + 393 on the canvas
(`36f77f70-fb03-461d-a0dd-8b43c4682e63`). His word to build: "Well.
Let's follow your ruling, then. It's important we continue to make
progress..." — read as the word to build to the design counsel ratified
on his behalf, the merge on his word.

## What shipped (by story)

| Story | Commit | What |
|---|---|---|
| 01 The design | `cb64cad8`, `9bbef950` | The settled design + the census + counsel's hunt and re-read + 17 boards; done on his word |
| 04 The voice law | `01a1a03b` | The scanner's `mic` rule per-element with a 24-entry reasoned allowlist; 8 raw sites + 9 opt-outs paid; ceiling 0; four 170 orphans parked |
| 02 The first correction | `f45bb9c8` | The `text` kind; the seam; `corrections_applied` (schema 76); the recorder's bus seam; the R4 route fixes; the server-side diff; the raw transcript; `N APPLIED` real; the six target labels; the teach row to its five boards |
| 03 The journal stream | `3b39422e` | The live push proven end to end; the row grammar; the FilterTokens species promoted; search, pages, two empty states; the opened row's verbs kept |
| 05 The desk answering the hand | `e1067485` | The Learned wing; Review → Journal; the well's mic off; the loop in one session |
| 07 The docs | `5a0a29f5` | USER_GUIDE `## Speak`, ARCHITECTURE `### The learning loop`, the pipeline guide's truth audit, README, glossary, POSITIONING's names; six shots under docs/assets/speak-loop/ |
| counsel-on-built paid | `3a573eb4` | C1 (P0) the delivery reply's three keys; C2 the frame honours the filter; C3 the secret guard widened; C4 `N TODAY` counts today; the seven moved fences; rule B locked at 32 |
| 08 The close | this commit | The gates, the suite classified, the walk's read-only leg, this summary |

## The gates at the close

- The 176 set (text kind · routes · scanner · ritual fence · frame
  registry), the ratchet at ceiling `mic: 0`, the api surface (668
  routes, no manifest change), the schema snapshot (76), the doc
  guards: green (evidence-story-08.md).
- The web baseline: zero branch-new (evidence-story-08.md).
- The suite in CI shape at `5a0a29f5` (`-n auto`, isolated HOME):
  26 failed / 10180 passed / 99 skipped / 1 error, classified: 12
  INHERITED (fail identically on a main worktree: the ask grounding
  pair, the ask runner migration, the desk seed pair, the 173 nudge
  template, the two broker density fences, product copy's 29
  offenders, the three project MCP tests); 7 176-NEW fences moved with
  the code and paid at `3a573eb4`; 7 rigs: four green serially
  (xdist-only), hs144 and hs153 fail identically on main (inherited),
  hs175's overflow test the rotating flaky family (green on retry).
- Counsel-on-built: BOUNCE → the P0 and three P1s paid; the re-read
  RATIFY-W-C found C1's SPOKEN half unpaid (the voice stream's `final`
  frame dropped the keys) — paid in the close commit; twelve P2s and
  two re-read notes parked in BACKLOG "AG. Phase 176 remainders";
  counsel's verdicts recorded in assets/counsel-on-built-176.md.
- The walk's read-only leg on his desk: six beats MATCH, zero defects,
  zero writes by the runner; his DB 9/0/6 before and after.

## The rulings this phase made (the record is current-phase-status.md)

1. The road continues (his deferral ruled).
2. A third correction kind `text`, exact-phrase, at the transcript seam;
   the routing kinds a pick over the real enum; one word one meaning.
3. Chips render only from a stored per-run fact; `N APPLIED` counts real
   firings on the retained journal.
4. No rig ever lands for real; the real landing is his walk's beat.
5. No MATCH score on the face (the wire carries none; painting the
   threshold would be a lie).
6. The pick is CycleGadget (no picker species exists); the chip is a
   library Button with a region; the receipt lives in the row only; the
   393 well wraps (PadGadget rows=1).
7. No search well on the Learned wing; no caption count on either wing;
   the footer's `N TODAY` is the one count per face and counts today.
8. The walk's writes are his own hand's; the runner asserts the
   write-set before and after and seeds nothing.

## Owed to him

- His attended walk (story 06): beat 0 first — the engine reads
  `GPT 5 mini · API.OPENAI.COM · KEY NOT SET`; set the key or pick a
  local engine; then beats 1–7 and the two walk questions (routing or
  words: 176 answers both with TEXT default; should a text rule's first
  application confirm?). The hub from this branch is up on his desk for
  it.
- His word on the merge.
- Unchanged from before: the attended walks 170–175, the queued
  "Already titled" job, 172–174's questions.

## Laws this phase added (UX-CANON.md and the handover carry them)

- A design drafted on one branch is re-verified against main before the
  canvas; a design's own census is recomputed on the tree it builds on.
- A `mic={false}` is a voice-law hole the raw-element count cannot see.
- A rig never types into the machine's focused window.
- A fence anchored to a file moves with the file (the ritual fence, the
  frame registry, the phase-143 censuses, the UAT recipe).
- A worker runs the canon scanner only to a scratch path; its default
  output rewrites another phase's tracked census.
