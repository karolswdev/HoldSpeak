# Handover — 2026-07-03 (afternoon) — the two-track day

One session, two tracks, owner-steered turn by turn: **Phase 18 (mobile,
Equilibrium's lead) went 2/7 → 6/7 with the gate staged**, and **Phase 79
(Backend Decomposition II) was opened, built, closed, and merged same-day.**
Nine PRs merged (#215–#222, plus #220).
This is the map: what shipped, what the owner decided, what remains, the traps.

## Where main stands

- **Merged today:** #215 (HSM-18-07 rider), #216 (HSM-18-01 teleprompter),
  #217 (HSM-18-05 nudges), #218 (HSM-18-02 CommandsBoard), #219 (HSM-18-03+04),
  #220 (18-06 docs half + the walk), #221 (the dictation classify fix).
- **#222 — Phase 79 CLOSED 6/6 — MERGED** on conclusion-checked green minutes
  after this handover was first written. Nine PRs merged total; main carries
  everything.
- **Suites at last full run:** 3,113 passed / 37 skipped
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`), web 17 pages,
  `swift test` 425. One recorded flake candidate:
  `test_replay_after_target_correction_changes_routing` (failed once in a
  combined run; green in isolation and on re-run).

## Track 1 — Phase 18, the iPad joins the dictation contracts (6/7)

| Story | PR | The one line |
|---|---|---|
| 18-07 rider | #215 | `origin` explicit on every artifact surface; run-born artifacts land on the iPad desk with the arrival beat; `HubRunResult.artifactId` kills a duplicate-on-sync bug |
| 18-01 | #216 | The voice teleprompter: readiness strip + opt-in "Preview first" receipt; hub `raw: true` = verbatim delivery (fixed a double-rewrite — the receipt used to lie) |
| 18-05 | #217 | Nudge cards + "Dictate with this" → Armed; the remote lane now consumes the Phase-53 selection pin |
| 18-02 | #218 | The CommandsBoard: author macros from the iPad (mic on every field, "runs code on your Mac" mark, per-card Test) |
| 18-03 + 18-04 | #219 | The ONE language resolver at all three WhisperKit sites; the user spoken-symbol dictionary + Settings editor |
| 18-06 (docs half) | #220 | Entry points current (README/ARCHITECTURE); the walk staged |
| classify fix | #221 | `.43` verified as the rewriter: the schema hint taught the nested extras shape and honest no-match was rejected — both hub bugs, fixed; live 0/5 → 5/5 |

**The audit's pattern confirmed 3×:** every dictation feature built on the
local path shipped silently broken on the remote lane (18-02 macros, 18-01
receipt, 18-05 pin). Standing rule: touching dictation means checking BOTH
lanes.

**What closes the phase:** the owner's device walk.
[`HSM-18-06-WALK.md`](../holdspeak-mobile/phase-18-ipad-dictation-contracts/HSM-18-06-WALK.md)
is press-play: point `dictation.runtime` at `.43`
(`http://192.168.1.43:8080/v1`, model `Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf`,
keep `~/run-qwythos-vision.sh` active — `run-qwythos-intel.sh` pins a `{"line"}`
grammar that breaks the classify), five checks W1–W5 with controls, fill the
trace. PASS×5 closes HSM-18-06 and the phase.

## Track 2 — Phase 79, Backend Decomposition II (CLOSED 6/6)

The Phase-63 discipline on today's three worst monoliths (survey corrected the
desk-era handover: `routes/meetings.py` was already split by Phase 72):
`db/activity.py` 1,596 → six concern mixins; `routes/system.py` 1,299 → five
routers + `_shared` (`settings.py` 701 on a named 800 budget);
`routes/primitives.py` 1,294 → seven family routers + `_shared`. Zero code-body
drift (programmatically checked per story), tests unmodified, zero
patch-target edits, manifest diffs module-fields-only, guard extended and
red-proven. New named watch item: `db/core.py`. Ledger:
[`final-summary.md`](./phase-79-backend-decomposition-ii/final-summary.md).

## Owner decisions today (standing)

1. **iPad parity before Lock-the-Walks/Agent-Sync/release** — Phase 18 resumed
   as authored + the Desk-Era rider (HSM-18-07).
2. **The backend decomp** picked over Phase 19 / Lock the Walks when the
   device walk was postponed.
3. **`.43` is the rewriter** for the 18-06 walk (verified end-to-end after the
   hub-side classify fixes).

## Outstanding — the owner's hands

- **The 18-06 walk** (above) — closes Phase 18.
- Still open from the desk-era handover: the **desk feel pass**, the
  **Phase-72 iPad walk** items, and the **release cut** (CHANGELOG
  `[Unreleased]` has grown again today: artifact `origin`, `raw` delivery,
  the remote-grounding fix, the classify fix).

## Outstanding — buildable headless (ranked)

1. **Phase 19 — the iPad joins the meeting contracts** (Equilibrium's designed
   pair to 18; the client layer already landed in Wave 3 — it is screens over
   shipped clients, the exact shape of today's run; its metal gate can join
   the 18-06 couch session).
2. **Lock the Walks** (desktop; still the desk-era handover's standing offer).
3. Equilibrium 21 (honest everywhere) / 23 (mesh-safe storage) — independent.
4. Watch items: `db/core.py` (guard-named), the flake candidate above.

## Traps (each cost real time today)

- **The remote-lane rule** (above) — three real bugs from one blind spot.
- **Carve mechanics:** lazy in-body relative imports gain a dot at EVERY
  level, including one-dot siblings; retarget with `(?m)^([ \t]+)from ...` —
  never `^(\s+)` (`\s` eats newlines and over-rotates column-0 imports).
  Heredoc generators: `\n` in generated string literals must be `\\n`.
  Tests import module-level public names from old paths — re-export from the
  package root. The PMO hook wants a literal `evidence-story-NN.md` per flip.
- **Simulator persisted defaults beat launch env** (`hs.peer.*`): uninstall
  the app before a live-hub run or the peer looks asleep.
- **`gh pr checks --watch` exits when ONE workflow finishes** — with two
  workflows, watch twice, then conclusion-check. Never chain a merge.
- **When a read model gains a field, sweep test FAKES in unit AND integration
  suites** (`SimpleNamespace` artifacts bit twice).
- **In-process `llama_cpp` segfaults** (exit 139) on the local Qwen3-4B GGUF;
  the sandbox blocks LAN (probe with it disabled); `gen_api_surface.py` and
  the gen-*.rb scripts are cwd-sensitive.
- **Proof hubs:** scratch DB + `hsdb.get_database` monkeypatch + in-process
  `Config.load` patch (never the owner's real config; redirect
  `hscfg.CONFIG_DIR/CONFIG_FILE` before any settings PUT); mtime-verify.

## Where things live

- Phase 18 evidence + screenshots + the walk:
  `pm/roadmap/holdspeak-mobile/phase-18-ipad-dictation-contracts/`.
- Phase 79: `pm/roadmap/holdspeak/phase-79-backend-decomposition-ii/` (per-story
  evidence quantifies every carve).
- Memory (Claude's): `project_equilibrium_program.md` carries the Phase-18 run
  + the classify/.43 findings; `project_phase79_backend_decomp_ii.md` carries
  the carve playbook.
