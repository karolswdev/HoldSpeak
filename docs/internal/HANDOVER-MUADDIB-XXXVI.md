# Handover — Muad'Dib XXXVI (2026-10-08, night)

Read first, in order: `CLAUDE.md`, this file, `pm/STATUS.md` (the Phase 15 line is the ledger of everything since 2026-10-07), `docs/internal/philo/phase-15/DAY-ONE.md` (v2, the owner's runbook), `docs/internal/HANDOVER-MUADDIB-XXXV.md` (Phase 15's close). Memory index: `MEMORY.md` (`project_fresh_start_2026_10_08`, `project_pi_third_harness`, `reference_worktree_venv_extra_dev_only`, `feedback_one_test_run_at_a_time`, `feedback_astra_brief_bounded_scope`).

Part I is the state. **Part II is the doctrine: how to orchestrate the Fedaykin without losing the day to test runs.** The owner ordered it tonight: "we have spent far too much time doing far too many iterations and especially were getting stuck on huge-ass test runs that took forever and locked each other out. The Muad'Dib who takes over is the one calling the system-level tests. And us, we will be doing the thing."

---

## Part I: the state

### The desk is FRESH

At the owner's word tonight ("start fresh … nuke my main environment … start the journey on our product together, from scratch") his real HoldSpeak state was PARKED, never deleted, at `~/HoldSpeak-parked-2026-10-08/` (README inside: `config/`, `data/` with the DB, three backups, log and six recordings, `dot-holdspeak/`, `Documents-HoldSpeak/`). Kept in place at his call: the 3 GB local models, the meaning-search model, the Claude Code and Codex hooks. Deleted at his call: the People Keychain key (the parked DB's People data is sealed). Left alone, on evidence: the `acli` Keychain item, which is the Atlassian CLI's own sign-in, not ours.

The hub was started from the main checkout at `6cd739cb6` and he was given his owner link. **Expect a first-run desk.** Every bounce he reports from here is the next phase's inventory. **Never read or write the parked folder without his word.**

### What landed after Phase 15 closed (all on main)

| PR | What |
|---|---|
| #1018 #1019 | B49 reconciled: Codex gets our MCP tools on an OpenAI model (verified with his ChatGPT sign-in, Codex 0.161). On the LAN box it does not: Codex sends the server as ONE Responses-API `namespace` tool, which llama.cpp drops. The "59 paid" at Phase 15's close was a tally; the count is 73 paid (4 in part), 17 open. |
| #1020 | SPIKE (22 min, report only): `pi` can be the third harness. `docs/internal/spikes/PI-HARNESS.md`. |
| #1022 | **pi is the third coding-agent harness** (`@earendil-works/pi-coding-agent` 1.1.0, on his PATH). `pi-default` profile; per-launch isolated `PI_CODING_AGENT_DIR` (`holdspeak/delivery/pi_launch.py`); one extension `holdspeak/agent_context/pi_extension/holdspeak-pi.ts` (gate fail-closed + rider); proven by a real Hand in YOLO against the LAN box. Astra found six MUSTs over two rounds, all paid: the HUB decides Secure MCP holds from the launch record (`GateService._decide_mcp`), reads outside the worktree are gated, Stop kills the recorded process group by generation (pgid + sid + start time), Write receipts complete, expiry deny wording. |
| #1024 | `holdspeak agent-hook install|uninstall --agent pi` (pi has no hook file; the CLI says so in tokens). |
| #1026 | **An agent's words render.** `web/src/desk/components/AgentWords.tsx` is the ONE renderer of an agent's (untrusted) markdown, on 11 surfaces. Rulings: a compact row shows THE ASK (last paragraph ending "?"); the 393 SENT line stops at the id. Canvas `docs/internal/philo/phase-16/02-canvas/agent-words.html`; shots `02-shots/`. |
| #1021 #1023 #1025 #1027 | Status entries. |

His machine, repaired tonight with backups beside each file: `~/.codex/config.toml` `codex_hooks` → `hooks`; `~/.codex/hooks.json` refreshed to the current template (his ccgram entries kept) and re-trusted. Doctor read all three agents installed before the fresh start; after it, Codex reads "does not trust the HoldSpeak hooks yet" because the trust stamp was parked: the first-run card's Use it re-trusts (the day-one path).

### Open (STATUS has every residual)

- Canvas question: the Room's ITEMS list has no Hand verb, so a project item cannot be handed from the desk itself.
- From Phase 15: B32 (no macOS calendar path), B76–B78 (drag-to-Project does nothing; NO SOURCE on a spoken commitment; "Carol"), B79–B89 (P3s), B90 (the second-morning Brief starts 17:00 the day before).
- pi: `edit` through the gate not walked on metal; a hold waiting at Stop stays WAITING; every pi MCP call is one hub round trip; a recycled group whose own leader also exited is indistinguishable by start time.
- AgentWords: a positive rendered test for a two-line paragraph; the shots read CLAUDE CODE ASKS with pi's words.
- Inherited reds on main: `test_rebrief_receipt_survives_send` (waits for `/steer`, Re-brief posts `/rebrief`), `test_hs201_09_connect_engine…[393]` (no Models menu item), one tsc error in `HandSheet.test.tsx`, `conductor.test.tsx` "LIST keeps the asking agent first".
- Lane 13's question stands: which tests hold > 1024 descriptors in an xdist worker.
- The "open by default" OSS pass awaits his go. No new features until his real first day is walked.

---

## Part II: the doctrine. How to orchestrate the Fedaykin.

### The one sentence

**The orchestrator owns every system-level run; a worker proves its change with the smallest run that can fail; one run on the machine at a time; one bounded brief, one bounded review, and the lane is done or it is in STATUS.**

### Why (the scars, with numbers)

- FAST is **11 minutes** under the lock with `-n 4` (it was 5:40 alone with `-n auto`). Every FAST is a lock the whole machine waits on. Today FAST ran **ten times** for five PRs. Three of those were wasted on a worktree venv I had synced with `--all-extras` (descriptor exhaustion, "Too many open files" in `popen-gw1`, thousands of errors). One was wasted on a stale grep that hid the real error.
- Astra timed out on the lock **four times** ("gave up after 300 s") and gave code-read verdicts. A code-read verdict is fine; a 25-minute wait for one is not.
- The pi lane took **three rounds** (build, r1 with four MUSTs, r2 with two MUSTs) because the brief said "prove a–e" but did not name the trust boundary cases (Secure MCP, reads outside the worktree, dead-leader Stop). Naming them in the brief would have cost ten lines and saved two hours.
- Workers running vitest, glass, pytest and `check_web_baseline` in sequence on one PR spent **~40 minutes on the lock** for a copy change. A copy change needs one vitest file.

### The rules

**R1. System-level runs are the orchestrator's, serial, at most once per PR.** FAST, the scoped glass set, `check_web_baseline --run`, the UX-canon ratchet over the whole tree, the atlas, the census. The orchestrator runs them AFTER Astra's verdict, on the final head with main merged in, once. A red goes back to the lane with the exact assertion line; the lane fixes it with its scoped run; the orchestrator reruns only the red file alone, then FAST once more only if the fix touched product code. Never run FAST while Astra's probes matter (routes, races, the gate); her round first, FAST after.

**R2. A worker's test budget is written in its brief, in files.** "Run `tests/unit/test_x.py` and `tests/unit/test_y.py` through the lock" or "one vitest file". A worker never runs FAST, never `check_web_baseline --run`, never glass_for's whole set, never the ratchet over the tree. If the worker believes a wider run is needed, it writes that in its report and the orchestrator decides. Default budgets: a backend change = the two or three unit files beside it; a face change = its vitest file plus ONE glass file at 1440 and 393; a copy change = one vitest file; a docs or status change = none.

**R3. The lock is law, and the lock is why budgets matter.** Every pytest/vitest/glass/graph run goes through `uv run python scripts/test_lock.py -- <cmd>` with `-n 4`. The lock serialises the machine; a worker holding it for 40 minutes stalls every other lane and Astra. Load above 60 means someone skipped it. A new worktree is synced with `uv sync --extra dev` ONLY; never `--all-extras`; plain `uv sync` strips pytest.

**R4. One brief, bounded, with the trust boundary named.** A brief states: what to build (numbered, each beside its twin in the code), the test budget (R2, in files), the proof (what must be seen, at which widths, which receipts), the rig law (isolated HOME; never the owner's real DB, Keychain, `~/.codex`, `~/.claude`, `~/.pi`; kill what you start), and THE CASES THAT WOULD MAKE ASTRA SAY DNR: for anything near the gate, custody or egress, name the bypass cases up front (an env flag as the only guard; a read outside the worktree; a dead leader; a recycled id; an empty hook answer; a name that looks like a read). A brief that names them is cheaper than a review that finds them.

**R5. Astra: one round, 20–25 minutes, four claims, four verify items, and the lock rule in the brief.** "If the lock is held longer than 5 minutes, give a code-read verdict and say what you skipped." Her second iteration is a re-check of the fix commit only. After it the orchestrator verifies the remaining MUSTs itself (read the code, run the one file) and merges; MAYs go to STATUS. A security MUST is never carried to STATUS: it is fixed before merge, however many rounds.

**R6. The orchestrator reads before it relays.** Every lane report and every Astra report is read in full before anything is sent on. Relay the exact assertion line, the exact file:line, the exact rule; never "fix the test". A red that passes alone is a load flake: record it in STATUS, do not chase it.

**R7. One lane, one PR, one status entry, one worktree removed.** Status entries are a one-line PR (`status/prNNNN`) merged at once, never bundled. The worktree is removed at merge. The owner's `~/dev/tools/wt-*` worktrees are his.

**R8. The owner's word is the only gate, and it is short.** "The word", "cool", "sounds like a great path forward" is a go. "I'm confused" is a stop: answer in plain words before anything else. A question from him is answered with the deliverable he asked for (an assessment, a table, a URL), not with a lane.

### The cadence of one lane (what it should cost)

| Step | Who | Budget |
|---|---|---|
| Brief (R4) | orchestrator | 10 min to write; names the twin files, the test files, the proof, the DNR cases |
| Build + scoped proof (R2) | one Fedaykin (`opus-worker`) | 30–90 min; its test runs total < 5 min on the lock |
| Astra r1 (R5) | orchestrator launches | 20–25 min, in parallel with nothing on the lock |
| Fix commit | the same Fedaykin (SendMessage, context intact) | 10–30 min; scoped runs only |
| Astra r2 (re-check) | orchestrator launches | 15–20 min |
| FAST + scoped glass, once, final head (R1) | orchestrator | 11 min + glass |
| Merge, status PR, worktree removed (R7) | orchestrator | 3 min |

Two hours for a real lane. Today's lanes took three to five because R1, R2 and R4 were not yet written down.

### What the owner and the orchestrator do meanwhile

The owner uses the product ("the thing"): his first real day from the runbook, on the fresh desk. The orchestrator sits with him: every bounce becomes a numbered row (B-numbers continue from B90), each row gets a lane or a queue, and the lanes run under Part II. The orchestrator does not build; the orchestrator briefs, reads, relays, runs the system-level tests, merges, records.

---

## Next

1. The owner's real first day on the fresh desk, from `DAY-ONE.md` v2. He has his owner link; the hub is running from the main checkout.
2. Bounces → lanes under Part II. The first lane is whichever he bounces first; the canvas question (Hand from the Room's ITEMS list) is likely.
3. Phase 16 is not chartered; name it from his first day, not from the backlog.
