# Handover (2026-11-08, one brain)

This is the ONE handover. It replaces every numbered handover before it (the owner, 2026-11-07: "kill all the previous handovers… default the latest one to just handover.md"). Rewrite it in place at each handover; history is in git.

Read first, in order: `CLAUDE.md` "How we work now" (the seven lines of 2026-11-07), this file, `pm/STATUS.md` (one line per merge), `docs/walks.md`. Two Brains is retired; nothing in `docs/internal/TWO-BRAINS.md` is current process.

## Part 0: how we think (the mentality, written down)

- **Move fast, with three checks and no ceremony.** A change is one concern, a few files, a worker in a worktree, a PR within the hour. A test that fails on main, one quick check per merge batch, his desk on main. Nothing else gates. A red is fixed forward at once, never debated; a revert is for security or data loss only.
- **One brain decides; workers build.** No mutual checks, no counsel rounds, no planning packages, no completion reports, no status paragraphs. A brief is the step text: the job, the settled decision, the owned files, the focused tests. The owner makes a ruling in one sentence; we do not ask twice.
- **The owner judges faces live, hand-held.** Every wave ends with a walk link. His answers, with the screen he saw, are the ruling and seed the next slices. When he says "apply my feedback", the orchestrator settles the design in the brief and builds at once; the canvas is for a face he rejected twice without a direction.
- **Subtract.** Every change removes a seam or a second implementation; it never adds one. Two implementations of one thing are a defect by definition.
- **Effortless and powerful, native, delightful.** The desk is strong; the glue and the core workflows are not. Pick work by core workflow, not by finding. A control that needs explaining has failed. No prose on faces, no modals, no counter of zero, no grey; the kit's material, the library Button for every verb.
- **Truth over comfort.** Say what failed, with the output. Say what was skipped. A flake is proven by a rerun, not assumed.
- **Diagnose before you theorize.** `kill -USR1` the hub and read the stack; `host` the link before blaming the phone; read the failing assertion before guessing the cause.
- **Never touch his real state.** Tests never see his HOME, DB or Keychain. Park, don't delete.

## Part I: the rulings (owner, verbatim where it matters)

1. **One brain, one loop, three checks** (2026-11-07). Muad'Dib decides; Opus 5.5 `opus-worker`s build in sibling worktrees and open PRs; the orchestrator merges, runs `scripts/quick_check.sh <last checked head>` once per batch on main, fixes a red forward, redeploys his hub. Codex is one bounded reviewer after a merge that touches a security surface (`scripts/astra check <brief.md> --tag <t> --effort high`; used on #1830: five real findings, fixed forward in #1834).
2. **No dogfooding our development through HoldSpeak Programs.**
3. **Plans are Programs or briefs, never documents.** `docs/internal/holdspeak-execution-plan/` is reference; its gates are ruled in its `DECISIONS.md` (2026-11-07). Waves 1 and 2 merged 2026-11-07; of wave 3, S25 merged 2026-11-08 (#1829); S32 and S12 open. Consolidation: S53 merged (#1828); S51, the bootstrap move, S24 disclosure-only open.
4. **The direction:** "an effortless system, a powerful system at the same time… not gluing everything together properly… nail the core workflows… not an overcomplicated architecture with multiple implementations of the same thing."
5. **Automate feedback: The Walk.** Every wave ends with a walk link. **The tailnet has no MagicDNS**: `karols-macbook-pro.tailad9943.ts.net` is NXDOMAIN; links are `http://<tailscale ip -4>:8765` (100.66.207.100), which `scripts/walk.py` prints since #1827, then 127.0.0.1, each in its own code block.
6. **The walk of 2026-11-08 (three answers, all Redo in words):** Programs' New program "I expected… some kind of a wizard… add effects… keep making UX better"; Needs you "way too cluttered, 'more' doesn't even look like a button… the 'Done', the 'Yours' (of course it's mine)"; the Room's Programs fold "not even a mention of anything like 'programs'" (it was in the DOM at display:none). Then: "apply my feedback, I was serious about it looking like shit and not being glued together." All three were built the same night (Part II).
7. **Still open from him:** the ask sheet pick (S1 two plates / S2 Keep leads / S3 the bar) on the canvas https://claude.ai/artifact/7drB7ysqd6gxj5zmZpKmbg; my recommendation is S2. The cursor (direction C) and the edge glow stand.

## Part II: what landed on 2026-11-08 (main 92a0c4a98 → bb138505b)

| PR | What |
|---|---|
| #1827 | The walk link is the Tailscale IP (MagicDNS dead) |
| #1828 | HS-S53: the destination form and its account words have one owner in `features/channels`; Settings and inline Send consume it |
| #1829 | HS-S25 branch A: a person-gated step merges on the latest review read, not a remembered approval; `facts.person_review`; `merge_requested_at` prevents a second dispatch |
| #1830 #1834 | ONE KEYSTORE: one master key in the Keychain via `/usr/bin/security`, every secret AES-GCM in `~/.local/share/holdspeak/keystore.enc`; migration from the old per-item entries; after Codex: key on stdin, tombstones, migration under the store lock, flock across processes, fsync and disk read-back before an old item is deleted |
| #1831 | Atlas citations follow #1828; the walk treats an undrawn part as missing and skips the step |
| #1832 | The Room's Now tab always shows its Programs fold (a CSS fold rule hid it live); rows share the list's step dots (`listStations`); none → "No Programs yet · New program" scoped to the project |
| #1833 | New program is a four-step wizard inside the Programs window (Where · What · How · Go); the inline project rows are gone; the scope `project:<id>` preselects |
| #1835 | Race fixtures re-recorded after #1829 widened the Program's shape |
| #1836 #1838 | Needs you: the row is the object (glyph · name · Done; press opens; the context menu carries Later/Drop/Hand/Open the Project); Mine · People one segmented control; Must fix/Should fix/Noted become the row's kind and order; then the open-grammar tests, the lamp word, A8 and mic ratchets fixed forward |
| #1837 | The iPhone walk browser case measures the sheet at rest (a flake under load) |

Quick check: green at 1f43a469f and at 336a6d87d; red once at d2438b793 (atlas, fixed #1831), once at 336a6d87d's batch (race fixture, fixed #1835), once at 17747e9c4 (#1836's four reds, fixed #1838); the check on bb138505b was running at handover.

## Part III: the hub, as it stands

- Served checkout `/Users/karol/dev/tools/wt-desk-main-20261025`, detached on main; venv Python 3.13 (`uv sync --python 3.13 --extra dev --extra line`). Redeploy: `git fetch && git checkout --detach origin/main && uv sync … && (cd web && npm ci && npm run build)`; `P=$(lsof -nP -iTCP:8765 -sTCP:LISTEN -t); kill $P; while kill -0 $P; do sleep 1; done`; start `HOME=/Users/karol HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open >> ~/.local/state/holdspeak/hub-main-20261107.log 2>&1 &`. Never run `quick_check.sh` in the served checkout while he walks (it rebuilds the bundle under him); run it in `/Users/karol/dev/tools/HoldSpeak`.
- **The first start after #1830/#1834 migrates his secrets** into the one keystore file: expect log lines `keystore: made the master key`, `keystore: open`, one `keystore: moved …` per secret; at most one Keychain dialog (a delete of an old item); Allow or Deny both keep the secret. The `security -i` add has not run against a real Keychain yet: if it misparses, secrets read as unavailable and nothing is overwritten. Watch `/api/setup/status` and Telegram after the restart.
- Voice: `/api/tts/status` → pocket/alba, model ready.
- His Programs from the dogfood attempt are PARKED (5); leave them. "AI SDLC" has no Programs filed (all six have an empty project_id), so its Room shows "No Programs yet".

## Part IV: open, in the order I would run it

0. Redeploy his hub on bb138505b (after the running check) and send the hand-held walk (`scripts/walk.py new docs/walks/2026-11-08-handheld.json`, words sharpened for the wizard, Needs you and the fold); read his answers (`scripts/walk.py read <id>`, shots in `~/.local/share/holdspeak/feedback/walks/<id>/`).
1. His ask-sheet pick → one build (`web/src/desk/walk/WalkRunner.tsx`, `walk.css`: handle row grip·dots·Skip·voice, question 20 px, Keep/Redo/mic row, no title line, no tints, no glyphs).
2. Wizard follow-ups the builder named: the frame's close drops the wizard unsaved (make it return to the list); the Walk's dots copied into `programs.css` (one kit dots component); the new row's settle unverified; the How step's agent/review defaults read "the template's".
3. Needs you follow-ups: Program rows (Later ▾ / Send ▾) are unchanged; the Today top rows share the component (verify live); `fold.grammar.test.tsx` "the CSS says Show and Hide" may be red on main (`today.css` `::before` vs `::after`), unverified.
4. Wave three rest: S32 delivery recovery (after S25; shares program_service), S12 startup intent last; S51 Program vocabulary out of program_service with aliases; bootstrap out of `web_server._create_app`.
5. Engine defects from the dogfood night (an agent can plan into its running Program; a refused write still ends Done; duplicates not folded).
6. Test lock: a worker reported `test_lock.py` exits 0 after a red pytest under `env …` (unverified; `subprocess.call` returns the code; check the reentrant path).
7. Canvases for Needs you, the Room and the Programs window as native apps remain the ruling device for the NEXT round if he rejects tonight's builds.

Measure (rule 7): 2026-11-07 38 merges; 2026-11-08 12 merges by 00:30 (#1827–#1838), 3 presses by him (the walk), finding→main minutes to two hours.
