# Handover — Muad'Dib XXXV (2026-10-08)

Read first, in order: `CLAUDE.md`, `pm/STATUS.md`, `docs/internal/philo/phase-15/PROPOSAL.md`, `docs/internal/philo/phase-15/DAY-ONE.md` (v2, the runbook), this file. Memory index: `MEMORY.md` (see `project_philo15_first_day.md`, `feedback_one_test_run_at_a_time.md`, `feedback_astra_brief_bounded_scope.md`, `reference_isolated_agent_rig.md`, `reference_scratch_home_cleanup.md`).

## What happened (2026-10-07 → 2026-10-08, one night after Phase 14's day)

Phase 14 closed with handover XXXIV. Under the owner's autonomy grant ("once you have already moved this mountain, that we move another one, of your choosing, that makes the most sense to work out, to PERFECT the experience with HoldSpeak") I chartered **PHILO Phase 15, The First Day** (#964): rehearse the owner's first real day on real metal with isolated credentials, pay every bounce in a lane, and leave him a runbook. No new face.

**Phase 15 is CLOSED.** 22 lanes, two rehearsals, 90 bounces logged (B01–B90), 73 paid in a merged lane (four in part), 17 open; the "59" first written here was a tally, reconciled 2026-10-08 (`pm/STATUS.md`), the runbook written. Main at the close: the merge of #1016.

| Movement | PRs | What the owner gets |
|---|---|---|
| Charter, inventory, script | #964, #972 | `PROPOSAL.md`, `DAY-ONE-INVENTORY.md` (18 ranked gaps), `DAY-ONE.md` v1 |
| Rehearsal 1 part A (the morning) | #977 | `rehearsal-1a/BOUNCES.md`: B01–B30, 76 shots; the worst: Whisper looping "finally" ×250, decisions OFF by default, the Brief saying "No changes" after a full day |
| Lanes 01–13 | #967 #966 #968 #974 #975 #981 #982 #983 #980 #985 #986 #989 #991 | The summaries blocker asks the route policy; OFF holds and is never a failure; a WAV import always ends; the Parked drawer; strong defaults (the Brief makes itself at 06:00 key-free); the transcript never loops silently; a meeting yields decisions and confirmable actions on day one; the Brief regenerates same-day, dated; READY only when probed, the LAN box on first run; doctor speaks plainly; four Dock sprites, honest widths; the onboarding-hooks flake fixed at its root |
| Rehearsal 1 part B (agents → PR → merge → update → Send) | #992 | `rehearsal-1b/BOUNCES-B.md`: B31–B57, 108 shots |
| Lanes 14–18 | #996 #998 #1000 #1001 #1002 | A Codex launch starts without a human and the lane tells the truth (B49 found: Codex 0.159 defers MCP tools behind tool search, the LAN model has none); YOLO works in its worktree, the desk answers as the desk; the Door registers the Project's repository; one sign-in truth, hooks for every agent, the owner's own name; a merged PR reaches the published update once, within one poll, by its title |
| Rehearsal 2 (the second morning) | #1008 | `rehearsal-2/BOUNCES-C.md`: B58–B89, 78 shots, under a time-machine clock; the merge receipt and the once-only Merged row held; the Brief carried none of yesterday; YOLO held ordinary reads; NOTHING VERIFIED missed all-inference drafts |
| Lanes 19–21 | #1010 #1011 #1012 | The Brief carries the day (order: merged → sent → PR → decision → done → launch); YOLO lets the agent read, Raw approves a cut call from an owner-only temporary store; the second morning tells no lies (QUIET UNTIL, Retry re-checks, Accept/Reject on every claim, NOTHING TO REPORT) |
| The runbook | #1015 | `DAY-ONE.md` v2: sections 0–10, every step Do / See / Else / Paid; v1 parked as `DAY-ONE-v1.md` |

Status PRs #973–#1016 carry every "Open from #…" residual. `pm/STATUS.md` line "PHILO Phase 15" is the ledger.

## Owner catches this session (binding)

- **"A ton of your workers are just running tests at the same time … keep breaking each other."** → ONE TEST RUN ON THE MACHINE: `scripts/test_lock.py` (#979), `-n 4`, at most five live lanes, workers never run FAST, load above 60 means someone skipped the lock. In CLAUDE.md.
- He asked to see Claude Artifacts of the work → the Phase 14 canvas and the "Phase 14 Built" gallery (https://claude.ai/artifact/FgdD7jmm9YXv3Y7xcBf8hf). Canvases and galleries are the only artifacts; documents live in the tree.

## Rulings I made under the grant (recorded in STATUS and the PRs)

- The 120-char held-command head STAYS; a long held call is CUT and approved in RAW from an owner-only store kept only while held, redacted, not encrypted (Astra's ruling adopted); `whole` only at the declared length, else Deny only.
- In YOLO an agent reads git config, runs `gh --version`/`gh auth status`/`gh pr view`, expands `$?` and worktree-reading `$(…)` as printed text, runs a script inside its worktree; substitutions resolve in the EFFECTIVE folder after every `cd`; writes of git config, pushes to another branch, anything outside the worktree hold.
- Turn ends: question > problem > done > chitchat; a question is a QUESTION whatever follows; "blocked by the desk / the gate / the owner" is a decision, blocked by anything else a problem; DONE/IDLE is never a Needs row; a routine answer quotes a brief line and gives no command outside it ("please" is an imperative).
- READY = ready to attempt through a validated adapter; summaries OFF holds and is never a failure; the Brief regenerates same-day, makes itself key-free under the read-only `brief-conductor` principal, and covers the previous day 17:00 through its hour; the order of its rows is merged → sent → PR → decision → done → launch.
- A source is never STALE because of HoldSpeak's own quiet hours (`QUIET UNTIL hh:mm`, not counted); Retry re-checks THAT source; a connector with no answer is a failed check.
- Verification is decided on the claims set, not formatting: a claim is verified only with evidence refs or the owner's review; unverified and unreviewed-inference claims are OMITTED whole from sent text; zero verified claims = NOTHING VERIFIED refused at preview and prepare; Accept is the review gesture, re-formatting is not review, only new owner words count; NOTHING TO REPORT is a claim the owner accepts.
- A merged PR is reported once, in the update actually published; a cut row stays excluded; the Heartbeat polls open PRs round-robin, 10 per poll, every 2 minutes, and discovers a new PR by branch.
- Exact self-name recognition never depends on People; only the one-edit match needs no Person with that name.
- Never delete: an unreadable launch ledger is parked byte-for-byte before any save.

## Lessons (scars)

1. **Astra's lock timeouts.** Her rounds wait on the shared lock; a FAST run ahead of her means a code-read verdict. Brief her with "if the lock is held > 5 min give a code-read verdict", and do not start FAST while her probes matter (routes, races).
2. **The load law pays.** Six reds this session were load flakes (`test_conductor_r4_hand_close::test_kept_worktree_stays_registered`, rail glass under "database is locked"); every one passed alone. Rerun the file alone before triage, record the flake in STATUS.
3. **A lane's FAST reds are the lane's.** Every real red (API surface drift, fixture regeneration, a third-door write, the UX-canon ratchet) came from the lane's own change. Send the exact assertion line; the lane fixes it in minutes.
4. **Rehearsal 2 under a fake clock.** `time-machine` in the worktree venv moved the hub's clock; GitHub, gh, Codex and SQLite stayed real, so some stamps read ten hours old. Mark those rows; do not chase them.
5. **Bounded Astra briefs work.** Four claims, four verify items, 20–25 minutes: she returned every time, with reproductions. Her rulings (the Brief order, the quiet-hours rule, the review gesture) were better than mine and were adopted.
6. **Lane 14's B49 is a platform limit**, not ours: Codex 0.159 offers deferred MCP tools only through tool search, which the LAN model lacks. Verified 2026-10-08 on the owner's sign-in: an OpenAI model gets them. Cause, same day: Codex 0.161 sends the server as one `namespace` tool (`mcp__holdspeak`), which llama.cpp's Responses shim drops; the owner ordered a spike of `pi` as a third harness for the LAN model (`docs/internal/spikes/PI-HARNESS.md`).

## Open at the close (for the next phase to weigh)

- **Not reached by any rehearsal:** a Hand to Claude Code (no key on the rig), email (no Resend key), live recording, the calendar, People, Parked, The week, the lane at 393.
- **B49** Codex + LAN model sees no HoldSpeak tool; VERIFIED RIG-ONLY 2026-10-08 on Codex 0.161 with the owner's ChatGPT sign-in (project.list and desk.needs_you called in one turn). **B75** Connections read NEVER CHECKED once after a SIGNED IN first run, cause unknown. **B90** the second-morning Brief starts at 17:00 the day before, so day-one daytime work is not in it.
- **Queued bounces:** B76 (drag a meeting onto a Project does nothing), B77 (a commitment the transcript says reads NO SOURCE), B78 ("Carol" stays his name in the Room, the agent brief and updates), the P3s B79–B89.
- The folder Send chip reads THIS DEVICE; the claim-review verb is a route with no registry operation; a renamed agent branch retires PR discovery; the Anthropic key has no execution adapter; `gen_docs.sh` stops on a stale `voice.json` line reference; one inherited tsc error in `HandSheet.test.tsx`; `conductor.test.tsx` "LIST keeps the asking agent first" is an inherited vitest red.
- Stale worktrees under `/Users/karol/dev/tools/wt-*` (philo-11-05b, philo-11-06, philo-13-b0-r2, two canvases, 202-01-baseline, one Astra check) are the owner's; not removed.

## Next

The owner's REAL first day, on his desk, from `DAY-ONE.md` v2. Everything he bounces is the next phase's inventory. Until then: no new features (his 2026-10-03 assignment stands); the "open by default" OSS pass still awaits his go.
