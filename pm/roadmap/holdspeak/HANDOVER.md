# HANDOVER — the Desk Chat port, mid-flight (written 2026-08-30, 04:15)

For the next agent. The previous session hit its context ceiling
mid-Phase-152. Read this whole file, then `git status` (the tree was clean at
handover; §4 maps what landed). Worktree:
`/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port`,
branch `worktree-warpdrv-chat-port`, **PR #507**.

## 0. The owner's ruling (verbatim, twice)

1. "Let's impl it!" on `docs/internal/PLAN_PHASE_DESK_CHAT.md` (the
   warpdrv port RFC; warpdrv is AGPL — NOTHING is copied, the clone is
   gone; `git grep -i warpdrv` must hit only the plan + phase records).
2. On seeing only DC-01: "I was totally hoping for a holistic
   implementation." → **DC-02..05 ship on PR #507, in order, same
   rigor.** Do not narrow again.

## 1. Where it stands

- **Phase 151 The Thread (DC-01): COMPLETE 8/8**, merged with main
  (`1c9e4d02`), close counsel M5 fixed. Renumbered 150→151 because the
  sibling session shipped its own Phase 150 (Delegation+Monday, PR #508).
  LAW: `git fetch` + check `origin/main` README "Current phase" and
  `ls pm/roadmap/holdspeak | tail` BEFORE numbering a phase.
- **Phase 152 The Hands (DC-02): 2/6 committed** (02 the gate
  `be973104`; 01 the loop `d44f8d74`, 80 passed). Remaining: 03 People fence
  (M1/M2 — the loop already accumulates `_sensitive_texts` and marks
  people results sensitive; story 03 = the real-coordinator pins + metal
  leg 2), 04 pending box + elicitation UI (`threads.ts`,
  `ThreadPullout.tsx`; frames exist), 05 renderers + `thread.set_status`
  tool, 06 walk. Settled design: `phase-152-the-hands/assets/settled-design.md`
  (the truth table in D2 is law).
- **Phase 153 The Practice: chartered** (`assets/settled-design.md`,
  `audit-census.md`, six stories scaffolded; story bodies NOT yet
  written — write them from the settled design before building). Both
  data-layer builders landed and are committed (§4).
- **Phase 154 The Call: reserved.** FEASIBILITY RULING (orchestrator,
  from the research): PyTorch `kokoro` needs Python <3.13 (we run
  3.13); `kokoro-onnx` works (MIT, weights Apache-2.0, RTF 0.6 on
  M-series, cold start 0.3 s) BUT depends on `phonemizer` + espeak-ng
  = **GPL-3.0**. Decision: default TTS = the browser Web Speech API
  (zero deps, zero egress, instant); `kokoro-onnx` = optional
  owner-installed extra (`holdspeak[tts]`) with a visible GPL note and
  the egress-badged weights download reusing the Model Library's
  download/receipt pattern (`holdspeak/web/routes/model_library.py:83`).
  VAD: reuse the EXISTING energy VAD (`web/src/lib/vad.ts` →
  `micSession.ts` → `/api/dictation/transcribe`); Silero later. Call
  mode state machine + `threads.call_mode` (counsel M9) in the
  research report (task output in this session; re-derive from
  `phase-152-the-hands/assets/counsel-design-beat.md` M9/S6/R4).
- **Phase 155 The Crew: reserved** (counsel RATIFY; 5-story cut in the
  counsel file).

## 2. CI truth

Main's own CI is red on every recent commit (the 64-name inherited
baseline: `phase-143-intelligence-router/assets/story-08-inherited-failure-baseline.txt`).
The honest gate = **name-diff against main's latest run** (the recipe:
`gh run view <id> --log-failed | grep -oE '(FAILED|ERROR) tests/[^ ]+'`
for both, `comm -23`). Last diff on `36757847`: zero branch-new. Web:
`uv run python scripts/check_web_baseline.py --run` (5 inherited names).

## 3. Standing laws this arc added (all scars)

- Fake-adoption unit tests hid three real-path defects; **drive the
  REAL coordinator with a fake engine factory** (`test_thread_service.py`
  `test_real_coordinator_with_fake_engine` is the pattern).
- `getattr(db, "_broker")` is always None — the broker is
  `holdspeak.kernel.runtime._service()`; one factory
  `holdspeak/web/routes/_thread_factory.py`. Production executors need
  the broker (`broker=None` is test-only).
- `SurfaceFooter` is a fixed 36 px bar; tall feet are their own flex
  child. Client contracts drift from server (flat GET, `[pos,total]`
  siblings, epoch seconds, inline parts) — glass finds it, jsdom does not.
- The harness blocks `HOME=` inline and `cd` chains; run isolated-HOME
  things via a scratch script or `dw evidence capture -- env HOME=…`.
  The evidence wrapper truncates long output (sweeps → scratch file).
- Glass/walk rigs clobber phases 141/143/144/145/147 shot assets —
  `git checkout -- pm/roadmap/holdspeak/phase-14*` after every run.
- NEVER `git stash` (shared stack; a worker dropped one entry — the
  three old ones survived). Workers must be told explicitly.
- Builders that finish early and are resumed >4× lose their transcript;
  spawn fresh with a full brief.

## 4. What landed at handover (all committed)

Run `git status --short` — it should be clean except untracked scratch. What was landed at handover:
- **HS-152-01 (the loop)** — committed `d44f8d74` (files: thread_service.py pass loop, thread_tool_protocol.py, inference_stream.py emitters, the three frames + web mirror, test_thread_tool_loop.py).
- **Phase 153 builders' work — BOTH LANDED GREEN AND COMMITTED** (`9cb769a9` modes/prompts, and the door/capabilities commit after it) — kept here as the map of what exists:
  (a) modes+prompts data layer — `recipes.kind`, `holdspeak/services/thread_modes.py`,
  seeds in `holdspeak/seeds/fresh-desk.yaml`, notes `?tag=` query,
  `tests/unit/test_thread_modes.py`; (b) `door.add_item` + `DoorService.add_item`
  + `action_items` source columns + capabilities `chat.guardrail`/`chat.compact`
  + `holdspeak/services/thread_practice.py` + backfill `chat-practice-assignments`
  + `tests/unit/test_hs153_practice_capabilities.py` + 143 ledgers. Census rows for
  `thread_practice.py` runner entrances are in place (122 scoped passed).
- `pm/roadmap/holdspeak/phase-153-the-practice/` story bodies are
  scaffolds (write them from D1–D6) — commit with the 153 charter.

## 5. Mechanics

Rigs: `phase-151-the-desk-chat/assets/story-08-rig.py` (glass, both
widths, foot-inside-card assertion), `story-08-metal.py` (real `.43`
llama.cpp, bus first-delta timing, captured cloud payload),
`tests/e2e/test_hs151_thread_glass.py`, door walk leg `thread`. The
`.43` deployment must be tool-QUALIFIED (`ToolQualification`) before the
152 metal leg. Docs law: touch README/USER_GUIDE/MCP_SIDECAR per phase;
tool count arithmetic (`len(TOOLS)` is truth). Shot exhibit for 151:
https://claude.ai/code/artifact/5f8ffe8d-63cb-45fa-8c67-6e6d4a655705 —
make one per phase before asking the merge word.

Go: finish 152 (03→04→05→06), then 153, 154, 155 —
each with counsel-close, glass, metal, and an honest sweep. The owner
wants the whole port; deliver it.
