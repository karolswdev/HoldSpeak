# Handover — Muad'Dib XXXVIII (2026-11-07, one brain)

Read first, in order: `CLAUDE.md` "How we work now" (the seven lines of 2026-11-07 and the evening amendment to rule 3), this file, `pm/STATUS.md` (one line per merge), `docs/walks.md`. Two Brains is retired; nothing in `docs/internal/TWO-BRAINS.md` is current process.

## Part I: the rulings of the day (owner, verbatim where it matters)

1. **One brain, one loop, three checks** ("I can't afford to have so much ceremony… the whole 'two-mind' thing… caused massive delays"). Muad'Dib decides; Opus 5.5 `opus-worker`s build in sibling worktrees; a worker runs ONLY its focused tests and opens its PR; the orchestrator merges, runs `scripts/quick_check.sh` ONCE on main per merge batch (base = the last checked head), fixes a red forward at once, redeploys his hub. Codex is one reviewer profile inside Programs for security-surface steps only, after the merge (used once tonight: three real findings on the Walk's token routes, fixed forward in #1810).
2. **No dogfooding our development through HoldSpeak Programs** ("massive waste of time… there will be a time and place"). The one attempt proved him right: an Audit Program's agents appended 13 steps to their own Program, writes refused, steps Done with no diff (engine defects to fix later: an agent can plan into its running Program; a refused write still ends Done; duplicates not folded).
3. **Plans are Programs or briefs, never documents.** `docs/internal/holdspeak-execution-plan/` (#1788, 100 files from an outside planner) merged as REFERENCE; every pending gate ruled in its `DECISIONS.md` (2026-11-07 section). Its slices ran as Opus lanes.
4. **The direction:** "an effortless system, a powerful system at the same time… our desktop environment… is really powerful now… we're not gluing everything together properly… the flows are not frictionless… nail the core workflows and adapt the architecture and the design around them… not an overcomplicated architecture with multiple implementations of the same thing." Every wave carries architecture subtractions (measured) AND experience slices.
5. **Automate feedback: The Walk** ("open a tailscale link from you pointing to a script and I give feedback in this hand-held way"). Every wave ends with a walk link. iPhone 18 Pro Max portrait (~430×932) is his primary device for walks.
6. **Delete, not park, kokoro** (explicit exception to the park rule): the desk's voice is the Line's Pocket TTS; one hub voice.
7. **Verdicts on faces (two walks):** Programs well "yes but expected a bigger jump"; Needs you "looks like a shitty webpage… totally rethought… OS native apps"; the Room opened in its update posture "UX absolutely sucks". → STOP patching Needs you, the Project Room and the Programs window; redesign each as a native app on a CANVAS first, he picks, then build. The Walk's own face was rejected twice (robot, bubbles, marching pixels "cringe… sterile"); he picked **direction C, "the cursor is the hero"** from the canvas https://claude.ai/artifact/7drB7ysqd6gxj5zmZpKmbg, "but make the cursor interesting".

## Part II: what landed (main 765a46ab1 → bd850d2bd and on; 38 merges on 2026-11-07)

| PRs | What |
|---|---|
| #1788 #1789 #1800 | The execution plan as reference (gates ruled); CLAUDE.md/AGENTS.md on one brain; the batch-check rule |
| #1791 #1795 #1807 | Doc-link red on main fixed; STATUS one-liners |
| #1790 #1792 #1793 #1794 | HS-S52 Room reads the open review through the repository; HS-S23 `within` lowers the bar only when coverage widens; HS-S43 Needs you coverage; HS-S11 global New creates in a chosen project |
| #1796 | Dead code parked (ProjectMemoryCore wrapper, SystemShade/AttentionDrawer shims, Serializable mixin), three web-layer imports cut from services, a new guard `tests/unit/test_services_import_no_web.py` |
| #1797 #1798 #1799 #1801 #1802 #1804 | HS-S22 a new step starts at origin's base, proved; HS-S13 the Room lists its Programs; HS-S33 People Add keeps the saved request; HS-S21 Add binds an action to one step; HS-S41 Meeting owner name + Room informed Link; HS-S42 decision filing scope/correction |
| #1803 #1805 #1806 | Batch-check reds fixed forward (a prose line, five failure strings, the API manifest) |
| #1808 #1810 #1811 #1812 #1813 #1814 #1815 | The Walk (hub `/w/<token>` + desk runner + `scripts/walk.py`); its token routes bounded (Codex findings); Needs you coverage as a toolbar People button; the Programs well as a project list; walk records the pressed choice / phone sheet / own-window targeting; the dim never covers the target; the hand-held rebuild (frame, robot, press/scroll/say, whole-viewport shots, voice) — face superseded by direction C |
| #1816 | ONE HUB VOICE: `/api/tts` speaks through the Line's Pocket TTS; kokoro deleted (owner ruling) |
| #1817 #1819 #1818 | SIGUSR1 dumps every hub thread's stack to the log (chain=False); a keystore read that does not answer is bounded (2 s) |
| #1820 #1821 | The walk link opens the desk by itself (carries the desk bootstrap token, read at request time) |
| #1822 | The walk starts only when the desk is ready (hubSeeded, `#desk-next` not busy, Dock drawn, no window loading) and moves one beat later |

The test lock is reentrant (`HOLDSPEAK_TEST_LOCK_HELD`), `quick_check.sh` is proportional (docs-only 27 s; build/web guards only when `web/` changed; sweep only when `web/` or `holdspeak/` changed). `/Users/karol/dev/tools/.metadata_never_index` keeps Spotlight off the worktrees.

## Part III: the hub, as it stands

- Served checkout `/Users/karol/dev/tools/wt-desk-main-20261025`, detached on main; venv is **Python 3.13** (`uv sync --python 3.13 --extra dev --extra line`; 3.14 has no onnxruntime wheel). Start: `HOME=/Users/karol HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_UI_FEEDBACK=1 nohup .venv/bin/python -m holdspeak.cli_entry web --no-open >> ~/.local/state/holdspeak/hub-main-20261107.log 2>&1 &`; wait on the old PID, not the port. Links: `http://karols-macbook-pro.tailad9943.ts.net:8765` and `http://127.0.0.1:8765` (both, each in its own code block, always).
- **The Keychain lesson (2026-11-07 ~21:00):** changing the hub's Python binary made macOS Keychain prompt for every keyring item (Telegram token, paired chat, People key…); a background hub never sees the prompt; 15 threads wedged in `find_generic_password`; the desk went empty. He pressed Always Allow on each. Diagnose a wedge with `kill -USR1 <hub pid>` and read the log; `pgrep SecurityAgent` says whether a prompt is pending. Slice owed: ONE master key in the Keychain + one encrypted keystore file, read once at startup with a deadline, and a stable launcher path.
- Voice: `/api/tts/status` → `{installed, model_ready, engine: "pocket", voice: "alba"}`; the Pocket weights are fetched (`holdspeak/line/models.py`, preset `speech_line_pocket_tts_en`, ~/.holdspeak/line/models). First synthesis ~1.3–2.3 s.
- Programs on his hub from the dogfood attempt are PARKED (5); leave them.

## Part IV: in flight at handover

- **Direction C build** (`face/walk-direction-c-20261107`, opus-worker): the living cursor (two-tone pixel-crisp arrow: arc, tilt, comet trail, hover a beat, squash-tap, warm ripple), warm edge glow, one caption + voice, target lifts with a halo, no dim by default; robot/bubble/frame/ring removed. It also carries two main reds from #1822: `DeskApp.test.tsx` import cycle (walk.ts imports `hubSeeded` at load → make it lazy) and `test_web_null_read_guard::test_product_components_do_not_mutate_global_dom_or_inject_html` (walk.ts `document.querySelector` → one sanctioned `walk/dom.ts`). When it lands: merge, `scripts/quick_check.sh 765a46ab1` in the served checkout, rebuild web, restart the hub, `scripts/walk.py new docs/walks/2026-11-08-handheld.json`, send him both links. His last walk link (mP-9HIQ…) stays valid.
- Main is red until that PR merges (the two items above). His hub runs the last green build.

## Part V: open, in the order I would run it

1. Finish Part IV; one walk link; read his answers with `scripts/walk.py read <id>` (the shots: `~/.local/share/holdspeak/feedback/walks/<id>/`).
2. **Canvases before builds** for Needs you, the Project Room, the Programs window as native apps (his words: OS-native, no web-page look). The canvas is the ruling device now; the Design artifact type works (see the walk canvas).
3. **Architecture subtractions, measured** (bundle size, hub start, files per change): service construction out of `web_server._create_app` into runtime composition; Program vocabulary + `ProgramRefused` + `_LOCK` out of `program_service.py` with aliases (plan HS-S51); the destination form to `features/channels` (HS-S53); the opener registry → one startup intent (HS-S12, last, touches everything). Keychain slice (Part III).
4. **Plan wave three**: HS-S25 current-review eligibility, HS-S32 delivery recovery; HS-S24 spending = disclosure-only (ruled; no code yet).
5. Walk gaps: `viewport-fit=cover` not set (iPhone safe-area insets may read 0); iPhone Safari full-viewport capture and post-tap audio unverified; a Room step must open the Room proper (done in #1815, verify live).
6. Engine defects from the dogfood night (Part I.2).
7. STATUS lines for #1796–#1822 are in this PR's `pm/STATUS.md`.

Measure weekly (rule 7): merges/day (38 today), presses by him (0 until the walks), hours finding→main (minutes tonight).
