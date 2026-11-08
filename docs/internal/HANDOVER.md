# Handover (2026-11-08 morning, one brain)

This is the ONE handover. It replaces every numbered handover before it (the owner, 2026-11-07: "kill all the previous handovers… default the latest one to just handover.md"). Rewrite it in place at each handover; history is in git.

Read first, in order: `CLAUDE.md` "How we work now" (the seven lines of 2026-11-07), this file, `pm/STATUS.md` (one line per merge), `docs/walks.md`. Two Brains is retired; nothing in `docs/internal/TWO-BRAINS.md` is current process.

## Part 0: how we think (the mentality, written down)

- **Move fast, with three checks and no ceremony.** A change is one concern, a few files, a worker in a worktree, a PR within the hour. A test that fails on main, one quick check per merge batch, his desk on main. Nothing else gates. A red is fixed forward at once, never debated; a revert is for security or data loss only.
- **One brain decides; workers build.** No mutual checks, no counsel rounds, no planning packages, no completion reports, no status paragraphs. A brief is the step text: the job, the settled decision, the owned files, the focused tests. The owner makes a ruling in one sentence; we do not ask twice.
- **The owner judges faces live, hand-held.** Every wave ends with a walk link. His answers, with the screen he saw, are the ruling and seed the next slices. When he says "apply my feedback", the orchestrator settles the design in the brief and builds at once; the canvas is for a face he rejected twice without a direction.
- **Subtract.** Every change removes a seam or a second implementation; it never adds one. Two implementations of one thing are a defect by definition. Measure the subtraction (`scripts/measure.py`) in the PR.
- **Effortless and powerful, native, delightful.** The desk is strong; the glue and the core workflows are not. Pick work by core workflow, not by finding: walk the workflow read-only first (Create a Program → it runs → it waits on you → you decide → it merges → the Room shows it), list the seams, build each seam as one lane.
- **Truth over comfort.** Say what failed, with the output. Say what was skipped. A flake is proven by a rerun, not assumed.
- **Diagnose before you theorize.** `kill -USR1` the hub and read the stack; read the failing assertion before guessing the cause. Never "prove" a tailnet name dead with `host`: the Mac's resolver lies, Tailscale's answers.
- **Never touch his real state.** Tests never see his HOME, DB or Keychain. Park, don't delete.

## Part I: the rulings (owner, verbatim where it matters)

1. **One brain, one loop, three checks** (2026-11-07). Muad'Dib decides; Opus 5.5 `opus-worker`s build in sibling worktrees (`/Users/karol/dev/tools/wt-*`, `uv sync --extra dev` only) and open PRs; the orchestrator merges (`gh pr merge --squash --delete-branch`; a `pm/STATUS.md` conflict keeps both lines), runs `scripts/quick_check.sh <last checked head>` once per batch on main, the browser files the batch touched under `scripts/test_lock.py`, fixes a red forward, redeploys his hub. Codex is one bounded reviewer after a merge that touches a security surface (`scripts/astra check <brief.md> --tag <t> --effort high`; #1830 → 5 findings → #1834; #1855 → 2 findings → #1868).
2. **No dogfooding our development through HoldSpeak Programs** ("massive waste of time"). The engine defects that night exposed were fixed in #1858/#1861.
3. **Plans are Programs or briefs, never documents.** `docs/internal/holdspeak-execution-plan/` is reference; its gates are ruled in its `DECISIONS.md`. Of wave 3: S25 #1829, S32 #1855, S12 #1859 merged. Consolidation: S53 #1828, S51 #1845/#1864, the bootstrap move #1849/#1853/#1866/#1867/#1900/#1915 merged; S24 disclosure-only still open.
4. **The direction:** "an effortless system, a powerful system at the same time… not gluing everything together properly… nail the core workflows… not an overcomplicated architecture with multiple implementations of the same thing."
5. **Automate feedback: The Walk.** Every wave ends with a walk link. **The link is the Tailscale Serve name over https**, `https://karols-macbook-pro.tailad9943.ts.net/w/<token>` (his ruling 2026-11-08 02:xx: "Need the tailscale dns. Not the ip"), then `http://127.0.0.1:8765/w/<token>`, each in its own code block. `scripts/walk.py` prints both since #1840 (`HOLDSPEAK_TAILNET` overrides). The IP version (#1827) was wrong: the Mac's `host` returns NXDOMAIN for the tailnet name while Tailscale's resolver answers; the phone needs https for the clipboard and the mic.
6. **The walks of 2026-11-08.** First (00:xx): Programs' New program "I expected… some kind of a wizard"; Needs you "way too cluttered… 'more' doesn't even look like a button… the 'Done', the 'Yours'"; the Room's Programs fold "not even a mention of 'programs'". Then "apply my feedback, I was serious about it looking like shit and not being glued together like shit". Second (02:xx): wizard Keep, Needs you Keep ("right window opened" after #1841), then "still uses the super unprofessional what where how and why" → #1843. Picks: **W2** (the object leads) for the wizard, **S3** (the bar) for the ask sheet; he wrote "W3" on the second line, I read it as S3 and said so; he did not correct it.
7. **"You're on the hook, bud. I'm going to sleep. Keep orchestrating and delivering all the way up until 10 AM."** (00:50). Done; Part II.
8. **Still open from him:** the Room's direction on the canvas https://claude.ai/artifact/YGKJLiQZdz8n6xCnGmT9U1 (R1 the brief, R2 the project's desk with a sidebar, R3 the ledger); my recommendation is R1. Programs well: "yes but expected a bigger jump" (2026-11-07 late) is not answered yet by a design; the window as one object is the next canvas if he says so again.

## Part II: what landed in the night of 2026-11-08 (main bb138505b → 622a719f9, #1839–#1919, 78 merges)

Grouped by concern, newest first within a group. Every line is in `pm/STATUS.md`.

**The walk and the feedback loop.** #1840 tailnet https name; #1841 a part's window comes to the front before it is marked; #1842 16 px fields on a touch phone (iOS zoom cropped the shots); #1863 `viewport-fit=cover`; #1848 the ask is one toolbar bar above the dock (S3); #1856 one kit `ProgressDots` for the walk and the wizard; #1895 the morning walk `docs/walks/2026-11-08-morning.json`.

**Programs: New program (W2).** #1843 no step words; #1844 the picked project is a card on every screen, the title bar names it and holds the dots; #1847 the phone-head rule lives in the frame; #1852 the frame's close is Cancel, screen 3 fits the phone; #1899 a Person row under Review writes `for_person_id`; #1898 the Drafting tray shows one thing from the plan row; #1878 **Create plans itself**: a goal is planned on the next tick, a Runs-by-itself Program starts with no press.

**Needs you: the row is the object.** #1854 a Program row is the Program, its quiet ask word and one verb (Merge, Decide, Open); Later and Send on the context menu; one rule in `needsFace.ts`; #1876 Decide opens the choices in place; #1882/#1883 one Run as a program (the agent session stays "Hand to an agent session", #1884/#1886 one name at 21 sites); #1885 one Done (`markDone` in `needsApi.ts`; follow-through complete and People's transition answer one receipt).

**One decision, one face, one writer.** #1877 one decision writer (`DecisionRecordService.create` files the record in its Project and names its Person); #1891 a decision with an owner Person and a Project commits once in the writer and is that Person's row; #1889 a meeting's Decide well row opens the record reader; #1897 "Committed · <name>"; #1906 **one face per decision**: every ref opens the Decisions window reader (Edit, Retire, Copy); the Decision pullout is parked in `web/src/desk/pullouts/_parked/`; #1907 a Desk decision's second edit reaches its record (sync revisions are not hand edits); fixes forward #1892 #1893 #1909 #1912 #1914 #1916 #1918.

**The Room.** #1832 the Programs fold always shows; #1873 the Room is a composition (`features/project-room/core/`, 12 files, `ProjectRoomCore.tsx` 2,591 → 488); #1890 a merged step leaves its receipt on the Program's origin (a note's PR line in its Room, a decision record's PR link); #1917 **the Room always opens on Now**; a kept draft waits on the head as "Update draft · <time>" with Continue (his 2026-11-07 "opened in its update posture: UX absolutely sucks"); #1913 `docs/PROJECT_ROOMS.md` describes the Room as it is; #1919 the Room glass case follows.

**Engine.** #1855 HS-S32 delivery recovery (Check, guarded Merge, stage-aware Retry, Skip, bound to the delivery line; #1868 Codex fixes: 40-hex head, PR URL and ref validation, no exception text); #1858 an agent never plans into a running Program, a hand that wrote nothing goes back once then parks, duplicate steps fold; #1861 the night backlog read adds again; #1859 HS-S12 one startup intent.

**Subtractions (measured).** #1845/#1864 `program_definitions.py` (program_service 5,670 → 5,406, importers 28 → 27); #1904 `program_reads.py` (63 reads; program_service → 4,370); #1894 `project_definitions.py`; #1902 `project_room_reads.py` (project_service 5,994 → 3,404); #1849/#1853 `runtime/composition.py` + `hub_composition.py` + `delivery_composition.py`; #1866/#1867 each shared adapter built once; #1900 `runtime/web_mount.py` (935 routes, fenced by a recorded list); #1915 `runtime/background.py` (web_server.py 2,500 → 1,456 lines); #1870/#1871/#1872 Settings is a composition (`pages/cores/settings/`, SettingsCore 2,900 → 272); #1903 the Programs app tests split by face; #1905/#1908 the desk chunk 2,417 → 1,537 KiB raw (CodeMirror, the Program window, the note window and the Room load lazily); #1865/#1862 A8 (no counter of zero) 26 → 0, A1 81 → 2; #1896/#1881/#1879 the API surface tags a web route only on a path and method match.

**Keystore.** #1830/#1834 one master key, one AES-GCM file; the owner allowed the one Keychain dialog at the migration; `/api/setup/status` answered in 0.6 s after.

**Tooling.** #1846/#1901 `scripts/measure.py` (merges per day, presses per night, first commit to merge, PR open to merge, bundle, cold start, code shape, seams in `scripts/measure_seams.json`); #1851 fold-grammar fence; #1887 `gen_docs.sh` runs to the end; #1910 the user docs follow the night.

Quick check: green on every batch head after a fix forward; the reds were all stale fences or tests encoding the old rule (atlas citations after moves, graph join paths, API surface drift, density budget, lamp words, pullout-era vitest/browser cases, the Room return rule). No red was a face defect. The Engines sweep stillness red is a flake (passed twice).

## Part III: the hub, as it stands

- Served checkout `/Users/karol/dev/tools/wt-desk-main-20261025`, detached on main; venv Python 3.13. Redeploy: `git fetch && git checkout --detach <sha> && uv sync --python 3.13 --extra dev --extra line && (cd web && npm ci && npm run build)`; `P=$(pgrep -f "holdspeak.cli_entry web --no-open"); kill $P; while kill -0 $P; do sleep 1; done`; start `HOME=/Users/karol HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open >> ~/.local/state/holdspeak/hub-main-20261107.log 2>&1 &`. Never run `quick_check.sh` in the served checkout; run it in `/Users/karol/dev/tools/HoldSpeak`, and never pull or branch there while a check runs (it ran on a moving tree once). Side fixes go in `/Users/karol/dev/tools/wt-viewport`.
- Tailscale Serve fronts 8765 as `https://karols-macbook-pro.tailad9943.ts.net`.
- The keystore migration ran on his hub (2026-11-08 ~01:00); secrets read; Telegram answered. The `security -i` add has still not been exercised against a Keychain that refuses.
- His Programs from the dogfood attempt are PARKED (5); leave them.

## Part IV: open, in the order I would run it

0. **His morning verdict.** The morning walk (`scripts/walk.py new docs/walks/2026-11-08-morning.json`) asks about the wizard, the Needs you rows, the Programs fold and the Decide project row; read with `scripts/walk.py read <id>` (shots in `~/.local/share/holdspeak/feedback/walks/<id>/`). His Room pick on the canvas (R1/R2/R3). One sentence from him is a ruling; build it the same day.
1. **The Programs window as one object** ("expected a bigger jump"): a canvas of three directions if he repeats it, else a brief from W2's grammar (the object leads, the window is the Program).
2. **Follow-ups the builders named:** the Note face does not yet show "Merged · PR #n" (the data is on the Room link, #1890); the review ask's person→destination link is name-matched (#1878); HS-S21 is kept over the merge-to-origin brief for actions (#1890); old sync revisions stay frozen (#1907); the API surface's method matching leaves ~60 routes to check by hand; `AgentWords` still carries Lezer (69 KiB) in the desk chunk.
3. **Subtract next:** `schema.py` 5,436 lines, `project_update_service.py` 4,050, `intel.py` 3,492; `WorkbenchWindow.tsx` 2,062, `NeedsDrawer.tsx` 1,580 (its one-row grammar is done; the drawer's three postures are not one component yet); S24 disclosure-only.
4. **Core workflow walk two:** a Person's week (1:1 → commitment → Needs you → the Room's People fold → the update) read-only first, seams as lanes, as the Program workflow was done this night.
5. Test lock: a worker reported `test_lock.py` exits 0 after a red pytest under `env …` (unverified).

Measure (rule 7): 2026-11-07 50 merges; 2026-11-08 by 07:00 78 merges (#1839–#1919) plus the 12 before midnight; his presses: 2 walks, 7 answers; finding → main 10 min to 3 h (median under an hour). Run `uv run python scripts/measure.py` each night; the day file is `docs/internal/measure/2026-11-08.md` (the night's run appends on top of the 05:21 baseline).
