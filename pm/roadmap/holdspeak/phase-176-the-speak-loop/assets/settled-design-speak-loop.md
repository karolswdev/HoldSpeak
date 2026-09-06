# The Speak Loop -- the settled design (Phase 176)

> **SETTLED against main @7a47904e (2026-09-06) -- counsel BOUNCED
> (assets/counsel-on-design-176.md); the orchestrator RULED R1--R14 and
> this document is rewritten to those rulings. The owner's word on the
> canvas pending.**

> **ON THE CANVAS (2026-09-06)** -- seventeen boards published at
> https://claude.ai/code/artifact/36f77f70-fb03-461d-a0dd-8b43c4682e63 ;
> counsel's re-read RATIFY-W-C, N1--N5 paid (assets/counsel-on-design-176.md);
> his word on the canvas gates the build; his word gates the merge.

Every file:line below was verified against the tree on
`feat/the-speak-loop` @ `7a47904e` (= main after 170--175 merged). Two
change ledgers ride at the end: the 2026-09-05 draft diff, and the
addendum recording rulings R1--R14.

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 6): dictation as
a daily tool -- the correction taught once and kept, the journal as a
stream, the voice law on every input, the desk answering the hand.

The face canon binds (docs/internal/UX-CANON.md). The 170 Speak face
(settled-design-four-faces.md section 2) is the ratified shape. The
Constitution articles III (local first), IV (voice first-class), V
(consent), VI (honest by construction) and XI (kernel receipts) bind
every line below.

## D0 -- the Tuesday moment

He dictates into his status file: *"postgress needs a version bump
before Charter ships."* The text lands in the utterance well. The RESULT
row shows the final text. It landed wrong -- he said **PostgreSQL**, the
transcript heard **postgress**.

He presses `Wrong`. The teach row unfolds. FIELD reads `TEXT` (the
default). Beneath it, ONE StringGadget pre-filled with the landed text.
He edits the one word to `PostgreSQL` and presses `Teach`. The desk
diffs heard against said at word level, finds one differing span, and
stores a word rule. The receipt: `TAUGHT · postgress -> PostgreSQL`.

Next time he says the word, the rule fires deterministically on the raw
transcript before anything else runs -- so the rewrite pass and the
router both see `PostgreSQL`. The RESULT row carries the chip
`APPLIED`. The Journal wing shows both utterances -- the first bare, the
second chipped -- timestamped, with `LANDED IN Claude Code` and `41 MS`.

When the landing is a *routing* mistake instead -- the utterance went to
the Browser when it should have gone to Claude Code -- he cycles FIELD
to `TARGET` and **picks** `Claude Code` from the real list of seven
profiles. The receipt: `TAUGHT · Claude Code`. The routing kinds match
by Jaccard as they always have; the text kind does not.

He switches to a Note editor. The text input has a MicButton. He clicks
it once (toggle, not hold), dictates a sentence, the text lands in the
Note. He returns to the Speak window; the Journal shows the Note
utterance with source `BROWSER`.

Every text input on the desk takes his voice. The mic is the OS, not a
feature.

## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Corrections stay on the machine | Constitution Article III | CorrectionStore writes to local SQLite through DictationCorrectionRepository (`holdspeak/db/corrections.py:29`); no sync, no egress, no cloud backup |
| A correction never re-fires a delivery | Constitution Article IV.2 | A correction changes the NEXT utterance's words or routing; it never replays or re-types a past utterance into a target. `Replay` (`Journal.tsx:102-104`) is preview-only and journals nothing (`pipeline.py:1236`, `journal=None`) |
| **The text kind is a correction, not a stage** | This design's carve (R1) | The `text` kind is applied at the existing transcript seam inside `Pipeline.run` (`plugins/dictation/pipeline.py:98`, before the stage loop at `:101`). It emits no `StageResult`, no `stage_ms` entry, no `requires_llm` flag, and adds nothing to the pipeline's stage list. It is a correction kind with a deterministic apply path -- not a new pipeline stage |
| The mic on every input -- click to toggle | Constitution Article IV.1, UX-CANON.md section B, owner ruling (MEMORY feedback_mic_click_to_toggle) | MicButton is a toggle (click once to start, click once to stop); never press-and-hold; the mic is an OS affordance on every text input |
| One mic authority at a time | Constitution Article IV.3 | The Speak face's `Talk` transport is that face's sole mic; the utterance well takes `mic={false}` (R13) |
| Watching is free | Constitution Article V.1 | The `dictation.journal.entry` bus frame, the journal read, the applied counts and the learning digest are reads: no admission, no receipt beyond the row already written |
| Refusal is by name | Constitution Article V.3 | A one-token gist on a routing kind is refused `REFUSED · ONE WORD`; a secret-like teach is refused `REFUSED · SECRET`; a text teach with no edit reports `NO CHANGE`. No silent no-op, no caution token that the arithmetic does not support (R7) |
| Honest by construction | Constitution Article VI | Every count on a face is a count of something that happened. The chip and the Learned wing's `N APPLIED` read a stored per-run fact, never a read-time "would match" (R2, R3) |
| Ledger not gate | Owner ruling (MEMORY feedback_ledger_not_gate_rule) | Teaching is receipted, never gated; `Forget` is one verb with a one-step in-world confirm |
| A replacing face keeps its verbs | 175 law | The rebuilt Journal row keeps `Replay` / `Copy` / `Delete` in its opened state (R11); the rebuilt Learned wing keeps `Forget` |
| No counters of zero | UX-CANON.md rule A.8 | The `APPLIED` chip is absent when nothing fired; `N APPLIED` is absent at zero; the Journal wing carries no caption count at all (the footer's `N TODAY` is the one count per face) |
| Every verb the library Button | UX-CANON.md rule A.1 | `Wrong`, `OK`, `Teach`, `Review`, `Export`, `Forget`, `Replay`, `Copy`, `Delete` and the four source filter tokens -- all library Button species; `ConfirmVerb` (`Surface.tsx:1188-1228`) already renders one |
| The name said once per face | UX-CANON.md rule A.7 | One word, one meaning (R8): the wing is `Learned`, the receipt is `TAUGHT`, the chip is `APPLIED`. `LEARNED` never appears as a receipt or a chip. The count `N TODAY` is said once, in the footer |
| The lead slot is the emblem | UX-CANON.md section B (SurfaceLedgerRow, 52px lead slot) | The Journal row's lead slot carries the time; the Learned row's lead slot carries the kind token (`TEXT` / `INTENT` / `TARGET`); neither is a free-text column |
| Egress where egress happens | UX-CANON.md rule A.9, Article III | `THIS DEVICE` on the Speak footer (`DictationCore.tsx:142`); the ENGINE row names its host via `EgressChip` (`SpeakFace.tsx:638`). The Journal, the Learned wing and the bus frame carry no egress chip because nothing there leaves the machine -- absence is the signal |
| Receipts wear human labels | UX-CANON.md section E.4 (no raw snake_case on a face), rule A.3 | The kind renders `TEXT` / `INTENT` / `TARGET`; the routing value renders its label (`Claude Code`), never its id (`claude_code`); the source renders `DRY RUN`, never `dry_run`. Label sources named in D3 |
| Honest states, plain reasons | UX-CANON.md rule A.10 | The refusal receipt reads the response's real key (`taught ?? recorded`, R4); a refused teach writes nothing and says so |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names. The teach receipt is a token pair, not a sentence -- this retires the footer sentence `"Taught · reaches similar dictations"` (`useSpeakDeck.ts:311`) |
| No modals | UX-CANON.md rule A.4 | The teach row unfolds in-world beneath the RESULT row (`SpeakFace.tsx:485-517`); the Learned list is a wing, not a dialog |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |

## D2 -- the faces (element by element, species named)

### (a) The RESULT row's teach loop

**Position:** below the RESULT row on the Speak face, inside the
`speak-result` section (`SpeakFace.tsx:464-519`, rendered by `ResultRow`
at `:438-520`, mounted at `:315-328` only when `deck.result` is truthy).
Unfolds when the owner presses `Wrong` (`:477-483` sets
`verdict="wrong"`; the row is gated at `:485`).

**The existing flow (verified on main, built by 170-04):**
- RESULT line (`SpeakFace.tsx:465-484`): the final text
  (`result.final_text ?? result.text ?? result.output`, `:461`) at
  primary step + `OK` (Button ghost, `:467-476`) + `Wrong` (Button
  ghost, `:477-483`). `OK` only announces `"Marked OK"`; it writes
  nothing.
- When `Wrong`: the teach row unfolds (`:485-517`) -- CycleGadget
  `Correction field` (`Delivery target` / `Intent`, `:491-499`) +
  StringGadget `Correct value` (`:500-505`) + `Teach` (Button primary
  dense, `:506-515`).
- **This flow is dead as built.** The StringGadget takes free text, but
  `intent` requires a loaded block id (`intent_router.py:215`) and
  `target` one of seven profile ids (`target_profile.py:26-34`, checked
  at `:149`). The placeholder says `Terminal`; the only accepted value
  is `terminal_shell` (`SpeakFace.tsx:504`). Anything the owner types
  is stored and never fires. That is P0-1.
- `Teach` calls `deck.teach()` (`useSpeakDeck.ts:291-318`), which
  prefers `POST /api/dictation/journal/{journal_id}/correct` when the
  run returned a `journal_id` (`_helpers.py:760, 888`) and falls back to
  `POST /api/dictation/corrections` otherwise (`:294-310`).
- The primary route teaches from **the entry's transcript**, not from
  what he typed: `recorded = store.record(kind, entry.transcript,
  value)` (`pipeline.py:1154`). What he types is the *value*.
- The receipt today is a **sentence on the footer**
  (`useSpeakDeck.ts:311`), surfaced through `ReceiptContext` into
  `SurfaceFooter` (`DictationCore.tsx:114-122, 140-149`). Rule A.3
  bounce.

**The teach row 176 builds (R1):**

**FIELD** -- a CycleGadget over three kinds: `TEXT` · `INTENT` ·
`TARGET`. `TEXT` is the default (the Tuesday mistake is a words
mistake).

**When FIELD = `TEXT`:** ONE StringGadget (mic default true),
pre-filled with the **RAW TRANSCRIPT** -- what the mic heard, before the
rewrite pass -- not the landed text (N2). He edits it to what he SAID.
On `Teach` the desk diffs **heard** (the raw transcript) against
**said** (his edit) at word level.

This is not a nicety: the rule is applied to `utt.raw_text`
(`plugins/dictation/pipeline.py:98`), so a key harvested from
`final_text` would be matched against a string it never equals whenever
any stage rewrote the text -- which is the rewrite pass's whole job --
and would never fire. The run response carries no raw transcript today
(`_helpers.py:750-770`, `final_text` at `:757`; `:883-896`, `final_text`
at `:894`); story 02 adds one field beside it, and the StringGadget
pre-fills from that.

| Diff outcome | Rule stored | Receipt |
|---|---|---|
| No difference | nothing | `NO CHANGE` |
| Exactly one contiguous differing span, spanning at most half the tokens | a **word rule**: `key` = the heard span, `value` = the said span | `TAUGHT · <heard span> -> <said span>` |
| More than one span, or one span over half the tokens | a **whole-phrase rule**: `key` = the full heard text, `value` = the full said text (it fires only on that exact sentence) | `TAUGHT · <heard> -> <said>` (both truncated 40ch) |

**When FIELD = `INTENT` or `TARGET`:** a **pick over the real enum** --
never free text. Species: CycleGadget when the option count is small
(the six target profiles), the library's picker species when a desk
carries many blocks. The label is on the face, the id is on the wire.

**`TARGET` offers SIX ids, never `auto` (N1):** `claude_code`,
`codex_cli`, `terminal_shell`, `browser`, `editor`, `chat`. `auto` IS a
member of `TARGET_PROFILE_OVERRIDE_OPTIONS` (`target_profile.py:26-34`)
and so clears the membership guard at `:149` -- and then
`_profile("auto", ...)` raises `KeyError` on `labels[profile_id]`
(`target_profile.py:272-296`, the lookup at `:291`), inside the live
typing path (`dictation_runner.py:389`, `:565`; `_helpers.py:811`, none
of which guards). It is also meaningless as a correction ("route this
to: whatever you were going to pick"). Story 02 additionally belt-fixes
`_profile` so no member of its own option set can raise.

The face prints the label map's string **verbatim** -- `Terminal shell`,
not `Terminal` (`target_profile.py:280-288`). There is no design-owned
label table (C12 note).

A gist of one token is refused by name: `REFUSED · ONE WORD` (R7),
enforced in `CorrectionStore.record` (`corrections.py:145-165`) so both
routes and the MCP surface inherit it -- never on the face (C7 note).
The receipt: `TAUGHT · <label>` (e.g. `TAUGHT · Claude Code`).

**FIELD casing:** the caption step is 11 mono uppercase (canon C), so
the cycle renders `TEXT` · `INTENT` · `TARGET` in uppercase on every
board.

**The receipts (R8 -- one word, one meaning):**
1. **After `Teach`:** the teach row replaces itself with the receipt
   line above -- `TAUGHT` as a surface-token (success) plus the pair or
   the label at secondary step. It fades after 5 s or on the next
   utterance. The footer sentence at `useSpeakDeck.ts:311` is retired.
2. **Refusals** are named, never smoothed (Article V.3, R4/R7): `NO
   CHANGE` · `REFUSED · ONE WORD` · `REFUSED · SECRET`. The face reads
   `taught ?? recorded` from the response, because the two routes use
   different keys (`pipeline.py:1195` vs `:997`).
3. **The `APPLIED` chip on the RESULT row.** When one or more stored
   rules fired on this utterance, the RESULT line shows `APPLIED`
   (surface-token, success) with no count. Absent when nothing fired
   (rule A.8). It renders from the run's own `corrections_applied`
   fact, never from a read-time "would match" (R2).
4. **Tapping `APPLIED`** opens a Disclosure beneath the RESULT, one
   block per rule that fired:
   - text rule: `HEARD <span>` / `SAID <span>`
   - routing rule: `WHEN <gist>` / `ROUTE <label>` / `MATCH 0.50`
     (the honest Jaccard score, two decimals -- routing only; a text
     rule is exact-phrase and has no score)
   Species: Disclosure, surface-token. No `KEY` / `VALUE` wire words.

**The utterance well takes `mic={false}` (R13).** `Talk`
(`SpeakFace.tsx:352`) is this face's mic authority (Article IV.3). The
built well is a bare `PadGadget` (`:296-308`) whose `mic` defaults true
(`gadgets.tsx:315`), so today a third mic renders beside `Talk` and
`Open mic` (`:388`). That is a 170 drift; the boards already draw the
well mic-less. Paid in story 05; the well joins the census allowlist
with the reason "the `Talk` transport is this face's mic authority".

**Species used:** Button (primary, ghost), CycleGadget, StringGadget
(with mic), surface-token[data-chip], Disclosure.

**Widths:** 1440 -- the teach row is a single line (FIELD cycle + the
StringGadget or the pick + `Teach`). 393 -- the value control wraps to a
second line; `Teach` sits at its trailing edge.

### (b) The JOURNAL wing as a SurfaceStream

**Position:** the Journal wing on the DictationCore window
(`DictationCore.tsx:32-36`, `WINGS = Speak / Journal / Blocks`; mounted
at `:102-111`).

**Today** (`Journal.tsx`, 258 lines): a `SurfaceLedger` (`:210-255`)
with `SurfaceStreamDay` grouping (`:237-253`). Rows (`JournalRow`,
`:31-147`) show time in the lead slot (`:68-70`), transcript as primary
(`:71`), `→ destination` (`:76-78`), `N ms` (`:79-81`) and a
`TAUGHT · N SIMILAR` cell gated on `row.corrected` (`:82-91`). Opening a
row reveals `EditInPlace` (`:95-100`) plus `Replay` / `Copy` / `Delete`
(`:101-121`). Loaded once per mount via
`useResource("/api/dictation/journal?limit=200")` (`:150-153`);
`useResource` (`pages/pageSupport.tsx:31-61`) has **no polling** -- no
interval and no push, so a new utterance never appears until the wing
remounts. Search is a StringGadget (`:214-219`) filtering client-side on
`transcript` only (`:158-164`). Counts: `countToken(todayCount,"TODAY")`
and `countToken(taughtCount,"TAUGHT")` (`:211`). **No source filter
control. No pagination. No real-time push.**

**What 176 rebuilds:**

1. **Real-time push.** New entries arrive via the existing runtime
   WebSocket bus as frame type `dictation.journal.entry` within 1 s of
   the pipeline completing. The frame carries: id, source, transcript,
   final_text, total_ms, `corrections_applied`, `taught_from`,
   intent_tag (block_id or null), target_profile. The frame is a read
   (Article V.1). The Journal subscribes with
   `useRuntimeBus().subscribe` (`web/src/runtime/RuntimeBus.tsx:106-111`)
   on mount and prepends new entries. It rides the SAME mechanism every
   other live frame uses (D3 "The bus seam"); no new socket, no new
   transport. Note for story 03: `useRuntimeBus` throws outside a
   provider (`RuntimeBus.tsx:106-111`), so any new Journal test wraps in
   `RuntimeBusProvider` or mocks the module the way
   `web/src/pages/cores/LiveCore.test.tsx:37-38` does.

2. **Row grammar** (SurfaceLedgerRow, one per utterance):
   - Lead slot (52px): time at secondary mono step (HH:MM) -- as today.
   - Primary (15/600): the transcript text (ellipsis, `min-width: 0`).
   - Cells:
     - `LANDED IN <target>` (secondary mono, muted; the target profile
       label or `DRY RUN`; absent when unknown). Replaces today's
       `→ <destination>` (`Journal.tsx:76-78`).
     - `41 MS` (secondary mono, uppercase -- today it renders lowercase
       `41 ms`, `:80`).
     - `APPLIED` (surface-token[data-chip], success; present only when
       this row's stored `corrections_applied` is non-empty; **no
       count**). Replaces today's `TAUGHT · N SIMILAR` (`:82-91`),
       which is read-time and counts similar transcripts, not firings
       (R2, R3).
     - `TAUGHT` (surface-token, muted; present only on the row he
       taught FROM -- the row that was wrong). Two facts, two words
       (R5, R8). **It stands (N5a):** the token is required here and in
       D5 beat 5, and the Journal boards must draw it on the taught row
       (14:19 on `JournalStream`), not leave it bare.
   - Trailing: source badge token (secondary mono, muted), human-labelled:
     `DICTATION` / `DRY RUN` / `BROWSER` / `HOTKEY` (never `dry_run`).

3. **The opened row keeps its verbs (R11).** Clicking a row opens it in
   place exactly as today: `EditInPlace` over the transcript
   (`Journal.tsx:95-100`) plus `Replay` (Button dense) · `Copy` (Button
   ghost dense) · `Delete` (ConfirmVerb) (`:101-121`), and the replay
   preview block beneath (`:122-144`). No verb is dropped; the 175 law
   binds. **The preview's two sentences are tokenised, not inherited**
   (C11 note): `Replay — preview only` (`:124-126`) becomes `REPLAY ·
   PREVIEW`, and `The replay completed without text.` (`:127-130`)
   becomes `NO TEXT`. Keeping the verbs is the law; keeping the prose
   would re-ratify an A.3 defect.

   **`Clear` is withheld on the quiet state** -- there is nothing to
   clear, and a verb that does nothing is a lie (rule A.11). It returns
   as soon as the ledger holds a row.

4. **Filter tokens (R6).** Four flat tokens above the stream:
   `ALL` / `DICTATION` / `BROWSER` / `HOTKEY`; one-tap toggle; `ALL`
   default. **`LedgerFilterBar` is NOT the species.** It renders a query
   `<input>` (`LedgerFilter.tsx:112`), a `matchCount/total` count
   (`:120-122`), two raw `<button>`s (`:124`, `:147`) and *removable*
   chips (`:134-155`), and it returns `null` below 5 items (`:104`,
   `SPARSE_THRESHOLD = 5` at `sparse.ts:4`). It also has zero consumers
   in `web/src` today, and `surface/contract.md` names no flat-token
   filter species at all. The library therefore lacks one.
   **The composition 176 uses** is the one already ratified on the
   Room's history wing (`ProjectRoomCore.tsx:1550-1566`): a
   `role="group"` span of library `Button` (ghost, dense) with
   `data-filter-active` + `aria-pressed`, sitting in the
   `SurfaceLedger` `controls` slot. Per canon B it is PROMOTED into the
   library as a species and documented in
   `web/src/desk/surface/contract.md`, then used. **The bar never
   returns null**: there is no sparse rule on it; it is present on the
   quiet state, showing all four tokens over an empty stream. It shows
   no `matchCount/total` -- that would be a second count on the face.

5. **Search.** The existing StringGadget (`Journal.tsx:214-219`, mic
   default true) stays, widened to match `final_text` as well as
   `transcript`.

6. **Scroll-to-load.** The stream shows the most recent 50 entries.
   Scroll-up triggers a paginated load
   (`/api/dictation/journal?limit=50&before=<oldest_id>`) and appends
   older entries.

7. **No caption count.** The SurfaceLedger caption carries **no** count
   token. The footer already renders `N TODAY`
   (`DictationCore.tsx:125, 144-149`); saying it twice on one face
   breaks A.7. The `countToken(...)` pair at `Journal.tsx:211` is
   dropped.

8. **Two empty states, two true lines** (A.3's single sanctioned
   exception):
   - all-time empty (nothing ever spoken): the token `NOTHING SPOKEN`.
   - a filter or search matching nothing: `NOTHING MATCHES` with the
     filter tokens still present so he can widen it.
   Today one line (`No dictations on this device`, `Journal.tsx:233`)
   covers both, and it is false in the second case.

9. **`Review` switches to the Journal wing.** The `Review` verb on the
   Speak footer (`DictationCore.tsx:152-158`) today calls
   `wings.setDoorOpen(true)` (`:155`), which opens the **Configure
   door** (`Configure()` at `:42-53`) -- the wrong thing. 176 points it
   at the Journal wing (`wings.setView("journal")`). The verb is kept,
   not retired: a working verb is never dropped, and the gear remains
   the way to Configure.

**Species used:** SurfaceLedger, SurfaceLedgerRow, SurfaceStreamDay,
SurfaceState, the promoted flat-token filter species, StringGadget,
EditInPlace, surface-token[data-chip], Button, ConfirmVerb.

**Widths:** 1440 -- the row is a single line (time / transcript / LANDED
IN / MS / APPLIED / source). 393 -- LANDED IN and MS wrap under the
transcript; source stays trailing.

### (c) The Learned wing (what the desk knows)

**Today.** The corrections list is `Memory()`
(`web/src/pages/cores/dictation/Memory.tsx:60-111`), mounted **inside
the Configure door** (`DictationCore.tsx:42-53`), so the only path to
what the pipeline learned is the gear. It is a `GadgetTable` (`:82-97`)
with head `Kind | Gist | Value | Reach`, verb
`ConfirmVerb label="×" confirmLabel="Forget?"` (`:90-96`) calling
`DELETE /api/dictation/corrections/{id}` (`:64-70`). Beside it a
"Learning digest" group (`:100-108`) renders
`WEEK · TAUGHT n · CORRECTED n · REACHED n`, or `WEEK · NO CORRECTIONS`
at zero (`:24-58`).

**A live defect the rebuild must fix.** `Memory.tsx:86` reads
`row.gist`, but the route returns the field as `key`
(`corrections.py:200-211`; the route adds only `similar`,
`pipeline.py:930-931`). The GIST column renders `—` for every row on
the owner's desk today.

**Position (176).** A new wing `Learned` on the DictationCore window
(`DictationCore.tsx:32-36`), appended after Blocks: Speak / Journal /
Blocks / Learned. `useCoreWings` (`:56`) takes the array, so a fourth
wing needs no shape change. The digest group stays in the Configure
door; the corrections table moves out. The owner decides wing-vs-gear
on the canvas.

**Content** (SurfaceLedger, one row per correction):

1. **Row grammar** (SurfaceLedgerRow):
   - Lead slot (52px): the kind as a human token, `TEXT` / `INTENT` /
     `TARGET` (secondary mono, muted).
   - Primary (15/600): the correction's `key` -- the heard span for a
     text rule, the gist for a routing rule.
   - Arrow: `->` (secondary mono, muted).
   - Value: the said span (text) or the routed **label** (routing) at
     primary step. Never a raw id (E.4; label sources in D3).
   - Cell: `N APPLIED` (secondary mono) -- **a real count of firings**:
     the number of journal rows whose stored `corrections_applied`
     contains this correction's id (R3). The teaching utterance is not
     one of them. Absent at zero (rule A.8). **It counts the RETAINED
     journal:** every journal write prunes to `retention`
     (`db/journal.py:93-94`, default 500), so this number can go
     **down** over time as old rows age out. That is honest and said
     here rather than discovered on his desk (C3 note).
     `reach_for_gist` is not
     shown on any face.
   - Trailing verb: `Forget` -- a `ConfirmVerb` with the word, not the
     `×` glyph, calling `DELETE /api/dictation/corrections/{id}`
     (`pipeline.py:999-1007`).

2. **Controls slot:** a search StringGadget (mic default true) over key
   and value. (The boards draw it; D2(c) now specifies it.)

3. **No caption count (N5b).** The Learned wing carries **no** count
   token on its SurfaceLedger caption. D1 rules that `N TODAY` is said
   once, in the footer, and D2(b).7 drops the Journal's caption for
   exactly that reason; the same law binds both wings. **The tab is the
   name, the rows are the count.** The earlier `countToken(n,
   "LEARNED")` is struck -- it also made `LEARNED` appear twice on one
   face (wing tab + caption), which is the very A.7 defect R8 paid.

4. **Empty state:** ONE true line, no zero token.

**Species used:** SurfaceLedger, SurfaceLedgerRow, StringGadget,
ConfirmVerb (library Button), SurfaceState, surface-token. No
`countToken` on this face (N5b).

**Widths:** 1440 -- the row is a single line (kind / key -> value /
N APPLIED / Forget). 393 -- value wraps under key; Forget stays
trailing.

### (d) The voice law's face: MicButton on every text input

**The census** (recomputed 2026-09-06 on this tree; full working in
`assets/mic-census-176.md`):

| Species | mic default | Render sites | Coverage |
|---|---|---|---|
| StringGadget | `mic=true` (`gadgets.tsx:243`; mic at `:298-299`, suppressed for `type="password"`) | 97 | Built in |
| PadGadget | `mic=true` (`gadgets.tsx:315`; mic at `:356-357`) | 16 | Built in |
| EditInPlace | `mic=true` (`Surface.tsx:1070`; mic at `:1169-1174`) | 6 | Built in |
| Standalone `<MicButton>` | n/a | 30 across 26 faces (33 total, 3 library-internal) | Standalone placement |

| Measure | Count |
|---|---|
| Raw `<input>` + `<textarea>` in `web/src/**/*.tsx` (excl. `*.test.*`, `_parked/`) | **44** |
| Covered (library-species internal, or an explicit MicButton in the same component) | **17** |
| Uncovered dictatable -- **THE GAP** | **8** |
| `mic={false}` opt-outs on mic-bearing gadgets | **14** (9 restore, 4 allowlist, 1 park) |
| **The allowlist: 19 raw + 4 opt-outs** | **23** |
| **176-04's real work** | **17 sites** (8 raw + 9 opt-outs) |

The eight uncovered raw elements: `LedgerFilter.tsx:112`,
`ThreadComposer.tsx:1060`, `ThreadPullout.tsx:211`,
`ThreadPullout.tsx:1634`, `ThoughtContextPicker.tsx:191`,
`ThoughtDocumentPane.tsx:90`, `ThoughtWorkspaceWindow.tsx:415`,
`NotePullout.tsx:409`. All eight are free text.
`ThoughtDocumentPane.tsx:90` is a comma-separated tag field -- it gets
the mic (the law is every text input) and is expected to read badly with
spoken punctuation. The nine opt-outs to restore: `FirstWords.tsx:413`,
`WorkbenchWindow.tsx:350`, `PeopleCore.tsx:242`, `:568`, `:585` (x2),
`:677`, `:696`, `:713`. A tenth opt-out is ADDED by R13:
`SpeakFace.tsx:296-308` (the utterance well) takes `mic={false}` with
the reason "the `Talk` transport is this face's mic authority (Article
IV.3)" -- which makes the allowlist **24** once story 05 lands. Until
then the design's number is 23.

The walk's beats 6 and 7 (the Room's ask well `ProjectRoomCore.tsx:1428`
+ MicButton `:1442`; the Door's outcome field `DoorCore.tsx:408` +
MicButton `:417`) are **already covered on main** -- the walk verifies
them, it does not wait on new work.

**What 176 does:**

1. **Census script** (`scripts/mic_census.py`): the working script that
   produced `assets/mic-census-176.md`, made permanent -- scans every
   `.tsx` under `web/src/` (excluding `*.test.*` and `_parked/`) for
   `<input`, `<textarea`, StringGadget, PadGadget, EditInPlace and
   `mic={false}`. Reports total, covered, uncovered, allowlist.

2. **Extend the scanner's EXISTING rule `mic`** -- not a new `A14`.
   `scripts/ux_canon_scan.py` already carries rule id `mic` ("Missing
   MicButton on text input", weight 1 at `:100`, file-level coverage
   flag at `:178-180`, text-input flag at `:360-363`, emitted at
   `:409-414`), ceiling `mic: 6` in `tests/ux_canon_ceiling.json`.
   **Four defects to fix (R9):**
   (i) the flag matches `<(?:input|StringGadget|TextInput)\b`
       (`:361`) and **never `<textarea`** -- three of the eight gap
       sites (`ThreadComposer.tsx:1060`,
       `ThoughtWorkspaceWindow.tsx:415`, `NotePullout.tsx:409`) are
       invisible to the rule today;
   (ii) it counts `<StringGadget` as an uncovered input, when a
       StringGadget is covered by definition -- per-element counting
       targets raw `<input`/`<textarea` plus `mic={false}` gadget
       instances only;
   (iii) it is file-scoped (one violation however many bare inputs);
   (iv) it is gated on `classify_face`, so non-face files are never
       checked -- dropping the gate widens the scan to the census's
       scope.
   The port is small: the emit moves into the line loop and keys a
   `path:line` allowlist, the shape rule `B` already uses
   (`ux_canon_scan.py:313-316`) and A1's allowlist already uses
   (`tests/unit/test_ux_canon_ratchet.py:104-125`).
   **The honest claim for the ceiling:** `mic: 0` with a **23-entry
   reasoned allowlist**, not "0 because every input has a mic". The six
   faces holding the current ceiling resolve as: `LedgerFilter` and
   `PeopleCore` fixed, `UtteranceWell` parked, and `ChoiceCardGroup`
   (radio) / `CalendarSnapshotReviewCore` (HH:MM) / `SettingsCore`
   (glyph) allowlisted. The census's counting scope matches the
   scanner's after the gate drops, so the number should not surprise.
   Rule `B` (raw controls, `:306-316`) keeps its ceiling of 34.

3. **Migration.** Each uncovered element is either
   (a) replaced with StringGadget/PadGadget (preferred -- gains the mic
       automatically), or
   (b) given an explicit `<MicButton>` beside it (when the surrounding
       layout prevents a gadget swap).
   The nine `mic={false}` opt-outs drop the prop.
   `LedgerFilter.tsx:112` is a library species: one fix covers every
   ledger filter on the desk.

4. **Park 170's orphans.** `pages/cores/dictation/UtteranceWell.tsx`,
   `InstrumentStrip.tsx`, `AimRow.tsx`, `ResultPanel.tsx` are not in the
   barrel (`pages/cores/dictation/index.ts`) and have zero importers;
   `UtteranceWell` nonetheless holds one of the six `mic` ceiling slots.
   Move them to `_parked/` (owner ruling: never delete -- park).

5. **Artboard.** One board at 1440 + 393 showing the MicButton placement
   per species: inside StringGadget (trailing), inside PadGadget
   (corner), inside EditInPlace (trailing in edit mode), standalone
   (beside the input). The display line reads `17 SITES` (a fact, not a
   sentence); the specimen strip carries the rest.

### (e) The desk answering the hand -- the full loop

**Position:** the Speak window, one session, no restart.

**The loop (shown once at each width):**

1. **Talk.** The owner clicks `Talk` (MicButton transport,
   `SpeakFace.tsx:352-386`). He speaks. The utterance appears in the
   well (PadGadget, `:296-308`, `mic={false}` after story 05).
2. **Land.** The pipeline runs. The RESULT row shows the final text.
   LANDS IN shows `Claude Code · 41 MS` (`:404-434`).
3. **Judge.** He presses `Wrong`. The teach row unfolds, FIELD = `TEXT`.
4. **Teach.** He edits the one wrong word and presses `Teach`. The
   receipt: `TAUGHT · postgress -> PostgreSQL`.
5. **Speak again.** The word recurs. The text rule fires
   deterministically on the raw transcript before the stage loop
   (`plugins/dictation/pipeline.py:98`). The RESULT row shows the
   corrected text with the chip `APPLIED`.
6. **The Journal.** Both utterances appear in the Journal wing, pushed
   live. The second carries `APPLIED`; the first carries `TAUGHT`.
7. **The receipt outside Speak.** The Room's ask well, the Door's name
   field, a Note editor -- the MicButton is there. He dictates into the
   ask well; the Journal shows it with source `BROWSER`.

**When `final_text == utterance`,** the RESULT line still renders the
final text -- it is the *landed* fact, not a repeat of the draft; the
well shows what he is holding, the RESULT what the pipeline produced.
When they are identical, the RESULT line carries the verdict verbs and
the well carries none, so the two rows are never mistaken for one
object.

**`OK` / `Wrong` framing** is one species in two states: both are
`Button variant="ghost" dense`; the *selected* verdict takes
`data-verdict-active`. A verb whose frame moves between boards reads as
two species; it is one.

**At 1440:** the loop fills one vertical scroll of the Speak window;
the transport row sits at the TOP (170 Face 2 item 1) with the `Open`
latch beside `Talk` (`SpeakFace.tsx:387-395`).

**At 393 (R14):** the board follows 170's ratified `SpeakPhone`
composition -- wings, the utterance well, LANDS IN, RESULT, ENGINE, and
the **transport at the foot** (sticky capture key, 170 Face 2 item 9),
footer last. The `Open` latch is drawn at 393 beside `Talk`; it is a
real verb on a real face and is not withheld at the narrow width.
(170's own `SpeakPhone.dc.html` omitted `Open`; 176 adds it rather than
inheriting the omission. Recorded as a board deviation from 170 in the
addendum, R14.)

## D3 -- the wire

### The third correction kind: `text` (R1)

**The store.** `CORRECTION_KINDS` (`corrections.py:33`) gains `"text"`:
`("intent", "target", "text")`. A `text` correction's `key` is the
phrase **as heard**, its `value` the phrase **as said**. The
`Correction` dataclass (`corrections.py:39-49`) and the durable
repository (`db/corrections.py:26` `VALID_CORRECTION_KINDS`,
`:34` `record_correction`) take the new kind additively; the ring
(`DEFAULT_CAP = 20`, `:34`/`:112`) is shared.

**The match is exact-phrase, not Jaccard.** `best_match_in`
(`corrections.py:70-94`) and `similarity` (`:62-67`) stay exactly as
they are and keep serving `intent` and `target` only. The `text` kind
uses a separate deterministic matcher:
- whitespace-normalized comparison;
- **punctuation-stripped tokens (N3).** `Utterance.raw_text` is
  *post-TextProcessor* on the capture path (`contracts.py:23-24`;
  `runtime/dictation_capture.py:121`), so spoken punctuation is already
  attached to the tokens -- `postgress,` not `postgress` + `,`. The diff
  strips leading and trailing punctuation from each span **before**
  storing, so the key is never `postgress,`;
- **the key is stored stripped and lowercased**; matching is
  case-insensitive;
- **the boundary is non-alphanumeric-or-string-edge** -- so `postgress`
  matches inside `postgress,` and `postgress.` and at either end of the
  string, and never inside `postgressive`. "Whole-word bounded" alone is
  necessary but not sufficient;
- **case-preserving on replace, first letter only**: when the heard
  occurrence's first letter is uppercase, the replacement's first letter
  is uppercased; the rest of the value is written as taught;
- all matching rules apply, longest `key` first (the 175 R1 precedent
  for longest-wins);
- a rule whose `key` is one token is legal for `text` (it is exact); the
  `REFUSED · ONE WORD` rule applies to routing kinds only (R7) and is
  enforced in `CorrectionStore.record` (`corrections.py:145-165`, which
  today guards kind, emptiness and `looks_like_secret` and has no
  token-count check), so both HTTP routes and the MCP surface inherit it
  -- never on the face (C7 note).

**Where it applies: a sibling seam inside `Pipeline.run`, NOT
`TextProcessor`.**

The obvious neighbour is the spoken-symbol substitution
(`holdspeak/text_processor.py:60-68` builds the tables from
`config.dictation.spoken_symbols`; `TextProcessor.process` at `:90-104`
does the work; wired at `web_runtime.py:240-242`). **It is the wrong
host**, and the reason is a fact about the tree:
`text_processor.process` is called only from the runtime capture path
-- `runtime/dictation_capture.py:121, 398, 412` and
`runtime/wake_glue.py:381`. It is never called by `dictation_runner.py`
and never by the browser or dry-run routes (`_helpers.py`). A text rule
riding `TextProcessor` would fire for HOTKEY and WAKE and be invisible
to BROWSER, DRY RUN and the remote path -- and it would never reach
`Pipeline.run` at all, so the router would still see the wrong words.

`Pipeline.run` (`plugins/dictation/pipeline.py:83-98`) is the one funnel
every source passes through. The seam:

- `run()` seeds `current_text = utt.raw_text` at `:98` and enters the
  stage loop at `:101`, passing the ORIGINAL `utt` to every stage
  (`stage.run(utt, list(results))`, `:108`).
- 176 applies the text rules to `utt.raw_text` at `:98` and builds a
  corrected `Utterance` with `dataclasses.replace` (`Utterance` is a
  frozen dataclass, `plugins/dictation/contracts.py:22-30`), then passes
  **that** to every stage and seeds `current_text` from it. The rewrite
  pass and the router therefore see the corrected words.
- The rules reach the Pipeline the same way the routing snapshot does
  today: `build_pipeline(..., corrections=correction_snapshot)`
  (`dictation_runner.py:342-345`, `:537`) already threads the snapshot;
  the Pipeline keeps the `text`-kind subset for itself and hands the
  routing subset to the intent-router stage as before.
- **It is not a stage** (D1's carve): no `StageResult`, no `stage_ms`
  key, no `requires_llm`, no entry in `self._stages`. It is a correction
  kind applied at an existing transcript seam. The ids of the rules
  that fired are collected on the `PipelineRun` for R2.

### The raw transcript on the run response (N2)

The face must diff against the string the rule is applied to. Neither
run response carries it today: the pipeline-off passthrough returns
`final_text` (`_helpers.py:750-770`, the field at `:757`) and the real
run returns `run.final_text` (`:883-896`, at `:894`). Story 02 adds one
field beside it -- the raw transcript as heard, before the rewrite pass
-- on both. The TEXT well pre-fills from that field, and the diff is
`heard(raw)` vs `said(his edit)`.

### The order against the spoken symbols (P2 note)

A text rule runs *after* `TextProcessor` on the capture path
(`runtime/dictation_capture.py:121` processes, then the pipeline runs)
and *instead of nothing* on the browser and dry-run paths (which never
call `process`). Two consequences worth stating rather than
discovering:

- **A rule's output is never re-scanned** for spoken symbols, so a text
  rule can never produce one.
- **The same sentence yields different `raw_text` on the two paths**, so
  a rule taught from a HOTKEY landing may not fire on a BROWSER one.
  Exact-phrase matching makes that visible rather than fuzzy: it simply
  does not fire, and the `APPLIED` chip is absent.

### The apply path for the routing kinds (unchanged)

1. **Intent.** `_apply_correction_nudge()` (`intent_router.py:206-234`)
   is called at `:190` after the LLM classifies, calling
   `best_match_in(..., min_similarity=_NUDGE_SIMILARITY)` (`:212-214`)
   with `_NUDGE_SIMILARITY = 0.5` (`:35`). On a match whose value is in
   `valid_ids` it boosts to `_NUDGE_CONFIDENCE = 0.85` (`:34`) or
   redirects, setting `extras["corrected"] = True` (`:225`, `:233`) and
   `metadata["correction_nudge"]` (`:195-196`).
2. **Target.** `apply_target_correction()`
   (`target_profile.py:126-151`) calls `best_match_in(..., "target",
   ...)` with `min_similarity` default `0.5` (`:131`, `:145`) and
   returns a profile with `source="correction"`, confidence 0.95
   (`:151`), which outranks the heuristic (`:186-187`).

Both take the snapshot from `dictation_runner.py:334-339` (and `:526-531`),
taken fresh at the start of every run -- a correction taught during one
utterance applies to the next, no restart.

### The label sources (R12 / C12)

The face renders labels; the wire carries ids.

| Kind | Id source | Label source | Served today? |
|---|---|---|---|
| `intent` | block ids from the loaded blocks YAML (`plugins/dictation/blocks.py:84-89`, `Block.id`) | `Block.description` (`blocks.py:87`) | **Yes** -- `GET /api/dictation/blocks?scope=global` returns the raw document (`web/routes/dictation/blocks.py:56-88`); `Blocks.tsx:39-44, 148-150` already reads `document.blocks[].id` / `.description`. Note `readiness.blocks.resolved` carries only `count` (`_helpers.py:411-417`) -- it is NOT a label source |
| `target` | **SIX** ids -- `TARGET_PROFILE_OVERRIDE_OPTIONS` (`target_profile.py:26-34`) **minus `auto`** (N1) | the `labels` map (`target_profile.py:280-288`: `claude_code -> "Claude Code"`, `codex_cli -> "Codex CLI"`, `terminal_shell -> "Terminal shell"`, `browser -> "Browser"`, `editor -> "Editor"`, `chat -> "Chat"`) | **No.** Neither the ids nor the labels are served to the web (`TARGET_PROFILE_OVERRIDE_OPTIONS` is referenced only at `target_profile.py:100, 103, 149`). Story 02 adds them: an `overrides: [{id, label}]` array on the readiness route's existing `target` payload (`pipeline.py:200-207, 330`) -- one field, no new route. The array carries six entries; `auto` is never offered |

**Why `auto` is excluded, and the belt (N1).** `auto` is a member of
`TARGET_PROFILE_OVERRIDE_OPTIONS`, so a `target` correction whose value
is `auto` clears the membership guard at `target_profile.py:149` -- and
then `_profile("auto", ...)` (`:272-296`) raises `KeyError` at
`label=labels[profile_id]` (`:291`), because the map has no `auto` key.
That raise lands inside the live typing path
(`dictation_runner.py:389`, `:565`) and the dry-run route
(`_helpers.py:811`), none of which guards it. Story 02 pays it twice:
the pick offers six ids, **and** `_profile` uses
`labels.get(profile_id, profile_id)` so no member of its own option set
can ever raise on the live path.

**The face prints the map's string verbatim (C12 note).** The label for
`terminal_shell` is `Terminal shell`, not `Terminal`. There is no
design-owned label table; the map at `target_profile.py:280-288` is the
one source, and the boards are corrected to it.

The Learned wing resolves `value -> label` through the same two
sources, so it prints `Claude Code`, never `claude_code` (E.4).

### The two stored facts, split (R5)

`corrected` is overloaded today: it means "he taught FROM this row" (set
only by `mark_corrected`, `db/journal.py:129-141`), and 176 needs the
opposite fact too ("a correction fired ON this row").

**The split, additively:**

| Wire field | Storage | Meaning | Set by |
|---|---|---|---|
| `taught_from` | the **existing** `corrected` column -- unchanged meaning, no data migration | this row is the one he taught from (the row that was wrong) | `mark_corrected` (`db/journal.py:129-141`), inside `if recorded` after R4 |
| `corrections_applied` | **one new column**, a JSON array of correction ids | which stored rules fired on this row (text rules + the routing nudge) | `DictationJournalRecorder.record` (`journal.py:111-157`) |

Migrations stay minimal (owner ruling): one additive column on
`dictation_journal`, defaulting to `'[]'`, reconciled by the one
declarative schema; the canonical snapshot regenerated.

**The INSERT seam.** `DictationJournalRepository.record` hardcodes
`..., corrected, correction_id) VALUES (..., 0, NULL)`
(`db/journal.py:70-74`). Story 02 adds a **named** `corrections_applied`
column and parameter -- named, never positional (the
positional-INSERT scar, MEMORY
reference_positional_inserts_reconcile_order). `_row_to_record`
(`db/journal.py:208-227`) and `_journal_to_dict`
(`pipeline.py:1302-1321`) gain the field.

**The recorder's read.** `DictationJournalRecorder.record`
(`journal.py:111-157`) passes only `intent.raw_label`, `intent.block_id`
and `intent.confidence` (`:141-152`) and `_target_name(target_profile)`
(`:143`, which drops `.source`), so `extras["corrected"]`
(`intent_router.py:225, 233`) and `source="correction"`
(`target_profile.py:151`) reach nothing today. 176 reads them, plus the
text-rule ids collected on the `PipelineRun`, and writes the id list.

**`PipelineRun` is frozen with six required fields (C5 note).**
`plugins/dictation/pipeline.py:47-56` declares `final_text`,
`stage_results`, `intent`, `warnings`, `total_elapsed_ms`,
`short_circuited` -- all required -- and `passthrough_run`
(`journal.py:32-49`) fakes a run with a `SimpleNamespace` that has none
of them beyond those it needs. So the new `corrections_applied` field
**must carry a default** on the dataclass, and the recorder **must read
it defensively** -- `getattr(run, "corrections_applied", [])` -- or the
pipeline-off passthrough path raises. Every construction site of
`PipelineRun` (`pipeline.py:85-92`, `:142-149`, `:160-167`) is named in
story 02.

**The chip never reads `learning` (R2).** `best_correction_signal`
(`dictation_learning.py:137-170`), computed at read time over the whole
journal (`pipeline.py:1062-1071`), paints `learning.matched` on rows
recorded *before* the correction was ever taught. The row and RESULT
chips render from `corrections_applied` alone.

**`N APPLIED` is a real count (R3).** The Learned wing's cell is the
number of journal rows whose `corrections_applied` contains that
correction's id -- a new repository query
(`DictationJournalRepository.count_applied(correction_id)`), computed
once for the whole list in the `GET /api/dictation/corrections` handler
(`pipeline.py:917-939`) in place of today's
`item["similar"] = reach_for_gist(...)` (`:930-931`). The teaching
utterance is not counted (it was never re-run). `reach_for_gist`
(`dictation_learning.py:99-113`) stays in the digest and appears on no
face.

### The teach routes, made honest (R4)

Today, on the primary route (`pipeline.py:1122-1201`):
- `recorded = store.record(kind, entry.transcript, value)` (`:1154`);
- `correction_id` is guessed from `list_for_display()[0]`
  (`:1156-1159`) -- somebody else's newest correction when nothing was
  recorded;
- `repo.mark_corrected(entry_id, correction_id=correction_id)`
  (`:1162`) runs **outside** `if recorded`, so a refused teach still
  flips `corrected` and links a wrong id;
- the response key is `taught` (`:1195`), while the fallback route's key
  is `recorded` (`:997`).

**176 pays all four:**
- `mark_corrected` and the `correction_id` linkage move inside
  `if recorded`;
- `record()` returns the stored row id so the linkage stops guessing.
  **This is a contract change with exactly two callers** --
  `pipeline.py:996` (the corrections route) and `pipeline.py:1154` (the
  journal correct route). `CorrectionStore.record` returns `bool` today
  (`corrections.py:145-165`); returning an `int | None` is additive and
  both callers already treat the result as truthy (C4 note);
- the face reads `taught ?? recorded`;
- a refused teach writes nothing, and the receipt says so -- `REFUSED ·
  SECRET` is then true.

**When does the fallback fire?** Only when the run returned no
`journal_id` -- `journal_enabled=false`, no repository attached, or an
unknown source (`journal.py:130-133`). On the owner's desk with the
journal on, the fallback is dead; a walk that exercises only the primary
route proves nothing about it. Story 02's unit tests cover the fallback
explicitly.

### The bus seam (name it; do not invent a second one)

The desk has exactly one live-frame mechanism, and
`dictation.journal.entry` rides it unchanged:

| Layer | Seam | file:line |
|---|---|---|
| Socket endpoint | one `/ws` per page; closes any principal without `PrincipalRight.OWNER` | `holdspeak/web/routes/system/ws.py:20-98` (admission at `:52-56`) |
| Fan-out | `WebSocketManager.broadcast(BroadcastMessage)` | `holdspeak/web_server.py:75-116` (frame shape `{"type","data"}` at `:66-72`) |
| Thread-safe entry point | `WebServer.broadcast(message_type, data)` -- reads `self._loop` at call time, no-ops without a loop, hands off with `run_coroutine_threadsafe`, swallows the result in a done-callback; cannot block or raise into the dictation thread | `holdspeak/web_server.py:523-540` |
| Route-side handle | `ctx.broadcast(type, data)` | `holdspeak/web_server.py:877`, `:1042` |
| Runtime-side handle | `self.server.broadcast(type, data)` | `web_runtime.py:342-345` (`audio_level`), `runtime/dictation_previews.py:41-43` (`dictation_preview`), `runtime/activity.py:48` (`runtime_activity`) |
| Existing dictation-learning frame | `learning_event` on a taught correction | `web/routes/dictation/pipeline.py:1180-1191` |
| Browser bus | `RuntimeBusProvider` (one socket, ping every 15 s, backoff reconnect), `subscribe(type)`, `useRuntimeFrame(type)` | `web/src/runtime/RuntimeBus.tsx:26-104`, `:106-111`, `:113-121` |
| Existing consumers (the precedent) | `AmbientLayer.tsx:24-25, 96, 352, 370`, `PresencePage.tsx:12`, `LiveCore.tsx:73`, `useMeetingData.tsx:121` | |

**The emit point: the recorder's constructor handle.**
`DictationJournalRecorder` has five call sites
(`dictation_runner.py:222, 422, 600`; `_helpers.py:742, 868`) and one
write chokepoint (`journal.py:137-155`). 176 gives the recorder an
optional `broadcast` callable at construction (`web_server.py:242`,
bound `broadcast=self.broadcast`) -- the same `notify=` shape the
meeting services use (`web/routes/meetings/intel.py:22`) -- and emits
once inside `record()` after the repository returns the stored row. All
three runner sites already hold `server`
(`dictation_runner.py:217, 420, 598`), so nothing needs plumbing; the
emit sits **inside** the elected publication closure, so a cancelled run
never broadcasts -- the correct fence. A recorder built without the
callable is a no-op, so every bare server and every test stays
byte-identical.

**The honest fallback is a module-level handle in `journal.py:137-155`,
not the two routes.** `_helpers.py:742` and `:868` are the **dry-run**
path: `:742` is the pipeline-off passthrough and `:868` the dry-run
executor, both taking `journal_source` from the dry-run route
(`dry_run` / `browser`). The owner's real Tuesday dictation goes through
`dictation_runner.py:422` / `:600`. Emitting route-side would push
exactly the sources he is not using and leave `DICTATION` and `HOTKEY`
-- the walk's beats 1--5 -- unpushed. The old "poll for the hotkey path"
sentence is struck.

**Redaction is by construction.** `record()` writes
`filter_secret(transcript)` and `filter_secret(final_text)`
(`journal.py:139-140`, `filter_secret` at `:52-59`) *before* the
repository call, and the frame is built from the **returned stored
row**, so redaction cannot be bypassed.

**Audience, stated for the record.** `/ws` admits owner principals only
(`ws.py:52-56`), so the frame is a read under Article V.1 with no
widened audience. It does carry the **full** transcript where the
existing `learning_event` carries a 120-char gist
(`pipeline.py:1183`) -- same audience, more text.

### The journal's durable rows and the stream route

`GET /api/dictation/journal` (`pipeline.py:1032-1079`) takes
`limit: int = 200` and `source: Optional[str] = None` -- the source
param already exists -- but clamps it to
`source if source in ("dictation", "dry_run") else None` (`:1049`), so
`browser` and `hotkey` silently fall through to "no filter". The
repository accepts any source (`db/journal.py:100-108`). There is no
`before` cursor.

**176 adds:** the bus frame; the clamp widened to the recorder's
`VALID_SOURCES` (`journal.py:28`); `?limit=50&before=<id>` pagination on
the route and on `DictationService.list_journal`.

**Seams:** `journal.py:28` · `journal.py:111-157` · `db/journal.py:70-74`
(the named INSERT) · `db/journal.py:100-108` (`recent`) ·
`pipeline.py:1032-1079` · `pipeline.py:1302-1321`.

### The `Forget` verb

`DELETE /api/dictation/corrections/{id}` (`pipeline.py:999-1007`) calls
`CorrectionStore.remove(id)` (`corrections.py:216-230`), deleting from
the DB and reloading the ring. `DELETE /api/dictation/corrections`
(`:1009-1016`) clears everything. No wire change needed.

### The mic census script (the ratchet fence)

**New file:** `scripts/mic_census.py` (the script behind
`assets/mic-census-176.md`). **Guard:** extend rule `mic` per D2(d).2.

**Seams:** `ux_canon_scan.py:100` · `:178-180` · `:306-316` (rule `B`,
the per-element shape to copy) · `:360-363` (the two flag defects) ·
`:409-414` · `tests/ux_canon_ceiling.json` ·
`tests/unit/test_ux_canon_ratchet.py:54-101`, `:104-125`.

## D4 -- counsel's hunts (rewritten to the rulings)

1. **A correction that reaches too far.** Jaccard is over the **union**
   of both token sets (`corrections.py:67`), so a *short* gist matches
   **narrowly**, not broadly -- the draft's caution pointed the wrong
   way and is struck (R7). The real hazard is two same-shaped sentences
   differing only in the payload word, which clear 0.5 at ordinary
   length: a `target` rule taught on "send the note to Dana" fires on
   "send the note to Alex" (0.667). That is a wrong-recipient delivery
   under Article V. **Open for the owner (walk question 2):** raise the
   bar, or confirm the first auto-application of a routing rule?

   **The `text` kind is narrower, not hazard-free (N4), and its blast
   radius is larger in the way that matters.** A routing nudge changes
   *where* text goes; a text rule changes *the words he types*.
   Exact-phrase removes the fuzzy false positive and keeps the
   common-phrase one: a rule `queue for -> Q4` rewrites every future
   utterance containing that ordinary English phrase -- "the queue for
   the build is long" becomes "the Q4 the build is long" -- on every
   dictation source, silently, with no similarity floor to stop it. D3's
   "all matching rules apply, longest key first" lets several rules
   compound on one utterance. **The guards are three and they are named
   on the face:** the matching is exact-phrase (no fuzz), the `APPLIED`
   chip's Disclosure names which rule fired, and `Forget` is one wing
   away. This joins walk question 2 as a question for the owner -- not
   as a hazard this design denies.
2. **A one-token routing gist.** It can only reach 0.5 against an
   utterance of at most two tokens; it cannot fire on a sentence. It is
   refused by name -- `REFUSED · ONE WORD` (Article V.3, the 175 R1
   precedent) -- rather than stored dead in a 20-slot ring. The
   `SpeakTaughtShort` board is removed.
3. **A journal entry that leaks a secret.** `filter_secret`
   (`journal.py:52-59, 139-140`) runs before the repository call and the
   frame is built from the stored row; the correction store checks the
   same on gist and value (`corrections.py:152-153`). Verified clean.
4. **A counter that is not a count.** `learning.similar` is
   `reach_for_gist` (`dictation_learning.py:99-113`) -- similar
   transcripts, including the teaching utterance itself (similarity
   1.000), so a brand-new correction would read `1 APPLIED` meaning
   zero. Struck: `N APPLIED` counts stored firings (R3), and
   `reach_for_gist` appears on no face.
5. **A mic that holds instead of toggles.** MicButton
   (`web/src/desk/components/MicButton.tsx`, re-exported by
   `desk/surface/controls/MicButton.tsx`) is click-to-toggle by design;
   the Speak transport uses `onState` (`SpeakFace.tsx:357-366`). No
   MicButton added in 176 may introduce a `hold`/`press` variant.
6. **A third mic on the Speak face.** Settled by R13: the well takes
   `mic={false}`; `Talk` is the face's mic authority.
7. **Two teach routes, two keys.** Settled by R4: the face reads
   `taught ?? recorded`; `mark_corrected` moves inside `if recorded`.
8. **Two counts on one face.** Settled: the Journal wing drops its
   caption count; the footer's `N TODAY` is the one count.
9. **Adopting a species that ships raw buttons.** Settled by R6:
   `LedgerFilterBar` is not adopted (two raw `<button>`s at
   `LedgerFilter.tsx:124, 147` would import two A1 residues into the
   Journal face).
10. **Dense hit targets at 393** (24--28px measured across the boards)
    are the library's dense-Button height -- a species property. By the
    owner's standing ruling a species problem is fixed in the library,
    never in a face. Raised as a library question, not a 176 board
    change.

## D5 -- the walk

The owner's attended walk on his real desk, both widths. Runner:
**`tests/e2e/live176_walk.py`** (written in story 06, following
`live170_walk.py` .. `live175_walk.py`).

**The true write set (R10).** The **runner** writes nothing and seeds
nothing: it drives the face and reads. The **product** writes exactly
what his own hand produces:

- **one journal row per utterance he speaks** -- the journal is the
  product's own record (`journal.py:137-155`), and each write prunes the
  table to `retention` (`db/journal.py:93-94`), so an old row may be
  evicted exactly as on any ordinary Tuesday. Beats 1, 2, 4, 6 and 7
  each write one;
- **one correction row** from his `Teach` (`pipeline.py:1154`);
- **the `taught_from` flag and `correction_id`** on the row he corrected
  (`pipeline.py:1162` after R4's fix);
- **`corrections_applied`** on the rows where a rule fired.

Beats 6 and 7 dictate into the Room's ask well and the Door's outcome
field and **do not submit**, so no Room or Door write occurs. `Forget`
and `Delete` remove all of it in one verb each. The claim "the walk
writes nothing except the one correction" is struck as false.

**The runner asserts the write set.** Before and after the walk it reads
`GET /api/dictation/journal?limit=1` (`count`) and
`GET /api/dictation/corrections` (`size`), and asserts: journal rows
added == the number of beats he dictated, and correction rows added ==
1. Any other delta fails the leg.

**Beat 0, before he speaks:** confirm `corrections_enabled` is on. The
config default is `True` (`config/meeting.py:389`), but every read falls
back to `False` (`dictation_runner.py:336-338`, `_helpers.py:716-720`,
`pipeline.py:1175`), so a stale or partial config makes the whole loop a
silent no-op. The runner reads it from
`GET /api/dictation/readiness` and fails the leg with a named reason
rather than letting him debug a dead teach live.

Seven beats:

1. **Talk.** He dictates a sentence. It lands correctly in the RESULT
   row. LANDS IN reads the target label + latency.
2. **Wrong landing.** He dictates a sentence containing a word the
   transcript gets wrong. He presses `Wrong`.
3. **Teach.** The teach row unfolds with FIELD = `TEXT` and the landed
   text pre-filled. He edits the one word. He presses `Teach`. The
   receipt: `TAUGHT · <heard> -> <said>`.
4. **The same word.** He dictates a sentence containing it. The rule
   fires deterministically. The RESULT row shows the corrected text with
   the `APPLIED` chip.
5. **The Journal.** He switches to the Journal wing (via the wing strip
   or `Review`). Both utterances appear -- the second pushed live,
   without a reload; the second carries `APPLIED`, the earlier one
   `TAUGHT`. Source filter: `DICTATION`.
6. **The mic on the Room.** He opens a Room. The ask well's input
   (`ProjectRoomCore.tsx:1428`) has its MicButton (`:1442`). He clicks
   it (toggle), dictates a sentence, the text lands in the field. He
   does not submit.
7. **The mic on the Door.** He opens the Door. The outcome field
   (`DoorCore.tsx:408`) has its MicButton (`:417`). He dictates a
   project name into the field. He does not submit.

Beats 6 and 7 verify coverage that already shipped in 169/170; they are
in the walk because the loop is only proven when the mic works outside
Speak.

**Three questions ride the walk (story 06):**
1. Is the correction a routing fix or a words fix? (176 answers "both",
   with `TEXT` as the default -- his word confirms or flips it.)
2. How wide should a routing correction reach? 0.5 Jaccard sends "the
   note to Alex" where "the note to Dana" was taught. **And should a
   text rule's FIRST application confirm?** (N4) A rule on a common
   phrase -- `queue for -> Q4` -- rewrites the words he types on every
   source, forever, with no similarity floor. Silent-and-undoable (the
   `APPLIED` chip names it, `Forget` removes it) or confirm-once?
3. Wing or gear for `Learned`? Four wings on Speak, or the corrections
   table stays behind the gear with the digest.

Both widths. The stopwatch per face. His verdict.

## Sizes

| Story | Size | Notes |
|---|---|---|
| 01 The design | S | This doc + the census + counsel's read (done); artboards at 1440 + 393 redrawn to R1--R14 |
| 02 The first correction | **L** | The `text` correction kind (store + repo + the deterministic matcher + the `Pipeline.run` seam), the word-level diff and its three outcomes, the enum pick + the target-options wire, the additive `corrections_applied` column with a named INSERT, the recorder reading the applied ids, the four R4 wire fixes, the `gist`/`key` fix, the token receipts and the `APPLIED` chip + Disclosure |
| 03 The journal stream | M | Bus frame on the recorder's one chokepoint + a RuntimeBus subscription; widen the source clamp; `before` pagination; row grammar (`APPLIED` / `TAUGHT`, uppercase MS, human source labels); the promoted flat-token filter species + contract.md; two empty states; drop the caption count; keep Replay/Copy/Delete |
| 04 The voice law | S--M | 8 raw elements + 9 `mic={false}` opt-outs + 4 orphans parked; the four `mic`-rule defects fixed and the rule made per-element with a 23-entry allowlist; ceiling lowered |
| 05 The desk answering the hand | S | Integration of 02+03+04; `Review` re-pointed at the Journal wing; the well's `mic={false}` (the 170 drift) |
| 06 The walk | S | Owner's attended walk; the runner `tests/e2e/live176_walk.py` with the before/after write-set assertion; no product code |
| 07 The docs | S | Doc updates for the new faces + the census |
| 08 The close | S | Full suite + web baseline + canon ratchet + PR |

**The biggest unknown is story 02's `Pipeline.run` seam:** every stage
receives the ORIGINAL `Utterance` (`plugins/dictation/pipeline.py:108`),
so applying text rules means constructing a corrected `Utterance` and
passing it everywhere -- and `Utterance` is frozen
(`contracts.py:22-30`), so the replacement is cheap but the blast radius
is every stage and every test that asserts on `utt.raw_text`. If that
proves wide, the fallback is to correct only `current_text` before the
loop and re-seed each stage's input text, which fixes the landed words
but leaves the router reading the uncorrected transcript -- a weaker
answer that must be said out loud rather than shipped quietly.

## Changes from the 2026-09-05 draft

- **Banner.** DRAFT -> SETTLED against `7a47904e`; every pointer
  re-verified.
- **D1 gains laws** carried from 175's D1 and the canon: one mic
  authority (IV.3), watching is free (V.1), refusal by name (V.3),
  honest by construction (VI), ledger not gate, a replacing face keeps
  its verbs (175), the name said once (A.7), the lead slot is the emblem
  (canon B), egress where it happens (A.9), receipts wear human labels
  (canon E.4), honest states (A.10).
- **D2(a): the teach path corrected.** The face's primary route is
  `POST /api/dictation/journal/{id}/correct` (`useSpeakDeck.ts:291-318`),
  and it teaches from the entry's transcript (`pipeline.py:1154`), not
  from what he types.
- **D2(b): the Journal's truths corrected.** `useResource` does not
  poll; the route's `source` param exists but is clamped to two of four
  (`pipeline.py:1049`); `corrected` and `learning` are already served;
  `Review` opens the Configure door, not the journal.
- **D2(c): a live defect named.** `Memory.tsx:86` reads `row.gist` while
  the route serves `key`, so the GIST column renders `—` today.
- **D2(d): the census replaced.** 31 "GAP" -> 8 uncovered raw elements +
  9 opt-outs (17 sites). StringGadget 89 -> 97, PadGadget ~10 -> 16.
  MicButton has no internal `<input>`; `Signal.tsx`'s
  `TextInput`/`TextArea` have zero call sites.
- **D2(d): rule `A14` -> extend rule `mic`** (`ux_canon_scan.py:100`).
- **D3: the intent threshold corrected** to `_NUDGE_SIMILARITY = 0.5`
  (`intent_router.py:35`).
- **D3: the bus seam named** with a file:line table and the recorder's
  `broadcast` callable chosen as the single emit point.
- **D5: the runner named** (`tests/e2e/live176_walk.py`).

## Addendum -- counsel on the design (2026-09-06): BOUNCE, the rulings R1--R14

Counsel's read: `assets/counsel-on-design-176.md` (VERDICT: BOUNCE on
P0-1; conditions C1--C14). The orchestrator ruled; this document is
rewritten to the rulings below.

| # | Counsel's item | The ruling | Where it moves the design / boards |
|---|---|---|---|
| R1 | **P0-1 / C1** -- both correction kinds are routing picks over a closed enum; the owner typing a corrected sentence records a value that can never fire. The Tuesday moment cannot happen on this wire. | The design does **not** shrink to routing picks. A third kind `text` is added (`CORRECTION_KINDS += "text"`, `corrections.py:33`): `key` = the phrase as HEARD, `value` = as SAID, applied **deterministically** on the raw transcript at the start of `Pipeline.run` (`plugins/dictation/pipeline.py:83-98`, before the rewrite pass and the router), exact-phrase, whitespace/case-normalized, case-preserving, whole-word bounded -- **not** Jaccard. The routing kinds keep Jaccard. It rides a **sibling seam inside `Pipeline.run`, not `TextProcessor`**, because `text_processor.process` is called only from the runtime capture path (`runtime/dictation_capture.py:121, 398, 412`; `runtime/wake_glue.py:381`) and never by `dictation_runner.py` or the browser/dry-run routes -- a TextProcessor rule would miss BROWSER and DRY RUN and never reach the router. FIELD cycles `TEXT · INTENT · TARGET`; TEXT is one StringGadget pre-filled with the landed text, diffed word-level on Teach (one span -> word rule; no diff -> `NO CHANGE`; many spans or >half the tokens -> whole-phrase rule); INTENT/TARGET are a pick over the real enum, label on the face, id on the wire. | D0 rewritten (postgress -> PostgreSQL); D1 gains the carve law; D2(a) rewritten; D3 gains "The third correction kind" and "The label sources"; boards `SpeakWrong` · `SpeakLoopPhone` · `SpeakLearned` · `SpeakRefused` · `SpeakApplied` redrawn |
| R2 | **C2** -- the chip renders from `learning` / `best_correction_signal`, a read-time "would match" that paints rows recorded before the correction existed. | The chip renders ONLY from a stored per-run fact: the recorder writes `corrections_applied` (the ids of the rules that fired -- text rules + the routing nudge) on the journal row. Never from read-time `learning`. | D2(a).3, D2(b).2, D3 "The two stored facts, split" and "The chip never reads `learning`" |
| R3 | **C3** -- `N APPLIED` is `reach_for_gist`: similar transcripts, not applications, and it counts the teaching utterance itself. | `N APPLIED` = the count of journal rows whose `corrections_applied` contains that correction's id -- a real count of firings; the teaching utterance is not one. Absent at zero. `reach_for_gist` is shown on **no** face. | D2(c).1; D3 "`N APPLIED` is a real count" (new repository query replacing `pipeline.py:930-931`) |
| R4 | **C4** -- the refusal receipt reads `recorded` while the primary route's key is `taught` (`pipeline.py:1195` vs `:997`), and `mark_corrected` fires outside `if recorded` (`:1162`), linking `correction_id` to an unrelated newest correction (`:1156-1159`). | Fix the key (`taught ?? recorded`); move `mark_corrected` and the id linkage inside `if recorded`; `record()` returns the stored id so the linkage stops guessing. A refused teach never shows TAUGHT and writes nothing -- `SpeakRefused`'s "nothing written" becomes true. | D2(a) receipts; D3 "The teach routes, made honest"; story 02 Scope + AC |
| R5 | **C5** -- `corrected` is overloaded (he taught FROM this row vs a correction fired ON this row), and the INSERT hardcodes it to `0`. | Split the flag: `taught_from` keeps the existing `corrected` column and its meaning (no data migration); `corrections_applied` is **one new additive column** (JSON array of ids, default `'[]'`). The INSERT at `db/journal.py:70-74` gains a **named** parameter -- never positional. Migrations stay minimal. | D3 "The two stored facts, split"; D2(b).2 draws both `APPLIED` and `TAUGHT` |
| R6 | **C6** -- `LedgerFilterBar` is not a toggle-token species: query `<input>` (`:112`), `matchCount/total` (`:120-122`), two raw `<button>`s (`:124`, `:147`), removable chips, and `null` below 5 items (`:104`). | `LedgerFilterBar` is **not** the species (it also has zero consumers in `web/src`, and `contract.md` names no flat-token filter at all). The four tokens compose from the library `Button` (ghost, dense) with `data-filter-active` + `aria-pressed` in a `role="group"` span -- the composition already ratified on the Room's history wing (`ProjectRoomCore.tsx:1550-1566`) -- PROMOTED into the library and documented in `surface/contract.md` per canon B. **No sparse rule: the bar never returns null**; it is present on the quiet state, and it shows no `matchCount/total`. | D2(b).4; D4 hunt 9 |
| R7 | **C7** -- `SHORT PHRASE · MATCHES BROADLY` is arithmetically false; Jaccard-union makes a short gist match *fewer* things. | The SHORT PHRASE caution is dropped entirely and the `SpeakTaughtShort` board is removed. A **one-token gist on a routing kind** is refused by name: `REFUSED · ONE WORD`. Text rules are exact-phrase, so no caution exists for them. The real hazard (same-shaped sentences at 0.5) is carried to the owner as walk question 2. | D1 (refusal by name); D2(a); D4 hunts 1--2 |
| R8 | **C8** -- `LEARNED` means three things on one face (wing, receipt, chip). | One word, one meaning: the wing is **`Learned`** (the noun -- what the desk knows); the receipt after Teach is **`TAUGHT · <heard> -> <said>`** (routing: `TAUGHT · <label>`); the chip where a rule fired is **`APPLIED`**. `LEARNED` never appears as a receipt or a chip. | D1 (A.7 row); D2(a), D2(b).2, D2(c) throughout; every Speak/Journal board |
| R9 | **C9** -- the scanner's mic flag never matches `<textarea>` (`:360-363`) and counts `<StringGadget` as uncovered. | Story 04 fixes both, plus the file-scope and `classify_face` gates. **The census numbers do not move** (the census script matched both tags directly), but the allowlist figure is stated as **23** (19 raw + 4 opt-outs) everywhere, and the ceiling claim is "`mic: 0` with a 23-entry reasoned allowlist", not "0 because every input has a mic". | D2(d).2; `assets/mic-census-176.md` summary |
| R10 | **C10** -- "the walk writes nothing except the one correction" is false; every dictating beat writes a journal row and prunes. | D5 rewritten honestly: the **runner** writes and seeds nothing; the **product** writes one journal row per utterance he speaks (retention-pruned as always), one correction row, the `taught_from` flag on the corrected row, and `corrections_applied` where rules fired. Beats 6 and 7 dictate and **do not submit**. The runner asserts, before and after, that journal rows added == his dictating beats and correction rows added == 1. | D5 rewritten |
| R11 | **C11** -- D2(b) drops the opened row's `Replay` / `Copy` / `Delete` in silence (175 law: a replacing face keeps its verbs). | The opened row keeps `EditInPlace` + `Replay` + `Copy` + `Delete` and the replay preview, exactly as `Journal.tsx:95-144` has them. D2(b) names them and the opened-row state. | D2(b).3 (new); D1 gains the 175 law row |
| R12 | **C12** -- the Learned wing draws `Delivery` / `Terminal` / `Calendar` while the wire serves `value` raw. | Label sources named with file:line: intent = `Block.description` (`blocks.py:84-89`) served by `GET /api/dictation/blocks` (`web/routes/dictation/blocks.py:56-88`, already read by `Blocks.tsx:39-44, 148-150`); target = the `labels` map (`target_profile.py:280-288`) over `TARGET_PROFILE_OVERRIDE_OPTIONS` (`:26-34`), which is **not served to the web today** -- story 02 adds an `overrides: [{id, label}]` array to the readiness route's `target` payload (`pipeline.py:200-207, 330`). `readiness.blocks.resolved` carries only `count` (`_helpers.py:411-417`) and is not a label source. | D3 "The label sources"; D2(a), D2(c) |
| R13 | **C13** -- the boards draw the utterance well mic-less; the built well has a third mic. | D2 states `mic={false}` on the utterance well; `Talk` is the sole mic on the Speak face (Article IV.3). The built `PadGadget`'s default-true mic (`SpeakFace.tsx:296-308`, `gadgets.tsx:315`) is a **170 drift, paid in story 05**, and the well joins the census allowlist with that reason (making it 24 after story 05). | D1 (one mic authority); D2(a) closing paragraph; D2(d) note; D2(e).1; D4 hunt 6 |
| R14 | **C14** -- `SpeakLoopPhone` drops the `Open` latch and moves the transport to the bottom; D2(e) says only "the transport stacks". | The 393 Speak board keeps the `Open` latch **and** puts the transport where 170's `SpeakPhone` board puts it -- at the foot, with the sticky capture key (170 Face 2 item 9). **Recorded deviation:** 170's own `SpeakPhone.dc.html` draws no `Open` latch (only the 1440 boards do), so 176 **adds** `Open` at 393 rather than restoring it. | D2(e) "At 393" (new paragraph) |

**The P2s, applied.** The `APPLIED` Disclosure shows `HEARD` / `SAID`
for a text rule and `WHEN` (gist) / `ROUTE` (label) with an honest
`MATCH 0.50`-style score for routing only -- no `KEY` / `VALUE` wire
words, and no invented similarity number. The Journal wing carries no
count in its caption (the footer's `N TODAY` is the one count per face).
An all-time empty Journal reads the token `NOTHING SPOKEN`; a
filter/search miss reads `NOTHING MATCHES`. The allowlist is **23** (19
raw + 4 opt-outs) in the design and the census alike. `Review` switches
to the Journal wing -- an existing verb kept, not retired. The Mic
board's display line reads `17 SITES`, not a sentence. The RESULT line's
behaviour when `final_text == utterance` is stated in D2(e), and
`OK`/`Wrong` are one species in two states.

**The bus fallback, re-verified.** Counsel is right. `_helpers.py:742`
is the pipeline-off passthrough and `:868` the dry-run executor; both
take `journal_source` from the dry-run route (`dry_run` / `browser`).
The owner's real dictation goes through `dictation_runner.py:422` /
`:600` (`dictation` / `hotkey`). The route-side fallback is struck from
D3; the recorder's constructor handle is primary and a module-level
handle in `journal.py:137-155` is the honest fallback.

## Addendum 2 -- counsel's re-read (2026-09-06): RATIFY-W-C, the conditions N1--N5

Counsel re-read the rewritten design, story 02, story 03 and all
seventeen boards. **VERDICT: RATIFY-WITH-CONDITIONS** -- C1--C14 paid or
paid-with-note, nothing unpaid; five new conditions. All five are RULED
accepted and applied below.

| # | Counsel's condition | The ruling | Where it moves the design / boards |
|---|---|---|---|
| N1 | **`Auto` in the target pick raises `KeyError` on the live typing path (P0, board).** `auto` IS a member of `TARGET_PROFILE_OVERRIDE_OPTIONS` (`target_profile.py:26-34`), so it clears the membership guard at `:149`; then `_profile("auto", ...)` does `label=labels[profile_id]` (`:272-296`, lookup at `:291`) and the map has no `auto` key. Reproduced under an isolated HOME. The call sites are `dictation_runner.py:389`, `:565` and `_helpers.py:811` -- none guards. `Auto` is also meaningless as a correction. | **The target pick offers SIX ids** -- `claude_code`, `codex_cli`, `terminal_shell`, `browser`, `editor`, `chat`. `auto` is never offered. Story 02 additionally **belt-fixes `_profile`** to `labels.get(profile_id, profile_id)` so no member of its own option set can raise on the live path. Both seams named. | D2(a) "`TARGET` offers SIX ids"; D3 label table target row + "Why `auto` is excluded, and the belt"; story 02 Scope + AC. **Board: `SpeakWrongRoute` drops `Auto`** |
| N2 | **The diff's *heard* side is the wrong text.** D2(a) pre-filled with the landed text; the rule is applied to `utt.raw_text` (`plugins/dictation/pipeline.py:98`). Whenever any stage rewrites text -- the rewrite pass's whole job -- a key harvested from `final_text` is matched against a string it never equals and never fires, and walk beat 4 fails for a reason invisible on the face. Neither run response carries a raw transcript today. | **The run response serves the RAW transcript** (as heard, before the rewrite pass) as one field beside `final_text`, on both paths -- the pipeline-off passthrough (`_helpers.py:750-770`, `final_text` at `:757`) and the real run (`:883-896`, at `:894`). **The TEXT well pre-fills from the raw transcript**, and the diff is `heard(raw)` vs `said(his edit)`. | D2(a) TEXT paragraph; D3 "The raw transcript on the run response"; story 02 Scope + AC. **Boards: the TEXT well shows the raw transcript** |
| N3 | **The word-level span must be punctuation-stripped.** `Utterance.raw_text` is post-TextProcessor on the capture path (`contracts.py:23-24`; `runtime/dictation_capture.py:121`), so spoken punctuation is already attached -- `postgress,` not `postgress` + `,`. A whitespace-token diff stores `postgress,` and fires on nothing else. "Whole-word bounded" is necessary but not sufficient. | The matcher **strips leading/trailing punctuation from each span before storing**; the key is stored **stripped and lowercased**; the boundary is **non-alphanumeric-or-string-edge** (so `postgress` matches inside `postgress,` / `postgress.` and never inside `postgressive`); **replace is case-preserving on the FIRST LETTER only**. | D3 "The match is exact-phrase" bullet list; story 02 AC |
| N4 | **"The `text` kind carries no such hazard" over-claims.** Exact-phrase is narrower than Jaccard but not hazard-free, and its blast radius is *larger* where it matters: a routing nudge changes where text goes, a text rule changes the words he types. `queue for -> Q4` rewrites "the queue for the build is long" on every source, silently, forever, with no similarity floor; "longest key first, all matching rules apply" lets rules compound. | D4.1 rewritten honestly: exact-phrase removes the *fuzzy* false positive and keeps the *common-phrase* one. **The three guards are named:** exact-phrase matching, the `APPLIED` Disclosure naming what fired, and `Forget` one wing away. **"Should a text rule's first application confirm?" rides the walk** as part of question 2. | D4 hunt 1 closing; D5 walk question 2 |
| N5 | **Two contradictions the rewrite left.** (a) D2(b).2 and D5 beat 5 require a `TAUGHT` token on the row he taught from; no Journal board draws it. (b) D1 rules "`N TODAY` is said once, in the footer" and D2(b).7 drops the Journal caption for that reason -- but D2(c).3 kept `countToken(n, "LEARNED")`, so the Learned face carries two counts and `LEARNED` appears twice (wing tab + caption). | (a) **The `TAUGHT` token stands** -- D2(b).2 says so explicitly and the boards will now draw it on the taught row. (b) **The Learned wing carries NO caption count**: the tab is the name, the rows are the count; the footer's `N TODAY` is the one count per face. The same law binds both wings. `countToken(n, "LEARNED")` is struck. | D2(b).2 (N5a note); D2(c).3 rewritten. **Boards: `JournalStream` / `JournalStreamPhone` / `JournalFiltered` / `JournalRowOpen` draw `TAUGHT` on 14:19; `Learned` / `LearnedPhone` / `LearnedQuiet` drop `3 LEARNED`** |

**Counsel's notes, folded.**

- **C3 note** -- `N APPLIED` counts the **retained** journal and can go
  **down**: every write prunes to `retention` (`db/journal.py:93-94`,
  default 500). Said in D2(c).1 rather than discovered on his desk.
- **C4 note** -- `CorrectionStore.record` returns `bool` today
  (`corrections.py:145-165`); "returns the stored id" is a contract
  change with exactly **two callers**, `pipeline.py:996` (the
  corrections route) and `pipeline.py:1154` (the journal correct route).
  Additive; both already treat the result as truthy. Named in D3 and
  story 02.
- **C5 note** -- `PipelineRun` is frozen with **six required fields**
  (`plugins/dictation/pipeline.py:47-56`) and `passthrough_run`
  (`journal.py:32-49`) fakes it with a `SimpleNamespace`. The new
  `corrections_applied` field carries a **default** on the dataclass and
  the recorder reads it as `getattr(run, "corrections_applied", [])`, or
  the pipeline-off path raises. The three construction sites
  (`pipeline.py:85-92`, `:142-149`, `:160-167`) are named in story 02.
- **C7 note** -- `REFUSED · ONE WORD` has a named seam:
  `CorrectionStore.record` (`corrections.py:145-165`, which today guards
  only kind, emptiness and `looks_like_secret`), so both HTTP routes and
  the MCP surface inherit the refusal. Never on the face.
- **C11 note** -- keeping the opened row's verbs also keeps its prose:
  `Replay — preview only` (`Journal.tsx:124-126`) and `The replay
  completed without text.` (`:127-130`). Tokenised in story 03 (`REPLAY ·
  PREVIEW` and `NO TEXT`) rather than re-ratified silently.
- **C12 note** -- the face prints the label map's string **verbatim**:
  `Terminal shell`, not `Terminal` (`target_profile.py:280-288`). There
  is no design-owned label table; the boards are corrected to the map.
- **P2 (spoken-symbol order)** -- a text rule runs after `TextProcessor`
  on the capture path and instead of nothing on the browser path, so its
  output is never re-scanned (a rule can never produce a spoken symbol)
  and the same sentence yields different `raw_text` on the two paths (a
  rule taught from HOTKEY may not fire on BROWSER; exact-phrase makes
  that a visible non-firing, not a fuzzy misfire). One paragraph in D3.
- **P2 (`corrections_enabled`)** -- the default is `True`
  (`config/meeting.py:389`) but every read falls back to `False`
  (`dictation_runner.py:336-338`, `_helpers.py:716-720`,
  `pipeline.py:1175`). D5 beat 0: the walk confirms it is on before
  beat 1 rather than debugging a silent no-op live.
- **P2 (FIELD casing)** -- the cycle renders `TEXT` · `INTENT` ·
  `TARGET` in uppercase (canon C's caption step). One casing, on every
  board.
- **P2 (`Clear` on the quiet Journal)** -- withheld when there is
  nothing to clear (A.11: a verb that does nothing is a lie). D2(b) now
  says so.
- **P2 (the 393 teach well)** -- D2(a) already requires the value
  control to wrap to a second line at 393; the TEXT kind is the one
  field he must read every word of, so it never truncates on one line.
- **Not paid, carried to the board lane:** the Mic boards were not
  redrawn; the display line still reads `17 inputs need the mic` where
  the P2 ruling says `17 SITES`.
