# The Speak Loop -- the settled design (Phase 176)

> **DRAFT -- pending 170's merge.**

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 6): dictation as
a daily tool -- the correction taught once and kept, the journal as a
stream, the voice law on every input, the desk answering the hand.

The face canon binds (docs/internal/UX-CANON.md). The 170 Speak face
(settled-design-four-faces.md section 2) is the ratified shape. The
Constitution articles III (local first), IV (voice first-class), and XI
(kernel receipts) bind every line below.

## D0 -- the Tuesday moment

He says "ship the Q4 platform on schedule" into Codex CLI. The text
lands in the utterance well. The RESULT row shows the final text. It
landed wrong -- `Q4` became `queue for`. He presses `Wrong`. The teach
row unfolds beneath the result: Field cycle shows `Delivery target`, but
he cycles to `Intent` and types `ship the Q4 platform on schedule` in
the correction well, presses `Teach`. The row receipts: `LEARNED --
applies to "ship the Q4 platform on schedule"`. The next time he says a
similar phrase the Jaccard matcher fires, the correction applies, `Q4`
lands right. The RESULT row carries a chip: `LEARNED -- 1`. The Journal
wing shows both utterances -- the first with no chip, the second with
`LEARNED -- 1` -- timestamped, with `LANDED IN Claude Code` and `41 MS`.

He switches to a Note editor. The text input has a MicButton. He clicks
it once (toggle, not hold), dictates a sentence, the text lands in the
Note. He returns to the Speak window; the Journal shows the Note
utterance with source `BROWSER`.

Every text input on the desk takes his voice. The mic is the OS, not a
feature.

## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Corrections stay on the machine | Constitution Article III | CorrectionStore writes to local SQLite only; no sync, no egress, no cloud backup |
| A correction never re-fires a delivery | Constitution Article IV.2 | The correction nudges the NEXT matching utterance's routing; it never replays or re-types a past utterance into a target |
| The mic on every input -- click to toggle | Constitution Article IV.1, owner ruling (MEMORY feedback_mic_click_to_toggle) | MicButton is a toggle (click once to start, click once to stop); never press-and-hold; the mic is an OS affordance on every text input |
| No counters of zero | UX-CANON.md rule A.8 | The LEARNED chip is absent when no correction applied; the Journal's TAUGHT count is absent at zero; the learning digest section is absent when corrections_made = 0 |
| Every verb the library Button | UX-CANON.md rule A.1 | `Wrong`, `OK`, `Teach`, `Review`, `Export`, `Forget` -- all library Button species |
| One egress vocabulary | UX-CANON.md, 170 settled (counsel M1) | `THIS DEVICE` on the Speak footer; the ENGINE row names its host |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names. The teach receipt is a token (`LEARNED`), not a sentence |
| No modals | UX-CANON.md rule A.4 | The teach row unfolds in-world beneath the RESULT row; the correction list is a section, not a dialog |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |

## D2 -- the faces (element by element, species named)

### (a) The RESULT row's teach loop

**Position:** below the RESULT row on the Speak face, inside the
`speak-result` section (SpeakFace.tsx:464-519). Unfolds when the owner
presses `Wrong` (the existing verdict mechanism).

**The existing flow** (170-04, already built):
- RESULT line: the final text at primary step + `OK` (Button ghost) +
  `Wrong` (Button ghost).
- When `Wrong`: the teach row unfolds -- CycleGadget (field: Delivery
  target / Intent) + StringGadget (correction value, with mic) + `Teach`
  (Button primary dense, loading while busy).
- POST /api/dictation/corrections with `{kind, text, value}` persists
  the correction (pipeline.py:978-997 -> CorrectionStore.record ->
  DictationCorrectionRepository).

**What 176 adds to the teach row:**
1. **The receipt after Teach.** When `Teach` succeeds, the teach row
   replaces itself with a receipt line: `LEARNED` (surface-token,
   success) + `applies to` (secondary step, muted) + the correction
   gist in quotes (secondary step, truncated 60ch). Species:
   surface-token[data-chip] for `LEARNED`, body step for the gist.
   The receipt fades after 5 s or on the next utterance (whichever is
   first).
2. **The correction chip on the RESULT row.** When the pipeline applied
   a correction on this utterance (the `corrected` field from
   `_apply_correction_nudge` in intent_router.py:190 or
   `apply_target_correction` in target_profile.py:126), the RESULT line
   shows: `LEARNED` (surface-token, success) + `N` (the times-applied
   count from the learning digest's `reach_for_gist`). Example:
   `LEARNED -- 1`. Absent when no correction fired (rule A.8).
3. **Tapping the correction chip** opens a Disclosure beneath the
   RESULT showing: the correction (key -> value in secondary mono), the
   Jaccard similarity score (secondary, 2 decimal places), the kind
   (intent / target as a muted token). Species: Disclosure,
   surface-token.

**Species used:** Button (primary, ghost), CycleGadget, StringGadget
(with mic), surface-token[data-chip], Disclosure.

**Widths:** 1440 -- the teach row is a single line (field cycle +
StringGadget fills + Teach). 393 -- the StringGadget wraps to a second
line; `Teach` sits at its trailing edge.

### (b) The JOURNAL wing as a SurfaceStream

**Position:** the Journal wing on the DictationCore window
(DictationCore.tsx:33, wings: Speak / Journal / Blocks).

**Today** (Journal.tsx): a SurfaceLedger with SurfaceStreamDay grouping.
Rows show time, transcript (primary), destination, ms, TAUGHT chip.
Loaded via polling (`useResource` at `/api/dictation/journal?limit=200`).
Search via StringGadget. No source filter. No real-time push.

**What 176 rebuilds:**

1. **Real-time push.** New entries arrive via the WebSocket bus
   (frame type `dictation.journal.entry`) within 1 s of the pipeline
   completing. The bus frame carries: id, source, raw_text,
   processed_text (final_text), total_ms, corrections_applied (boolean),
   intent_tag (block_id or null), target_profile. The frame is a read
   (Article V.1: watching is free). The Journal component subscribes on
   mount and prepends new entries to the top of the stream.

2. **Row grammar** (SurfaceLedgerRow, one per utterance):
   - Lead slot (52px): time at secondary mono step (HH:MM).
   - Primary (15/600): the transcript text (ellipsis, `min-width: 0`).
   - Cells:
     - `LANDED IN <target>` (secondary mono, muted; the target profile
       name or `DRY RUN`; absent when unknown).
     - `41 MS` (secondary mono; the total pipeline latency).
     - `LEARNED -- 1` (surface-token[data-chip], success; present ONLY
       when a correction applied to this utterance; the count is the
       correction's times-applied from `reach_for_gist`; absent when no
       correction fired -- rule A.8).
   - Trailing: source badge token (secondary mono, muted):
     `DICTATION` / `BROWSER` / `HOTKEY`.

3. **Filter tokens.** A LedgerFilterBar above the stream with flat
   tokens (UX-CANON.md rule D -- filters are flat tokens): `ALL` /
   `DICTATION` / `BROWSER` / `HOTKEY`. One-tap toggle; `ALL` is
   default. The filter applies to both the stream and the paginated
   history. Species: LedgerFilterBar (the existing flat-token filter
   species).

4. **Search.** A StringGadget (with mic by default) in the
   SurfaceLedger controls slot. Filters rows client-side over
   raw_text and final_text (LIKE match).

5. **Scroll-to-load.** The stream shows the most recent 50 entries.
   Scroll-up triggers a paginated load (`/api/dictation/journal?limit=50
   &before=<oldest_id>`) and prepends older entries. The total count is
   shown via `countToken` on the SurfaceLedger (e.g. `9 TODAY`).

6. **`Review` scrolls here.** The `Review` verb on the Speak footer
   (DictationCore.tsx:155) switches to the Journal wing (sets
   `wings.view` to `"journal"` instead of opening the Configure door).

**Species used:** SurfaceLedger, SurfaceLedgerRow, SurfaceStreamDay,
SurfaceState, LedgerFilterBar, StringGadget, surface-token[data-chip],
countToken, Button (ghost for Clear).

**Widths:** 1440 -- the row is a single line (time / transcript / LANDED
IN / MS / LEARNED / source). 393 -- LANDED IN and MS wrap under the
transcript; source stays trailing.

### (c) The LEARNED section (the corrections list)

**Position:** a new wing `Learned` on the DictationCore window,
appended after Blocks: Speak / Journal / Blocks / Learned. Or: a
SurfaceSection within the existing Memory configure panel
(Memory.tsx).

**Decision:** propose a new wing `Learned` for discoverability -- the
owner should not need to open Configure to see what the pipeline
learned. The owner decides on the canvas.

**Content** (SurfaceLedger, one row per correction):

1. **Row grammar** (SurfaceLedgerRow):
   - Primary (15/600): the correction's `key` (gist) at primary step.
   - Arrow: `->` (secondary mono, muted).
   - Value: the correction's `value` at primary step.
   - Cells:
     - Times applied: `N APPLIED` (secondary mono; from
       `reach_for_gist` over the journal; absent at zero -- rule A.8).
     - Kind: `INTENT` / `TARGET` (secondary mono, muted token).
   - Trailing verb: `Forget` (Button ghost danger) -- calls
     DELETE /api/dictation/corrections/{id} (pipeline.py:999-1007).

2. **Empty state:** absent (the wing/section is absent when
   corrections_made = 0 -- rule A.8). When shown with corrections: the
   wing is always visible.

3. **Count:** `countToken(corrections.length, "LEARNED")` on the
   SurfaceLedger caption. Example: `3 LEARNED`.

**Species used:** SurfaceLedger, SurfaceLedgerRow, Button (ghost),
surface-token, countToken.

**Widths:** 1440 -- the row is a single line (gist -> value / N APPLIED
/ kind / Forget). 393 -- value wraps under gist; Forget stays trailing.

### (d) The voice law's face: MicButton on every text input

**The census (recon, 2026-09-05 on branch feat/the-great-pass):**

| Species | mic default | Rendered instances | Coverage |
|---|---|---|---|
| StringGadget | `mic=true` (gadgets.tsx:243) | 89 | Built in |
| PadGadget | `mic=true` (gadgets.tsx:315) | ~10 | Built in |
| EditInPlace | `mic=true` (Surface.tsx:1070) | 6 | Built in |
| Explicit `<MicButton>` (standalone) | n/a | 33 placements across 29 files | Standalone placement |
| Raw `<input>` outside gadgets | no mic | 22 | GAP |
| Raw `<textarea>` outside gadgets | no mic | 9 | GAP |

The gadget species (StringGadget, PadGadget, EditInPlace) carry
MicButton by default. The gap is the 31 raw `<input>` + `<textarea>`
elements that live outside the gadget system. These are in:

- Component internals (MicButton.tsx's own input, combobox patterns,
  password fields, numeric inputs) -- some are legitimately
  non-dictatable.
- Older surfaces not yet migrated to the gadget system.

**What 176 does:**

1. **Census script** (`scripts/mic_census.py`): scans every `.tsx` file
   under `web/src/` for `<input`, `<textarea`, StringGadget, PadGadget,
   EditInPlace. Reports: total text inputs, covered (by gadget or
   explicit MicButton), uncovered, and the allowlist (with reasons).

2. **Ratchet guard** in `scripts/ux_canon_scan.py`: a new rule `A14`
   (voice law) counting text inputs without mic. Ceiling = allowlist
   size (password fields, the MicButton's own internal input, etc.).
   Non-dictatable inputs are named in the allowlist with reasons, as
   the A1 (raw button) allowlist does today.

3. **Migration.** Each uncovered raw `<input>`/`<textarea>` that accepts
   dictatable text is either:
   (a) replaced with StringGadget/PadGadget (preferred -- gains mic
       automatically), or
   (b) given an explicit `<MicButton>` beside it (when the surrounding
       layout prevents a gadget swap).

4. **Artboard.** One board at 1440 + 393 showing the MicButton
   placement per species: inside StringGadget (trailing), inside
   PadGadget (corner), inside EditInPlace (trailing in edit mode),
   standalone (beside the input). The artboard names the five inputs
   from the gap that are being migrated.

### (e) The desk answering the hand -- the full loop

**Position:** the Speak window, one session, no restart.

**The loop (shown once at each width):**

1. **Talk.** The owner clicks `Talk` (MicButton transport). He speaks.
   The utterance appears in the well.
2. **Land.** The pipeline runs. The RESULT row shows the final text.
   LANDS IN shows `Claude Code -- 41 MS`.
3. **Judge.** He presses `Wrong`. The teach row unfolds.
4. **Teach.** He types the correction, presses `Teach`. The receipt:
   `LEARNED -- applies to "ship the Q4 platform..."`.
5. **Speak again.** A similar phrase. The Jaccard matcher fires
   (corrections.py:70-94, threshold 0.5). The pipeline applies the
   correction (intent_router.py:206-229 or target_profile.py:126-151).
   The RESULT row shows the corrected text with the chip `LEARNED -- 1`.
6. **The Journal.** Both utterances appear in the Journal wing. The
   second carries the `LEARNED` token. The learning digest (if
   corrections > 0) shows the updated reach.
7. **The receipt outside Speak.** The Room's ask well, the Door's name
   field, a Note editor -- the MicButton is there. He dictates into the
   ask well; the Journal shows it with source `BROWSER`.

**At 1440:** the loop fills one vertical scroll of the Speak window.
**At 393:** the transport stacks; the teach row wraps; the Journal is
one wing-tap away.

## D3 -- the wire

### The correction store (grow past 20?)

**Today.** corrections.py: a ring buffer (`deque(maxlen=20)`,
corrections.py:34,112). The durable layer
(DictationCorrectionRepository, db/corrections.py) has no cap -- it
stores every correction ever taught. The in-memory ring is the fast
path; the DB is the persistence layer. On construction the store loads
the most recent `cap` rows from the DB (corrections.py:119-143).

**What 176 changes.** The ring cap stays at 20 for the in-memory nudge
path (the pipeline reads the snapshot on every run). But the Learned
wing reads from `list_for_display()` (corrections.py:192-214) which
queries the DB directly -- so the UI shows ALL persisted corrections,
not just the ring's 20. The `reach_for_gist` count
(dictation_learning.py:99-113) runs over the full journal, using the
same Jaccard threshold (0.5) the live matcher uses. A durable table
with applied counts is NOT added in 176 -- the count is computed on
read from the journal. A materialized `times_applied` column is a
future candidate if the journal grows large.

**Seams:**
- corrections.py:34 (`DEFAULT_CAP = 20`) -- the ring cap.
- corrections.py:112 (`deque(maxlen=self._cap)`) -- the ring.
- corrections.py:192-214 (`list_for_display`) -- the DB read path.
- dictation_learning.py:99-113 (`reach_for_gist`) -- the reach counter.

### The apply path

**Today.** The next dictation applies corrections in two places:

1. **Intent corrections** (intent_router.py:190,206-229):
   `_apply_correction_nudge()` is called after the LLM classifies. It
   takes the correction snapshot, calls `best_match_in(corrections,
   "intent", text, min_similarity=0.6)`. If a match is found AND the
   corrected block_id is valid, it either boosts the model's confidence
   (when the model agreed) or redirects to the corrected block (when the
   model disagreed). The nudge is recorded in `metadata["correction_nudge"]`.

2. **Target corrections** (target_profile.py:126-151):
   `apply_target_correction()` is called after target detection. It
   calls `best_match_in(corrections, "target", text, min_similarity=0.5)`.
   If a match is found AND the corrected target is a valid override
   option AND differs from the current pick, it returns the corrected
   profile.

Both paths take the correction snapshot from `dictation_runner.py:335-338`:
```
correction_snapshot = (
    corrections_store.snapshot()
    if corrections_store is not None and bool(getattr(pipeline_cfg, "corrections_enabled", False))
    else None
)
```

The snapshot is taken fresh at the start of every run. A correction
taught during one utterance is available for the next utterance in the
same session -- no restart required.

**What 176 adds.** The wire is already complete. 176 adds:
- The `corrected` flag on the journal row (so the Journal wing can show
  the LEARNED chip). The journal recorder (journal.py:111-157) already
  has access to the run's intent tag; the `corrected` field from the
  intent_router's metadata needs to be surfaced.
- The WebSocket bus frame `dictation.journal.entry` for real-time push.

**Seams:**
- dictation_runner.py:335-338 -- snapshot taken per run.
- intent_router.py:206-229 -- intent correction nudge.
- target_profile.py:126-151 -- target correction apply.
- journal.py:111-157 -- journal recording.
- pipeline.py:978-997 -- POST /api/dictation/corrections.

### The journal's durable rows and the stream route

**Today.** DictationJournalRecorder (journal.py:93-157) writes one row
per pipeline run through DictationJournalRepository. Fields: source,
transcript, final_text, intent, block_id, target_profile, project_root,
stage_ms, total_ms, rewrite_pass_ms, confidence, warnings, retention.
The journal is queried via GET /api/dictation/journal (pipeline.py,
further up in the file).

**What 176 adds.**
- A WebSocket bus frame `dictation.journal.entry` emitted by the
  recorder after a successful write. The frame carries the journal row's
  id, source, transcript, final_text, total_ms, target_profile,
  corrections_applied, intent_tag.
- Source filter on the GET route: `/api/dictation/journal?source=dictation`
  filters by the source field (VALID_SOURCES: dictation, dry_run,
  browser, hotkey).
- Pagination: `/api/dictation/journal?limit=50&before=<id>` for
  scroll-to-load.

**Seams:**
- journal.py:27 (`VALID_SOURCES`) -- valid source values.
- journal.py:111-157 (`DictationJournalRecorder.record`) -- the write.
- The bus emit point: after the `record()` call returns the stored row.

### The `Forget` verb

**Today.** DELETE /api/dictation/corrections/{id} (pipeline.py:999-1007)
calls `CorrectionStore.remove(id)` (corrections.py:216-229) which
deletes from the DB and reloads the ring.

**What 176 adds.** The Learned wing calls this route on `Forget`. No
wire change needed.

### The mic census script (the ratchet fence)

**New file:** `scripts/mic_census.py`. Scans `web/src/**/*.tsx` for text
input elements. Reports covered vs uncovered. Produces a JSON summary.

**Guard integration:** `scripts/ux_canon_scan.py` gains rule `A14`
(voice law). The rule counts `<input>` and `<textarea>` elements in
.tsx files that do not sit inside a StringGadget, PadGadget, or
EditInPlace AND do not have an explicit `<MicButton>` nearby (within the
same component function). Non-dictatable inputs (password, MicButton's
own internal input, numeric pickers) are named in the allowlist.

**Seams:**
- scripts/ux_canon_scan.py -- the scanner's rule registry.
- tests/ux_canon_ceiling.json -- the ceiling file.
- tests/unit/test_ux_canon_ratchet.py -- the ratchet test.

## D4 -- counsel's hunts

1. **A correction that rewrites unrelated text.** The Jaccard threshold
   (0.5 on the intent path at intent_router.py:213; 0.5 on the target
   path at target_profile.py:131) is the only guard against false
   positives. A correction with a short, common gist (e.g. "the") would
   match nearly everything. Hunt: the teach flow should warn when the
   gist is shorter than 3 tokens (the `_tokens` function in
   corrections.py:58-59 produces the token set). A gist below 3 tokens
   gets a cautionary receipt: `LEARNED -- short phrase, may match
   broadly`. Not a refusal (Article V.3: refusal is by name).

2. **A journal entry that leaks a secret.** The journal recorder already
   runs `filter_secret()` (journal.py:52-59) on transcript and
   final_text, using `looks_like_secret` from
   `project_doc_suggestions.py`. The correction store also checks
   `looks_like_secret` on both gist and value (corrections.py:152-153).
   The seam: the WebSocket bus frame for `dictation.journal.entry`
   should NOT carry redacted text either -- the frame must run through
   the same `filter_secret` before emission.

3. **A mic that holds instead of toggles.** The MicButton species
   (MicButton.tsx / components/MicButton.tsx) is a click-to-toggle by
   design. The transport variant on the Speak face uses `onState`
   callbacks. Hunt: confirm that no new MicButton placement introduced
   in 176 overrides the toggle behavior with a `hold` or `press` prop.

4. **A counter of zero on LEARNED.** The LEARNED chip on a RESULT row
   must be absent when no correction applied. The LEARNED count on the
   Learned wing must be absent at zero. The Journal's TAUGHT count at
   zero is already handled by `countToken` (which returns null at zero).
   Hunt: the correction chip's rendering condition must check
   `corrections_applied === true`, not `corrections_applied !== null`.

## D5 -- the walk

The owner's attended walk on his real desk, both widths. Seven beats:

1. **Talk.** He dictates a sentence. It lands correctly in the RESULT
   row. LANDS IN reads the target name + latency.
2. **Wrong landing.** He dictates a sentence. The pipeline gets a word
   wrong. He presses `Wrong`.
3. **Teach.** The teach row unfolds. He types the correction. He
   presses `Teach`. The receipt shows `LEARNED -- applies to "..."`.
4. **The same phrase.** He dictates a similar sentence. The correction
   fires. The RESULT row shows the corrected text with the `LEARNED`
   chip.
5. **The Journal.** He switches to the Journal wing. Both utterances
   appear. The second carries the LEARNED token. Source filter:
   `DICTATION`.
6. **The mic on the Room.** He opens a Room (or a Note). The ask well's
   text input has a MicButton. He clicks it (toggle), dictates a
   sentence, the text lands.
7. **The mic on the Door.** He opens the Door. The name field has a
   MicButton. He dictates a project name.

Both widths. The stopwatch per face. His verdict.

## Sizes

| Story | Size | Notes |
|---|---|---|
| 01 The design | S | Artboards only; the faces are designed above |
| 02 The first correction | M | The teach receipt + correction chip + learning digest. Wire exists; face is new |
| 03 The journal stream | M | WebSocket push + source filter + scroll-to-load. Journal exists; stream is new |
| 04 The voice law | M | Census + migration of ~31 raw inputs + ratchet guard |
| 05 The desk answering the hand | S | Integration of 02+03+04 into the full loop; mostly wiring |
| 06 The walk | S | Owner's attended walk; no code |
| 07 The docs | S | Doc updates for the new faces |
| 08 The close | S | Full suite + PR + merge |
