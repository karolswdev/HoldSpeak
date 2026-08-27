# HANDOVER — the functional era begins (written 2026-08-27)

For the next agent. Main is at `671b33c6`: **Phase 143 (Intelligence
Router) is COMPLETE, 15/15, merged.** The plumbing era is OVER by the
owner's explicit direction — the next arc is FUNCTIONAL, owner-visible
product work. Read this whole file, then orient (`.githooks/dw context
holdspeak --compact`), then go. The owner's verb is "gooo" / "keep
making progress" — open the next work and run the full arc without
asking permission at each step. This file supersedes the phase-143
`HANDOVER.md` (historical now) and distills six stories of
orchestration across Terra builders and opus auditors.

## 1. What the world looks like now

- Every production inference call rides ONE router: assignment →
  frozen route/operation plan → controller-owned fallback →
  `InferenceRunner` → receipt. Canonical doc:
  `docs/internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md` (the Recipe-run
  trace inside it is verified line-by-line — trust it).
- Two owner surfaces shipped and walked: **Model Library**
  (availability only; adding a model provably changes zero
  assignments) and **Assignments** (seven rows, one shared editor,
  ABA-safe Use default, Next-run receipts). Settings→Models and
  Settings→Assignments are peers; `/profiles` deep-links the Library.
- Transport parity: 12 MCP twins over the same services as HTTP;
  the raw `destination.*`/`model_profile.*` MCP families and the
  `download-and-use` aliases are GONE (disappeared, not deprecated).
  MCP inventory: 134 tools / 32 resources (`docs/MCP_SIDECAR.md`).
- The phase's final record: `pm/roadmap/holdspeak/
  phase-143-intelligence-router/assets/phase-143-closeout-ledger.md`
  (write-once; 12 kill + 9 exit criteria with verified citations) and
  `final-summary.md` beside it.
- Honest residue: **11 inherited test failures** (ledger §4, named
  non-router owners — the suite lawfully exits 1 on them; the baseline
  file is `assets/story-08-inherited-failure-baseline.txt`); **seven
  Swift leaves HELD** by owner ruling with the admitted-attempt bridge
  frozen compile-green on `hold/hs143-10-slice5-swift-bridge` (pushed);
  documented carries in ledger §5.

## 2. What to work on (the owner decides; present these)

The owner's hunger is FUNCTIONAL bits. The ruled/standing candidates:

1. **Phase 139 — The Settings Reckoning** (chartered 0/7, owner crisis:
   "usability = yuck, engine = great"; census 101→33 controls). NOTE:
   Phase 143's Stories 12/13 already rebuilt the Models/Assignments
   rooms — re-scope 139's charter against what shipped before working
   it, or it will re-plow finished ground.
2. **The Dashboard Door** — ruled "next" after Phase 138; repeatedly
   deferred. The owner has wanted this door for a long time.
3. `pm/roadmap/holdspeak/BACKLOG.md` — the parking lot; don't
   mega-bundle from it.

Ask the owner with a short menu, not an essay. Their standing charter
question for every surface: **"will you use this on a tired Tuesday?"**
and **"does this operate with joy?"**

## 3. The standing laws (violate none)

1. **YOLO bar + TIE-BREAKER.** Product runs YOLO. Findings count only
   when a normal product action reproduces damage. Crash-window/
   sleep-resume/race/adversarial = LEDGER NOTES even when reproducible.
   YOU (the orchestrator) tie-break over all counsel/audit output —
   never fix to make a reviewer happy.
2. **Ceremony budget.** Rulings only where text is genuinely unruled.
   Open choices become [ORCH-CALL] items YOU decide with recorded
   dispositions. Counsel (when used at all): one ruling round + one fix
   round, hard cap.
3. **Models.** Workers = Terra (`model: "terra"` on general-purpose)
   ONLY when paired with opus legs in the same arc; `opus-worker` for
   gate audits/verification. Never Terra alone end-to-end; never
   delegate to Fable. Author PMO/roadmap content YOURSELF, directly.
4. **CI is dead** (out of GH minutes). Verification is local-only.
   Push/merge ONLY on the owner's explicit word — then merge without
   watching checks.
5. **Shots before merge** on every owner-facing surface: real-hub
   Playwright at 1440+393 (+200% zoom leg), populated/empty/ERROR
   states, SENT to the owner before the merge word. Beauty pass after
   every functional pass. Flat/ugly-but-lawful is REJECTED.
6. **Web is the spec.** Swift/iPad stays frozen until the owner says
   otherwise; the seed branch is named above.
7. **Never delete — park instead.** "Not in scope"/"stop" ≠ discard.
   Stash with a label, branch, or leave dirty. Deletion only on an
   explicit "throw it away." (Learned the hard way; the owner's own
   words: "why unwinding it tho?")
8. **Isolated HOME, always, for anything that can open a DB —
   documented generators included.** A manifest generator run without
   it touched the owner's REAL database this arc; only the
   marker-integrity guard prevented damage. `HOME="$(mktemp -d)"` on
   every such command, no exceptions. And always
   `uv run --python 3.13.11` (bare uv grabs 3.14; those results get
   discarded).
9. **No modals; no prose in UI; mic on every text input (click-to-
   toggle, never credentials); one egress badge; errors in-flow; debug
   behind one folded RAW well; replace-never-sit-beside.**

## 4. The arc rhythm (proven across six consecutive stories)

1. **Open**: `dw story status holdspeak <phase> <NN> in-progress`;
   branch `feat/...` from fresh main.
2. **Plan**: ONE Terra research worker, read-only, writes
   `assets/story-NN-...-plan.md` — obligation register, file:line
   inventory, 3–6 slices with NAMED proof files and focused commands,
   [ORCH-CALL]s each WITH a recommendation (no open questions). You
   rule the calls and append a dispositions section to the plan.
   Pre-stage the NEXT story's plan worker while the current story
   closes — read-only planning overlaps safely.
3. **Build**: Terra workers, 1–2 slices per round. The brief
   boilerplate that matters: never stage/commit; focused tests only
   with isolated HOME + the Python pin; proofs construct PRODUCTION
   objects (decorated fakes are a named sin; only external wire
   boundaries may be faked); grep-audit every deleted symbol AND run
   every referencing test file; census/anchor/manifest regens are the
   LAST act of a round; pre-empt the "provider" scope misfire (state
   plainly: "provider = HoldSpeak's own engine seam, not vendor SDKs").
4. **Verify EVERYTHING yourself.** Rerun the worker's focused sets
   with your own commands and read the tails. Workers inflate reports
   and misfile their own breakage as "pre-existing" — this arc a
   worker filed typecheck errors in ITS OWN new files under "existing
   errors." Check provenance of every "baseline" claim. For UI: LOOK
   at the screenshots yourself (Read the PNGs) and apply the joy bar
   before the owner ever sees them.
5. **Gate audits**: `opus-worker`, READ-ONLY, briefed with the bar
   restated + "report EVIDENCE, not verdicts — the orchestrator
   tie-breaks; ONE report, no rounds." Run them on COMMITTED diffs so
   they can overlap the next build round. Eight audits this arc; seven
   returned zero product bugs. Their ledger notes are cheap to close
   in the next story — carry them explicitly.
6. **Sweep**: full CI-style suite DETACHED —
   `HOME_REAL=$HOME nohup env HOME=$(mktemp -d)
   PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright
   npm_config_cache=$HOME/.npm uv run --python 3.13.11 pytest -q -n
   auto --ignore=tests/e2e/test_metal.py > <log> 2>&1 & disown` plus a
   Monitor on the PID (harness-backgrounded runs get killed ~98%).
   Triage FAILED vs the baseline file. Zero-branch-new is the bar.
   Non-baseline names: serial ×2 (twice over if they repeat across
   sweeps) — green = flake (families listed in §6), red = REAL, back
   to a worker with the chain. After EVERY sweep: `git checkout --
   pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/` (glass
   e2es clobber those PNGs every single time).
7. **Commit per round** through the gate: stage by explicit path,
   `.githooks/dw contract new --story <ID>`, flip every box HONESTLY,
   commit with a real narrative. One story flips done per commit.
8. **Close**: `dw evidence capture` of the full sweep — run it via
   Bash `run_in_background` (it exceeds the 10-min foreground cap) and
   note it lawfully exits 1 on the baseline (`--tests-capture` refuses
   nonzero; use the plain contract and certify Tests-ran on output you
   read). Append YOUR triage note to the evidence file. Flip, update
   the status doc + README `Last updated` line, close commit. When ALL
   phase stories are done, `dw check` demands a `final-summary.md` —
   write it or the gate blocks.
9. **Merge on the owner's word.** Deliver shots first for UI stories.

## 5. Orchestration knowledge (what actually made this fast)

- **Parallelize audits against builds** (committed diff vs dirty
  tree), and pre-stage the next plan while closing the current story.
  Six stories closed in ~2 days this way.
- **Workers die on transient API errors** (WebSocket 1000/1006 +
  HTTP 500) — happened 3× this arc. `SendMessage` to the same agent id
  ALWAYS resumes with full context. Resume brief: "transient error,
  not a refusal; `git status --short` first; anything dirty is YOUR
  partial work — keep it." Corollary: even deleted uncommitted work is
  recoverable — the worker's transcript holds every file it wrote;
  resume it and ask it to re-apply.
- **The shared-file law** (this arc's most expensive lesson): editing
  a HOST file (SettingsCore, SurfaceWindows routing) puts the ENTIRE
  neighboring surface's e2e file in your round's net. "That surface is
  untouched" is FALSE when its host is touched. The `/profiles`
  misroute broke the whole Model Library with zero JS errors — the
  room just never mounted. Corollary: surface REPLACEMENT drags
  cross-cutting tests (old-glass e2es, API manifest, interior-canon
  guards, censuses) — name them IN the slices; Story 11 did and got
  the phase's only zero-branch-new first sweep.
- **Guards are friends.** Twice this arc a "failing guard" was a REAL
  product regression (the Runs-on folded-room law; the interior canon)
  — restore the law, never weaken the guard. The marker-integrity
  guard saved the owner's real database.
- **Flakes get diagnoses, not labels.** The 393 glass flake failed
  1-in-3 SERIALLY — not load. Diagnosis: hydration race; fix: a
  server-fact readiness attribute the test awaits. No sleeps, no
  retries, proven 15× + xdist. If it recurs it is BRANCH-NEW by ruling.
- **Fix ledger notes when they're cheaper than ledgering** (the
  error_500 secret scrub turned out real on a normal path; the
  MCP_SIDECAR count was a 2-number edit). The bar cuts both ways.
- **cwd trap**: after `cd web` or `cd apple`, relative pytest paths
  silently resolve wrong ("no tests ran" ≠ pass). Run from repo root;
  subshell `(cd web && ...)` for npm.
- **Agent-naming ghosts**: workers sometimes ask about "dim"/other
  agents from stale context. Tell them plainly: sole ownership,
  proceed. Don't let a worker block on a dead fork.
- **dw specifics**: contract AFTER staging (restage invalidates);
  `dw next` may surface stale phase-91 — the roadmap README's
  "Current phase" line is truth; evidence files are dw-stamped —
  workers may hand-author narrative but the CAPTURE must be real.

## 6. Known xdist/e2e flake families (serial-green, don't chase)

workbench deadline-expiry · device-recording tick sender-exception ·
refinement recovers-owner / reciprocal-stop / late-success-suppressed ·
jira/github enablement · conductor deadline · delivery-campaign ·
glass e2es under load (1440 sibling of any leg) · sigkill process-input
· kernel real-hub sigkill cursor replay. The assignments-overview 393
leg is NOT on this list anymore — it is fixed; recurrence = branch-new.

## 7. The 11 inherited failures

Named with owners in the closeout ledger §4 — they predate Phase 143,
reproduce on main, and the suite lawfully exits 1 on them. Never call a
sweep containing exactly them "broken," and never call it "green"
either: say "baseline-exact, zero branch-new."

Go make the functional bits sing. The engine underneath them finally
deserves it.
