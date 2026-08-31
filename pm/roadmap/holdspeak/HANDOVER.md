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
- **Phase 152 The Hands (DC-02): COMPLETE 6/6, holding for the owner's
  shot verdict + merge word.** Exhibit
  https://claude.ai/code/artifact/cf089f7c-3d39-4eff-9322-23a8b4ddfb97.
  Read each story's §"What shipped" before touching the loop — every
  story found real-path defects the fake-adoption tests hid (03: five;
  04: Allow-always + elicitation answers; 05: tool-role rows rendered as
  assistant rows + the missing 32 KB cap; 06: the owner's real-DB
  reconcile blocker, modes counted as CREW, practice capabilities gating
  the Thoughts & notes starter). Laws added: `CHAT_PALETTE` ≠ census;
  `profile_override` = invocation next-run override; `chat.turn` needs NO
  `ToolQualification` (llama.cpp emits native tool_calls for Qwen3.6);
  the LIVE metal path = a LEGACY `profiles` row (the 151 v2 seeding +
  injected engine is NOT the real path); `chat.guardrail`/`chat.compact`
  = group `chat_practice`, visibility `internal`. Rigs:
  `assets/story-03-hub-leg.py` (DRY / `HS152_LIVE=1`), the two glass
  files, the door walk `leg_thread`, `assets/counsel-close.md`.
- **Phase 153 The Practice: COMPLETE 6/6** (01 modes `d2c88d0d`, 02
  slash/prompts `102904a6`, 03 guardrails `5fadacad`, 04 annotations
  `3934cb70`, 05 compact/todo `2c9a6e5b`, 06 walk+close). Counsel
  RATIFY-W-C; M1 (practice capabilities must redact on their OWN
  resolved boundary, not chat.turn's) + S1–S3 fixed in-round. Metal DRY
  6/6 + LIVE 6/6 on .43. Exhibit:
  https://claude.ai/code/artifact/33bb0b5b-1c78-4f8f-977d-258f7cb81d64.
  LAWS added: the .43 server runs a DEFAULT dictation grammar — engine
  sends `grammar:""` on non-tool custom-endpoint calls (probe with curl
  before blaming the model); CHECK constraints never reach existing DBs
  (reconcile kind-drift rebuild for `thread_message_parts`); mocked
  entrances hide dead runners (`run_guardrail`/`run_compact` were dead
  through the real runner until 05).
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

Go (2026-08-31): **PHASE 156 THE FRONT DOOR COMPLETE 7/7 on PR #517**
(feat/the-front-door) — packs A/B/C, one-confirmation apply, the
library reform + ratchet fence, plain words, the topology map,
the stopwatch (0.36 s machinery vs the <60 s bar), counsel RATIFY;
HOLDING for the owner's attended walk. LAWS from this phase: visual
shot-sheet gates at three boundaries are standing process (two stories
bounced and rebuilt); never a positional INSERT; wrappers must cd to
the CURRENT tree; `npm --prefix web run check` in every close. NEXT:
155 The Crew (chartered, in main), then the backend model-era collapse
(BACKLOG.md). Earlier — Go (2026-08-30 night, post-#511-merge): the port lives on MAIN
(fb2d1082) with the platform reset. **Phase 154 The Call COMPLETE 5/5
on PR #513** (feat/desk-chat-the-call) — voice/ear/call-mode/glyph/walk;
counsel RATIFY-W-C, M1+S1–S4 fixed in-round; metal DRY 5/5 + LIVE 5/5;
exhibit https://claude.ai/code/artifact/bc5bb869-3817-4b96-8936-b128cdb1b7a3;
HOLDING for the owner's attended voice leg (it holds the merge word).
Next: Phase 155 The Crew (chartered, in main) on a fresh branch off
main after #513 merges. Earlier: 152 AND 153 were done and holding (153
The Practice COMPLETE 6/6 — modes, prompts+slash, guardrails, annotations,
compact+todo, walk+close; counsel RATIFY-W-C, M1+S1–S3 fixed in-round;
metal LIVE 6/6 on .43; NEW LAW: the .43 llama.cpp server runs a DEFAULT
dictation grammar — free text is forced into {"line":…}; the engine now
sends grammar:"" on non-tool custom-endpoint calls; probe with a trivial
curl before blaming the model). Next is 154 The Call, then 155 — each with counsel-close, glass, metal, and an honest sweep (the
name-diff recipe in §2; `pytest -n auto` collects nothing in the
sandbox, use `-n 4`/`-n 6`; NEVER run pytest un-isolated — it opens the
owner's real DB). The owner wants the whole port; deliver it.
