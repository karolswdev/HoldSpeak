# Counsel on the design — 176 The Speak Loop

Counsel read `assets/settled-design-speak-loop.md` (SETTLED @ `7a47904e`),
`assets/mic-census-176.md`, all fifteen boards under `assets/mockups/`
(rendered headless at their canvas sizes and read), and the code every
claim points at. Read-only; no git verb touched the tree; the two
reproductions ran as pure-Python Jaccard arithmetic (no DB, no HOME).

Canon measured against: Constitution III (local first), IV (voice
first-class, one mic authority), V (consent, refusal by name), VI
(honest by construction; copy never promises what the code does not
do), VII (no prose, no modals), IX (proof over claim), XI (receipts);
UX-CANON A.1, A.2, A.3, A.7, A.8, A.9, A.10, A.11, B, D, E.4; the
175 law "a replacing face keeps its verbs".

---

## VERDICT: BOUNCE — one reason (P0-1). Conditions C2–C14 hold either way.

**The Tuesday moment cannot happen on this wire.** Both correction
kinds are *routing* corrections whose `value` must be a member of a
closed set: `intent` requires a loaded **block id**
(`intent_router.py:215` — `if match is None or match.value not in
valid_ids: return intent, None`), `target` requires one of seven
**profile ids** (`target_profile.py:26-34`, checked at `:149`). The
design's D0, D2(a) and six of the fifteen boards have the owner typing
free text — the corrected *sentence* — into a StringGadget labelled
`Correct value` and pressing `Teach`. That records a correction whose
value is in neither set, so `_apply_correction_nudge` and
`apply_target_correction` both return unchanged **forever**. `Q4` never
lands right; the `LEARNED · 1` chip on `SpeakApplied.dc.html` can never
render from that teach; D5 beat 4 fails live on his desk.

This is already true on main: the built well's placeholder is `Terminal`
(`SpeakFace.tsx:504`) while the only accepted value is `terminal_shell`.
The teach loop 170-04 shipped is dead for any owner who types what the
placeholder tells him to type.

The fix is a design change, not a code fix: the correction field is a
**pick over the real enum** (blocks for `intent`, the seven profiles for
`target`), rendered with human labels and sent as the id. That redraws
D0, D2(a), and `SpeakWrong` · `SpeakLoopPhone` · `SpeakLearned` ·
`SpeakTaughtShort` · `SpeakRefused` · `SpeakApplied`. Nine boards
(Journal ×4, Learned ×3, Mic ×2) stand, subject to the conditions.

If the orchestrator instead rules that 176 adds a **third correction
kind** that rewrites text, that is a new store kind + a new pipeline
stage + a new apply path — outside story 02's `M`, and it must be said
out loud rather than implied by the boards.

---

## The conditions

| # | Condition | Sev |
|---|---|---|
| C1 | The correction field becomes a pick over the real enum (block ids / the seven target profiles), human-labelled, id on the wire. D0 + six Speak boards redrawn. | **P0** |
| C2 | The row/RESULT chip renders from a **stored per-run fact**, never from `learning` — `best_correction_signal` is a "would match" computed at read time and paints rows recorded before the correction existed. | P1 |
| C3 | `N APPLIED` on the Learned wing is `reach_for_gist` — *similar journal transcripts*, not applications, and it counts the teaching utterance itself (similarity 1.0). Relabel `REACHES N`, and drop `· N` from the per-row chip entirely. | P1 |
| C4 | The refusal receipt reads the wrong key, and a refused teach still writes. On the primary route the key is `taught` (`pipeline.py:1195`), not `recorded` (`:997`); and `mark_corrected` fires unconditionally (`:1162`), linking `correction_id` to somebody else's newest row (`:1159`). | P1 |
| C5 | `corrected` is overloaded: today it means "he taught from this row"; 176 wants it to mean "a correction fired here". Two opposite facts, one column. Also `DictationJournalRepository.record` writes `corrected` as a hardcoded `0` (`db/journal.py:73`) — the design names no seam for the new value. | P1 |
| C6 | `LedgerFilterBar` is not the species the design and boards assume: no toggle mode, its own raw `<input>`, `×`-removable chips, and it returns `null` below 5 items. | P1 |
| C7 | `SHORT PHRASE · MATCHES BROADLY` is arithmetically false. Under Jaccard-union a short gist matches *fewer* things. The real false-positive class is same-shape sentences at exactly 0.5. | P1 |
| C8 | `LEARNED` means three different things on one face (wing name, teach receipt, applied chip). Rule A.7. | P1 |
| C9 | The scanner's `mic` flag never matches `<textarea>` (`ux_canon_scan.py:360-363`) — 3 of the 8 gap sites are textareas — and counts `<StringGadget` as an uncovered input. | P1 |
| C10 | D5's "the walk writes nothing except the one correction" is false: every beat that dictates writes a journal row. State the true write set. | P1 |
| C11 | D2(b) drops the opened row's `Replay` / `Copy` / `Delete` in silence. The 175 law: a replacing face keeps its verbs. | P1 |
| C12 | The Learned wing draws `Delivery` / `Terminal` / `Calendar`; the wire serves `value` raw. Name the id→label source or the wing prints `terminal_shell` (E.4). | P1 |
| C13 | Rule D4 hunt 5 in D2: the utterance well takes `mic={false}` (the boards already draw it mic-less; the built well has one). | P1 |
| C14 | `SpeakLoopPhone` drops the `Open` latch and moves the transport to the bottom. D2(e) says only "the transport stacks". | P1 |

---

## The hunts

### H1 — a correction that rewrites unrelated text

**Read:** `corrections.py:58-94` (`_tokens`, `similarity`,
`best_match_in`), `intent_router.py:34-35, 206-234`,
`target_profile.py:126-151`, `SpeakTaughtShort.dc.html`, D4 hunt 1.

**Found.** `similarity` is Jaccard over the **union** of both token sets
(`corrections.py:67`). The design's caution therefore points the wrong
way. Reproduced (pure arithmetic, no state):

```
0.500  'ship the Q4 platform on schedule' ~ 'ship the q4 platform on schedule'   (identical → 1.000)
0.333  'ship the Q4 platform on schedule' ~ 'the platform'      ← short gist does NOT fire
0.500  'the platform is down'             ~ 'the platform'      ← it fires only on SHORT utterances
0.500  'open the browser'                 ~ 'open the terminal' ← FIRES
0.667  'send the note to Dana'            ~ 'send the note to Alex' ← FIRES
0.500  'cut the scope'                    ~ 'cut the build'     ← FIRES
```

A short gist matches **narrowly**, not broadly — `SHORT PHRASE ·
MATCHES BROADLY` on `SpeakTaughtShort.dc.html` is a claim the code
contradicts (Article VI.3, rule A.10). The real hazard is the opposite
one the design never names: two *same-shaped* sentences differing only
in the payload word clear 0.5 at ordinary length. A `target`
correction taught on "send the note to Dana" redirects "send the note
to Alex". That is a wrong-recipient delivery under Article V.

**Is a 1-token gist ever useful?** Effectively never. A 1-token gist can
only reach 0.5 against an utterance of ≤2 tokens (`'platform' ~ 'the
platform'` = 0.500; `~ 'deploy the platform'` = 0.333). It cannot fire
on a sentence. It is dead weight in a 20-slot ring.

**Sev: P1 (C7).** **Change:** replace the token's text with the true
fact — `2 TOKENS · MATCHES SHORT UTTERANCES` (or `· RARELY FIRES`) —
and add the caution the arithmetic actually justifies: when the taught
gist differs from an existing correction's gist by ≤1 token, say so.
Refuse a 1-token gist **by name** (`REFUSED · ONE WORD`, Article V.3,
the 175 R1 precedent) rather than storing something that cannot fire.

---

### H2 — the teach path: two routes, two receipts

**Read:** `useSpeakDeck.ts:291-318`, `pipeline.py:978-997`
(corrections route), `pipeline.py:1122-1201` (journal route),
`corrections.py:145-165`.

**Found, three things.**

1. **The gist is not what he types.** The primary route teaches from
   `entry.transcript` — `recorded = store.record(kind, entry.transcript,
   value)` (`pipeline.py:1154`). What he types in the correction well is
   the **value**. D0's "he types `ship the Q4 platform on schedule` in
   the correction well" therefore sets the *value*, not the gist. The
   receipt on `SpeakLearned.dc.html` — `LEARNED · applies to "ship the
   Q4 platform on schedule"` — is drawing the value where the gist
   belongs. Feeds P0-1.

2. **Can the face show LEARNED when nothing was recorded? Yes.** The
   primary route reports `{"corrected": true, "taught": <bool>}`
   (`pipeline.py:1194-1195`); the fallback reports `{"recorded":
   <bool>}` (`:997`). D2(a).4 says the receipt reads `recorded ===
   false`. On the primary route `recorded` is `undefined`, so a
   secret-like teach renders `LEARNED`. Worse, `repo.mark_corrected(...)`
   at `:1162` runs **outside** the `if recorded` — a refused teach still
   flips the journal row's `corrected` flag and links `correction_id` to
   `list_for_display()[0]` (`:1156-1160`), i.e. an unrelated newest
   correction. So `SpeakRefused.dc.html`'s `REFUSED · SECRET / nothing
   written` is itself false: a row was written.

3. **Can it show REFUSED when it was recorded? No** — `taught` /
   `recorded` are faithful to `CorrectionStore.record`'s return.

**When does the fallback fire?** Only when the run returned no
`journal_id` — i.e. `journal_enabled=false`, no repository attached, or
an unknown source (`journal.py:113-117`). On the owner's desk with the
journal on, the fallback is dead; a walk that only exercises the
primary route proves nothing about it.

**Sev: P1 (C4).** **Change:** D2(a).4 reads `taught ?? recorded`;
`mark_corrected` and the `correction_id` linkage move inside `if
recorded`; `SpeakRefused`'s second line becomes `NOTHING LEARNED`
(true) instead of `nothing written`.

---

### H3 — the bus frame: can the recorder reach `broadcast`?

**Read:** `web_server.py:66-72, 75-116, 235-244, 523-540`;
`dictation_runner.py:210-231, 419-435, 592-612` (the three runner call
sites and their `_elected_publication` fences); `_helpers.py:742, 868`;
`journal.py:111-157`; `runtime/RuntimeBus.tsx:100-121`;
`routes/system/ws.py:20-56`.

**Found — the design's chosen seam is right; its fallback is not.**

- `WebServer.broadcast` (`web_server.py:523-540`) reads `self._loop` at
  call time, no-ops when there is no loop, hands off with
  `run_coroutine_threadsafe` and swallows the result in a done-callback.
  It cannot block or raise into the dictation thread. Binding
  `broadcast=self.broadcast` at `web_server.py:242` is safe (the loop is
  resolved later, not captured).
- All three runner sites already hold `server`
  (`getattr(server, "dictation_journal", ...)` at `:217, :420, :598`),
  so no plumbing is needed — the handle rides the recorder.
- The emit sits **inside** the elected publication closure, so a
  cancelled run never broadcasts. That is the correct fence, not a
  problem.
- A recorder built without the callable is a no-op, so every bare
  server and every test stays byte-identical.

**The fallback is wrong.** `_helpers.py:742, 868` are the browser and
dry-run *routes*. The owner's real Tuesday dictation goes through
`dictation_runner.py:422` / `:600`. Emitting only route-side would push
exactly the sources he is not using and leave `DICTATION` and `HOTKEY`
— the walk's beats 1–5 — unpushed, with "poll for the hotkey path"
papering over it. If the constructor seam ever fails, the honest
fallback is to emit from `journal.py:137-155` with a module-level
handle, not to split the seam by source.

**Redaction: yes.** `record` writes `filter_secret(transcript)` and
`filter_secret(final_text)` (`journal.py:139-140`, `filter_secret` at
`:52-59`) *before* the repository call, and the repository returns the
stored row, so a frame built from the return value carries the redacted
text by construction.

**Audience: correct.** `/ws` closes any principal without
`PrincipalRight.OWNER` (`ws.py:52-56`), so the frame reaches the owner's
sockets only (Article III/V.1). Note for the record that the frame
carries the **full** transcript where the existing `learning_event`
carries a 120-char gist (`pipeline.py:1183`) — same audience, more text;
acceptable, but say it in D3.

**Sev: none (verified clean).** **Change:** D3 replaces the
"biggest unknown" paragraph — the seam is proven; state the fallback as
the chokepoint handle, not the two routes.

---

### H4 — the `corrected` flag and whether `N` lies

**Read:** `journal.py:137-155`, `intent_router.py:225, 233`,
`target_profile.py:151`, `db/journal.py:63-97, 126-141`,
`dictation_learning.py:99-113, 137-170`, `pipeline.py:1053-1071`,
`Journal.tsx:82-91`.

**Found.**

1. **The gap is confirmed.** `DictationJournalRecorder.record` passes
   only `intent.raw_label`, `intent.block_id`, `intent.confidence`
   (`journal.py:141-152`) and `_target_name(target_profile)` (`:143`,
   which drops `.source`). `extras["corrected"]` set at
   `intent_router.py:225, 233` and `source="correction"` at
   `target_profile.py:151` reach nothing. Today `corrected` is set only
   by `mark_corrected` (`db/journal.py:126-141`).

2. **The column cannot take the new value as written.** The INSERT
   hardcodes `..., corrected, correction_id) VALUES (..., 0, NULL)`
   (`db/journal.py:70-73`). Story 02 needs a named `corrected` kwarg on
   `DictationJournalRepository.record` — a seam D3 never names, and one
   that must stay *named* (the positional-INSERT scar).

3. **The two meanings collide.** `corrected=1` today means "he taught
   from this row" (the row that was **wrong**). 176 wants it to mean "a
   correction fired here" (the row that was **fixed**). Merged, the
   `LEARNED` chip appears on both — and `JournalStream.dc.html` draws
   the opposite: 14:19 (the row he corrected) bare, 14:22 (the fixed
   one) chipped. The board and the proposed wire disagree. → C5.

4. **`N` lies twice.**
   - `learning.similar` is `reach_for_gist` (`dictation_learning.py:99-113`)
     = how many **journal transcripts** the gist matches at ≥0.5. It is
     not "times applied", and it always counts the teaching utterance
     itself (its transcript *is* the gist → 1.000). A brand-new
     correction reads `1 APPLIED` on the Learned wing meaning *zero
     applications*. That is worse than a counter of zero (A.8, Article
     VI.1).
   - `best_correction_signal` (`:137-170`) is computed at **read time**
     over the whole journal, so it paints `learning.matched` on rows
     recorded before the correction was ever taught. A chip driven by it
     claims a fix that never happened.

**Sev: P1 (C2, C3, C5).** **Change:** per-row chip = the stored
per-run fact, no count (`APPLIED`, or `TAUGHT` on the row he corrected —
two facts, two words). The Learned wing's cell reads `REACHES N`, never
`N APPLIED`.

---

### H5 — counters of zero, the name said once, prose, raw buttons, the well's mic

**Read:** every board's rendered text and `<button>` inventory
(all fifteen), plus `DictationCore.tsx:32-36, 125-165`,
`count.ts`, `SpeakFace.tsx:292-308, 352-397`.

**Found.**

- **No counters of zero anywhere.** `LearnedQuiet` and `JournalQuiet`
  omit the count token; `Learned.dc.html` row 3 omits `N APPLIED`
  without shifting `Forget`. Clean.
- **`LEARNED` means three things on one Speak face** — the wing tab
  (the corrections store), the teach receipt (the event that just
  happened), and the RESULT chip (a correction fired on this utterance).
  On the Journal face it means two (wing + row cell). D2(b) claims this
  as a virtue ("one word for one thing"); it is three things wearing one
  word. Rule A.7. **Sev P1 (C8). Change:** wing `Learned`; receipt
  `TAUGHT · applies to "…"` (the wire's own word, `pipeline.py:1195`);
  row/RESULT chip `APPLIED`.
- **A second duplication:** `JournalStream.dc.html` prints `5 TODAY` in
  the ledger caption *and* `5 TODAY` in the footer (`DictationCore.tsx`
  puts `journalToken` in the footer receipt slot at `:126, :146-150`).
  Same count, one face, twice. **Sev P2.** Drop the caption or the
  footer token on the Journal wing.
- **Prose:** none on the Speak/Journal/Learned boards — tokens, verbs,
  counts. The Mic boards' display line `17 inputs need the mic` is a
  sentence with a verb; the other boards' display is a fact. **Sev P2**
  — prefer `17 SITES` with the specimen strip carrying the rest.
- **Raw buttons:** every verb on every board renders as a framed
  library-Button species. Clean. *But* `LedgerFilterBar` itself ships
  two raw `<button>`s (`LedgerFilter.tsx:124, 148`) — adopting it as-is
  imports two A1 residues into the Journal face. → C6.
- **A mic on the utterance well:** the boards draw the well **without**
  one, which is the right answer (Article IV.3, the 170 line). The built
  well is a bare `PadGadget` (`SpeakFace.tsx:296-308`) whose `mic`
  defaults true (`gadgets.tsx:315, 356-357`), so today it renders a
  third mic beside `Talk` (`:352`) and `Open mic` (`:388`). D4 hunt 5
  asks the question; the boards already answer it. **Sev P1 (C13):**
  D2(a) states `mic={false}` on the well with the census reason "the
  `Talk` transport is this face's mic authority (Article IV.3)".
- **Egress:** stated exactly once per face — `THIS DEVICE` on the
  footer. The ENGINE row's `EgressChip` is off-board on these boards
  (folded into `DICTATION · Qwen 3.5 0.8B · READY`); worth checking at
  build that the two do not both render on the Speak face at once.
  **Sev P2.**

---

### H6 — the Learned wing: fourth wing or section?

**Read:** `DictationCore.tsx:32-36` (`WINGS`, three), `:56`
(`useCoreWings(WINGS, "speak", …)`), `:42-53` (`Configure`),
`Memory.tsx:60-111`, `Learned*.dc.html`.

**Found.** A fourth wing does not break the 170 shape mechanically —
`useCoreWings` takes the array. Discoverability is the right argument:
today the only path to what the pipeline learned is the gear
(`DictationCore.tsx:42-53`), and `Memory.tsx:86` reads `row.gist` while
the route serves `key` (`corrections.py:203-208`), so the GIST column
renders `—` on his desk right now. The design names that defect; good.

**Lawful under A.8/A.10?** Yes — a wing is not a counter, and
`LearnedQuiet` shows one true line with no zero token, which is A.3's
single sanctioned exception. Nothing here bounces.

**Two board-only elements D2(c) does not specify:** a `search`
StringGadget on the Learned wing (drawn on `Learned` and
`LearnedQuiet`), and the human labels in the value column (C12).
**Sev P2 / P1.** Add the search to D2(c) or drop it from the boards.

---

### H7 — the mic rule: per-element scanning, and is ceiling 0 reachable?

**Read:** `scripts/ux_canon_scan.py:100, 178-180, 306-316, 360-363,
409-414`; `tests/ux_canon_ceiling.json`;
`tests/unit/test_ux_canon_ratchet.py:104-125`; the census.

**Found.**

- **Per-element is a small change, not a rewrite.** The scanner already
  walks lines and appends `Violation(rel, i, rule, msg)` inside the loop
  (the `B` rule does exactly this at `:313-316`). Moving `mic`'s emit
  into the loop and keying an allowlist on `path:line` — the shape A1's
  allowlist already uses (`test_ux_canon_ratchet.py:104-125`) — is
  roughly the `B` rule's body. Feasible.
- **Two defects in the flag the design must name.** (i)
  `ux_canon_scan.py:360-363` matches `<input|StringGadget|TextInput`
  — **never `<textarea`**, so three of the eight gap sites
  (`ThreadComposer.tsx:1060`, `ThoughtWorkspaceWindow.tsx:415`,
  `NotePullout.tsx:409`) are invisible to the rule today and would stay
  invisible after a naive per-element port. (ii) It counts
  `<StringGadget` as a text input needing a MicButton, when a
  StringGadget is *covered by definition* — per-element counting must
  target raw `<input`/`<textarea` plus `mic={false}` gadget instances.
  **Sev P1 (C9).**
- **Ceiling 0 is reachable, but by bookkeeping as much as by coverage.**
  The six faces holding `mic: 6` resolve as: `LedgerFilter` +
  `PeopleCore` fixed, `UtteranceWell` parked, and
  `ChoiceCardGroup` (radio) / `CalendarSnapshotReviewCore` (HH:MM) /
  `SettingsCore` (glyph) *allowlisted*. Say that plainly in D2(d) —
  "0 with a 23-entry reasoned allowlist" is a different claim from "0
  because every input has a mic", and the owner should read the true
  one. Also note that dropping the `classify_face` gate widens the
  scan to non-face files; the census's scope matches, so the count
  should not surprise, but the design should commit to the number.
- **Is any of the 8 not dictatable?** All eight are free text. The one
  worth a note is `ThoughtDocumentPane.tsx:90` (**tags**): dictating
  into a comma-separated token field produces spoken punctuation.
  Keep it (the law is every text input), but expect it to read badly.
  `ThreadPullout.tsx:211` is the `text` branch of the elicitation form
  (`:209-215`) — its `enum`, `boolean` and `number` siblings at
  `:186-205` are correctly allowlisted. **Sev P2.**

---

### H8 — the 393 boards

**Read:** `SpeakLoopPhone`, `JournalStreamPhone`, `LearnedPhone`,
`MicPlacementPhone` rendered at 393, plus a measured pass over every
interactive element.

**Found.**

- **No unreadable wrap.** Journal rows ellipsis correctly at
  `min-width: 0`; the Learned row stacks value under gist as D2(c)
  says; the Mic specimen strip stacks cleanly.
- **A verb disappears at 393.** `SpeakLoopPhone` drops the `Open` latch
  (present at 1440 as `OPEN`) and moves the whole transport from the top
  to the bottom of the window, leaving ~200px of dead space between the
  ENGINE row and it. D2(e) says only "the transport stacks". **Sev P1
  (C14):** draw `Open` at 393 or say in D2(e) why it is withheld.
- **Hit targets are 24–28px, not 44.** Measured: `OK` 28, `Wrong` 28,
  `Intent` 28, `Teach` 28, `Clear` 28, `Forget` 24, `Review`/`Export`
  24. The `Talk` MicButton is 52×52. Honest framing: the boards
  reproduce the **library's** dense-Button height, so this is a species
  property, not a face defect — and by the owner's standing ruling a
  species problem is fixed in the library, never in a face. **Sev P2:**
  raise it as a library question, not as a 176 board change.

---

### H9 — the walk's writes

**Read:** D5; `journal.py:111-157`; `db/journal.py:63-97` (`_prune`);
`pipeline.py:1122-1201`; the 167/168 scar.

**Found.** "The walk writes nothing on his desk except the one
correction he teaches" is **not true**. Every beat that dictates writes
a durable row to `dictation_journal` (`journal.py:137-155`) *and*
prunes the table to `retention` (`db/journal.py:88-89`) — so beats 1,
2, 4, 6, 7 each write, and each may evict his oldest row. Beat 3 writes
the correction **and** flips `corrected`/`correction_id` on a journal
row (`pipeline.py:1162`). Beats 6 and 7 dictate into the Room's ask
well and the Door's outcome field; if he submits either, that is a
third class of write.

The distinction the design wants is real but must be stated correctly.
**Sev P1 (C10). Change:** D5 reads —

> The **runner** writes nothing and seeds nothing: it drives the face
> and reads. The **product** writes exactly what his own hand produces:
> one journal row per utterance he speaks (the journal is the product's
> own record, retention-pruned as always), one correction row from his
> `Teach`, and the `corrected` flag on the row he corrected. Beats 6
> and 7 dictate into the field and **do not submit**. `Forget` and
> `Delete` remove all of it in one verb each.

---

### H10 — drift between D2, D3 and the boards

**Read:** every board against D2, and D2/D3 against the tree.

Beyond C1–C5 above:

1. **`LedgerFilterBar` is not the species the design describes.**
   D2(b).3 wants four flat tokens, one-tap toggle, `ALL` default. The
   species (`LedgerFilter.tsx:76-160`) renders a query `<input>`
   (`:112`), a `matchCount/total` count (`:120-122`), a raw `Clear`
   button (`:124`), and `tokens` as *added* filters each with a raw `×`
   (`:134-155`). It also **returns `null` below 5 items**
   (`:104`, `SPARSE_THRESHOLD = 5` in `sparse.ts:4`) — yet
   `JournalQuiet.dc.html` draws all four tokens over an empty stream.
   And its `matchCount/total` would be a *third* count on the Journal
   face, reading `0/5` when nothing matches (A.8). **Sev P1 (C6).
   Change:** name the library work — a toggle-token mode on
   `LedgerFilterBar`, documented in `surface/contract.md` per canon B —
   or draw a different species. Say what the bar does at 0 items.
2. **The opened Journal row loses three verbs in silence.** Today:
   `EditInPlace` + `Replay` + `Copy` + `Delete`
   (`Journal.tsx:95-121`). D2(b)'s row grammar and every Journal board
   omit them. The 175 law is explicit. **Sev P1 (C11).**
3. **The Disclosure prints wire field names.** `SpeakApplied.dc.html`
   reads `KEY ship the q4 platform on schedule / VALUE Delivery /
   SIMILARITY 0.71 · INTENT`. `KEY` and `VALUE` are engineer words for a
   receipt (canon E.4, A.3). **Sev P2.** Propose `GIST` / `ROUTES TO`.
4. **The board's similarity number is arithmetically wrong.** For its
   own two strings — "Ship the Q4 platform in October" vs "ship the q4
   platform on schedule" — Jaccard is **0.500** (∩=4 {ship,the,q4,
   platform}, ∪=8), not `0.71`. **Sev P2**; the owner reads numbers.
5. **The Mic board's allowlist count disagrees with D2(d).** Board:
   `23 ALLOWLIST`. D2(d) table: `19`. Both are defensible (19 raw +
   4 opt-out), but one number must win. **Sev P2.**
6. **`JournalQuiet`'s empty line is scoped wrong.** The ledger is
   all-time (today + YESTERDAY groups on the other boards) and the
   empty state fires on `!filtered.length` (`Journal.tsx:233`), which
   is also true when a search or filter matches nothing. `Nothing
   spoken today` is false in both cases. **Sev P2.** Propose `Nothing
   spoken yet` for the empty journal and a distinct filtered-empty
   line.
7. **`OK`/`Wrong` change framing between boards.** `SpeakWrong` frames
   `Wrong`; `SpeakApplied` frames `OK`. A selected-verdict state D2(a)
   never names, and a verb whose frame moves reads as two species.
   **Sev P2.**
8. **The utterance is drawn twice at the same weight** — once in the
   well, once as the RESULT primary — and on `SpeakApplied` the two
   strings are identical. Inherited from 170, but D1's "the name said
   once" law claims otherwise. **Sev P2.** Say what the RESULT line
   shows when `final_text == utterance`.
9. **`Review` will duplicate a visible tab.** D2(b).6 re-points
   `Review` (`DictationCore.tsx:152-158`) at the Journal wing — which
   is one tap away in the wing strip on the same face. Re-pointing it
   away from the Configure door is right (it opens the wrong thing
   today); consider retiring the verb instead of duplicating a tab.
   **Sev P2.**
10. **A build hazard for story 03.** `useRuntimeBus` throws outside a
    provider (`RuntimeBus.tsx:106-111`). No `Journal` test exists today,
    so nothing breaks now — but any new Journal test must wrap in
    `RuntimeBusProvider` or mock the module, the way
    `LiveCore.test.tsx:38-39` does. **Sev P2.**

---

## Verified clean (no finding)

- The bus mechanism, its thread-safety, its fence behaviour and its
  redaction (H3).
- `/ws` owner-only admission (`ws.py:52-56`) — the frame is a read under
  Article V.1 with no widened audience.
- `countToken` returns null at n≤0 (`count.ts:12-21`); every board
  obeys A.8.
- The census's arithmetic: 44 raw = 17 covered + 8 gap + 19 allowlist,
  and the 14 `mic={false}` opt-outs. Spot-checked against the tree.
- `Forget` needs no wire change (`pipeline.py:999-1007`).
- The route's `source` clamp (`pipeline.py:1049`) and the missing
  `before` cursor are correctly named in D3.
- The correction ring's 20-cap vs the uncapped DB read
  (`corrections.py:34, 112, 192-214`) — the design's reading is right.

---

## Three questions for the owner (ride the walk, story 06)

1. **Is the correction a routing fix or a words fix?** The wire only
   does routing. If he expects "teach it the word `Q4`", that is a new
   correction kind and a new phase.
2. **How wide should a correction reach?** 0.5 Jaccard sends "the note
   to Alex" where "the note to Dana" was taught. Higher bar, or a
   confirm on the first auto-application?
3. **Wing or gear for `Learned`?** Four wings on Speak, or the
   corrections table stays behind the gear with the digest.

---

## Counsel's re-read (2026-09-06)

Read: the rewritten `settled-design-speak-loop.md` (992 lines, addendum
R1--R14 and every section it moved), `story-02`, `story-03`, and all
**seventeen** boards re-rendered headless at their canvas sizes
(`SpeakTaughtShort` gone; `SpeakWrongRoute`, `SpeakAppliedRoute`,
`JournalRowOpen` new). Every new wire claim re-checked against the tree;
one reproduction ran under an isolated HOME with no DB write.

### VERDICT: RATIFY-WITH-CONDITIONS — five (N1–N5). C1–C14 are paid or paid-with-note; nothing is unpaid.

The `text` kind is the right call and the seam is the right seam. The
carve (a correction kind at an existing transcript seam, not a stage) is
honest, the reasoning against `TextProcessor` is factually correct, and
`Utterance` is frozen exactly as D3 says (`contracts.py:22-30`), so the
`dataclasses.replace` is sound. The five conditions are one board row
that crashes the typing path, one seam the design points at the wrong
side of, and three things the design asserts more confidently than the
code supports.

### The conditions

| # | Condition | Sev |
|---|---|---|
| N1 | **`Auto` in the target pick crashes the live typing path.** Drop it — six options, not seven. | **P0 (board)** |
| N2 | **The diff's *heard* side is the wrong text.** D2(a) pre-fills with the landed text; the rule is applied to `utt.raw_text`. Serve the raw transcript on the run response and diff against it. | P1 |
| N3 | **The word-level span must be punctuation-stripped.** On the capture path `raw_text` is post-TextProcessor, so tokens carry attached punctuation. | P1 |
| N4 | **"The `text` kind carries no such hazard" over-claims.** The boards' own rule (`queue for -> Q4`) silently rewrites every future occurrence of a common phrase, in the text he types. | P1 |
| N5 | **Two board/design contradictions the rewrite left.** The `TAUGHT` row token D2(b).2 requires is on no Journal board; the Learned face carries two counts against D1's own "one count per face". | P1 |

---

### C1 — the correction can never fire · **PAID-WITH-NOTE**

Ruled the other way (R1) and the ruling holds up on the tree.

Verified: `Utterance` is `@dataclass(frozen=True)` with the docstring
"One post-Whisper, post-TextProcessor utterance entering the pipeline"
(`plugins/dictation/contracts.py:22-30`) — `dataclasses.replace` is the
right instrument. `Pipeline.run` seeds `current_text = utt.raw_text`
(`plugins/dictation/pipeline.py:98`) and passes the original `utt` to
every stage (`:108`), so replacing it before the loop reaches the
rewrite pass and the router, exactly as D3 says. `build_pipeline(...,
corrections=...)` already threads the snapshot on **both** paths — the
runner (`dictation_runner.py:342-345`, `:537`) and the dry-run/browser
route (`_helpers.py:787-791`) — so the text kind rides one funnel.
`CORRECTION_KINDS` (`corrections.py:33`) and
`db/corrections.py:26 VALID_CORRECTION_KINDS = frozenset({"intent",
"target"})` both take the third kind additively.

The `TextProcessor` rejection is correct as stated: `process` is called
only at `runtime/dictation_capture.py:121, 398, 412` and
`runtime/wake_glue.py:381`, never by `dictation_runner.py` or
`_helpers.py`.

The routing pick is real: `SpeakWrongRoute.dc.html` unfolds the enum
in-world under the row (no overlay, A.4 clean), and the seven ids at
`target_profile.py:26-34` are drawn with labels. Three notes ride as
N1, N2 and N4 below.

### C2 — the chip from a stored fact · **PAID**

D3 "The chip never reads `learning`" is explicit, and D2(a).3 / D2(b).2
render only from the run's own `corrections_applied`. The boards agree:
`APPLIED` sits on 14:22 (the fixed row) and on no other. The read-time
signal (`dictation_learning.py:137-170`, wired at
`pipeline.py:1062-1071`) is left to the digest.

### C3 — `N APPLIED` counts firings · **PAID-WITH-NOTE**

D2(c).1 + D3 "`N APPLIED` is a real count": a new
`count_applied(correction_id)` over stored `corrections_applied`,
replacing `item["similar"] = reach_for_gist(...)`
(`pipeline.py:930-931`). `reach_for_gist` appears on no face. The
`Learned` board's third row carries no cell at zero (A.8 clean).

**Note:** each journal write prunes to `retention`
(`db/journal.py:93-94`, default 500), so `N APPLIED` is a count over
the *retained* journal and can go **down** over time. Honest, but it
should be said in D3 rather than discovered on his desk.

### C4 — the refusal receipt and the refused write · **PAID**

D3 "The teach routes, made honest" names all four fixes against the
right lines (`pipeline.py:1154`, `:1156-1159`, `:1162`, `:1195` vs
`:997`), and `SpeakRefused`'s `nothing written` becomes true once
`mark_corrected` moves inside `if recorded`.

**Note (mechanical):** `CorrectionStore.record` returns `bool` today
(`corrections.py:145-165`) with exactly two callers
(`pipeline.py:996, 1154`); "`record()` returns the stored id" is a
contract change on both. Additive and safe — just name it in story 02.

### C5 — the overloaded flag · **PAID**

The split is right and minimal: `taught_from` keeps the existing
`corrected` column and its meaning (no data migration), and
`corrections_applied` is one additive JSON column defaulting `'[]'`.
The INSERT seam is named with the positional scar cited
(`db/journal.py:70-74`), and `_row_to_record` / `_journal_to_dict` are
named. Verified the hardcode is exactly where D3 says.

**Note:** `PipelineRun` is frozen with six required fields
(`plugins/dictation/pipeline.py:47-56`) and `passthrough_run` fakes it
with a `SimpleNamespace` (`journal.py:33-49`). The new field needs a
default, and the recorder must read it with
`getattr(run, "corrections_applied", [])` or the pipeline-off path
raises.

### C6 — the filter species · **PAID**

`LedgerFilterBar` is rejected on facts I re-verified: its query
`<input>` (`LedgerFilter.tsx:112`), its two raw `<button>`s (`:124`,
`:147`), its `matchCount/total` (`:120-122`), its `null` below
`SPARSE_THRESHOLD = 5` (`:104`, `sparse.ts:4`), and **zero consumers** —
grep finds it only in `surface/index.ts:95-96` and its own test.
`contract.md` has no filter species (0 grep hits), so "the library lacks
one" is true. The adopted composition is verbatim the ratified Room one
(`ProjectRoomCore.tsx:1550-1566`: `role="group"`, library `Button`
ghost dense, `data-filter-active`, `aria-pressed`). Every board renders
the four tokens as `<Button>`, including `JournalQuiet` — the sparse
rule is genuinely gone.

### C7 — the false caution · **PAID-WITH-NOTE**

The caution is struck, `SpeakTaughtShort` is deleted, and the arithmetic
in D4.1 is now the arithmetic I measured. `REFUSED · ONE WORD` is a
routing-only rule and correctly does not apply to the exact-phrase kind.

**Note:** the refusal has no named seam. `CorrectionStore.record`
(`corrections.py:145-165`) checks kind, emptiness and
`looks_like_secret` — there is no token-count guard. Story 02 must name
where `REFUSED · ONE WORD` is enforced (the store, so both routes and
the MCP surface get it — not the face).

### C8 — one word, one meaning · **PAID-WITH-NOTE**

`LEARNED` / `TAUGHT` / `APPLIED` are now three words for three facts
(D1's A.7 row, D2(a) receipts, D2(b).2, D2(c)), and the boards obey:
the receipt is `TAUGHT · queue for -> Q4`, the chip is `APPLIED`, the
wing is `Learned`. → see N5 for what the boards still contradict.

### C9 — the scanner · **PAID**

All four defects named against the right lines, including the one I
found — the flag matches `<(?:input|StringGadget|TextInput)\b`
(`ux_canon_scan.py:361`) and never `<textarea`, hiding three of the
eight gap sites. The ceiling claim is stated honestly ("`mic: 0` with a
23-entry reasoned allowlist", not "0 because every input has a mic").

### C10 — the walk's write set · **PAID**

D5's rewrite is exact, cites the prune (`db/journal.py:93-94`), marks
beats 6 and 7 as no-submit, and adds a real assertion (journal rows
added == dictating beats; correction rows added == 1). "The walk writes
nothing except the one correction" is struck as false in the design's
own words.

### C11 — the replaced face keeps its verbs · **PAID**

D2(b).3 names `EditInPlace` + `Replay` + `Copy` + `Delete` + the replay
preview against the real lines (`Journal.tsx:95-100`, `:101-121`,
`:122-144`), and `JournalRowOpen.dc.html` draws all three verbs under
the open row.

**Note:** the preserved preview block carries prose — `Replay — preview
only` and `The replay completed without text.`
(`Journal.tsx:130-137`). Keeping the verbs is right; keeping the
sentences is an inherited A.3 defect that 176 now formally re-ratifies.
Tokenise them or ledger them.

### C12 — the label sources · **PAID-WITH-NOTE**

Both sources verified: `Block.description` (`blocks.py:84-89`) served by
`web/routes/dictation/blocks.py:56-88` and already read by
`Blocks.tsx:39-44, 148-150`; the `labels` map (`target_profile.py:280-288`)
over `TARGET_PROFILE_OVERRIDE_OPTIONS` (`:26-34`), genuinely unserved
today (referenced only at `:100, :103, :149`), with the readiness
`target` payload (`pipeline.py:200-207`, `:330`) the right place to add
`overrides`.

**Note:** the boards do not use the map they cite. `SpeakWrongRoute` and
`Learned` print **`Terminal`**; the map says **`Terminal shell`**. Pick
one — the map, or a design-owned label table — and say which.

### C13 — the third mic · **PAID**

D1's mic-authority row, D2(a)'s closing paragraph, D2(d)'s allowlist
note (23 now, 24 after story 05) and D2(e).1 all state `mic={false}`
with the reason. The boards draw the well mic-less.

### C14 — the 393 transport · **PAID**

`SpeakLoopPhone.dc.html` now draws `TALK` **and** `OPEN` at the foot
with `LEVEL`; the deviation from 170's own `SpeakPhone` board is
recorded in R14 rather than inherited silently. → one note in N-list
(the teach well truncates at 393).

### The P2s

Paid: the `HEARD`/`SAID` and `WHEN`/`ROUTE` Disclosure (no `KEY`/`VALUE`
wire words); `MATCH 0.50` — the honest Jaccard for those two strings,
which I recomputed and which is exactly 0.500; the Journal's caption
count dropped (footer `N TODAY` only); `NOTHING SPOKEN` /
`NOTHING MATCHES`; the allowlist stated as 23 everywhere; `Review` kept
and re-pointed; `OK`/`Wrong` declared one species in two states
(`data-verdict-active`); the `final_text == utterance` behaviour stated;
the `useRuntimeBus` provider hazard carried into D2(b).1 with the right
precedent (`LiveCore.test.tsx:37-38`, verified).

**Not paid:** the Mic boards were not redrawn (file mtimes 22:07 against
22:28–22:30 for the rest). The display line still reads `17 inputs need
the mic`; the P2 ruling says `17 SITES`.

---

### New findings

#### N1 — `Auto` in the target pick raises `KeyError` on the typing path · **P0 (board)**

`SpeakWrongRoute.dc.html` draws the pick as seven options, `Auto` first.
`auto` **is** a member of `TARGET_PROFILE_OVERRIDE_OPTIONS`
(`target_profile.py:26-34`), so it passes the membership guard at
`:149` — and then `_profile("auto", ...)` does `label=labels[profile_id]`
(`:280-288`), where the map has no `auto` key. Reproduced (isolated
HOME, no DB):

```
apply_target_correction(profile, text='ship the q4 platform',
                        corrections=[Correction('target', 'ship the q4 platform', 'auto', 1)])
-> RAISED KeyError 'auto'
```

The call site is the live hotkey dictation path
(`dictation_runner.py:389`, again at `:565`, and the dry-run route at
`_helpers.py:811`) with no local guard. So: he picks `Auto`, teaches,
speaks a similar sentence, and target detection raises inside the
typing loop.

`Auto` is also meaningless as a correction ("route this to: whatever you
were going to pick"). **Change:** the pick offers **six** ids —
`claude_code`, `codex_cli`, `terminal_shell`, `browser`, `editor`,
`chat` — and D3's label table says so. (Belt: `_profile` should not
KeyError on a member of its own option set; a one-line `labels.get(...)`
fix belongs in story 02 regardless of the board.)

#### N2 — the diff's *heard* side is text the rule never sees · **P1**

D2(a): the TEXT StringGadget is "pre-filled with **the landed text**",
and the diff is heard-vs-said over it. D3: the rules are applied to
`utt.raw_text` at `plugins/dictation/pipeline.py:98`.

Those are two different strings whenever any stage rewrites text — which
is the rewrite pass's entire job. A key harvested from `final_text` is
matched against `raw_text` and never fires; the walk's beat 4 then fails
on his desk for a reason no one can see on the face.

The run response makes it worse: it carries `final_text` and no raw
transcript (`_helpers.py:756-768` for the passthrough,
`:883-894` for the real run). The face has nothing correct to diff
against today.

**Change:** state in D2(a) that *heard* is the **raw transcript** and
*said* is his edit; add the raw transcript to the dry-run/deliver
response in story 02 (one field beside `final_text`); the StringGadget
pre-fills from it. If the orchestrator prefers to keep pre-filling with
the landed text, then the rules must apply to the landed text instead —
but that forfeits D3's whole reason for the seam ("the rewrite pass and
the router both see `PostgreSQL`"), so the first fix is the right one.

#### N3 — the word-level span must be punctuation-stripped · **P1**

`Utterance.raw_text` is post-TextProcessor on the capture path
(`contracts.py:23`; `dictation_capture.py:121`), so spoken punctuation
is already attached to tokens — `postgress,` not `postgress` `,`. A
whitespace-token diff therefore yields spans that carry punctuation, and
a rule keyed `postgress,` fires on `postgress,` and on nothing else.
D3's "whole-word bounded" is necessary but not sufficient.

**Change:** D3 states that the diff strips leading/trailing punctuation
from each span before storing the key and the value, and that the
whole-word boundary is "non-alphanumeric or string edge" — so
`postgress` matches inside `postgress,` / `postgress.` and never inside
`postgressive`.

#### N4 — "the `text` kind carries no such hazard" over-claims · **P1**

D4.1 closes with "The `text` kind is exact-phrase and carries no such
hazard." Exact-phrase is narrower than Jaccard; it is not hazard-free,
and its blast radius is **larger** in one way that matters: a routing
nudge changes where text goes, a text rule changes **the words he
types**.

The boards' own example is the demonstration: `queue for -> Q4` rewrites
every future utterance containing that ordinary English phrase — "the
queue for the build is long" becomes "the Q4 the build is long" — on
every source, silently, forever, with no similarity floor to stop it.
D3's "all matching rules apply, longest key first" means several rules
can compound on one utterance.

**Change:** D4.1 says what is true — exact-phrase removes the *fuzzy*
false positive and keeps the *common-phrase* one; the `APPLIED`
Disclosure is the visible undo path (it names the rule; `Forget` is one
wing away); and this joins walk question 2 as a question for him, not as
a hazard the design denies.

#### N5 — two contradictions the rewrite left · **P1**

- **The `TAUGHT` row token is on no board.** D2(b).2 requires it on the
  row he taught from, D5 beat 5 says "the earlier one `TAUGHT`", and
  `JournalStream` / `JournalStreamPhone` / `JournalFiltered` /
  `JournalRowOpen` all draw 14:19 (the taught row) bare. Draw it, or
  strike it from D2(b).2 and D5.
- **The Learned face carries two counts.** D1 rules "The count
  `N TODAY` is said once, in the footer" and D2(b).7 drops the Journal
  caption for exactly that reason — but D2(c).3 keeps
  `countToken(n, "LEARNED")` and every Learned board shows `3 LEARNED`
  in the caption **and** `5 TODAY` in the footer. Also `LEARNED` then
  appears twice on that face (wing tab + caption). Rule which law wins
  and apply it to both wings the same way.

### Smaller notes (P2, no condition)

1. **Spoken-symbol order, stated.** A text rule runs *after*
   `TextProcessor` on the capture path and *instead of nothing* on the
   browser path, so (a) its output is never re-scanned — a rule can
   never produce a spoken symbol, and (b) the same sentence yields
   different `raw_text` on the two paths, so a rule taught from a
   HOTKEY landing may not fire on a BROWSER one. One paragraph in D3.
2. **Can a text rule leak a secret into the frame? No.** The store
   refuses a secret-like key or value (`corrections.py:152-153`), and
   the frame is built from the stored row after
   `filter_secret(transcript)` / `filter_secret(final_text)`
   (`journal.py:139-140`). A rule that *inserts* a secret-shaped string
   causes the whole `final_text` field to be redacted — availability,
   not disclosure. Verified clean.
3. **`corrections_enabled` gates the whole loop.** Default `True`
   (`config/meeting.py:389`), but every read falls back to `False`
   (`dictation_runner.py:336-338`, `_helpers.py:716-720`,
   `pipeline.py:1175`). The walk should confirm it is on before beat 1
   rather than debug a silent no-op live.
4. **The 393 teach well truncates.** `SpeakLoopPhone` renders the
   pre-filled sentence as `Ship the queue for platform on s…` on one
   line; D2(a) says the value control wraps to a second line at 393.
   The TEXT kind is the one field he must read every word of.
5. **FIELD casing.** D2(a) writes the cycle as `TEXT · INTENT ·
   TARGET`; the boards render `Text` / `Target`. One casing.
6. **`Clear` is withheld on the quiet Journal** (present on the other
   Journal boards, absent on `JournalQuiet`). Correct by A.11, but D2(b)
   does not say it.
