# Phase 176 - The Speak Loop

**Last updated:** 2026-09-06 — CLOSED 7/8 on the gates (final-summary.md); story 06 his attended walk OPEN until his hand (the read-only leg on his desk green; the hub from this branch up for him); draft PR #566 out of draft on the close; merge on his word.

## Goal

Dictation becomes a daily tool. The correction is taught once, kept
forever, and applied to the next matching utterance. The journal is a
live stream of everything the owner spoke into the desk. The voice law
is satisfied: MicButton on every text input across the desk, not just
the seven surfaces that have it today. The desk answers the hand:
speak, see it land, judge it, teach it, see the teaching applied. The
learning loop that has never been trained gets its first real data.

## Status

**CLOSED 7/8.** 01 the design, 02 the first correction, 03 the journal stream, 04 the voice law, 05 the desk answering the hand, 07 the docs, 08 the close DONE; counsel-on-built's bounce paid (C1–C4) and its re-read recorded; the suite in CI shape classified; 06 HIS ATTENDED WALK open until his hand (the runner's read-only leg on his desk: six beats MATCH, zero writes). Merge on his word.

**Depends on:** Phase 170 merged (the Speak face is rebuilt in 170's
Great Pass; the correction flow and journal stream build on that
rebuilt face) — SATISFIED: 170–175 merged to main (#553–#558, #564).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 09:30. He holds the key, speaks a sentence about a
PostgreSQL migration. The text lands in the editor. He sees "postgress"
and taps Correct: "PostgreSQL." The correction is saved. Ten minutes
later he dictates again: "...the PostgreSQL schema..." — the pipeline
applies the correction automatically. In the Speak window the journal
shows every utterance as a live stream: source, target, latency, the
correction that fired. The learning digest reads "1 correction, reached
3 utterances." He never trained it before; now the desk learns how he
works.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
dictation_corrections 0 (the "learns how you work" loop untrained);
the correction store exists (corrections.py:1-56, CorrectionStore with
Jaccard matching, durable via DictationCorrectionRepository) but has
never been taught; the journal exists (journal.py:1-50,
DictationJournalRecorder, durable, secret-redacted) but is not a live
stream on the face; MicButton is on 7 surfaces but ~92 text inputs
exist across web/src/desk/ — the voice law (Article IV.1) is not
satisfied. (The 2026-09-06 recount against main supersedes the mic
numbers: 17 sites; and the store's two kinds are routing corrections,
so the "postgress" Tuesday needs the `text` kind this phase adds.)

## Scope

- In:
  - The first correction: the teach row on the Speak face completed
    (`Wrong` → FIELD `TEXT · INTENT · TARGET` → `Teach` → the `TAUGHT`
    receipt); a third correction kind `text` (heard phrase → said
    phrase) persisted via DictationCorrectionRepository and applied
    deterministically at the transcript seam inside Pipeline.run on
    the next utterance that carries the phrase (the `APPLIED` chip);
    the routing kinds taught as a pick over the real enum; the
    learning digest reads > 0.
  - The journal as a stream: the Journal face
    (web/src/pages/cores/dictation/Journal.tsx) shows utterances as a
    live feed (source, target, latency, corrections applied, intent
    tag from DIR-01); filterable by source
    (dictation/browser/hotkey); searchable by text.
  - The voice law: MicButton on every dictatable text input across
    the desk (Article IV.1; UX-CANON.md rule B). The census
    (assets/mic-census-176.md, main `7a47904e`) finds 17 sites: 8 raw
    elements and 9 unjustified `mic={false}` opt-outs; the scanner's
    `mic` rule made per-element with a 23-entry reasoned allowlist.
  - The desk answering the hand: the full loop from speak → land →
    judge → teach → apply, visible in one session on the Speak
    window. The correction fires on the next matching utterance
    without the owner reopening Settings or restarting the hub.
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: one correction taught and applied.
- Out:
  - New dictation pipeline stages beyond DIR-01 (the pipeline is
    shipped; this phase uses it, does not extend it). The `text`
    correction kind is a correction applied at the existing transcript
    seam, not a stage: no StageResult, no stage_ms, no requires_llm.
  - Cloud-based correction or learning (all local; Article III).
  - Correction import/export (the correction store is local; file
    exchange is a future phase).
  - Voice command authoring (the spoken-symbol dictionary and voice
    commands are separate capabilities; this phase is about the
    correction loop).
  - Correction UI beyond the Speak window (the correction flow lives
    on the Speak face; a Settings page for corrections is a future
    candidate).

## Exit criteria (evidence required)

- [ ] A `text` correction is taught via the Speak face, persisted by
      DictationCorrectionRepository, and applied deterministically to
      the next utterance carrying the phrase; a routing correction is
      taught as a pick over the real enum and nudges the next similar
      utterance; the correction count on his desk is > 0.
- [ ] The learning digest (dictation_learning.py) reads > 0
      corrections with honest reach numbers.
- [ ] The journal face shows utterances as a live stream with source,
      target, latency, and corrections applied; filterable by source;
      searchable.
- [ ] MicButton is on every dictatable text input across web/src;
      the census shows 0 uncovered sites and the scanner's `mic` rule
      reads 0 with the reasoned allowlist (Article IV.1).
- [ ] The full speak → land → judge → teach → apply loop works in one
      session without restart.
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: one correction taught and applied, the
      journal as a stream, MicButton everywhere; his word.
- [ ] Zero egress (Article III); every operation receipted (Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-176-01 | The design (the correction flow, the journal stream, the MicButton census on the canvas) | done | [story-01-the-design](./story-01-the-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-176-02 | The first correction (teach, persist, apply to the next match; learning digest > 0) | done | [story-02-the-first-correction](./story-02-the-first-correction.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-176-03 | The journal as a stream (live feed, filterable, searchable; the voice-typing act visible) | done | [story-03-the-journal-stream](./story-03-the-journal-stream.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-176-04 | The voice law (MicButton on every text input across the desk; the census gap closed) | done | [story-04-the-voice-law](./story-04-the-voice-law.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-176-05 | The desk answering the hand (the full loop: speak, land, judge, teach, apply) | done | [story-05-the-desk-answering-the-hand](./story-05-the-desk-answering-the-hand.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-176-06 | The walk (his desk: correction taught, journal streaming, MicButton everywhere, the loop) | backlog | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-176-07 | The docs (the Speak Loop in the guide; the correction flow in the architecture) | done | [story-07-the-docs](./story-07-the-docs.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-176-08 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | done | [story-08-the-close](./story-08-the-close.md) | [evidence-story-08](./evidence-story-08.md) |

## Where we are

CLOSED 7/8 (2026-09-06). Story 08 DONE: the gates (evidence-story-08.md:
the 176 set 154 passed; ratchet at `mic: 0`; api surface 668, no manifest
change; schema snapshot 76; web baseline 2336 passed, zero branch-new;
the suite in CI shape classified — 12 inherited, 7 176-new paid, 7 rigs
serial-green or inherited), counsel-on-built paid, final-summary.md,
UX-CANON's new laws, the handover. Story 06 OPEN: his attended walk
(beat 0: the engine reads KEY NOT SET). Story 07 DONE: docs/USER_GUIDE.md `## Speak`
(the four wings, the teach loop and its five receipts, text vs routing
corrections, the APPLIED chip, the Journal wing, the Learned wing,
Review, `corrections_enabled` ON by default, retention and redaction,
the mic law), docs/ARCHITECTURE.md `### The learning loop` (the three
kinds, the matcher's rules, the Pipeline.run seam, `corrections_applied`
vs `corrected`, the bus frame, a Mermaid diagram, the routes-and-fields
table), the pipeline guide's truth audit, README's row, three glossary
rows, five canonical names in POSITIONING.md; every claim verified
against the shipped tree (file:line in the story's evidence). Story 05 DONE: the fourth wing LEARNED
(TEXT | INTENT | TARGET emblem · key → label · N APPLIED absent at
zero · Forget; NOTHING LEARNED; no caption count), `Review` → the
Journal wing (and closes the door), the utterance well's mic off (Talk
the sole mic; the allowlist needle kept), the Configure door's Memory
panel now the digest only, the loop proven in one hub session without a
restart (land → Wrong → teach → APPLIED → Journal TAUGHT+APPLIED →
Learned 1 APPLIED → Forget → NOTHING LEARNED → Review), shot at 1440 +
393 (assets/story-05-shots/). Build ruling: no search well on the
Learned wing (the boards draw none; the design's D2(c).2 parenthetical
was wrong). Story 03 DONE: the Journal wing as a stream
(the bus frame prepended live, deduped; the row grammar with one fixed
APPLIED/TAUGHT slot; day bands as tokens; the opened row keeps Replay ·
Copy · Delete with its preview as tokens; the four filter tokens as the
new library species FilterTokens promoted from the Room's composition
and documented in contract.md; search over final_text; scroll-to-load
with `before`; no caption count; NOTHING SPOKEN / NOTHING MATCHES;
Clear withheld on the quiet state), shot at 1440 + 393
(assets/story-03-shots/); the rig proves record → broadcast → /ws →
RuntimeBus → prepend without a reload. Build rulings: older entries are
reached by scrolling DOWN (newest-first list); the empty token is
SurfaceState's plain label (species geometry). Story 02 DONE: the `text` correction kind
(exact-phrase, punctuation-stripped, whole-word bounded, first-letter
case kept) applied at the seam inside Pipeline.run before the stage
loop; `corrections_applied` on the run and the journal row (schema 76,
named INSERT, snapshot regenerated); the recorder's bus seam; the R4
route fixes, the server-side diff, the raw transcript on the run
response, `N APPLIED` as a real count, the six target labels on
readiness; the teach row FIELD `TEXT · INTENT · TARGET` with the
receipts `TAUGHT` · `NO CHANGE` · `REFUSED · SECRET|ONE WORD` and the
`APPLIED` chip + its well, shot at 1440 + 393 through the real routes
(assets/story-02-shots/); the ritual fence re-pointed at SpeakFace.
Build rulings: no MATCH score (the wire carries none; painting the
threshold would be a lie); the pick is CycleGadget (no picker species
exists); the chip is a library Button + region (Disclosure cannot sit
inline); the receipt lives in the row only (the footer never mirrors
it); the 393 well is PadGadget rows=1 autoGrow (a single-line field
cannot wrap). Story 04 DONE: the scanner's `mic` rule made
per-element and un-gated with a 24-entry reasoned allowlist (23 from
the census + the utterance well pre-armed for story 05), the 8 raw
sites and 9 opt-outs paid, ceiling `mic: 0`, rule B healed 34 → 32
(locked at the close), the four 170 orphans parked under `_parked/`;
web baseline zero branch-new. Story 01 DONE: the settled design re-verified
against main, the mic census recomputed, seventeen boards at 1440 + 393
under assets/mockups/ on the canvas
(https://claude.ai/code/artifact/36f77f70-fb03-461d-a0dd-8b43c4682e63),
counsel's hunt (BOUNCE → the rulings) and re-read (RATIFY-W-C, N1–N5
paid), his word ("Let's follow your ruling"). Wave 1 in flight: lane A
the wire core (02), lane B the routes (02+03), lane C the voice law
(04). Then the face lanes to the boards, 05, counsel-on-built, docs,
his walk, the suite, the close.

The recon below was taken 2026-09-05 on feat/the-great-pass; the
settled design and assets/mic-census-176.md hold the numbers as of
main today (they win where the two disagree).

The recon is complete:

**Correction store today:** exists and is fully wired but untrained.
CorrectionStore (corrections.py:1-56) is a bounded ring buffer
(cap=20) of Correction(kind, key, value, sequence) dataclasses with
Jaccard token-overlap matching. Durably backed by
DictationCorrectionRepository (wired at web_runtime.py:97-109,
web_server.py:225-228). API routes exist: GET/POST/DELETE at
/api/dictation/corrections (pipeline.py:917-1009). Census:
dictation_corrections 0 on the owner's desk.

**Learning digest today:** exists as a read-only aggregation
(dictation_learning.py:1-58) over journal + corrections with honest
reach numbers using the same Jaccard matcher the live pipeline uses.
Computes but never writes. With 0 corrections, the digest is empty.

**Journal today:** DictationJournalRecorder (journal.py:1-50) writes
one durable row per pipeline run (source, raw_text, processed_text,
intent_tag, latency, corrections_applied). The Journal face
(Journal.tsx) exists on the Speak window but is not a live stream
with filtering and search.

**MicButton today:** on 7 surfaces (gadgets.tsx:299,357;
Surface.tsx:1174; ChairHome.tsx:540; ThreadPullout.tsx:751;
NoteEditor.tsx:166; RecipeEditor.tsx:113; DecisionsView.tsx:167).
~92 text inputs exist across web/src/desk/. The voice law
(Article IV.1: "every text input can be spoken into") is not
satisfied — the gap is ~85 uncovered inputs.

**DIR-01 pipeline today:** fully built at holdspeak/plugins/dictation/
(pipeline.py, contracts.py, runtime.py, three backends, grammars.py,
blocks.py, builtin stages, journal, corrections, telemetry_store).
The pipeline is shipped and functional; this phase uses it, does not
extend it.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Correction quality (Jaccard false positives) | Medium | The ring buffer is capped at 20; the threshold is tunable; a false correction is one tap to remove; the correction flow shows what fired | > 30% of corrections fire on unrelated utterances during the walk |
| MicButton coverage regression | Low | A guard test counts MicButton instances vs text inputs; the ratchet enforces the coverage; the UX-CANON scanner tracks the gap | The guard count drops below the ceiling after a subsequent phase |
| Journal stream performance with large history | Low | The journal is durable rows with an index; the stream paginates; the face shows the most recent N with scroll-to-load | The journal face takes > 500 ms to render 100 entries |

## Decisions made (this phase)

- **2026-09-06 — the road continues (the orchestrator's ruling on the
  owner's deferral).** The owner: "muad'dib... you decide. we push
  this forward, or it's phase 200 time..." Ruled PUSH FORWARD: 176
  chartered and active. Reasons: the road to 180 is his standing goal
  (THE-TUESDAY-ARC.md section 6); this phase's charter and recon were
  already written against the tree; the voice law (Constitution
  Article IV.1) is an unpaid canon debt; the correction loop has never
  been taught (dictation_corrections 0 on his desk); "phase 200" names
  no thesis anywhere in the tree, so a pivot would abandon a named road
  for an unnamed one. What stays his: the canvas (his word before any
  face is built) and the merge.
- **2026-09-06 — the design is refreshed, not redrawn.** The 2026-09-05
  draft (settled-design-speak-loop.md) was written on
  feat/the-great-pass; every file:line pointer is re-verified against
  main after 170–175, the mic census is recomputed
  (assets/mic-census-176.md), the face shapes stand unless the built
  tree makes one impossible (changes listed at the end of the design).
- **2026-09-06 — counsel's bounce and the ruling: a third correction
  kind.** Counsel (assets/counsel-on-design-176.md) found the P0: the
  correction store holds ROUTING corrections only (`intent` = a block
  id, `target` = a profile id; corrections.py:33, intent_router.py:215,
  target_profile.py:149), so the charter's Tuesday ("postgress →
  PostgreSQL") cannot happen on this wire, and the teach row 170
  shipped is dead for a typed sentence. Counsel proposed shrinking the
  teach to a pick over the enum. RULED otherwise: the Tuesday is a
  TEXT correction, so the store gains a `text` kind (heard phrase →
  said phrase), applied deterministically at the transcript seam
  before the rewrite pass and the router (beside the spoken-symbol
  substitution in text_processor.py), exact-phrase not Jaccard; the
  teach field cycles TEXT · INTENT · TARGET, TEXT as one pre-filled
  well the owner edits (the desk learns the differing span), the
  routing kinds as a pick over the real enum with human labels. The
  carve: this is a correction kind at an existing seam, not a new
  pipeline stage. Counsel's C2–C14 accepted as rulings R2–R14 (the
  design's addendum): chips render only from a stored per-run fact;
  `N APPLIED` counts real firings; the refusal key and the
  mark-corrected order fixed; the overloaded flag split; the filter
  species named truly; the one-word routing gist refused by name;
  one word one meaning (LEARNED the wing, TAUGHT the receipt, APPLIED
  the chip); the scanner sees textareas; the walk's writes stated
  honestly; the Journal's opened-row verbs kept; labels sourced; the
  well's mic off; the phone board follows 170.
- **2026-09-06 — counsel's re-read: RATIFY-W-C, five conditions, all
  ruled accepted (N1–N5 in the design's addendum).** N1 `auto` in the
  target pick raises on the live path (no label in the map): six ids
  offered, `_profile` belt-fixed. N2 the TEXT well pre-fills with the
  RAW transcript (as heard), which the run response now serves; the
  diff runs against it. N3 the matcher strips punctuation; boundary =
  non-alphanumeric-or-edge. N4 a text rule rewrites every future
  occurrence of its phrase on every dictation source; said honestly in
  D4; "should a first application confirm?" rides to his walk. N5 the
  Journal row he taught from wears `TAUGHT`; the Learned wing carries
  no caption count (the tab is the name, the rows are the count).
- **2026-09-06 — his word: build.** The owner: "Well. Let's follow your
  ruling, then. It's important we continue to make progress..." Read
  as his word to build to the design counsel ratified on his behalf
  (HANDOVER §0: a face is built only to boards he or
  counsel-on-his-behalf ratified); the merge stays on his word, shots
  beside boards before it. Wave 1 (wire) launched: lane A the `text`
  kind + the Pipeline.run seam + the journal column + the recorder's
  bus seam; lane B the routes (R4 fixes, the diff, the raw transcript,
  N APPLIED, the label sources, the journal clamp + pagination); lane
  C the voice law (scanner per-element, 17 sites, 4 orphans parked).
- **2026-09-06 — counsel-on-built: BOUNCE (assets/counsel-on-built-176.md),
  the rulings.** C1 (P0) the real Talk path `POST /api/dictation/remote`
  dropped `raw_text`, `corrections_applied`, `journal_id`, so on a real
  landing the APPLIED chip never showed, the TEXT well pre-filled the
  landed text and teach took the fallback route — paid: the three keys
  served, proven by a route test with delivery stubbed and by the face's
  vitest; RULED: no rig ever lands for real (a rig must never type into
  the machine's focused window), the real landing is his walk's beat.
  C2 (P1) the live frame now honours the active filter and search.
  C3 (P1) `_looks_secret` widened to the common token shapes (the
  board's own `sk-live-4f2a9c` was not refused). C4 (P1) the footer's
  `N TODAY` counts today's rows (local day), not the all-time retained
  count. C5–C16 (P2) parked to BACKLOG.md under "Phase 176 remainders".
- **2026-09-06 — the suite in CI shape, classified.** Run once at
  `5a0a29f5` with no product lane editing (`-n auto`, isolated HOME,
  28 min): 26 failed, 10180 passed, 99 skipped, 1 error. Classified
  against a main worktree at `7a47904e`: 12 INHERITED (they fail
  identically on main: test_ask_grounding_claims ×2,
  test_ask_runner_migration, test_desk_seed ×2, test_hs173_nudge_wire
  template, test_kernel_effect_fence ×2 (the broker density fences),
  test_product_copy (29 pre-existing offenders), test_project_mcp ×3);
  7 176-NEW fences that moved (the realtime frame registry ×2 — the
  new `dictation.journal.entry` frame; the journal replay fence; the
  UAT honest-count test (`similar` → `applied`); the phase-143
  inference/routing censuses ×3) — paid by the fence lane; 7 rigs to
  re-run serially (xdist-only vs real): hs144 door, hs153 practice,
  hs154 call, hs170 speak-unset, hs172 settings-meetings 393, hs175
  arrival week strip (the 1 error is a setup error in the same rig
  file, test_arrival_cancel_idle_event_born), hs176 loop 393.
  Serial re-run (`5a0a29f5` + the fix lanes' working tree): hs154, hs170
  speak-unset, hs172 393 and hs176 loop 393 GREEN (xdist-only); hs144
  door deep-link (a console 404) and hs153 practice guardrail (deny vs
  allow) fail IDENTICALLY on the main worktree (INHERITED); hs175
  arrival's overflow test flipped (green on main, red once serially on
  the branch, green on the retry) — the rotating flaky rig family.
- **2026-09-06 — counsel's re-read after the fixes: RATIFY-W-C; C1's
  SPOKEN half NOT PAID, then paid.** The typed landing carried the three
  keys; the spoken one (Talk → the voice stream → the `final` frame →
  MicButton `onText` → `onReleased` → the raw remote send) still dropped
  them at the `final` frame (voice_stream.py). RULED: carry the facts on
  the `final` frame through the callback into the deck; never a
  read-time newest-row lookup (R2). PAID in the close commit
  (voice_stream.py's `final` frame, dictation_runner's publication
  sink, MicButton's `onText` second argument, the deck's merge; 15 new
  tests). Its finding paid too: a field mic writes NO journal row, so
  the walk's beats 6 and 7 and the design's D0/D5 say so. N2: a spoken Speak-face utterance
  journals as `browser` — RULED to keep it (the browser mic is the
  source); the walk's beat 5 and the guide say BROWSER for Talk on the
  Speak face, DICTATION for the desktop hotkey. C3's blast radius named:
  the widened secret guard drives `filter_secret` (whole-field
  redaction) and the project-doc suggestions product-wide.
- **2026-09-06 — the walk's read-only leg on his desk.** A hub from
  this branch booted on his real HOME (the final build on port 49353
  after the spoken-landing fix; the URL and token only in the session
  scratchpad); `tests/e2e/live176_walk.py`
  read-only: six beats MATCH (corrections_enabled True; four wings;
  the well mic-less with Talk; his nine real journal rows under ALL ·
  DICTATION · BROWSER · HOTKEY with no caption count; NOTHING LEARNED;
  Review crosses to the Journal), zero defects, zero writes by the
  runner (Clear / Delete / Replay / Forget DENIED); his DB read-only
  census before and after: journal 9/9, corrections 0/0, meetings 6/6;
  the only change is the product's own additive `corrections_applied`
  column on startup (schema 76). Two findings for his eye: the engine
  reads `GPT 5 mini · API.OPENAI.COM · KEY NOT SET` (a cloud engine
  without a key; Talk cannot land until beat 0 fixes it), and one Aug
  21 row has an empty transcript (BACKLOG). The attended beats (talk,
  the wrong landing, the teach, the same phrase again, the mic on a
  Room and on the Door, the two walk questions) are HIS; the hub stays
  up for them. Story 06 stays open until his hand.
- **2026-09-06 — the walk's writes.** The walk on his desk writes what
  his own hand writes: the journal rows of his dictations, the
  retention prune, and the one correction he teaches; the runner seeds
  nothing and asserts the rows added equal his beats.

## Decisions deferred

- The exact correction UX on the Speak face (inline edit vs a
  correction well beneath the utterance) -- decided on the canvas.
- Whether the journal stream auto-scrolls to the latest utterance or
  stays at the user's scroll position -- decided at design time.
- The MicButton placement rule for compound gadgets (e.g. a
  StringGadget inside a LedgerRow: does the mic sit inside the
  gadget or on the row?) -- decided on the canvas.
