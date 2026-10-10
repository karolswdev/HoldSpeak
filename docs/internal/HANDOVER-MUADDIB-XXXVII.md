# Handover — Muad'Dib XXXVII (2026-10-10)

Read first, in order: `CLAUDE.md`, this file, `pm/STATUS.md` (the Phase 16 paragraph is the ledger), `docs/internal/philo/phase-16/COMPOSITOR.md` (the window grammar, §1–§13), `docs/internal/HANDOVER-MUADDIB-XXXVI.md` Part II (the test doctrine; it held). Memory index: `MEMORY.md` (`project_phase16_compositor`).

## Part I: what landed

PHILO Phase 16, THE COMPOSITOR, chartered 2026-10-09 from the owner's bounce ("too sterile … zero concept of a compositor … zero regard to delighting the user") and his word ("Orchestrate away. Approval granted."). Fourteen PRs in two days.

| PR | Lane | What |
|---|---|---|
| #1030 | canvas | `COMPOSITOR.md` §1–§13 + `01-canvas/compositor.html` (artifact WBa6SK1fx2RqX9prBf45Do, v3): the light, the depth ladder, title bar B + icon/sans/lamp, the interior joins the material, the interior kit (§11), the composition doctrine for internal apps (§12), ten software-design lessons from PhreshOS/system (§13). Owner-ratified; the Needs-you fold on the canvas was later RETRACTED (HS-200-15/B11 outrank a canvas). |
| #1032 | A1 | the material and the chrome: tokens (the light; HS-110-01 amended: light returns, glass stays dead), `window-interior.css` (one remap moves every face), the ladder by `data-plane`, the title bar, the backdrop floor (Quiet Desk default), dock seats for every window (nub chips parked) |
| #1034 | A2 | the compositor core: `web/src/desk/compositor/` (layers as a type; planes from a depth counter; share+px geometry; timing; shared-resize; anticipate; departure), `panelDepth` replaces `panelOrder`, nine verbs + keys, Exposé as live windows, the derived divider |
| #1035 | A3 | the interior kit (eight species in the library + contract) and four faces swept (Needs you, Room, Conductor, meeting) |
| #1036 | C | Runs on: the Models app as a Switchboard (drag to patch with CAS + revision-bound Undo; Try it REACHED/READY/HEARD/NOT CHECKED; FOUND + Use it; downloads in place; the Concierge, pickers, Adjust, the assignment sheet parked) |
| #1039 #1047 #1051 | R, R2, R3 | the inherited reds on main at their causes (a reduced-motion 0.01 ms transition; three 393 fences; the quiet-hours fences; a first-use "flake" that was a viewport check; thirteen more incl. the thought foot wrap) |
| #1041 | C2 | a task handed back after a Runs on patch comes to the front |
| #1044 | C-atlas | 24 Concierge atlas cases ported to Runs on; the rig reaches no real engine; the read-only live walk |
| #1049 | RIG | the rig never reads or writes the owner's state (agent config paths, active window, notifications, channel keys, gh config, git system config; replyless boundaries refused before boot) |
| #1046 | B | window authority to the hub: `desk_window_service.py`, `/api/desk/windows`, MCP `desk_window_*`, `hubWindows.ts` (the browser as a presentation); two browsers = one desk |

Status entries: #1031 #1033 #1037 #1038 #1040 #1042 #1043 #1045 #1048 #1050 #1052 #1053.

### Open (STATUS has every residual)

- Lane 16a-R4 (running at handover): the two People reds on main (prep glass seed 503; people_preparation reads `ready` for an unreadable key): likely #1049's glass keystore env.
- `test_finish_face_polish` flaky under load ("config version" `.first` hidden); a Setup readiness row cuts its detail at 1440.
- 16b backlog: `defaultGeometry` as shares in the registry; a lane opened only through a steering session is not synced; the owner's first press after a remote change ends the quiet period; a 393 sheet that unmounts without closing is not sent as closed; view-local families (inspectors, editors, delivery-*, trust, session, schedule, attention, ask, intelligence:desk); not verified on a real iPad.
- Runs on backlog: a per-object wire on the board (per-subject overrides parked); route-probe adapters per capability; FOUND shows addresses only; a phone cannot make an inherited engine a job's own wire; `test_hs201_09` still talks to the real LAN engine.
- Atlas: `record_only.no_speech_head` blocks on `browser_audio_device`; other cases observe at `arrival-blocker` (stale since PHILO-14 A5); every other WAV-importing case still loads real Whisper; the live walk's roster fingerprint omits existing capability assignments' engines/revisions.
- Faces: the meeting's old wells (summary/send/decide/transcript, MD/SRT/Park, list chrome) stay beside the kit; "No engine for summaries" status line atop the Meetings window; HOOKS UNKNOWN token on the Agents card went in without a canvas (rig-only); the 393 kit-verb fence measures height/halo, not pointer ownership.
- Not run on a real iPad; the owner has not yet used the new desk.

## Part II: what the doctrine taught in two days

1. **Astra round 1 is never a RATIFY.** Every lane came back DO-NOT-RATIFY with 4–8 MUSTs, two of them SECURITY (C: a pending Try-on-host consent re-resolved the engine at confirm, then compared no host). Round 2 cleared most; 16b needed a third correctness round. Budget two rounds and the orchestrator's own read of what remains.
2. **The orchestrator's run finds what the lane's budget cannot.** Every lane's scoped glass (32–65 files) found 4–21 reds the lane's one-file budget missed; 16b needed the WHOLE browser suite (three runs: 45 → 22 → 4) because "one hub is one desk" changed every multi-page rig. When a change touches every window, run the whole suite, not the scoped set.
3. **Quiet hours (22–08) turn fences red at night.** Attention, preparation brief, recipe catalog: each counted a quiet source as stale. Fences compute expected the producer's way, or seed past the quiet window (20 h+).
4. **A "flake" is a fence reading the wrong thing.** The first-use record-refresh was a viewport check on a 393 result below the fold; the palette contrast was a reduced-motion `transition-duration: 0.01ms !important` read mid-transition. Three runs through the lock before calling anything flaky.
5. **The rig reads the owner's machine unless told not to.** EventKit, the agent config paths, the front window, the Notification Center, the Keychain: none honour HOME. Every rig hub now sets the four switches and the paths inside HOME (`_isolated_hub_env`, `glass_infra._boot`). A new read of machine state needs a switch, default on.
6. **Merge main into a lane the moment a sibling lands; the orchestrator says when.** Workers never rebase; the orchestrator instructs the merge and names the conflicts (the A1 stopgap line A2 had to delete; A3's contract.md section beside C's).
7. **A canvas detail can be wrong.** The Needs-you fold copied the old face; the owner's rulings (HS-200-15, B11) outranked it. Workers must flag a canvas detail that breaks a ruling; the orchestrator retracts it.
8. **The lock serialises; the budget keeps it short.** 16b held the lock ~40 min for a full-suite run while four lanes queued. Whole-suite runs are the orchestrator's and should be scheduled when no lane is waiting on a budget run.
9. **Rate limits kill agents mid-commit.** Both lanes alive at the limit left uncommitted work in their worktrees; SendMessage resumed them with the state named. Check `git status` in every lane worktree before resuming.

## Next

1. R4 lands → merge; then the owner's real day on the new desk (Mac + iPad: the same desk) is the next inventory. Every bounce = Phase 17's rows.
2. Phase 17 is not chartered; name it from his first day on the compositor, not from the backlog above.
