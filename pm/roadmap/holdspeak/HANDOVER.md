# Handover — Phase 118→119

**Written:** 2026-08-05, end of a marathon session.
**Author:** Opus 4.6 (1M context), acting as orchestrator.
**For:** The next agent who picks up this repo cold.

---

## What HoldSpeak is

HoldSpeak is a **local-first voice desk OS** for developers. Two
modes: dictation (hold hotkey, speak, text lands in your editor with
corrections and learning) and meetings (record, extract decisions/
action items/ADRs via LLM plugins). Everything runs on the user's
machine — Whisper transcribes locally, LLM is user-provided.

The product surface is **the Desk** — a spatial 2.5D PixiJS diorama
where meetings, notes, agents, and artifacts live as draggable objects
in a windowed OS metaphor. Think macOS if macOS were built by one
developer who cares about consent, privacy, and honest construction.

**Scale:** ~103K Python, ~69K TypeScript, ~228K Swift (iPad, dormant),
452 test files, 118 phases shipped. This is a real product, not a
weekend hack.

## The Constitution

`docs/internal/CONSTITUTION.md` — the supreme canon. 11 articles.
Every phase, story, and design decision is measured against them.
The ones you'll hit most:

- **Article II:** Everything is a DeskPrimitive. UI is derived.
- **Article IV:** Every text input can be spoken into.
- **Article V:** Consent is the spine. Propose → approve → execute.
- **Article VI:** Honest by construction. No demo state, no silent
  failures, counts honest at zero.
- **Article VII:** No prose in UI. No modals.
- **Article VIII:** Native-grade craft. 60fps, compositor-only motion.
- **Article XI:** Every consequential operation admitted through the
  kernel before acting, with terminal receipts.

Cite articles in every phase charter. If you disagree with one,
don't ignore it — flag it for the owner to amend.

## The orchestration philosophy

This session established a pipeline that works. Follow it:

### Opus implements → Terra verifies → Sol reviews → Orchestrator decides

1. **You (Opus) implement** in isolated worktrees. Each story gets a
   full brief with the spec, relevant file paths, and clear
   instructions. Use `isolation: "worktree"` on Agent calls.

2. **Terra verifies against spec.** Launch a Terra agent for each
   story with the story spec + worktree path. Terra checks every
   deliverable, finds bugs, reports PASS or FAIL with specific issues.
   Terra is rigorous, sometimes pedantic — that's the point.

3. **Sol reviews for product feel.** Brief Sol with full HoldSpeak
   context (Constitution, what the Desk is, what the phase is
   building, why it matters). Sol thinks about UX, cohesion, edge
   cases, and whether the interaction feels right. Sol is verbose and
   explicit about reasoning — that's what you need to make decisions.

4. **You make the call.** Synthesize Terra (spec compliance) and Sol
   (product vision). Fix what's real. Reject what's pedantic. Accept
   remediations where the fix is real but not a blocker. Be explicit
   about your reasoning — the owner reads it.

### Practical mechanics

- **Launch agents in parallel** where dependencies allow. Wave one of
  Phase 118 ran 6 Opus agents simultaneously, then 6 Terra agents,
  then 4 fix agents.
- **Worktree merging is painful.** Patches from worktrees often fail
  due to line-number shifts when the worktree is behind main. Use
  `git apply --3way` and resolve conflicts manually. For files
  modified in multiple worktrees, apply in dependency order.
- **The DW gate is real.** Every commit needs: story status flipped,
  evidence file created, contract generated (`.githooks/dw contract
  new`), checkboxes flipped, then `git commit`. The gate refuses
  hand-written contracts. See CLAUDE.md for the full process.
- **Bundle multiple stories** with `.tmp/BUNDLE-OK.md` containing a
  one-line rationale. The gate allows it.
- **Read test output before flipping.** The standing feedback
  (`feedback_read_output_before_flip.md`) says: never chain
  flip/commit behind a test run. Read the output first.

### What went well this session

- 25+ Opus agents, 20+ Terra passes, 4 Sol reviews, ~10K lines
  shipped across 3 commits in one session
- The Opus→Terra→Sol→Orchestrator pipeline caught real bugs every
  round (migration ordering, kernel admission, transcript delay,
  paste suppression, triage lifecycle)
- Worktree isolation prevented agent conflicts
- Direct orchestrator fixes for narrow issues were faster than
  launching another agent round

### What to watch out for

- **Worktrees fall behind main.** Phase 117 split `db/models.py` into
  `db/models/`. Worktrees created from main HEAD have the split, but
  agents that rewrite files from scratch often reference the old path.
  The `models/` directory is in `.gitignore` (broad pattern). You may
  need to `git add -f holdspeak/db/models/workbench.py`.
- **Schema version must match.** If you add columns, bump
  `SCHEMA_VERSION` in `schema.py` AND add migration logic in
  `migrations.py`. The user's live DB is at v37 now.
- **The user's DB is at `~/.local/share/holdspeak/holdspeak.db`.**
  Config is at `~/.config/holdspeak/config.json`. Auth token:
  `uMcN-J7wwRrQRTWcac5Ucc_2Wf9kv6wf`. Hub URL:
  `http://localhost:PORT?token=...` (port is dynamic, check with
  `lsof -iTCP -sTCP:LISTEN -P | grep Python`).
- **`tests/e2e/test_metal.py` hangs without a mic.** Always exclude
  it: `--ignore=tests/e2e/test_metal.py`.
- **The web bundle is gitignored.** Edit `web/src/`, commit source
  only. Run `npx vite build` to update the served assets.
- **`uv run` is the Python runner.** Not `python` or `pip`.

## Where we are

### Phase 118 — The Hopper (9/10 shipped)

The Workbench evolved from a configured agent workspace into a hopper.
Nine stories shipped in three commits:

| Story | What | Status |
|-------|------|--------|
| 01 Zone name uniqueness | DB-enforced unique zone names | Done |
| 02 Conductor ref hydration | Forward qualified refs to agent | Done |
| 03 The inlet | Single text field + grounding tray replaces composer | Done |
| 04 @-reference tokenizer | Type @zonename, autocomplete resolves | Done |
| 05 Voice drawer resolution | Two-tier: fast substring + LLM resolver | Done |
| 06 Output minting | Auto-mint pending-review artifacts, kernel-admitted | Done |
| 07 Sprite states | System-level: every primitive has visual state | Done |
| 08 Browser mic pipeline | Browser mic feeds full dictation pipeline | Done |
| 09 Artifact triage | Accept/reject/rework on minted outputs | Done |
| 10 The walk | **NOT DONE** — rolled into Phase 119 | Blocked |

Story 10 blocked because: the dev environment exposed integration
regressions (presence freezes, WebSocket "RECONNECTING", mic UX
hostile). Can't prove the walk when the platform isn't stable.

### Phase 119 — The Revision (chartered, 0/4)

Three pillars + the walk:

1. **Click-to-toggle mic** — Browser MicButton changes from
   hold-to-talk to click-to-toggle with streaming real-time
   transcription. Every surface inherits it.
2. **Integration regression sweep** — Exercise every existing system
   path (presence, WS, meetings, dictation, conductor, kernel,
   seed, migration) against the Phase 118 codebase. Fix what broke.
3. **Seed revision** — Curated toolkit baseline: inference profiles
   (local-4B, local-medium, cloud), starter workbench, one zone.
4. **The walk** — Phase 118+119 combined proof on real device.

### Key files you'll touch

**Backend:**
- `holdspeak/web_server.py` — FastAPI app
- `holdspeak/workbench_conductor.py` — the agent run engine
- `holdspeak/voice_resolver.py` — LLM voice resolution (new)
- `holdspeak/dictation_runner.py` — dictation pipeline
- `holdspeak/kernel/` — operation admission broker
- `holdspeak/db/schema.py` — schema (v37)
- `holdspeak/db/migrations.py` — upgrade path
- `holdspeak/db/workbenches.py` — workbench repository
- `holdspeak/db/plugins.py` — artifact repository
- `holdspeak/db/primitives.py` — directory repository (zone uniqueness)
- `holdspeak/web/routes/primitives/workbenches.py` — all workbench API

**Frontend:**
- `web/src/desk/components/WorkbenchWindow.tsx` — the big one (~1600 lines)
- `web/src/desk/components/MicButton.tsx` — **your Phase 119 target**
- `web/src/lib/speakToFill.ts` — capture lifecycle
- `web/src/lib/micSession.ts` — session management
- `web/src/lib/drawerResolver.ts` — zone name resolver
- `web/src/desk/components/InletAutocomplete.tsx` — @-reference popover
- `web/src/lib/spriteStates.ts` + `spriteVariants.ts` + `spriteStateStore.ts`
- `web/src/desk/gl/engine.ts` — PixiJS world renderer
- `web/src/components/AmbientLayer.tsx` — sprite state watcher lives here

**Test commands:**
- `uv run pytest -q` (all Python tests)
- `uv run pytest -q tests/ -k workbench` (workbench tests)
- `npx tsc --noEmit` (type check, run from `web/`)
- `npx vitest run` (frontend tests, run from `web/`)

**DW commands:**
- `.githooks/dw context holdspeak --compact` — status snapshot
- `.githooks/dw next holdspeak` — next actionable story
- `.githooks/dw story status holdspeak <phase> <story> <status>`
- `.githooks/dw contract new --story HS-NNN-NN --consent yes --reasons "..."`

## The owner

The owner has high standards. They care about:
- **UX quality** — flat/basic is rejected. Things must feel good.
- **Honesty** — no demo state, no silent failures, no prose in UI.
- **Voice-first** — every input gets a mic. Voice is a system
  primitive, not a feature.
- **The Constitution** — cite articles. Don't hand-wave.
- **Deep design, not mechanical** — research first, then implement.
  Material model, not decorations.
- **Proof on real metal** — seeded sims aren't proof. Use real mic,
  real model, real device.

Read the full memory index at
`~/.claude/projects/-Users-karol-dev-tools-HoldSpeak/memory/MEMORY.md`
for all standing directions and feedback.

## Your first move

1. Read Phase 119's charter:
   `pm/roadmap/holdspeak/phase-119-the-revision/current-phase-status.md`
2. Run `.githooks/dw context holdspeak --compact` to see the roadmap
   state.
3. Start with **Story 02 (integration regression)** — find and fix
   what broke before building new things. The presence freeze and
   WebSocket issues are the immediate blockers.
4. Then **Story 03 (seed revision)** — so the dev environment has a
   clean baseline for testing.
5. Then **Story 01 (click-to-toggle mic)** — the big UX change.
6. Finally **Story 04 (the walk)** — prove it all works.

Good luck. Make this desk sing.
