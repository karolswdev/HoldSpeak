# Phase 63 — Backend Decomposition: final summary

**Closed:** 2026-06-12, 6/6 stories, opened and closed the same day on
owner direction ("E, puh-lease"). Backlog row **E** shipped — the backend
twin of Phase 54.

## What shipped

The two backend god-objects paid down their debt, behavior-preserving:

- **`web_runtime.py`: 2,635 → 555 lines** (boot, config apply, presence
  sync, onboarding nudges, signals, run). Eight mixins in
  `holdspeak/runtime/`: dictation_capture (413), wake_glue (~360),
  device_glue (~315), meeting_glue (552), routing_glue (450), activity
  (264), plugin_queue (171), transcriber_state (144).
- **`meeting_session.py`: 1,674 → a package** with a 795-line lifecycle
  core, the pure models in `models.py` (240), and four mixins
  (transcribe_loop 270, mutations 285, intel_analysis 207, persistence
  145). The module became the package, so every existing import works —
  zero test edits on the meeting side.
- **The verbatim standard held**: per-story body-line diffs lost exactly
  ONE original line across the whole phase — each `class X:` statement,
  rewritten as its mixin composition.
- **The test-edit policy held**: the scaffold's monkeypatch census
  predicted every test change; the only edits were patch-target /
  source-lock paths (13 sites across 5 files), assertions byte-identical.
- **The shape is locked**: 5 backend density guard tests
  (carve-don't-bump messages; routes/meetings.py recorded as the named
  watch item) + `ARCHITECTURE_BACKEND_RUNTIME.md` (the pattern, the
  concern map, the five rules, the add-a-concern walkthrough) +
  CONTRIBUTING pointer.

## The closeout's two production bugs (the phase's biggest finds)

The live boot proof (`run_web_runtime` in a subprocess, real HTTP, real
Chromium) caught two PRE-EXISTING bugs in the live meeting path, which no
suite or dogfood had exercised end to end since Phase 60:

1. **Live meeting start was broken since Phase 60**: HS-60-03 added
   `on_wake_type=` to the `MeetingSession(...)` constructor (it belongs
   only on `WebRuntimeCallbacks`); every real start raised a TypeError,
   masked by the FakeMeetingSession's `**kwargs`. Fixed + locked by an
   AST/signature contract test.
2. **Transcriber construction was racy with a process-fatal blast
   radius**: the warmup thread and first-use raced the unlocked
   check-then-construct; two `_MlxTranscriber` instances → mlx_whisper's
   process-level model cache → cross-thread MLX → `libc++abi: no
   Stream(gpu, N)` death at meeting stop. Fixed with a dedicated init
   lock + an 8-thread race lock test.

Both fixes are the refactor-phase exception done right: the closeout gate
required a working live path, and the bugs were proven pre-existing
against the original files.

## The smaller lessons (recorded in the architecture doc)

- Patch targets live where the lookup happens — proven twice (a missed
  `Transcriber` patch loaded REAL MLX inside a unit test and aborted; a
  wrong-module patch passed two tests coincidentally).
- Relative imports gain a dot at EVERY indentation when a module becomes
  a package — guarded `except ImportError` fallbacks mask the mistake.
- No unused imports in mixin modules: an importable-but-uncalled name is
  a patching trap (auto-trimmed everywhere).

## Numbers

- Final suite: **2775 passed, 17 skipped** (+7 this phase: 5 guard + 2
  regression locks).
- 6 commits, one per story, plus the scaffold; PR merged on green CI.

## Where this leaves the backlog

**E is shipped.** The named watch item is `web/routes/meetings.py`
(1,525). The strongest remaining strategic row is the launch moment.
