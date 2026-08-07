# HS-117-08 — The dictation decomposition

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** HS-117-07
- **Unblocks:** ---
- **Owner:** unassigned

## The thesis (the bar)

`DictationCore.tsx` is 1,818 lines -- the largest core in the
codebase. It contains 13 internal components, but `SpeakFace` alone
is 567 lines (388-955) with 20+ `useState` calls, 8 async handlers,
the instrument strip, aim row, utterance well, result panel, and
correction form all inlined. `Journal` (195 lines) buries an 80-line
row renderer inline. `Blocks` (193 lines) inlines a drafting form.
`Knowledge` (159 lines) combines two unrelated sections (KB table +
instructions).

When this story ships, `DictationCore.tsx` is a thin shell (~200
lines) that composes extracted sub-components. Each sub-component
lives in `web/src/pages/cores/dictation/` and owns its own state.
The file drops from 1,818 to ~200 lines. Total line count stays
roughly the same (code moves, it does not disappear).

**Articles served:** VI (honest construction -- 567-line components
are not honest), X (sustainability -- isolated units are testable
and reviewable in isolation).

## Deliverables

### 1. Create `dictation/` directory and barrel

Create `web/src/pages/cores/dictation/index.ts` re-exporting every
sub-component. `DictationCore.tsx` imports from the barrel only.

### 2. Extract `SpeakFace` and decompose it (lines 388-955)

Move `SpeakFace` to `dictation/SpeakFace.tsx`. Then decompose its
567 lines into focused children:

- `dictation/InstrumentStrip.tsx` (lines 694-792): the mic button
  row, pipeline toggle, runs-on picker. ~100 lines.
- `dictation/AimRow.tsx` (lines 795-813): delivery aim selector
  with `AIM_KEY`/`AIM_OPTIONS`/`AIM_FACT` constants. ~50 lines.
- `dictation/UtteranceWell.tsx` (lines 814-847): the durable-draft
  textarea with `useDurableDraft` hook. ~60 lines.
- `dictation/ResultPanel.tsx` (lines 883-952): the response display
  with correction form (916-947) inlined. ~90 lines.
- `dictation/useSpeakDeck.ts`: a reducer or hook that owns the 20+
  state variables (`busy`, `result`, `aim`, `phase`, `refusal`,
  `receiptTone`, etc.) and the 8 async handlers (`deliver`,
  `correct`, `release`, `startCapture`, `stopCapture`, etc.).
  ~150 lines.

After extraction, `SpeakFace.tsx` is ~80 lines of composition.

### 3. Extract `Blocks` drafting form (lines 970-1163)

Move to `dictation/Blocks.tsx`. Extract the tile renderer
(1054-1106) and the drafting form (1107-1149) as local components
within the file. ~193 lines, self-contained.

### 4. Extract `Journal` and `JournalRow` (lines 1423-1618)

Move to `dictation/Journal.tsx`. Extract the 80-line inline row
renderer (1529-1609) as `JournalRow` -- it has its own replay
logic and deserves isolation. ~195 lines total.

### 5. Extract `Knowledge` sections (lines 1259-1418)

Move to `dictation/Knowledge.tsx`. Split into `KbTable` and
`InstructionsSection` as local components. ~159 lines.

### 6. Move remaining small components

- `Readiness` (135-246) + `ReadinessLine` (251-307) ->
  `dictation/Readiness.tsx` (~170 lines).
- `Memory` (1168-1219) -> `dictation/Memory.tsx` (~51 lines).
- `LearningDigestFacts` (1223-1257) -> stays inline (34 lines,
  trivially small).
- `Runtime` (1622-1636), `Hooks` (1641-1684), `Nudges` (1688-1752)
  -> `dictation/DictationSections.tsx` (~120 lines combined).

### 7. Slim down `DictationCore.tsx`

The remaining shell: imports from `dictation/`, the `WINGS` constant,
the `DictationCore` export (1754-1800) composing sub-components via
wings, and the `Configure` wrapper (1806-1817). Target: ~200 lines.

## What NOT to do

- Do NOT change any rendering logic or visual output. This is a
  pure decomposition -- move code, do not rewrite it.
- Do NOT rename props, hooks, or state variables. Consumers must
  not notice the change.
- Do NOT add new features or fix bugs discovered during the move.
  File issues instead.
- Do NOT refactor the `useDurableDraft` or mic-session hooks.
  They work; they just need a proper home.

## Test plan

1. `npx tsc --noEmit` -- zero type errors.
2. `npx vitest run` -- all existing web tests pass.
3. Verify `DictationCore.tsx` is under 250 lines:
   `wc -l web/src/pages/cores/DictationCore.tsx` < 250.
4. Verify the `dictation/` barrel exports all sub-components:
   `grep -c "export" web/src/pages/cores/dictation/index.ts` >= 8.
5. `uv run pytest -q` -- backend tests unaffected.
6. Playwright screenshot walk at 1440px and 393px -- the dictation
   surface (speak face, blocks, journal, knowledge, readiness)
   renders identically.

## Estimated scope

~1,600 lines moved into ~10 new files under `dictation/`. ~200
lines remain in `DictationCore.tsx`. Net new lines: ~50 (imports,
barrel, prop interfaces for extracted components).
