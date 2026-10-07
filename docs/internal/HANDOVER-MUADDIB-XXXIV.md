# Handover — Muad'Dib XXXIV (2026-10-07)

Read first, in order: `CLAUDE.md`, `pm/STATUS.md`, `docs/internal/philo/phase-14/PROPOSAL.md`, `docs/internal/philo/phase-15/PROPOSAL.md`, this file. Memory index: `MEMORY.md` (see `project_philo14_desk_is_objects.md`, `feedback_desk_is_objects_not_apps.md`, `feedback_full_autonomy_phase14.md`, `feedback_astra_brief_bounded_scope.md`).

## What happened this session (2026-10-07, one day)

The owner opened with three catches of one diagnosis: the Conductor's face "ABSOLUTELY STINKS"; the Desk had drifted from "Workbench 2.0+ on steroids" into "Windows 1.0 territory"; the features had become "just kind of ... apps", the explorer "still with `[ ]` in the copy". Then he handed me the calls: "you make ALL the calls, including the icon selection", and "once you have already moved this mountain, that we move another one, of your choosing".

**PHILO Phase 14, The Desk Is Objects**, chartered, canvassed, built and closed in the day. Twenty product and docs PRs merged on main:

| Movement | PRs | What the owner can now do |
|---|---|---|
| Charter + canvas | #924, #927 | One page, three alternatives, 45 shots; RULED A Workbench + C's station track (artifact https://claude.ai/artifact/E7E4JwVzSD9ieY6hpDQFjY) |
| A objects | #934 A0b, #956 A0c, #939 A1, #951 A1b, #959 A1d, #954 A1c, #937 A2, #945 A2b, #935 A5 | The Chair is a SCREEN of objects, not tiles: drawers with the Room's own count, loose objects, agents, the Conductor drawer, Needs you, Parked; windows float and remember; a Project opens as a DRAWER (icons or a real list, Get Info, Park, the Room one press away); Needs you is a smart drawer, one object one row, every ask folded into its item, no Approve on a cut command anywhere; D1 "Workbench+" icons at 64 and a true 32 px set, one kind one silhouette, Codex keeps its face on every face; the summary card opens Capture and sits in its slot |
| B material | #932 B1, #958 B2 | The object species in `web/src/desk/surface/objects/` (DeskIcon, IconLamp, IconGrid, ObjectList, GetInfo, TimelineRail, StationTrack, AskWell, PRCard, FilesChanged, ConfirmLine, NeedsRow, DropTarget); the bevel grammar; plated Buttons raised again, chips are lamps with a word, filters lightly raised (canon D amended), one sunken well per window |
| C the Conductor as objects | #925 C0, #953 C0b, #933 C2, #941 C2b, #946 C3, #947 C4 | The hub keeps the agent's timeline (spooled by the hook, drained on reads AND on a 2 s hub timer); a launched agent's face is its LANE (station track, the question with voice answer, the rail, PR card, Deny/Approve, Re-brief, Stop, Raw); drag an object onto the Conductor or an agent to HAND it (ConfirmLine in YOLO, HandSheet otherwise); the Agents application folded into the Conductor drawer (Dock ⌘3) |

Built shots beside the boards: artifact https://claude.ai/artifact/FgdD7jmm9YXv3Y7xcBf8hf ("Phase 14 Built"). Status entries with every Astra condition and owner: `pm/STATUS.md` "Current phase".

## Owner rulings this session (binding)

- **Full autonomy for the phase:** Muad'Dib ratifies canvases, picks icons, rules defaults; no owner gates or questionnaires; shots in PRs are the record.
- **The next mountain is Muad'Dib's choice**, "to PERFECT the experience with HoldSpeak". Chosen: PHILO Phase 15, The First Day (§Next).
- Carried in unchanged: one Astra round per PR (max 2 iterations), FAST before every merge, one FAST at a time, never delete, build what was ratified.

## Rulings I made under the grant (recorded in the PRs and STATUS)

- A Workbench + C's station track; D1 Workbench+ icons.
- One object one row; the most urgent ask on the row, `+N MORE`; every ask folds into its item whatever its mute or wait.
- No Approve on a cut command on any surface (Deny + Open/Raw); the hook sends the 120-char head and the REDACTED length only.
- The drawer is the Project's face, the Room its intelligence, one press away; explicit Room verbs stay; a proposal row opens the Room with that proposal selected.
- One press selects, Enter or a double press opens. Desktop TALK one press at the screen's foot-left. Phone Needs you / Brief / The week are Go's first rows.
- Windows: saved positions restored; unsaved placed by the canvas rule or cascaded. No age-based filing.
- YOLO hand = ConfirmLine; Secure/Normal = HandSheet. Stop is two presses and ends the session.
- A landed summary opens Capture at both widths; the card sits in Capture's slot; an arranged Capture keeps its geometry and scrolls.
- UX-CANON D: filters are lightly raised tokens, wings keep the full Steel bevel, never alike.
- An answer must name the current `wait_id` (409 `wait_not_current`).

## Lessons (scars)

- **Bound every Astra brief.** My #951 brief said "run every atlas case": she walked 130 of 176 for the whole 60-minute cap and wrote no report. Her data survived in `events.jsonl` and her `/tmp` work dir; I mined it. Law: at most ~10 named cases, or "a sample you pick"; sweeps are a worker's job, Astra judges the table (`feedback_astra_brief_bounded_scope.md`).
- **A shot found what tests did not, twice.** The Codex agent wore Claude Code's robot on the screen, the lane title, the drawer's members and the hand confirm line (`row.agent` dropped at each site); a long-red glass test (`test_philo14_a0b_codex_sprite_glass.py`) was that defect, not a stale test. Never dismiss a red glass as stale without the diagnosis.
- **A test that races the paint lies about the face.** The 393 "missing icons" were a screenshot taken before the sprites decoded; `_images_loaded` in `tests/e2e/glass_infra.py` now waits. Read the PNG before believing the claim either way.
- **Merging a lane that rewrites a face breaks its neighbours' tests on main.** A5 replaced the Chair's Needs-you section; nine glass tests and three vitests went red on main within the hour, found by other lanes. After a face-replacing merge, run the neighbours' glass on main at once (lane A5b pays it).
- **The null-read guard caught a `document.querySelector` in product code (A1c r2)** and the fix was React state, not an exemption. Its regex misses `querySelector<T>(`; widen it in a hygiene lane.
- **`gh pr merge` says UNKNOWN right after main moves**; wait 8 s and retry. CONFLICTING means merge main in the lane worktree, resolve, run the touched suites, push, then merge. A fresh worktree needs `npm ci`. `npx vitest` must run from `web/`.
- **Under load 80+ the same families flake**: the real-hub kernel test, the philo11 document rig fixture, `ComponentsPage` a11y, park bulk-restore. Rerun alone before calling a red real.
- **Workers' shots that live only in `.tmp/evidence-shots/` vanish with the worktree.** Commit the PR's shots under `docs/internal/philo/phase-14/<lane>-shots/` (the later lanes did).
- **Hand-off tmux session names** must stay ≤59 chars (A2b): 40 of the slug + an 8-hex hash + the suffix.

## Open (also in `pm/STATUS.md`, per PR)

- A5b (in flight at writing): the post-A5 Needs paths; 3 vitests and 9 glass tests red on main since #935.
- The atlas: 28 non-aftercare cases still click `arrival-blocker-verb-*`; rig gaps (`route_failure` and `browser_audio_device` substitutions unimplemented); j9 provider-reply seam; the phase-3 engine-setup path; the fresh-HOME brief always carries "No engine for summaries"; WAV import on an isolated HOME needs `HF_HOME` at the real Whisper cache + `HF_HUB_OFFLINE=1`; two Floor toast cases block on `.desk-hub-dot`.
- Spool: the committed-but-not-unlinked memory is process-local (a restart can replay); sessions HoldSpeak did not launch drain only on reads; `drain_spool` swallows SQLite insert errors silently.
- Faces: window title icons (20 px) scale the 64; kb/roadmap wear `artifact`, story `note`, capability kinds `cartridge`; the old `desk-chip` family and the Settings `gadget-chip` are still flat chips; the raised bevel is subtle at 1x; the lightened Dock glyphs unchecked on a dark Dock; the 393 seventh Needs row sits under the Dock (scroll reach unverified).
- Leftover worktrees `wt-conductor-*` inside the checkout from XXXIII: park or remove when idle; never delete branches.
- Still waiting on the owner's go: the "open by default" OSS pass (XXXIII).

## Next (chartered: PHILO Phase 15, The First Day)

`docs/internal/philo/phase-15/PROPOSAL.md` (#964). The owner has never used HoldSpeak once; the last handover's own next step was one real Conductor action on his desk. Phase 15 builds no new face: it rehearses his first real day end to end on real metal with ISOLATED credentials, at both widths, every bounce paid in a lane the same day, then the second morning, then `DAY-ONE.md` as the runbook he follows (and a canvas page for the phone). Lane 00, the Day One inventory, is running at writing.
