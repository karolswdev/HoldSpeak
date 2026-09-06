# HS-176-03 — The journal as a stream

- **Project:** holdspeak
- **Phase:** 176
- **Status:** in-progress
- **Depends on:** HS-176-01, HS-176-02
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

The journal exists (journal.py:93-157, DictationJournalRecorder writes
one durable row per pipeline run) and the Journal face exists
(Journal.tsx on the Speak window), but it is not a live stream.

- **No push, and no polling either.** The face loads once through
  `useResource("/api/dictation/journal?limit=200")` (Journal.tsx:150-153);
  `useResource` (pages/pageSupport.tsx:31-61) has no interval and no
  subscription, so a new utterance never appears until the wing
  remounts.
- **The source filter is half-built.** The route's `source` param
  exists (pipeline.py:1034) but is clamped to `("dictation","dry_run")`
  at :1049, silently dropping `browser` and `hotkey`; the repository
  itself accepts any source (db/journal.py:100-108). The face has no
  filter control at all.
- **No pagination.** `limit` only; no `before` cursor.
- **The `TAUGHT · N SIMILAR` cell is not honest.** It renders from
  `row.corrected` plus read-time `learning` / `best_correction_signal`
  (pipeline.py:1062-1071, Journal.tsx:82-91) — a "would match" computed
  over the whole journal that paints rows recorded *before* the
  correction existed, with a count of similar transcripts rather than
  firings (counsel C2/C3; rulings R2, R3).
- **Two counts on one face.** The ledger caption renders
  `countToken(todayCount,"TODAY")` (Journal.tsx:211) while the footer
  already renders `N TODAY` (DictationCore.tsx:125,144-149) — the same
  count said twice (rule A.7).
- **One empty line covers two states.** `No dictations on this device`
  fires on `!filtered.length` (Journal.tsx:233), which is also true when
  a search or filter matches nothing — false in that case.
- **`Review` opens the wrong thing.** The Speak footer's `Review`
  (DictationCore.tsx:152-158) calls `wings.setDoorOpen(true)` (:155),
  opening the Configure door, not the journal.

The bus seam the frame rides is named with file:line in the settled
design D3 ("The bus seam"): `/ws` (routes/system/ws.py:20-98) →
`WebSocketManager.broadcast` (web_server.py:75-116) →
`WebServer.broadcast` (:523-540) → the recorder's constructor handle
(bound at web_server.py:242) → `RuntimeBus` (web/src/runtime/RuntimeBus.tsx:26-121).

The arc says "the journal as a stream."

## Scope

- In:
  - **Real-time push.** A `dictation.journal.entry` frame emitted
    **once inside `DictationJournalRecorder.record`**
    (journal.py:137-155) after the repository returns the stored row,
    via an optional `broadcast` callable given to the recorder at
    construction (web_server.py:242, `broadcast=self.broadcast`) — the
    `notify=` shape web/routes/meetings/intel.py:22 already uses. One
    chokepoint covers all five call sites
    (dictation_runner.py:222,422,600; _helpers.py:742,868); a recorder
    built without the callable is a no-op.
    - The frame carries: id, source, transcript, final_text, total_ms,
      `corrections_applied`, `taught_from`, intent_tag, target_profile.
    - It is built from the **stored row**, so `filter_secret`
      (journal.py:52-59,139-140) cannot be bypassed.
    - **Route-side emission is explicitly rejected**: _helpers.py:742 is
      the pipeline-off passthrough and :868 the dry-run executor, both
      carrying `dry_run`/`browser`; the owner's real dictation runs
      through dictation_runner.py:422/:600 (`dictation`/`hotkey`). The
      honest fallback, if the constructor seam fails, is a module-level
      handle in journal.py:137-155 — never a per-source split.
  - **The Journal face subscribes** with `useRuntimeBus().subscribe`
    (RuntimeBus.tsx:106-111) on mount and prepends new entries.
  - **Row grammar to the HS-176-01 artboard:** lead slot = time;
    primary = transcript; cells = `LANDED IN <target label>` ·
    `41 MS` (uppercase) · `APPLIED` (present only when the row's stored
    `corrections_applied` is non-empty, **no count**) · `TAUGHT`
    (present only on the row he taught FROM — **it stands (N5a)**: the
    token is required here and in D5 beat 5, and the Journal boards draw
    it on the taught row); trailing = a human source badge `DICTATION` /
    `DRY RUN` / `BROWSER` / `HOTKEY` (never `dry_run`). `LEARNED`
    appears nowhere (R8).
  - **The opened row keeps every verb** (the 175 law, R11):
    `EditInPlace` over the transcript plus `Replay` · `Copy` · `Delete`
    and the replay preview, exactly as Journal.tsx:95-144 has them.
  - **The preview's two sentences are tokenised, not inherited** (C11
    note): `Replay — preview only` (Journal.tsx:124-126) becomes
    `REPLAY · PREVIEW`; `The replay completed without text.` (:127-130)
    becomes `NO TEXT`. Keeping the verbs is the law; keeping the prose
    would re-ratify an A.3 defect.
  - **`Clear` is withheld on the quiet state** — nothing to clear, and a
    verb that does nothing is a lie (rule A.11). It returns as soon as
    the ledger holds a row.
  - **Four flat filter tokens** — `ALL` / `DICTATION` / `BROWSER` /
    `HOTKEY`, one-tap toggle, `ALL` default — composed from the library
    `Button` (ghost, dense) with `data-filter-active` + `aria-pressed`
    in a `role="group"` span, the composition already ratified at
    ProjectRoomCore.tsx:1550-1566, **promoted into the surface library
    and documented in web/src/desk/surface/contract.md** (canon B).
    `LedgerFilterBar` is **not** adopted (R6): it renders a query
    `<input>` (LedgerFilter.tsx:112), a `matchCount/total` count
    (:120-122), two raw `<button>`s (:124,:147) and removable chips
    (:134-155), and returns `null` below 5 items (:104,
    sparse.ts:4). The new bar has **no sparse rule and never returns
    null** — it is present on the quiet state — and shows no
    `matchCount/total`.
  - **The route's clamp widened** (pipeline.py:1049) to the recorder's
    `VALID_SOURCES` (journal.py:28) so the tokens work.
  - **Search** — the existing StringGadget (Journal.tsx:214-219, mic
    default true) widened to match `final_text` as well as
    `transcript`.
  - **Scroll-to-load** — `?limit=50&before=<oldest_id>` on the route and
    on `DictationService.list_journal`; scroll-up appends older
    entries.
  - **No caption count** — the `countToken` pair at Journal.tsx:211 is
    dropped; the footer's `N TODAY` is the one count per face (R8's
    A.7 reading).
  - **Two empty states, two true lines**: the token `NOTHING SPOKEN`
    when the journal is empty all-time; `NOTHING MATCHES` when a filter
    or search matches nothing, with the tokens still present so he can
    widen it.
  - **`Review` switches to the Journal wing** — `wings.setView("journal")`
    at DictationCore.tsx:155. The verb is kept, not retired (a working
    verb is never dropped); the gear remains the way to Configure.
- Out:
  - The `corrections_applied` column, the recorder writing it, and the
    `text` correction kind — those are HS-176-02, on which this story
    depends.
  - Journal export (the footer's `Export` already exists) and journal
    analytics (the learning digest is the aggregation surface).
  - Removing `Delete` or making the journal append-only — the row's
    existing verbs stay (R11).

## Acceptance criteria

- [ ] A new utterance appears in the Journal wing within 1 s of the
      pipeline run completing, pushed — not polled (Article IX.1).
- [ ] The frame is emitted from `DictationJournalRecorder.record`, so
      all four sources (`dictation`, `dry_run`, `browser`, `hotkey`)
      push; a bare server with no `broadcast` callable behaves
      byte-identically.
- [ ] The frame carries only redacted text (built from the stored row).
- [ ] The frame reaches owner sockets only (`/ws` closes any principal
      without `PrincipalRight.OWNER`, ws.py:52-56) — it is a read under
      Article V.1.
- [ ] Each row shows time, transcript, `LANDED IN <label>`, `N MS`,
      and a human source badge; `APPLIED` appears only where the stored
      `corrections_applied` is non-empty and carries **no count**;
      `TAUGHT` appears only on the row taught from (Article VI.1).
- [ ] No row or cell renders from `learning` /
      `best_correction_signal` (R2).
- [ ] The opened row still offers `EditInPlace`, `Replay`, `Copy` and
      `Delete` (the 175 law), and the replay preview carries tokens
      (`REPLAY · PREVIEW`, `NO TEXT`), not sentences (rule A.3).
- [ ] The `TAUGHT` token renders on the row he taught from (N5a).
- [ ] `Clear` is absent on the quiet Journal and present once the ledger
      holds a row (rule A.11).
- [ ] The four source tokens are library Buttons in a `role="group"`,
      promoted to the surface library and documented in contract.md; no
      raw `<button>` is added to the Journal face (rule A.1); the bar
      renders on an empty stream.
- [ ] `?source=browser` and `?source=hotkey` filter the route (the
      clamp is widened).
- [ ] Scroll-up paginates with `before` without refetching the whole
      history.
- [ ] The Journal wing shows no count in its caption; `N TODAY` is said
      once, in the footer (rule A.7).
- [ ] An all-time empty journal reads `NOTHING SPOKEN`; a filter or
      search miss reads `NOTHING MATCHES` (rule A.3's single
      exception).
- [ ] `Review` on the Speak footer switches to the Journal wing.
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k journal`
  - A pipeline run writes a journal row and calls the recorder's
    `broadcast` callable exactly once with type
    `dictation.journal.entry`.
  - A recorder built without the callable never broadcasts and writes
    identically.
  - The frame's transcript is the redacted stored value for a
    secret-like utterance.
  - `?source=browser` and `?source=hotkey` return only those rows.
  - `?limit=50&before=<id>` returns the page before that id.
- Web unit: `uv run python scripts/check_web_baseline.py --run`
  - The Journal renders `APPLIED` from `corrections_applied` and never
    from `learning`.
  - The opened row exposes Replay / Copy / Delete.
  - The four filter tokens toggle and render on an empty stream.
  - `NOTHING SPOKEN` vs `NOTHING MATCHES`.
  - **Any new Journal test wraps in `RuntimeBusProvider` or mocks the
    module** — `useRuntimeBus` throws outside a provider
    (RuntimeBus.tsx:106-111); LiveCore.test.tsx:37-38 (`vi.mock`) is the pattern.
- Integration: the rig boots a hub, opens the Journal wing, runs a
  dictation, and asserts the row appears without a reload.
- Manual: the owner dictates three sentences; the Journal shows them
  arriving live; he filters by source; he searches a word from the
  second sentence; he opens a row and replays it.

## Notes / open questions

- The frame carries the **full** transcript where the existing
  `learning_event` frame carries a 120-char gist (pipeline.py:1183) —
  same audience (owner sockets only), more text. Stated for the record
  in the settled design D3.
- Whether `Review` should be retired rather than re-pointed (it
  duplicates a visible wing tab) is counsel's P2; the ruling keeps it —
  a working verb is never dropped.
