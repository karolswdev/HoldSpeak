# HS-176-02 — The first correction

- **Project:** holdspeak
- **Phase:** 176
- **Status:** backlog
- **Depends on:** HS-176-01
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

The correction store exists (corrections.py, CorrectionStore with
Jaccard matching, durable via DictationCorrectionRepository, wired at
web_server.py:227-229) and the API routes exist (pipeline.py:917-1016),
but the owner's desk has 0 corrections and **the loop as built cannot
carry his Tuesday mistake**.

Counsel's P0-1 (assets/counsel-on-design-176.md): both correction kinds
are *routing* corrections whose value must be a member of a closed set
— `intent` requires a loaded block id (intent_router.py:215), `target`
one of seven profile ids (target_profile.py:26-34, checked at :149).
The teach row 170-04 shipped takes free text in a StringGadget
(SpeakFace.tsx:500-505) whose placeholder says `Terminal` while the only
accepted value is `terminal_shell` (:504). Anything the owner types is
stored and never fires. His actual Tuesday mistake — "postgress" for
**PostgreSQL**, "Charter" for the status file — is a **words** mistake,
which the wire cannot express at all.

Ruling R1 (assets/settled-design-speak-loop.md, Addendum): a third
correction kind `text` is added, applied deterministically on the raw
transcript at the start of Pipeline.run; FIELD becomes a three-way cycle
`TEXT · INTENT · TARGET`; the routing kinds become a **pick over the
real enum**, label on the face, id on the wire.

Five more wire defects the same read found, all ruled:
- The chip cannot render honestly: the live nudge's
  `extras["corrected"]` (intent_router.py:225,233) never reaches the
  recorder (journal.py:141-152), and `learning` /
  `best_correction_signal` is a read-time "would match" that paints rows
  recorded before the correction existed (R2).
- `N APPLIED` would be `reach_for_gist` — similar transcripts, counting
  the teaching utterance itself, so a brand-new correction reads
  `1 APPLIED` meaning zero applications (R3).
- The refusal receipt reads the wrong key (`recorded` at pipeline.py:997
  vs `taught` at :1195) and `mark_corrected` fires **outside**
  `if recorded` (:1162), linking `correction_id` to an unrelated newest
  correction (:1156-1159) — so a refused teach still writes (R4).
- `corrected` is overloaded: today "he taught FROM this row", 176 needs
  "a correction fired ON this row"; and the INSERT hardcodes it to `0`
  (db/journal.py:70-74) (R5).
- The Configure door's corrections list reads `row.gist` while the route
  serves `key` (Memory.tsx:86, corrections.py:200-211), so the GIST
  column renders a dash on his desk today.

Counsel's re-read (RATIFY-W-C) found two more, both ruled:
- **`auto` in a target correction crashes the live typing path (N1).**
  `auto` is a member of `TARGET_PROFILE_OVERRIDE_OPTIONS`
  (target_profile.py:26-34) so it clears the membership guard at :149,
  and then `_profile("auto", ...)` raises `KeyError` at
  `label=labels[profile_id]` (:272-296, the lookup at :291) — inside
  `apply_target_correction`'s call sites on the hotkey path
  (dictation_runner.py:389, :565) and the dry-run route
  (_helpers.py:811), none of which guards. Reproduced by counsel under
  an isolated HOME.
- **The run response carries no raw transcript (N2).** The `text` rule
  is applied to `utt.raw_text` (plugins/dictation/pipeline.py:98), but
  both responses serve only `final_text` (_helpers.py:750-770, the
  field at :757; :883-896, at :894). A key harvested from the landed
  text would be matched against a string it never equals whenever any
  stage rewrote it — the rewrite pass's whole job — and would never
  fire.

The settled design (assets/settled-design-speak-loop.md D2(a), D3) holds
every pointer as of main `7a47904e`.

## Scope

- In:
  - **The `text` correction kind.** `CORRECTION_KINDS` gains `"text"`
    (corrections.py:33) and `VALID_CORRECTION_KINDS` likewise
    (db/corrections.py:26); `key` = the phrase as HEARD, `value` = as
    SAID.
  - **Its deterministic matcher (N3)** — exact-phrase, whitespace
    normalized, **punctuation-stripped**, longest key first. **Not**
    Jaccard; `best_match_in` (corrections.py:70-94) is untouched and
    keeps serving `intent` / `target` only. Precisely:
    - `Utterance.raw_text` is post-TextProcessor on the capture path
      (contracts.py:23-24; runtime/dictation_capture.py:121), so spoken
      punctuation is already attached to tokens (`postgress,`). The diff
      **strips leading/trailing punctuation from each span before
      storing**.
    - The key is stored **stripped and lowercased**; matching is
      case-insensitive.
    - The boundary is **non-alphanumeric-or-string-edge** — `postgress`
      matches inside `postgress,` and `postgress.` and at either end of
      the string, never inside `postgressive`.
    - Replace is **case-preserving on the first letter only**: an
      uppercase first letter on the heard occurrence uppercases the
      replacement's first letter; the rest is written as taught.
  - **Its apply seam: inside `Pipeline.run`, not `TextProcessor`.** The
    rules apply to `utt.raw_text` at plugins/dictation/pipeline.py:98,
    before the stage loop at :101, by constructing a corrected
    `Utterance` (frozen dataclass, contracts.py:22-30) passed to every
    stage — so the rewrite pass and the router both see the corrected
    words. It emits **no StageResult, no stage_ms entry, no
    requires_llm**: it is a correction kind at an existing seam, not a
    new pipeline stage. (`text_processor.process` is rejected as the
    host: it is called only from runtime/dictation_capture.py:121,398,412
    and runtime/wake_glue.py:381, never by dictation_runner.py or the
    browser/dry-run routes.)
  - **The teach row rebuilt to the HS-176-01 artboard.** FIELD =
    CycleGadget `TEXT · INTENT · TARGET` (uppercase, canon C's caption
    step), TEXT default. TEXT: one StringGadget (mic) pre-filled with
    the **RAW TRANSCRIPT** (N2), not the landed text; on `Teach` a
    word-level diff of `heard(raw)` vs `said(his edit)` — one
    contiguous span (≤ half the tokens) → a word rule; no difference →
    nothing stored, receipt `NO CHANGE`; more than one span or a span
    over half the tokens → a whole-phrase rule. INTENT / TARGET: a
    **pick over the real enum** (never free text), human label on the
    face, id on the wire.
  - **The raw transcript on the run response (N2).** One field beside
    `final_text` on both paths — the pipeline-off passthrough
    (_helpers.py:750-770) and the real run (:883-896) — carrying the
    transcript as heard, before the rewrite pass. The TEXT well
    pre-fills from it.
  - **The target pick offers SIX ids, never `auto` (N1):**
    `claude_code`, `codex_cli`, `terminal_shell`, `browser`, `editor`,
    `chat`. **Belt:** `_profile` (target_profile.py:272-296) uses
    `labels.get(profile_id, profile_id)` at :291 so no member of its own
    option set can raise on the live path, board or no board.
  - **The face prints the label map's string verbatim** — `Terminal
    shell`, not `Terminal` (target_profile.py:280-288). No design-owned
    label table (C12 note).
  - **The label sources wired.** intent = `Block.description`
    (blocks.py:84-89) via `GET /api/dictation/blocks`
    (web/routes/dictation/blocks.py:56-88); target = an
    `overrides: [{id, label}]` array added to the readiness route's
    existing `target` payload (pipeline.py:200-207, 330) from
    `TARGET_PROFILE_OVERRIDE_OPTIONS` (target_profile.py:26-34) **minus
    `auto`** — six entries — and the `labels` map (:280-288).
  - **The receipts, one word one meaning (R8).** `TAUGHT · <heard> ->
    <said>` for text, `TAUGHT · <label>` for routing, in place of the
    footer sentence (useSpeakDeck.ts:311). Refusals named:
    `NO CHANGE` · `REFUSED · ONE WORD` (a one-token gist on a routing
    kind) · `REFUSED · SECRET`. **`REFUSED · ONE WORD` is enforced in
    `CorrectionStore.record`** (corrections.py:145-165, which today
    guards only kind, emptiness and `looks_like_secret` and has no
    token-count check), so both HTTP routes and the MCP surface inherit
    it — never on the face (C7 note).
  - **The `APPLIED` chip on the RESULT row**, from the run's own stored
    fact, with no count; absent when nothing fired. Tapping it opens a
    Disclosure: `HEARD` / `SAID` for a text rule, `WHEN` / `ROUTE` /
    `MATCH 0.50` for a routing rule.
  - **The stored facts split (R5).** `taught_from` keeps the existing
    `corrected` column and its meaning (no data migration);
    `corrections_applied` is **one new additive column** (JSON array of
    correction ids, default `'[]'`) on `dictation_journal`, written by
    `DictationJournalRecorder.record` (journal.py:111-157) from the
    intent extras, the target profile's `source`, and the text-rule ids
    collected on the `PipelineRun`. The INSERT (db/journal.py:70-74)
    takes a **named** parameter, never positional.
    **`PipelineRun` is frozen with six required fields (C5 note)**
    (plugins/dictation/pipeline.py:47-56) and `passthrough_run`
    (journal.py:32-49) fakes it with a `SimpleNamespace`, so the new
    field carries a **default** on the dataclass and the recorder reads
    it as `getattr(run, "corrections_applied", [])` — otherwise the
    pipeline-off path raises. The three construction sites are
    pipeline.py:85-92, :142-149, :160-167.
  - **The four R4 wire fixes.** `mark_corrected` and the
    `correction_id` linkage move inside `if recorded`; `record()`
    returns the stored row id so the linkage stops guessing; the face
    reads `taught ?? recorded`; a refused teach writes nothing.
    **`record()`'s return type is a contract change with exactly two
    callers (C4 note)** — pipeline.py:996 (the corrections route) and
    pipeline.py:1154 (the journal correct route); `bool` →
    `int | None` is additive and both already treat the result as
    truthy.
  - **`N APPLIED` as a real count (R3).** A repository query counting
    journal rows whose `corrections_applied` contains the correction's
    id, computed once for the list in `GET /api/dictation/corrections`
    (pipeline.py:917-939), replacing `item["similar"] =
    reach_for_gist(...)` (:930-931). `reach_for_gist` stays in the
    digest and appears on no face. **It counts the RETAINED journal**
    and can go down as rows age out (db/journal.py:93-94 prunes to
    `retention`, default 500) — stated on the face's design, not
    discovered on his desk (C3 note).
  - The `gist`/`key` mismatch fixed (Memory.tsx:86).
  - The correction is durable: restart the hub, it persists and applies.
- Out:
  - The Journal wing's stream, filters and row grammar (HS-176-03).
  - Correction import/export.
  - Correction suggestions from the model (the correction is typed or
    picked by the owner, never generated).
  - Bulk correction editing.
  - Cloud-based correction sync (Article III).
  - Raising the routing Jaccard bar or adding a first-application
    confirm — that is walk question 2 (HS-176-06); 0.5 stands until his
    word.

## Acceptance criteria

- [ ] `CORRECTION_KINDS` is `("intent", "target", "text")` and a `text`
      correction round-trips through `DictationCorrectionRepository`
      and survives a hub restart.
- [ ] A `text` rule applies **deterministically** on the raw transcript
      inside `Pipeline.run` before the first stage, and the router's
      stage receives the corrected words (Article IX.1).
- [ ] The `text` matcher is exact-phrase and **punctuation-stripped**
      (N3): each diff span is stripped of leading/trailing punctuation
      before storing; the key is stored stripped and lowercased; the
      boundary is non-alphanumeric-or-string-edge, so `postgress` fires
      inside `postgress,` and `postgress.` and never inside
      `postgressive`; replace is case-preserving **on the first letter
      only**. It never uses Jaccard, and `best_match_in` is unchanged.
- [ ] The apply path adds no `StageResult` and no `stage_ms` key — the
      text kind is not a pipeline stage (D1's carve).
- [ ] FIELD cycles `TEXT · INTENT · TARGET` (uppercase); TEXT pre-fills
      the **raw transcript** in one StringGadget (N2); INTENT / TARGET
      render a pick over the real enum with human labels and send the
      id.
- [ ] Both run responses carry the raw transcript beside `final_text`
      (_helpers.py:750-770 and :883-896), and the diff runs
      `heard(raw)` vs `said` (N2).
- [ ] The target pick offers **six** ids and never `auto` (N1); a
      `target` correction whose value is `auto` cannot be created from
      the face.
- [ ] `_profile` (target_profile.py:291) uses
      `labels.get(profile_id, profile_id)`: no member of
      `TARGET_PROFILE_OVERRIDE_OPTIONS` can raise `KeyError` on the live
      typing path (dictation_runner.py:389, :565; _helpers.py:811) —
      proven by a regression test that teaches `auto` directly through
      the store and runs a matching utterance (N1 belt).
- [ ] Every routing label on the face is the map's string verbatim —
      `Terminal shell`, never `Terminal` (C12 note).
- [ ] The word-level diff produces the three ruled outcomes: word rule,
      `NO CHANGE`, whole-phrase rule.
- [ ] The teach receipt is `TAUGHT · <heard> -> <said>` (text) or
      `TAUGHT · <label>` (routing) — a token pair, never a sentence
      (rule A.3). `LEARNED` appears nowhere as a receipt or a chip
      (rule A.7).
- [ ] A one-token gist on a routing kind is refused `REFUSED · ONE
      WORD`, **enforced in `CorrectionStore.record`** so both routes and
      the MCP surface inherit it (C7 note); a secret-like teach is
      refused `REFUSED · SECRET` (Article V.3).
- [ ] A refused teach writes **nothing**: no correction row, no
      `taught_from` flag, no `correction_id` linkage (Article VI).
- [ ] The face reads `taught ?? recorded`; both routes are covered by
      unit tests, including the fallback (no `journal_id`).
- [ ] `dictation_journal` gains one additive `corrections_applied`
      column via the declarative schema; the INSERT names every column;
      the canonical snapshot is regenerated.
- [ ] `PipelineRun`'s new field carries a default and the recorder reads
      it as `getattr(run, "corrections_applied", [])`; the pipeline-off
      `passthrough_run` path (journal.py:32-49) does not raise (C5
      note).
- [ ] `CorrectionStore.record`'s new return type is honoured at both
      callers, pipeline.py:996 and :1154 (C4 note).
- [ ] The `APPLIED` chip renders only from the row's stored
      `corrections_applied`, never from `learning` /
      `best_correction_signal` (Article VI.1).
- [ ] `N APPLIED` on the corrections list counts journal rows where the
      rule actually fired; the teaching utterance is not counted; the
      cell is absent at zero (rule A.8). `reach_for_gist` appears on no
      face.
- [ ] The Learned wing carries **no caption count** (N5b) — the tab is
      the name, the rows are the count; `N TODAY` is said once, in the
      footer.
- [ ] The corrections list renders the gist (the `gist`/`key` fix) and
      renders routing values as human labels, never raw ids (rule E.4).
- [ ] The correction count on his desk is > 0 (the census fact paid).
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k correction`
  - A `text` correction is created via the API, persists across
    restart, and applies exact-phrase, whole-word, case-preserving.
  - A `text` rule does NOT fire inside a longer word
    (`postgress` never matches `postgressive`) but DOES fire against
    `postgress,` and `postgress.` and at either string edge (N3).
  - A span carrying attached punctuation is stored stripped and
    lowercased; replace uppercases only the first letter (N3).
  - A `target` correction with value `auto`, forced directly into the
    store, does not raise on the apply path (N1 belt, `_profile`'s
    `labels.get`).
  - `Pipeline.run` hands the corrected `Utterance` to every stage; the
    router sees the corrected words; no `StageResult` is added.
  - `best_match_in` is unchanged and still serves `intent`/`target`
    only; a routing correction still fires by Jaccard at 0.5.
  - A refused teach (secret-like) writes no correction row, leaves
    `corrected` at 0 and `correction_id` NULL.
  - The `corrections_applied` column round-trips as a JSON id list;
    `count_applied` returns a real firing count and excludes the
    teaching utterance.
- Integration: the rig boots a hub, teaches one `text` correction
  through the API, runs a matching utterance through the pipeline, and
  asserts the corrected text lands and the journal row's
  `corrections_applied` names the rule.
- Web unit: the teach row's three FIELD modes; the diff's three
  outcomes; the three refusal receipts; the `APPLIED` chip absent when
  `corrections_applied` is empty.
- Manual: the owner teaches one `text` correction on the Speak face,
  dictates a sentence containing the word, and sees it corrected with
  the `APPLIED` chip.

## Notes / open questions

- The ring buffer cap is 20 (corrections.py:34) and is now shared by
  three kinds. If the owner hits the cap the oldest is evicted; the
  durable store is uncapped and the Learned wing reads it
  (corrections.py:192-214). A per-kind cap is a future candidate.
- The routing Jaccard threshold (0.5) is unchanged. Counsel's
  reproduction shows same-shaped sentences firing across each other
  ("send the note to Dana" → "send the note to Alex", 0.667). That is
  walk question 2, not this story's scope.
- The walk (HS-176-06) confirms `corrections_enabled` before beat 1:
  the config default is `True` (config/meeting.py:389) but every read
  falls back to `False` (dictation_runner.py:336-338,
  _helpers.py:716-720, pipeline.py:1175), so a stale config makes the
  whole loop a silent no-op.
- A text rule's blast radius is larger than a routing nudge's — it
  changes the words he types, on every source, forever, with no
  similarity floor (N4). The guards are exact-phrase matching, the
  `APPLIED` Disclosure naming what fired, and `Forget`. "Should a text
  rule's first application confirm?" rides the walk as question 2.
- The biggest unknown is the `Pipeline.run` seam's blast radius: every
  stage receives the ORIGINAL `Utterance`
  (plugins/dictation/pipeline.py:108), so constructing a corrected one
  touches every stage and every test asserting on `utt.raw_text`. If it
  proves wide, the weaker fallback (correcting only `current_text`,
  leaving the router on the uncorrected transcript) must be said out
  loud, not shipped quietly.
