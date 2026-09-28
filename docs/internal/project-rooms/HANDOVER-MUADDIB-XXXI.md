# Muad'Dib handover XXXI — 2026-09-27 → 2026-09-28: PHILO Phase 9 The Room on the Contract, chartered, built and closed

Read with XXX (laws 9–13), XXIX (the method), `docs/internal/TWO-BRAINS.md` (amended by #679), and `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/final-summary.md` (the exits, both brains per story, THE LEDGER). Memory: `feedback_phase9_rulings.md` is the running record of this phase.

## Where it ended (main `7afdce77`)

- **PHILO Phase 9 — CLOSED 2026-09-28** on the owner's word ("Reviewed — close after story 05", https://claude.ai/artifact/C66EYhCAcDBbPdkeZJFFYD). Rehearsed, owner-reviewed; not a sitting. Seven stories: 01 #680, 02 #684, 03 #686, 04 #683, 05 #688, 06 #687, 07 #685; plus the charter #677, the steward beat #678, the canvases #681, main's inherited reds #682, the two-brains canon #679. Exits 1, 2, 3, 6, 9 MET; 4, 5, 7, 8 MET WITH QUALIFICATION. Residual 284 → 240; public tools 229 → 237; atlas 167 → 184.
- **What he can do now:** work a project in the Room over MCP and on the face — items with an honest late milestone, a steward run whose card tells the truth, draft → publish → copy → mark delivered (several per update, each with a receipt), receipts that say REFUSED when refused; grant an agent run/stop/publish on one project and stop it (also when archived); a cold Codex session does the whole job from the catalogue alone.
- **No phase is chartered.** THE LEDGER in the final summary is the menu. Top of it: he has still not used it; delivery is copy+confirm only (his Q0); items enter only by MCP; the AI bar covers selected note text at 393; the 1440 Ask well covers RECEIPTS (a Condition 7 design call).

## The owner's rulings this stretch (verbatim picks in memory)

D1 work in a project room; D2 one desk-debt story; D3 Codex closes. Charter: Q0 real delivery → "Copy to clipboard only"; Q1 by effect; Q2 bounded delegation (bound run/stop/publish); Q3 show items, enter by MCP; "Several per update"; "Ratify, build it". Canvases: "Ratify as drawn". **"Just get it in. Why does GH PR matter so much to you?" → CI does not gate merges** (`feedback_ci_does_not_gate.md`). He caught idle workers polling CI ("It feels like one of our workers is stuck…") → lanes never watch CI.

## The two brains, this stretch

Codex Astra checked everything: charter r1–r5 (DNR, DNR, R-W-C, R-W-C, R-W-C), canvases r1–r3 (DNR, DNR, RATIFY), story 01 counsel r1–r3, 02 r1–r3, 03 r1–r2, 04 r1–r2, 05 r1–r2, 06 r1, 07 r1–r2, the summary r1. Every first counsel on a built story found a real defect (a wrong-Room write; a resurrected run; a refused delivery shown green; stop-by-name; lost evidence). Astra's own lane (the steward beat) self-invoked a `claude -p` check labelled as Muad'Dib's — relabelled, re-checked, and the canon fixed (#679: a dispatched lane never self-checks; a `claude -p` run is advice only).

## Laws added (with XXX's 9–13)

14. **CI does not gate** (owner). Merge on the lane's red→green scoped proof + the other brain's verdict; CI is a post-merge signal.
15. **Lanes never watch CI.** Push, report, end the turn; one central watcher; start counsel in parallel with CI.
16. **A worktree-isolated agent cannot set HOME** → it cannot run isolated tests. Test lanes run non-isolated in a plain `../wt-*` worktree (`uv sync --python 3.13 --all-extras --all-groups`; `HOME=$(mktemp -d) .venv/bin/python -m pytest`).
17. **A conflicting PR runs no CI, and stale runs for superseded heads hog the single macOS runner** — merge main into lanes when it moves; cancel superseded runs.
18. **Close a replay class with ONE store, written in the terminal transaction** (effect + answer + receipt), never a second table.
19. **A name is not an actor.** Authority compares actor kind + identity.
20. **An evidence copier keys by case × width × run** and refuses reuse; a screenshot byte-identical to another proves nothing — assert on-screen, unobscured visibility.
21. **A wrapper script propagates every status** (`${pipestatus[n]}`), proven over all success/failure combinations.
22. **Build what was ratified** — map the ratified words on the face; the hub's words stay the hub's.

## Open, for the next session

- Ask the owner what is next, with THE LEDGER as the menu (the value-era question). Codex Astra checks; Opus workers build in plain worktrees.
- Worktrees left in place (never delete, park): `../wt-philo-9-02`, `-03`, `-05`, `-06`, `-07`, `-close`, `../wt-canon-law8`, `../wt-astra-p9*`, `../wt-philo9-check-*`, `../wt-handover-31`.
