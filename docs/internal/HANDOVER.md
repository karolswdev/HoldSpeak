# Handover (2026-11-08 afternoon, one brain)

This is the ONE handover. It replaces every numbered handover before it (the owner, 2026-11-07: "kill all the previous handovers… default the latest one to just handover.md"). Rewrite it in place at each handover; history is in git.

Read first, in order: `CLAUDE.md` "How we work now" (the seven lines of 2026-11-07), this file, `pm/STATUS.md` (one line per merge), `docs/internal/UX-CANON.md` ("The language, 2026-11-08"), `docs/walks.md`. Two Brains is retired; Codex is one bounded reviewer after a merge that touches a security surface.

## Part 0: how we think (the mentality, written down)

- **Move fast, with three checks and no ceremony.** A change is one concern, a few files, a worker in a worktree, a PR within the hour. A test that fails on main, one quick check per merge batch, his desk on main. Nothing else gates. A red is fixed forward at once, never debated; a revert is for security or data loss only.
- **One brain decides; workers build.** No mutual checks, no counsel rounds, no planning packages, no completion reports. A brief is the step text: the job, the settled decision, the owned files, the focused tests. The owner makes a ruling in one sentence; we do not ask twice.
- **The owner judges faces live, hand-held.** Every wave ends with a walk link. His answers, with the screen he saw, are the ruling and seed the next slices. A face he rejects twice gets a canvas of three directions; he picks by letter, or says "go with suggestions", and we build the same day.
- **Bold, modern, unique. Never bland, never generic.** His words 2026-11-08: "let's be even bolder… modern, but unique… extend our design system and philosophy where needed"; on the old palette "so bland"; on Space Grotesk "I fucking hate that font". Grey on grey is a defect. One language for every app (Part I.6).
- **Subtract.** Every change removes a seam or a second implementation; it never adds one. Measure it (`scripts/measure.py`) in the PR.
- **Pick work by core workflow, not by finding.** Walk the workflow read-only, list the seams, build each seam as one lane.
- **Truth over comfort.** Say what failed, with the output. Say what was skipped. A flake is proven by a rerun, not assumed; a red that passes alone is diagnosed, not shrugged at (today's "flake" was a Playwright wait that never waited).
- **Never touch his real state.** Tests never see his HOME, DB or Keychain. Park, don't delete.

## Part I: the rulings (owner, verbatim where it matters)

1. **One brain, one loop, three checks** (2026-11-07). Opus 5.5 `opus-worker`s build in sibling worktrees (`/Users/karol/dev/tools/wt-*`, `uv sync --extra dev` only) and open PRs; the orchestrator merges (a `pm/STATUS.md` conflict keeps both lines), runs `scripts/quick_check.sh <last green head>` once per batch on main plus the browser files the batch touched, fixes a red forward, redeploys his hub. Codex (`scripts/astra check <brief.md> --tag <t> --effort high`) reviews one security-surface merge per round: #1830 → #1834, #1855 → #1868, #1936 (observer) → DO-NOT-RATIFY → #1941.
2. **No dogfooding our development through HoldSpeak Programs.**
3. **Plans are Programs or briefs, never documents.** The execution plan (`docs/internal/holdspeak-execution-plan/`) is now BUILT: the 13 stories (S11 S12 S13 S21 S22 S23 S25 S32 S33 S41 S42 S43 S52) by 2026-11-08 morning; the consolidation and tail slices today: S14 #1930, S24 #1926 (disclosure only, by ruling), S31 #1929, S34 #1946, S35 #1935, S51 #1845/#1864, S53 #1828, S54 #1928, S55 #1933, S56 #1948, the bootstrap move (#1849 … #1915), the schema package #1927. What remains in the plan is acceptance designs (S91 S92 S93), not work.
4. **The direction:** "an effortless system, a powerful system at the same time… nail the core workflows… not an overcomplicated architecture with multiple implementations of the same thing."
5. **The Walk.** Every wave ends with a walk link: `https://karols-macbook-pro.tailad9943.ts.net/w/<token>` (Tailscale Serve, his ruling), then `http://127.0.0.1:8765/w/<token>`, each in its own code block. `scripts/walk.py new <file>` / `read <id>`.
6. **The language (2026-11-08, after two canvas rounds).** Round 1 (https://claude.ai/artifact/XmTRmoq3FDwdBjzDbDXpRk): "pushing us in the right direction. But let's be even bolder." Round 2 (https://claude.ai/artifact/AxbHCoShatgcXMSqxjEnxq): "Better. But what the fuck are those rectangles?" (placeholders → the desk's illustrated glyphs, never a coloured block); "Make the color scheme more refined, more contrast, don't make it so bland"; "I fucking hate that font [Space Grotesk]… the holdspeak copy top-left too"; then on Bricolage/Archivo/Schibsted "none of the fucking fonts. Try harder." Built (#1932): **Fraunces** (a soft serif) for every mast, section head and the wordmark; Inter body; JetBrains Mono for facts; ink text; six meaning colours (steel runs, **brass = waits on you, the only warm colour**, moss done, coral at risk, graphite parked, navy the desk); three material tiers; the **Mast** and the **Spine** kit patterns; the brass Button; four motion words. The face is on his desk now and the afternoon walk asks "Is this the face?". If he rejects Fraunces, the next pick is NOT a grotesk.
7. **"All apps."** Needs you, Programs and the Room rebuilt in the language (Part II). **"Write update" misleads** ("feels like a button that lets me write a note about the project, which is not what it does") → **Draft update** everywhere; the Update posture's mast says "<engine> drafts from the sources · you send" (#1937).
8. **Hands off 09:15–15:15:** "material improvement… UI/UX, architecture (simplification where feasible), and performance… our original slices." Delivered; Part II and Part V.

## Part II: what landed 2026-11-08 (two sessions)

**The night (00:50–07:10, #1839–#1921, 80 merges):** the walk fixed (tailnet https, window raise, 16 px fields, S3 ask bar, one dots pattern); New program wizard W2 (no step words, the project as a card, Person row, Create plans itself #1878); Needs you one-row grammar (#1854 #1876 #1882 #1885); one decision writer and one face (#1877 #1891 #1906 #1907); the Room opens on Now with the Continue row (#1917); HS-S32 delivery recovery (#1855/#1868), engine defects (#1858 #1861), HS-S12 (#1859); subtractions: program_definitions/program_reads (program_service 5,670 → 4,370), project_definitions/project_room_reads (project_service 5,994 → 3,404), runtime/composition + hub_composition + web_mount + background (web_server 2,500 → 1,456), Settings and Room compositions, desk chunk 2,417 → 1,537 KiB; keystore #1830/#1834; measure.py (#1846 #1901 #1921).

**The day (07:10–12:00, #1922–#1952, 31 merges):**

- **Faces.** #1922 a bare action item opens itself (the item reader). #1923 the Room's Now face R1. #1932 the language (kit). #1937 **the Room** in the language: mast with the state spine, Draft update, What changed as a pull-quote plate with Continue, What is open as object plates with spines, cadence in the status bar; Prepare a brief and the standing pages (Open · Risks · Changed) live in History. #1939 **the Programs window is the Program**: a 64 px rail of Program glyphs with state dots, the mast, the numbered step spine (steel done, brass waits, breathing while running), the current step as a raised plate with the brass verb, Earlier steps; one component hosts the window and the pullout; #1944 the hub's list carries `night {program_id, start, queued}` for the rail's night tile. #1945 **Needs you is the desk of today**: the lamp mast ("Sunday · 3 must fix", mono counts, Mine · People, Later, Muted toggle), the spine, the one thing that waits first as a raised plate with the brass verb, the ledger by weight (To do / Must fix / Should fix / Noted), 46 px rows with the desk's sprites; NeedsDrawer.tsx 1,599 → 403 lines (NeedVerbs, NeedRow, NeedsMast, FirstPlate, Ledger).
- **Architecture.** #1927 `holdspeak/db/schema.py` (5,436 lines) → `holdspeak/db/schema/` (17 modules ≤474 lines; SCHEMA_SQL byte-identical, fenced). #1928 one home for the time/id helpers (51 copies → 0). #1933 the project-update source policy in one module (project_update_service 4,050 → 3,898; engine_tool_loop 537 → 309). #1930 HS-S14 one keyed Program read (two windows, one request; a stale-load race closed). #1946 HS-S34 the Thread turn lifecycle (`services/thread_turns.py`): three real defects fixed (cancel after save was reported as a stop; a raising terminal frame leaked the turn; a late answer reached a detached Ask). #1948 HS-S56 retirements (a shim module, a deprecated function, a duplicate definition, 67 unused names; parked, never deleted). #1952 one writer of /api/settings (the You fields went through their own PUT with their own revision: Language did not save after an alias save).
- **Performance.** #1936 desk open 674 → 303 ms (React's Suspense held the desk 300 ms after its chunk arrived; the Desk is preloaded), meeting-name formatters cached (99 ms of main thread per open), roadmaps served stale-while-rebuilding (a 2 s wait every 5 min gone), projections OR-scan → two indexed reads (153 → 7 ms), needs-you fresh 104 → 39 ms; measure.py gains "Desk open" rows. Codex found the observer head-read not byte-identical and disclosing over-guard text → #1941 restores the exact old summary and keeps most of the speed by caching (needs-you fresh ≈ 61 ms).
- **Slices.** S24 #1926 (spend amount is a note, read as "spend note · 40 USD", no cap: a test proves a Program over its note still runs), S31 #1929 (`queue_outcome` from retained records: cancelled never revived, unknown never repeated), S35 #1935 (`reach`/`reach_words` beside a checkpoint's stored ref; history never rewritten), S54, S55, S14, S34, S56 above.
- **Hygiene.** #1942 and #1949: Playwright's `wait_for_function` does not await an `async () =>` check; five browser waits never waited; one helper `glass_infra.wait_for_hub`, a guard test, and the Settings Language bug it exposed (#1952). Fixes forward of the day: #1924 #1931 #1934 #1938 #1940 #1943 #1947 #1950.

Quick check: green on every batch head after its fix forward; the reds were stale citations, fences that keyed by file path (product-copy exception, HS-S51 import fence, badge token dropped by a token regeneration), wire fixtures (#1878's plan_goal checkpoint, #1935's reach fact), and parallel-merge seams (S24 vs the Programs rebuild). None was a face defect.

## Part III: the hub, as it stands

- Served checkout `/Users/karol/dev/tools/wt-desk-main-20261025`, detached on main (be095cadf at 11:00, ced8aa9ad at 11:20; the chain redeploys on green). Redeploy by hand: the session scratchpad `redeploy.sh <sha>` = `git fetch && git checkout --detach <sha> && uv sync --python 3.13 --extra dev --extra line && (cd web && npm ci && npm run build)`; kill the old `holdspeak.cli_entry web --no-open` pid and wait; start `HOME=/Users/karol HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open >> ~/.local/state/holdspeak/hub-main-20261107.log 2>&1 &`.
- The quick check runs in `/Users/karol/dev/tools/HoldSpeak`; never pull or branch there while it runs; run `(cd web && npm ci)` there after a `package.json` change (the kit's font package made the build red once). Side fixes go in `/Users/karol/dev/tools/wt-viewport`. The check's kept logs: `.tmp/quick-check/<stamp>/*.log`.
- Tailscale Serve fronts 8765 as `https://karols-macbook-pro.tailad9943.ts.net`.
- His Programs from the dogfood attempt are PARKED (5); leave them.

## Part IV: open, in the order I would run it

0. **His afternoon verdict** (`docs/walks/2026-11-08-afternoon.json`: the face, Draft update, Needs you, the Programs window). One sentence is a ruling; build it the same day. If the face is Redo: the next display face is not a grotesk; show three on the language board before building.
1. **Checks by eye the builders asked for:** Needs you's Later meaning (his uncounted rows for a later day, plus what he set to Later); the Programs rail at 393 (a wrapped strip); the Room's People plate without a next 1:1 (the read has no field); the night tile; the brass Button's deeper fill (#9c6b0b, for contrast).
2. **Desk open: 44–51 API requests.** Under 15 needs one batched read transport (19 collections at open + ~30 window reads); ~75 web tests stub fetch per path, ~30 browser files watch requests per path: its own lane. Duplicate reads at open (settings ×3, people readiness ×3, needs-you ×2) and the palette fetching the whole needs-you answer for counts.
3. **Second implementations still standing:** the first-run You card and the People window save the owner's name through their own PUT (`ownerName.ts`); Calls still reads `ThreadService._tool_executor._handles` directly (S21 consumer cleanup); `_read_week_sources` has its own People-names check; the AgentWords Lezer parser (69 KiB) in the desk chunk; `.desk-panel-title` still at display weight 700 (the wordmark should be the only 700); the warm `--kind-*` colours (brass is not yet the only warm colour on the desk); "At risk" words are coral now, but check every state word.
4. **Routes without a web or iOS reader: 303 of 935** (`docs/api-surface.json`); each needs its own proof (MCP twin, parity test, docs) before parking.
5. **Pre-existing reds found today, fixed or in flight:** `test_philo10_face_words` (`email_key_store_locked` reads failed/unknown, should be refused) and ruff F821 in `db/core.py` (lane running at handover); parked browser files still use the async-wait shape (not collected).
6. **Docs:** `docs/PROJECT_ROOMS.md` follows #1937; a lane makes README, USER_GUIDE, programs.md and DESK_OBJECT_MODEL describe the day's faces (running at handover). Generated docs (`scripts/gen_docs.sh`) still name `schema.py`.
7. **Program checkpoint reach** runs `git for-each-ref` in the Program's repository (not origin: nothing pushes those refs).

## Part V: measure (rule 7)

| Measure | 2026-11-08 05:21 | 07:03 | 11:25 |
|---|---|---|---|
| Merges on 2026-11-08 | 63 | 83 | 114 |
| Desk open, navigation to the desk screen | 674 ms (seeded, #1936's rig) | | 303 ms seeded · 152 ms empty |
| Desk open, API requests | 50 | | 44–51 |
| needs-you fresh / Room read / projections (ms, seeded) | 104 / 17 / 153 | | ≈61 / 8 / 7 |
| Hub cold start, median of 3 | 2.34 s | 1.53 s | 1.62 s |
| Desk chunk, raw | 2,417 KiB | 1,537 KiB | 1,577 KiB (the new faces) |
| schema.py / program_service / project_service / project_update_service | 5,436 / 5,591 / 5,459 / 4,050 | 5,436 / 4,370 / 3,404 / 4,050 | 474 (largest module) / 4,376 / 3,404 / 3,898 |
| web_server.py | 2,500 | 1,456 | 1,456 |
| NeedsDrawer.tsx / ProgramWindow.tsx / ProgramsWindow.tsx | 1,580 / 1,210 / 366 | | 403 / 848 / 127 |
| His presses, 24 h | | 25 answers, 6 walks | 28 answers, 7 walks |

Finding → main: the morning's dead rows 08:10 → fixed on his hub 08:40; the Room "looks like shit" 08:10 → R1 live 08:50 → the language live 11:00. Run `uv run python scripts/measure.py` each night (under the lock, with no chain running); the day file is `docs/internal/measure/2026-11-08.md`.
