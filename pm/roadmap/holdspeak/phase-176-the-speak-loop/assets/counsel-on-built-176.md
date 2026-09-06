# Counsel on the built phase — 176 The Speak Loop

Counsel read the working tree on `feat/the-speak-loop` (2026-09-06), HEAD
`3b39422e` plus story 05's uncommitted files. Read-only; every claim carries a
`file:line`; every reproduction ran under an isolated `HOME` on temp databases
and never touched `~/.local/share/holdspeak` or `~/.config/holdspeak`. Scripts
live under
`/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/counsel-built/`.

Canon measured against: Constitution Articles III (local first), IV (voice
first-class; one mic authority), V (consent; refusal by name), VI (honest by
construction), XI (receipts); UX-CANON A.1, A.3, A.7, A.8, A.9, A.10, A.11, B,
C, E.4; the settled design with Addendum 1 (R1–R14) and Addendum 2 (N1–N5).

**Disclosure of working-tree drift caused by counsel.** Running
`scripts/ux_canon_scan.py` (H8) rewrote three files it owns as side effects:
`pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/{ranking.md,violations.json,violations.md}`.
They were **stale in the tree** (they still carry `PeopleCore` debt 17; the
current tree measures 12, i.e. they predate 176-04's fixes), so the new content
is truer than the committed one — but the change is mine, not the build's, and
counsel may not run a git verb that moves the tree. The orchestrator decides
whether to keep or restore them.

---

## VERDICT: BOUNCE

The wire is genuinely good. The `text` kind is a real, deterministic,
exact-phrase matcher at the one funnel every source passes through, and the
corrected `Utterance` really does reach every stage — reproduced: a probe stage
receives `PostgreSQL needs a bump` from a raw `postgress needs a bump`, and
`run.corrections_applied == (5,)` (`plugins/dictation/pipeline.py:115-122`,
`:212-229`). R4's four wire fixes are paid and both teach routes now go through
one `_teach` (`web/routes/dictation/pipeline.py:77-134`). N1's belt is paid
(`target_profile.py:291-296`). The schema is additive and reconciles cleanly on
an older DB (H12, reproduced). The `mic` rule is per-element and reads 0.

The phase's spine is not true on the path the owner actually uses.

1. **`POST /api/dictation/remote` — what pressing `Talk` calls — returns
   `{"success", "final_text", "delivered"}` and nothing else**
   (`holdspeak/web/routes/dictation/pipeline.py:1019`). It carries no
   `raw_text`, no `corrections_applied`, no `journal_id`, although the run that
   produced it computed all three. Consequently, on a real landing:
   - the `APPLIED` chip **never appears** (`useSpeakDeck.ts:165-171` reads
     `result.corrections_applied`) — walk beat 4 fails;
   - the TEXT teach well pre-fills with the **landed** text, not the raw
     transcript (`useSpeakDeck.ts:160-162` falls back to `final_text`) — this
     is exactly the N2 defect the design paid, resurrected on the one path
     that matters; a key harvested there will not match `utt.raw_text` on the
     next run whenever the rewrite pass did its job — walk beats 3 and 4 fail;
   - `teach()` takes the **fallback** route because `journal_id` is absent
     (`useSpeakDeck.ts:443-453`), so `mark_corrected` never runs and the
     Journal row he taught from never wears `TAUGHT` — walk beat 5 fails.
2. **Nothing in the phase proves the real path.** The loop rig latches DRY RUN
   before the loop (`tests/e2e/test_hs176_loop_glass.py:153`, `:260`), the
   Speak rig does the same (`test_hs176_speak_glass.py:172`, `:199`), and the
   only shot of the loop shows `✓ DRY RUN` latched with the footer reading
   `REHEARSED · NOT DELIVERED` (`assets/story-05-shots/loop-speak-1440.png`).
   The full loop is proven on the rehearsal route only.

This is a code fix of an hour, not a redesign: copy `raw_text`,
`corrections_applied` and `journal_id` out of `processed` into the body at
`pipeline.py:1019`, and add one rig beat that lands **without** DRY RUN. The
boards stand; the faces stand. The bounce is on Articles VI and IX — the phase
claims a loop it has not run.

His word outranks counsel. If he rules the rehearsal path is the loop he wants
proven, C1 becomes a P1 to pay before his walk and the verdict lifts to
RATIFY-WITH-CONDITIONS on C2–C4.

---

## Conditions

**P0 — blocks the merge**

- **C1.** `POST /api/dictation/remote` serves `raw_text`,
  `corrections_applied` and `journal_id` beside `final_text`
  (`pipeline.py:1019`; the values are already in `processed`,
  `pipeline.py:953` and `:972`), and one rig beat lands without DRY RUN
  and asserts the `APPLIED` chip, the raw-transcript pre-fill and the
  `TAUGHT` mark on the journal row.

**P1 — pay before the merge**

- **C2.** The Journal's live frame must honour the active source filter
  (`Journal.tsx:330-344`): skip the frame when `source && entry.source !== source`.
  Today a HOTKEY utterance is prepended while the wing shows `BROWSER`.
- **C3.** `REFUSED · SECRET` promises more than the guard delivers. The
  ratified board's own example, `sk-live-4f2a9c`
  (`assets/mockups/SpeakRefused.dc.html`), is **not** refused — reproduced;
  the rig had to substitute `sk-live4f2a9c1b2d3e4f`
  (`test_hs176_speak_glass.py:55`) to make the receipt fire. Widen
  `_looks_secret` (`project_doc_suggestions.py:235-242`) to the common
  credential prefixes (`sk-proj-`, `AKIA`, `ghp_`, `xox[baprs]-`, `-----BEGIN`)
  **or** strike the "verified clean" claim in the design's D4.3 and correct the
  board. A `text` rule's value is stored plaintext, shown on the Learned wing,
  and typed into every future matching utterance.
- **C4.** The footer's `N TODAY` is the **all-time** retained journal count
  (`DictationCore.tsx:71-75, 134` reads `count`, which is `repo.count()`,
  `services/dictation_service.py:77`). 176 removed both wings' caption counts
  on the argument that this is the one true count per face (design D1,
  D2(b).7, N5b) — so the phase's only surviving count is mislabelled. Either
  count today's rows or rename the token (`N SPOKEN`).

**P2 — park to BACKLOG (one line each)**

- **C5.** `APPLIED` can name a rule that changed nothing: a case-only text rule
  fires on already-correct text and is still recorded
  (`corrections.py:246-261`; the docstring at `:211-214` says "actually changed
  the text"). Reproduced. → BACKLOG: *only record a text rule's id when the
  replacement differs from the matched span.*
- **C6.** The intent nudge's *reinforce* branch sets `extras["corrected"]=True`
  even when the block and the confidence are unchanged
  (`builtin/intent_router.py:220-228`), so `APPLIED` can mark a routing nudge
  that did nothing. → BACKLOG: *reinforce only marks `corrected` when it
  actually raised the confidence or changed the block.*
- **C7.** 17 of the 24 `MIC_ALLOWLIST` entries suppress nothing — the rule's own
  `type` filter already excludes them (`ux_canon_scan.py:334-343`). Reproduced.
  → BACKLOG: *trim `MIC_ALLOWLIST` to the 7 load-bearing entries, or add a test
  that every entry suppresses at least one element.*
- **C8.** A pure insertion or deletion becomes a whole-sentence rule that can
  only fire on that exact sentence again (`_helpers.py:1119-1131`), and the
  receipt still reads `TAUGHT`. → BACKLOG: *say `TAUGHT · PHRASE` for a
  whole-sentence rule, or refuse it by name.*
- **C9.** `Learned` subscribes to `learning_event` (`Learned.tsx:164-167`),
  which a `text` teach never emits (`similar` is forced to 0 for `text`,
  `pipeline.py:1378-1382`, and the broadcast is gated on `similar > 0` at
  `:1390`). Dead for the phase's own default kind. → BACKLOG.
- **C10.** After `Forget`, an unresolved id in a still-mounted run renders an
  empty `HEARD`/`SAID` well with a `RULE` chip (`useSpeakDeck.ts:177-192`,
  `SpeakFace.tsx:445-467`). → BACKLOG: *drop unresolved ids from
  `appliedRules`.*
- **C11.** The footer receipt survives a wing switch and masks `N TODAY` on the
  Journal and Learned faces (visible in `assets/story-05-shots/learned-1440.png`:
  `REHEARSED · NOT DELIVERED` on the Learned wing). → BACKLOG.
- **C12.** A teach that 500s after the store already wrote (e.g.
  `repo.mark_corrected`, `pipeline.py:1371`, unguarded) shows
  `REFUSED · nothing written` (`useSpeakDeck.ts:477-481`) though a rule exists.
  → BACKLOG.
- **C13.** `Pipeline.run` returns before the seam when the pipeline is disabled
  (`plugins/dictation/pipeline.py:100-108`), and the hotkey path returns before
  `run()` when the dictation runtime is not loaded
  (`dictation_runner.py:352-357`, `:545-551`) — so a purely lexical text rule
  silently does nothing on both. → BACKLOG: *state it, or apply text rules on
  the passthrough too.*
- **C14.** The design's D2(c).2 requires a search StringGadget on the Learned
  wing; the built wing has none — but the ratified board draws none either
  (`assets/mockups/Learned.dc.html`). The board wins (the 175 law); the design
  line is stale. → correct D2(c).2 in the close.
- **C15.** The Journal row's primary shows the raw transcript while search also
  matches `final_text` (`Journal.tsx:381-393`), so a hit's visible text can lack
  the needle. → BACKLOG.
- **C16.** A frame that arrives between the initial GET and `setRows(items)`
  (`Journal.tsx:305-321` vs `:330-344`) is discarded — the row is missing until
  the next load. Narrow. → BACKLOG.

---

## The hunts

### H1 — Does the text kind apply on the live typing path?

**Ran.** `counsel-built/h1_seam.py` — a probe stage inside a real
`DictationPipeline`.

```
stage saw: ['PostgreSQL needs a bump']
final_text: PostgreSQL needs a bump
corrections_applied: (5,)
pipeline disabled -> final_text: postgress needs a bump | applied: ()
```

**Found.** The seam is where the design put it: `run()` calls
`_apply_text_corrections` before seeding `current_text`
(`plugins/dictation/pipeline.py:115-124`), and `dataclasses.replace` hands the
corrected `Utterance` to every stage (`:229`, consumed at `:134`). The rewrite
pass and the router therefore both see the corrected words. The snapshot
reaches the Pipeline through the same gate the router uses
(`plugins/dictation/assembly.py:103-108`, `:130-139`), and it is threaded on
both live entry points (`dictation_runner.py:334-345`, `:526-537`). So the
answer to "does it work on the hotkey path and not only in the browser" is
**yes** — the seam is source-independent.

**`corrections_enabled=false` disables text rules silently.**
`intent_corrections` is `None` when the flag is off (`assembly.py:105-108`), and
the Pipeline gets that same `None` (`:138`), so the whole `text` kind is off with
it. **The default is `True`** — measured on a fresh isolated HOME:
`enabled=True corrections_enabled=True journal_enabled=True journal_retention=500`.
Every read still falls back to `False` on a missing attribute
(`dictation_runner.py:337`, `:529`), which is why the design's walk beat 0
reads the flag first; that stands.

**Two silent no-ops the design does not name** (severity P2, C13): a disabled
pipeline returns from `run()` above the seam
(`plugins/dictation/pipeline.py:100-108`), and the hotkey path returns before
`run()` when `runtime_status != "loaded"` (`dictation_runner.py:352-357`,
`:545-551`). A `text` rule needs no model, but on a desk whose dictation
runtime does not load it never fires and no journal row is written. The
dry-run/browser route has no such gate (`_helpers.py:835-842` runs the pipeline
regardless), so the same sentence behaves differently on the two paths for a
second reason beyond the `TextProcessor` one the design already records.

**Severity:** the seam itself — no finding. C13 — P2.

---

### H2 — Compounding and order

**Ran.** `counsel-built/h2_h4.py`.

```
rules: "queue for"->Q4 (seq 1, id 11), "q4"->"quarter four" (seq 2, id 12)
input  "the queue for the build is long"
output ('the Quarter four the build is long', (11, 12))     # insertion order
output ('the Quarter four the build is long', (11, 12))     # reversed order
```

**Found.** Deterministic and order-independent: `apply_text_corrections` sorts
by `(len(normalized key), sequence)` descending (`corrections.py:230-234`), so
the ring's load order cannot change the outcome. The ring reload replays
oldest-first (`corrections.py:302-313`) so `sequence` after a restart matches
insertion order; a restart cannot flip the tie-break.

**Compounding is real and is applied to the text as previous rules left it**
(`corrections.py:237-258`) — `queue for → Q4` then `q4 → quarter four` yields
`Quarter four`. The docstring says so (`:209`); the design's N4 carried the
hazard to the owner as walk question 2. No new finding, but note the
first-letter case rule propagates through the cascade (the `Q` of `Q4` makes
`Quarter`), which is a slightly odd artefact of a rule firing on another
rule's output.

A key that is a substring of another rule's value compounds across utterances:
`test → test suite` turns `run the test suite` into `run the test suite suite`
(reproduced). That is the owner's own rule doing what it says; the `APPLIED`
disclosure names it and `Forget` removes it. No condition.

**Severity:** no finding.

---

### H3 — Secrets

**Ran.** `counsel-built/h2_h4.py` plus a direct `looks_like_secret` probe.

```
'Set the token to sk-live-4f2a9c'   -> False      <- the ratified board's example
'AKIAIOSFODNN7EXAMPLE'              -> False
'my api key is 12345'               -> False
'sk-abcdefghijklmnopqrst'           -> True
'access_token abc'                  -> True
CorrectionStore.record("text", "my token is", "sk-live-51H9...") -> stored=True
```

**Found.** The redaction plumbing is right. `filter_secret` runs on
`transcript` and `final_text` before the repository call
(`plugins/dictation/journal.py:211-212`), and the bus frame is built from the
**stored row** (`journal.py:129-152`, emitted at `:231`), so a redacted field
cannot be bypassed onto the wire. `/ws` admits owner principals only
(`web/routes/system/ws.py:52-56`). The store refuses a secret on either side
(`corrections.py:344-345`). The design's audience note stands.

**The guard itself is much narrower than the phase's own face promises.**
`_looks_secret` is one regex over five name-shaped patterns
(`project_doc_suggestions.py:235-242`). The board `SpeakRefused.dc.html` draws
`Set the token to sk-live-4f2a9c` → `REFUSED · SECRET`; that string is not
refused (the hyphen after `live` breaks `sk-[a-z0-9]{16,}`). The rig had to
substitute `sk-live4f2a9c1b2d3e4f` (`test_hs176_speak_glass.py:55`) — the build
worked around the board rather than reporting it. Real-world shapes that pass:
`sk-proj-…`, `AKIA…`, `ghp_…`, `xoxb-…`, a bare 40-char hex token.

What 176 changes about the stakes: before this phase a correction's value was a
block id or a profile id; now it is **free text that the desk types for him on
every future matching utterance**, is displayed verbatim on the Learned wing
(`Learned.tsx:205-207`), and is stored plaintext in `dictation_corrections`.
Nothing leaves the machine (Article III holds), so this is local plaintext, not
egress — but a named refusal the owner will trust is mostly decorative.

A whole-phrase rule can absolutely store a secret-looking sentence: the diff
takes the full heard/said text as key/value (`_helpers.py:1129-1131`) and only
the same weak check stands between it and the store.

**Severity:** P1 (C3) — widen the check, or bound the claim and fix the board.

---

### H4 — The diff

**Ran.** `counsel-built/h2_h4.py`, `diff_text_correction` on eight shapes.

| case | heard → said | rule |
|---|---|---|
| punctuation + case only | `hello world.` → `Hello world!` | phrase `hello world` → `Hello world` |
| case only | `postgress needs a bump` → `Postgress …` | word `postgress` → `Postgress` |
| one word | `postgress needs a version bump` → `PostgreSQL …` | word `postgress` → `PostgreSQL` |
| pure insertion | `needs a bump` → `needs a version bump` | **phrase** (full sentence) |
| pure deletion | `needs a version bump` → `needs a bump` | **phrase** (full sentence) |
| 2 of 4 tokens | `a b c d` → `a X Y d` | word `b c` → `X Y` |
| 3 of 4 tokens | `a b c d` → `a X Y Z` | phrase (full sentence) |
| 1 of 2 tokens | `postgress bump` → `PostgreSQL bump` | word `postgress` → `PostgreSQL` |

**Found.** The ≤ half-tokens boundary is `(i2 - i1) * 2 <= len(heard_tokens)`
(`_helpers.py:1125`) and behaves as the design says at both edges. N3's
punctuation stripping is real (`_strip_span`, `:1077-1079`) and the key is
lowercased at `:1136`. A pure-case-or-punctuation difference is **not**
`no_change`: `key_raw == value` is compared case-sensitively (`:1133`), so
`postgresql → PostgreSQL` is stored — and that rule then fires on
already-correct text (H6).

**The pure-insertion / pure-deletion outcome is dead weight, and it should say
so.** A whole-sentence rule keyed on 24 words fires only when the owner utters
that exact sentence again — vanishingly unlikely for dictation. The receipt
still reads `TAUGHT · <40ch>… → <40ch>…`, which reads like a rule that will
help. It is honest about what was stored and dishonest about what it will do.
Say `TAUGHT · PHRASE`, or refuse a >N-token phrase rule by name.

**Severity:** P2 (C8).

---

### H5 — The two teach routes

**Read.** `pipeline.py:77-134` (`_teach`), `:1114-1162` (fallback),
`:1306-1420` (journal correct), `useSpeakDeck.ts:442-484`.

**Found — this is the cleanest part of the build.** Both routes go through the
one `_teach`, so the diff, the refusal vocabulary and the stored-id linkage
cannot drift (`:112-134`). Both answer with `recorded` as the canonical key
(`:139`, `:1406`); `taught` survives only as the journal route's mirror
(`:1407`). `mark_corrected` is inside `if recorded` (`:1370-1371`) and the id is
`record()`'s own, not `list_for_display()[0]` (`_helpers.py:1178-1211`).
`RecordOutcome` stays truthy-compatible (`corrections.py:88-89`), so the C4
contract change is safe. `_newest_correction_id` survives only on the
accepted branch of the legacy shape (`_helpers.py:1211`) — R4's actual defect
is gone.

**On HTTP 5xx** the face shows `REFUSED · nothing written`
(`useSpeakDeck.ts:477-481`). That is true for every refusal the routes name,
and false in exactly one case: a 500 raised **after** `record()` succeeded —
`repo.mark_corrected` at `pipeline.py:1371` is unguarded, as is
`reach_for_gist` at `:1378`. Narrow, but the receipt then lies about a written
rule.

**Severity:** the routes — no finding. The 5xx-after-write receipt — P2 (C12).

---

### H6 — `APPLIED` and `N APPLIED` honesty

**Ran.** `counsel-built/h2_h4.py`.

```
rule: "postgresql" -> "PostgreSQL"   (a case-only rule the diff will happily store)
input  'the PostgreSQL schema'
output ('the PostgreSQL schema', (7,))   text changed? False
```

**Found.**

1. **A firing that changed nothing is still recorded.**
   `apply_text_corrections` sets `fired` on a bounded match regardless of
   whether the replacement differs (`corrections.py:246-256`) and appends the
   id at `:259-261`; `_apply_text_corrections` returns `applied` even when
   `corrected == utt.raw_text` (`pipeline.py:227-228`). The docstring claims the
   ids are "the rules that actually changed the text" (`corrections.py:211-214`).
   So the `APPLIED` chip and `N APPLIED` can both count a no-op — and H4 shows
   the diff readily produces exactly the rule that triggers it.
2. **The routing nudge's reinforce branch is worse.**
   `_apply_correction_nudge` sets `extras["corrected"] = True` in the reinforce
   branch (`builtin/intent_router.py:220-228`) even when the block already
   matched and `min(1.0, max(confidence, 0.85))` leaves the confidence
   untouched. `_intent_correction_id` then names the rule
   (`pipeline.py:231-252`) and the recorder writes it (`journal.py:109-115`).
   `APPLIED` on a run where nothing was corrected. Pre-existing behaviour that
   176 newly surfaces as a chip.
3. **`N APPLIED` itself is honest.** `count_applied` matches ids in Python over
   the parsed JSON arrays, so `12` cannot be counted as a hit for `1`
   (`db/journal.py:241-262`) — reproduced: `count_applied(7)=1`,
   `count_applied(79)=0` on a row holding `[7, 9]`. The list route computes it
   in one pass (`pipeline.py:1194-1216`). The teaching utterance is genuinely
   not counted. The C3 note (it counts the *retained* journal and can go down)
   is stated in code (`db/journal.py:246-248`) and on the design.
4. **`Forget` leaves ids dangling** in `corrections_applied` on old journal
   rows. On the Journal face that is fine — the row records that a rule fired,
   which is true. On the Speak face the `APPLIED` well then renders an unresolved
   rule as empty `HEARD`/`SAID` plus a `RULE` chip (`useSpeakDeck.ts:177-192`;
   `SpeakFace.tsx:445-467` uses `(rule.kind || "rule").toUpperCase()`). Reaching
   it needs a `Forget` without leaving the Speak face, which the wing structure
   makes hard, so it is narrow.

**Severity:** 1 and 2 — P2 (C5, C6). 3 — no finding. 4 — P2 (C10).

---

### H7 — The bus

**Read.** `plugins/dictation/journal.py:129-246`, `web_server.py:240-249`,
`runtime/RuntimeBus.tsx:31-39`, `Journal.tsx:305-379`.

**Found.**

- **One frame per record on every source.** The recorder is the single write
  chokepoint (`journal.py:209-232`) and `_emit` fires from it (`:231`); the one
  instance is built with `broadcast=self.broadcast` at `web_server.py:246-249`
  and shared by all five call sites via `server.dictation_journal`. So hotkey,
  dictation, browser and dry-run all emit. The frame is built from the stored
  row, so redaction and the row id are both guaranteed.
- **Lifecycle is clean.** `subscribe` returns its unsubscribe
  (`RuntimeBus.tsx:31-39`), is `useCallback([])`-stable, and both wings return
  it from their effect (`Journal.tsx:330-344`, `Learned.tsx:164-167`). No
  double subscribe, no leak. Only one wing is mounted at a time
  (`DictationCore.tsx:110-120`), so a wing switch is a remount and a fresh
  read — which is also why the `TAUGHT` mark appears correctly after a teach.
- **A frame arriving while the wing is filtered to another source is shown
  anyway.** The handler prepends unconditionally (`Journal.tsx:332-341`); it
  never compares `entry.source` to `source`. Select `BROWSER`, speak on the
  hotkey, and a `HOTKEY` row appears in a `BROWSER`-filtered stream. The filter
  is the face's one honest claim about what it is showing.
- **The initial-load race** drops a frame that lands between the GET and
  `setRows(items)` (`:313` replaces the array). Narrow; the row returns on the
  next load.

**Severity:** the filter leak — P1 (C2). The race — P2 (C16).

---

### H8 — The ratchet and the mic law

**Ran.** `scripts/ux_canon_scan.py` (totals below), plus
`counsel-built/h8_allow.py` and `h8_gap.py`, which drive `scan_mic` directly
over `web/src/**/*.tsx`.

```
Totals per rule: B: 32  A8: 24  emoji: 21  raw-ids: 16  A3-prose: 11
                 A1: 4  C: 4  A3-sentence: 1        (mic absent = 0)
with the 24-entry allowlist: mic violations = 0
with NO allowlist:           mic violations = 7
dead entries (suppress nothing): 17
```

**Found.**

- **`mic: 0` is real,** and every ceiling entry is at or under
  (`tests/ux_canon_ceiling.json` holds `A8: 25 / B: 34` against a measured
  24 / 32 — headroom, not a breach). The four rule defects are paid: `<textarea`
  matches (`ux_canon_scan.py:334`), the species are not counted as uncovered
  (`:345-348`), the emit is per element (`:350-366`), and the `classify_face`
  gate is gone.
- **17 of the 24 allowlist entries suppress nothing.** Every radio, checkbox,
  number, range, date, password and file entry is already excluded by the
  rule's own `type` filter at `:336-342`, before the allowlist is consulted.
  The honest number is a **7-entry** allowlist (both `Signal.tsx` dead exports,
  the cron field, both `CalendarSnapshotReviewCore` HH:MM fields, the
  `SettingsCore` glyph, and the Speak well). The 17 are not merely decorative:
  they are latent blind spots — if `TopologyMapView`'s provider input ever
  became `type="text"`, the entry keyed on `placeholder="Provider"` would
  silently allow it.
- **The component-scoped coverage gap is bounded and benign.** Measured across
  the tree, exactly one component has more raw text elements than MicButtons:
  `desk/surface/Surface.tsx::EditInPlace` (2 elements, 1 MicButton) — the
  library's own input/textarea pair, only one of which renders. C's worry does
  not bite today; `ThoughtDocumentPane` is covered.
- **The Speak well's opt-out fails safe in one direction and silently in the
  other.** The needle is `label="Utterance"` (`ux_canon_scan.py:214`): rename
  the label and the scanner *flags* the well (good). Remove `mic={false}` and
  the element stops being a candidate at all — no violation, a third mic back
  on the face. That hole is covered by `speakWellMic.test.tsx` and by the loop
  rig's `.speak-well .desk-mic` count assertion
  (`test_hs176_loop_glass.py:283`), so it is fenced — but not by the scanner.

**Severity:** the dead entries — P2 (C7). The rest — no finding.

---

### H9 — Every face against canon

**Read.** `SpeakFace.tsx`, `Journal.tsx`, `Learned.tsx`, `Memory.tsx`,
`FilterTokens.tsx`, `DictationCore.tsx`; the shots in
`assets/story-0{2,3,5}-shots/` beside `assets/mockups/`.

**Found.**

- **A.1 — every verb a library Button.** No raw `<button>` anywhere in the new
  faces (grepped). `FilterTokens` is a `role="group"` of library Buttons with
  `aria-pressed` and no sparse rule (`FilterTokens.tsx:52-71`), promoted and
  documented in `web/src/desk/surface/contract.md` as canon B requires. R6 is
  paid properly.
- **A.7 — the name said once.** `LEARNED` appears only as the wing tab; the
  receipt is `TAUGHT` and the chip is `APPLIED` (`shared.ts:111-133`). Both
  wings drop their caption counts (`count={null}`, `Journal.tsx:442`,
  `Learned.tsx:179`), paying N5b. `TAUGHT` on a Journal row and `TAUGHT` as a
  Speak receipt never coexist on one face — different wings, one mounted at a
  time.
- **A.8 — no counters of zero.** `appliedToken` returns "" at zero
  (`Learned.tsx:77-80`); `countToken` nulls at zero. The Journal's `MS` cell is
  guarded by `took > 0` (`Journal.tsx:181-183`).
- **A.11 — no verb with nothing to do.** `Clear` is withheld on the quiet
  Journal (`Journal.tsx:435`, `:452-458`); `Review` now crosses to the Journal
  wing (`DictationCore.tsx:166-175`), paying D2(b).9.
- **A.3 — prose.** The replay preview is tokenised (`REPLAY · PREVIEW` /
  `NO TEXT`, `Journal.tsx:236-248`), paying C11. The receipt tails read
  `nothing written` in lowercase (`shared.ts:129-132`) — the ratified boards
  draw exactly that string, so it is his, not a drift. `OK` still announces
  `Marked OK` (`SpeakFace.tsx:563-566`), inherited from 170.
- **A.9 — egress.** `THIS DEVICE` on the footer plus the ENGINE row's
  `EgressChip` — two chips on the Speak face, explicitly sanctioned by the
  design's D1 (different facts: the desk's boundary and the engine's host). The
  Journal, Learned and the bus frame carry none, as ruled.
- **E.4 — labels, never ids.** `landedLabel` and `valueLabel` resolve through
  readiness `target.overrides` and the blocks' descriptions
  (`Journal.tsx:101-106`, `Learned.tsx:62-74`), with `deSnake` as the floor. The
  loop rig asserts no `claude_code` / `dry_run` reaches the face
  (`test_hs176_loop_glass.py:194-195`).
- **393.** The phone shot follows 170's `SpeakPhone` with the transport at the
  foot and `Open` beside `Talk` (R14) — `assets/story-05-shots/loop-speak-393.png`.
  The rigs assert zero element overlaps at both widths
  (`test_hs176_loop_glass.py:241`). Dense hit targets remain the library
  question D4.10 parked.
- **The one dishonest count on the face** is `N TODAY` — see C4.
- **The footer receipt is sticky across wings** — `REHEARSED · NOT DELIVERED`
  is still on the footer of `learned-1440.png`, masking the count the design
  says that footer is for.

**Severity:** `N TODAY` — P1 (C4). The sticky receipt — P2 (C11). The rest —
no finding.

---

### H10 — The replacing faces keep their verbs

**Read.** `git diff 7a47904e -- web/src/pages/cores/dictation/Memory.tsx`,
`Journal.tsx`, `Blocks.tsx`.

**Found.** The Configure door loses the corrections `GadgetTable` and its
`ConfirmVerb` — both re-appear on the `Learned` wing with a fuller grammar
(`Learned.tsx:188-229`), and `Forget` gains the word in place of the `×` glyph.
The digest stays behind the gear (`Memory.tsx:52-64`). Nothing else in the door
is touched; `Readiness`, `Knowledge`, `Runtime`, `Hooks`, `Nudges` are
untouched (`DictationCore.tsx:50-61`). The long-standing `gist` / `key` defect
dies with the table (the wing reads `row.key`, `Learned.tsx:199`).

The Journal's opened row keeps `EditInPlace`, `Replay`, `Copy` and `Delete`
(`Journal.tsx:207-235`) plus the replay preview and its `Copy result`
(`:236-260`). The 175 law is honoured. Blocks is untouched.

One design/board disagreement: D2(c).2 requires a search StringGadget on the
Learned wing; the wing has none — and neither does the ratified board
(`assets/mockups/Learned.dc.html` renders only tabs, rows and the footer). Per
the 175 law the board wins; the design line is stale.

**Severity:** no finding (C14 is a doc correction at the close).

---

### H11 — The walk: the first three things likely to go wrong on his desk

1. **He presses `Talk`, not `Rehearse`, and the loop does not show.** No
   `APPLIED` chip, a teach well pre-filled with the landed text, and no
   `TAUGHT` on the journal row — see C1. This is the walk's beats 3, 4 and 5.
   It is also the reason the shots look right: they were taken with DRY RUN
   latched.
2. **The footer reads `N TODAY` over his all-time journal.** His desk has a
   real journal with retention 500; the footer will say whatever
   `SELECT COUNT(*)` returns, labelled TODAY — see C4. Counsel did not read his
   database (forbidden), so the number is unknown; the mislabel is not.
3. **A word he teaches may not fire on a different source.** A rule taught from
   a HOTKEY landing is keyed on post-`TextProcessor` text and a BROWSER landing
   is not (the design's P2 paragraph), and — new — if his dictation runtime is
   not loaded on the hotkey path, `Pipeline.run` is never reached at all
   (C13). Exact-phrase makes the failure a visible non-firing (no chip) rather
   than a wrong word, which is the right failure mode, but he will read it as
   "it did not learn".

Worth adding to the runner: beat 0 already reads `corrections_enabled`; it
should also assert the landing beat ran **without** DRY RUN, or the leg proves
the rehearsal path a second time.

---

### H12 — The schema

**Ran.** `counsel-built/h12d.py` — built a schema-75 database from `SCHEMA_SQL`
with the new column stripped, inserted a row, opened it through `Database`.

```
before reconcile: [... 'warnings', 'corrected', 'correction_id']
after  reconcile: [... 'warnings', 'corrected', 'correction_id', 'corrections_applied']
existing row value: [(1, '[]')]
new row: 2 [7, 9]        old row read back: 1 []
count_applied(7) = 1     count_applied(79) = 0
```

**Found.** Clean. `SCHEMA_VERSION = 76` is informational and the reconcile is
shape-based (`db/schema.py:11`, `:859`); the column is `TEXT NOT NULL DEFAULT
'[]'`, so an older DB backfills correctly and the reconcile takes its own
backup first. The INSERT is fully named — 14 named columns, 14 placeholders,
`corrected`/`correction_id` as literals (`db/journal.py:105-128`);
`tests/unit/test_no_positional_inserts.py` passes. The read is defensive of a
row shape without the key (`db/journal.py:29-55`), and `count_applied` parses
rather than `LIKE`s (`:241-262`).

Focused suite, isolated HOME:

```
HOME=$(mktemp -d) uv run pytest -q tests/unit/test_hs176_text_correction.py \
  tests/unit/test_hs176_routes.py tests/unit/test_no_positional_inserts.py \
  tests/unit/test_db_schema_policy.py tests/unit/test_ux_canon_ratchet.py
83 passed in 124.60s (0:02:04)
```

**Severity:** no finding.

---

## What counsel could not verify

- **The owner's real database.** Forbidden by the brief; the `N TODAY` number
  and his `corrections_enabled` value on his own config are unknown, not
  broken.
- **A real `Talk` landing.** No dictation runtime loads under an isolated HOME,
  so C1 is proven by reading the response body's construction
  (`pipeline.py:1019`) and the face's readers (`useSpeakDeck.ts:160-171`,
  `:443-453`), not by a live delivery. The absence of the three keys from the
  body is textual and certain; the downstream consequence is inferred from the
  readers.
- **The e2e rigs were not re-run** (the brief scoped counsel to the focused
  tests); their assertions are quoted from source, and story 05's evidence
  records `40 passed` for the three glass rigs plus the ritual fences.

---

## Counsel's re-read (2026-09-06, after the fixes)

Read at commit `3a573eb4` on `feat/the-speak-loop`. Read-only; reproductions
under an isolated HOME. Focused re-runs: `99 passed in 28.34s`
(`tests/unit/test_hs176_routes.py`, `test_hs176_text_correction.py`) and
`30 passed` (`web` vitest, `speakFaceTeach.test.tsx` + `journal.test.tsx`).

**VERDICT: RATIFY-WITH-CONDITIONS — C2, C3, C4, C14 and the P2 parking are
paid; C1 is paid for the TYPED landing and NOT PAID for the SPOKEN one, which
is the walk's own beat 1.**

### C1 — the delivery reply carries the loop's three facts — **NOT PAID (half)**

**Paid, and paid well, for a typed utterance.** `processed` is kept
(`holdspeak/web/routes/dictation/pipeline.py:934`) and the terminal body now
carries `raw_text`, `corrections_applied` and `journal_id` from the run that
computed them (`:1029-1038`) — never recomputed. Proven at the route
(`tests/unit/test_hs176_routes.py:540-582`, including that `journal_id` names a
real row the journal correct route then accepts, `:562-583`) and at the face
(`web/src/pages/cores/dictation/__tests__/speakFaceTeach.test.tsx:264-300`).
The ruling that no rig may type into the machine's focused window is accepted;
these are the right substitutes.

**Not paid for a spoken utterance, and that is the Tuesday.** The Speak
transport's `onText` is `deck.onReleased` (`SpeakFace.tsx:348`), which delivers
with `{ pipelined: true }` (`useSpeakDeck.ts:335`), which sends `raw: true`
(`:295`). The `raw` branch returns its own body — `{success, final_text,
delivered}` plus the receipt — and returns **before** the C1 code
(`pipeline.py:835-846`). The build knows this and fences it:
`test_remote_verbatim_send_carries_no_run_facts`
(`tests/unit/test_hs176_routes.py:586-598`). The branch is right not to invent
facts: it runs no pipeline. **The facts exist elsewhere and are thrown away.**
The spoken leg already ran the pipeline and wrote the journal row inside
`process_transcript` (`holdspeak/web/routes/system/voice_stream.py:333-343`),
and then answers the browser with `{"type":"final","text": final_text}` and
nothing else (`voice_stream.py:362`).

So on his walk, pressing `Talk` and speaking: the words land corrected (the rule
does fire), but the `APPLIED` chip is absent, `Wrong` pre-fills the TEXT well
from the LANDED text rather than the raw transcript, and `Teach` goes to the
corrections fallback so the journal row never wears `TAUGHT` — beats 3, 4 and 5
of D5, exactly the three the bounce named.

**Exact fix:** `voice_stream.py:362` sends `raw_text`, `corrections_applied` and
`journal_id` on the `final` frame (they are all in reach at `:333-343`);
`MicButton`'s `onText` carries them; `onReleased` seeds `result` from them
rather than from the verbatim delivery reply. Alternatively `process_transcript`
returns the facts and the stream forwards them. Either way it is one frame, not
a redesign. **A read-time lookup of "the newest journal row" is not an
acceptable substitute — R2 forbids it.**

### C2 — the live frame honours the filter — **PAID**

`frameMatchesSource` gates the subscription (`Journal.tsx:136-139`, applied at
`:401`). C16 is paid with it: a frame racing an in-flight read is buffered in
`pending` and merged against the response's ids (`:323`, `:355`, `:366-368`,
`:402-406`), with a `loadSeq` guard so a stale response cannot overwrite a
newer one (`:353`, `:363`). C15 is paid too: a hit that lives only in
`final_text` wears `IN FINAL` (`matchedFinalOnly`, `:144-150`; rendered at
`:231-233`). The search deliberately has no frame gate, and the comment says
why (`:391-395`) — `filtered` re-applies the needle, so the behaviour is
consistent rather than special-cased.

### C3 — `REFUSED · SECRET` refuses what the board promises — **PAID-WITH-NOTE**

`_looks_secret` is now three regexes (`project_doc_suggestions.py:250-289`):
the old name-shaped words, a case-insensitive prefix set (`sk-`, `gh[pousr]_`,
`github_pat_`, `xox[abeprs]-`, `glpat-`) and a case-sensitive one (`AKIA`,
`AIza`), each token-bounded and requiring a ≥6-char run. Reproduced — all ten
credential shapes now refuse, the board's own `sk-live-4f2a9c` included:

```
OK    'Set the token to sk-live-4f2a9c'      OK    'ghp_16CharsAtLeastHere'
OK    'sk-proj-abc123def456'                 OK    'xoxb-123456-abcdef'
OK    'AKIAIOSFODNN7EXAMPLE'                 OK    'AIzaSyD-abcdefghijk'
OK    'glpat-xxxxxxxxxxxxxxxx'               OK    '-----BEGIN RSA PRIVATE KEY-----'
```

**False positives, hunted deliberately.** Fifteen ordinary architect sentences
(the PostgreSQL bump, the scikit-learn spike, "Ask Priya…", "risk-averse
posture", "The API key rotation runbook is out of date", "Rotate the
credentials after the migration", the Alaska vendor, the Q4 cut) produced
**one** flag — `"…deferring the AKIA-style access review"` — and a synthetic
`"sk-ipping is fine"`. Both need a credential prefix glued to a ≥6-character
word at a token boundary; the ≥6 run is what saves `sk-learn`, `ghp_owner`,
`glpat-form` and `xox-team`, all of which I tried and none of which flags. That
is a good trade.

**The note, because the blast radius grew.** This function also gates
`filter_secret`, which redacts the **whole field** (`plugins/dictation/journal.py:53-60`),
so one false positive costs an entire transcript in his journal, not a
substring — and it now gates project-doc suggestions product-wide, not only
176's corrections. The widening is right; it should be named in the phase close
as a product-wide change, and `AKIA`/`AIza` are the two entries most likely to
catch prose (they are ordinary letter runs, unlike `ghp_` or `glpat-`).

### C4 — the footer's `N TODAY` is today — **PAID**

`count_today` counts rows on the **local calendar day**, resolving the zone per
instant (`db/journal.py:241-271`) and converting an offset-bearing legacy row
before taking its date; `count` stays the all-time retained total for Export and
the trust statement. The service serves both, with a `getattr` fallback for a
repository double (`services/dictation_service.py:74-97`), the route forwards
`today` (`web/routes/dictation/pipeline.py:1280`), and the footer reads it
(`DictationCore.tsx:78`, `:137`) through `countToken`, so it is still absent at
zero (A.8).

### C14 — the design corrected — **PAID**

D2(c).2 now reads "**Controls slot:** none. No search well on the Learned wing:
the ratified boards … draw none, and the board wins over this text"
(`assets/settled-design-speak-loop.md:400-403`).

### C5–C13, C15, C16 — parked — **PAID**

All twelve are in `pm/roadmap/holdspeak/BACKLOG.md:1011-1024` under
"AG. Phase 176 remainders", each with its seam and its fix. C15 and C16 were
additionally *fixed* by the C2 lane and their backlog lines say so honestly
("a `MATCHED · FINAL` token was added"; the token as shipped reads `IN FINAL`,
a one-word drift between the backlog entry and the code). The lane also parked
two stale code comments and the `DICTATION_PIPELINE_GUIDE.md` §12 rewrite,
which counsel had not found — good.

### New findings from the fixes

- **N1 (P1, folded into C1 above).** The spoken landing carries no run facts,
  because it delivers `raw: true`. Named here rather than left inside C1: the
  fix lives in `voice_stream.py`, not in the delivery route, so it is a
  different lane from the one that paid C1.
- **N2 (P2 → BACKLOG).** A spoken utterance from the Speak face journals with
  source **`browser`** (`voice_stream.py:332` passes `source="browser"` to
  `process_transcript`, which forwards it verbatim, `dictation_runner.py:250-251`).
  D5 beat 5 tells him to filter the Journal to `DICTATION` to see the two
  utterances he just spoke; they will be under `BROWSER`. Either re-tag the
  Speak face's streaming leg or correct the walk script. → BACKLOG: *the Speak
  face's spoken utterances journal as `browser`; beat 5's DICTATION filter
  hides them.*
- **N3 (no finding, noted).** `count_today` reads every retained row's
  `created_at` and parses it in Python (`db/journal.py:257-271`) — ≤ 500 rows
  per footer read, so cheap; worth an index-friendly `WHERE created_at >= ?`
  only if retention ever grows.
