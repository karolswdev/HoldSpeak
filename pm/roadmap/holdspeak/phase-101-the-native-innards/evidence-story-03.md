# Evidence - HS-101-03

- **Story:** HS-101-03 - The build (authored at the gate)
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T21:34:02Z

- **Command:** `sh -c uv run pytest -q tests/unit/test_interior_canon_guard.py && cd web && npx vitest run src/desk/surface --maxWorkers=2 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c0b2eae4563f1ff8b106eb363980f41c1562e072

```text
..                                                                       [100%]
2 passed in 0.04s
   Start at  15:34:03
   Duration  635ms (transform 160ms, setup 99ms, import 297ms, tests 191ms, environment 465ms)
```

### B1 — summary

The kit and the rail ban: `EditInPlace` shipped in the surface kit
(present ↔ same-geometry editor, Enter/blur commits, Escape reverts,
locked values name why; 6 vitests). The aerogel inset shipped as
`.surface-aerogel` (and `.surface-preview` converted onto it) riding
the `--desk-aerogel-*` tokens; `.desk-session-question` (the coder's
asked question) re-cut as aerogel. ALL SIX shipped `border-left`
accent rails removed (surface.css ×1, desk.css ×5).
`tests/unit/test_interior_canon_guard.py` now refuses ANY non-zero
`border-left` in web/src CSS by file:line — the rail cannot return
under any color. Interior type-scale classes (`.surface-display`,
`.surface-primary`) ride the `--desk-type-*` tokens. Full web check
green (tokens, architecture guard, typecheck, vitest, build).

### Captured run — 2026-07-19T21:37:31Z

- **Command:** `uv run pytest -q tests/unit/test_interior_canon_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0f723907d7289a7a722a03c6fa863462dee5e07c

```text
...                                                                      [100%]
3 passed in 0.03s
```

### B2 — summary

The fluid desk, kit-level: row verbs ease to the pointer (opacity +
2px rise on --duration-short/--ease-quart), aerogel receipts inflate
from their row (surface-aerogel-in, --ease-back), sections — and so
wing faces, which compose them — rise in (surface-rise-in,
--duration-medium/--ease-quart), and the one menu vocabulary springs
(desk-transient-in, transform-origin at its anchor corner). All
compositor-only, all token-ridden (gate clean), all silenced under
prefers-reduced-motion. The guard grew test_fluidity_census: the
named moments must keep their motion and both files their
reduced-motion silence. Desk vitests 247/247; build green.

### Captured run — 2026-07-19T21:56:10Z

- **Command:** `sh -c uv run pytest -q tests/unit/test_dictation_routes_split.py tests/integration/test_web_dictation_correction_ritual.py tests/unit/test_interior_canon_guard.py && cd web && npx vitest run src/desk/surface --maxWorkers=2 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c316c34b787d65ce59853a87d7a05ae872291119

```text
............                                                             [100%]
12 passed in 1.59s
   Duration  1.23s (transform 187ms, setup 198ms, import 467ms, tests 240ms, environment 885ms)
```

### B3 — summary

The Journal reads like a journal, live-proven on a staged hub
(seeded-desk, run-20260719T214511): SurfaceStream/Day/Entry joined
the kit with the stream time grammar in format.ts (epoch seconds/
millis/ISO, junk → "Undated"; 20 surface vitests). The Journal face
rebuilt: "N today · M taught" leads at display step (both counts
day-honest), day bands, the spoken text at the primary step AS the
material — EditInPlace commits to the new PUT
/api/dictation/journal/{id} (the one write rule 1 needed; corrected
flag untouched; empty refuses 422; missing 404; proven by driving
the editor live and re-reading after a full page reload), verbs on
the entry's meta line (no reserved band), the replay receipt floating
in aerogel. Route census updated deliberately (37 → 38) and the API
surface regenerated. Shots at 1440 + 393 + the aerogel receipt in
assets/hs-101-03/, looked at.

### Captured run — 2026-07-19T22:09:03Z

- **Command:** `sh -c uv run pytest -q tests/ -k block 2>&1 | tail -1 && cd web && npx vitest run src/desk/surface --maxWorkers=2 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 07f95ea74ca1f85a39211aee2fcef9b4ad6401cd

```text
153 passed, 2 skipped, 4020 deselected in 54.42s
   Duration  1.49s (transform 255ms, setup 195ms, import 632ms, tests 486ms, environment 968ms)
```

### B4 — summary

Blocks reads like a library, live-proven on the staged hub:
SurfaceLibrary/Tile/Ghost joined the kit — the tile FACE is the
block's injection template (mono, fading), the spine carries the
name and the spoken matches as quoted chips, the inject mode as a
quiet caption, create is a ghost tile in the shelf (the side form is
dead). Edits land on the material: the template and the name are
EditInPlace commits to the existing PUT. Along the way the build
exposed that the old face's create payload NEVER matched the block
schema (match must be {examples: [...]}, inject {mode, template},
description required — creation from the web was silently broken)
and that its "active" pill had no schema field behind it — both
fixed by composing the honest fields. Driven live: three blocks
created through the ghost tile, a rename in place, chips splitting
correctly. Block pytest 153 passed; web suite 306/306; shots at
1440 + 393 in assets/hs-101-03/.

### Captured run — 2026-07-19T22:17:57Z

- **Command:** `sh -c cd web && npx tsc --noEmit && npx vitest run src/desk/surface --maxWorkers=2 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5819c15531fdf3ce8c2ffc2c48148bf11ada3aad

```text
   Duration  1.26s (transform 236ms, setup 226ms, import 538ms, tests 244ms, environment 866ms)
```

### B5 — summary

Runs on reads like a switchboard, live-proven on the staged hub:
SurfaceSwitchboard/SurfaceBay joined the kit — one bay per
destination, the DEFAULT bay leading full-width on the accent tint
with its model at display step, lamps paired with liveness text
(never color-only), the offline reason named in full from
mesh_liveness ("offline — last seen just now"), the destination-class
badge (canon vocabulary via destinationClassLabel) at the point of
decision, verbs overlaid on hover. "Make default" is the new bay
verb, wired to the ESTABLISHED settings write
(dictation.runtime.profile_id partial PUT — the same call site the
recovery flow uses); driven live: created the LAN endpoint + a mesh
node through the editor, made the endpoint the default, the bay
re-led with the tag. Shots at 1440 + 393 in assets/hs-101-03/.

### Captured run — 2026-07-19T22:22:38Z

- **Command:** `sh -c cd web && npx vitest run src/desk/components/__tests__/systemShade.test.tsx 2>&1 | tail -2 && npm run tokens:gate --silent 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0a9333e9ba62fa8f5af39bb1c82c201662e77125

```text
   Duration  617ms (transform 59ms, setup 63ms, import 155ms, tests 62ms, environment 247ms)

token gate: clean (62 allow-listed exceptions, all in use)
```

### B6 — summary

The system shade is live behind the bell: SystemShade drops from the
bar on the transient material (desk-shade-drop spring, reduced-motion
instant), grouping the projections feed honestly — "Needs you" with
Open / Acknowledge / Dismiss inline, "Finished" receipts with Open,
"Learned" from the corrections store. Zero says zero ("Nothing needs
you", "No corrections taught yet"); the full Desk-memory browser
stays one verb away (the drawer window is unchanged, only the bell's
target re-shaped). The "Recovered" group from the canon inventory has
NO server feed today and is deliberately not faked — it lands when a
recovery feed exists (recorded as a rider). Driven live: bell →
shade with the day's real receipts (the B3 replays), Escape closes,
click-out closes. Vitest 2/2 (groups + honest zero + Escape); token
gate clean (a stray raw z-index caught and removed).

### Captured run — 2026-07-19T22:37:07Z

- **Command:** `sh -c HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py geometry && HS_WALK_BASE=http://127.0.0.1:8792 uv run python scripts/desk_gl_walk.py keys`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 56cda984caeca0bfdc5fbe7da3f9c0a67493d375

```text
geometry walk: 12 windows measured against the grammar — heads, lights, padded bodies, no sideways scroll, no tab walls, reflow at 360px
keys walk: Meta+1/Meta+4 open the applications, Meta+M minimizes, Meta+W closes, Meta+/ draws the sheet, Escape clears it
```

### B8 — summary

The keyboard grammar and the grown walk, both live on the staged hub
(capture above): ⌘1–⌘4 open/switch the four applications (restore if
minimized, focus if open, launch otherwise — same paths as the dock),
⌘W closes and ⌘M minimizes the front window (typing-guarded; the
front is the last non-minimized id in the stacking order), ⌘/ draws
the shortcut sheet on the transient material (portaled to the body —
fixed inside the transformed dock anchored wrong, and the portal then
escaped the .desk-next CSS scope: both caught by looking), Escape
clears it. The geometry leg grew the interior-canon assertions: on
the converted-faces ledger (Speak, Runs on — grows per interior),
>=3 distinct type-scale steps and ZERO label+input stacks outside
configuring faces. The grown leg immediately caught and killed three
real defects: two .hs-field stacks on the working Speak face (the
Utterance and grounding-scope inputs now aria-labeled material) and
an invisible 13px horizontal overflow in Settings (the switch's
hidden checkbox was position:absolute with no anchor — escaped the
window body). speakflow still 4 interactions; web suite 308/308; a
new `keys` walk leg pins the grammar.

### Captured run — 2026-07-19T22:51:40Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/glassDrop.test.tsx 2>&1 | tail -2 && npx tsc --noEmit && echo tsc-clean`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9d93edaa77746522d70c3577d0739693791e67f1

```text
   Duration  462ms (transform 56ms, setup 48ms, import 104ms, tests 27ms, environment 203ms)

tsc-clean
```

### B7 — summary

Through the glass, all three directions on the real wire:
(1) FILES IN — GlassDropLayer on the desk root: an OS file drag arms
a veil before the drop; a dropped .vtt/.srt/.txt or audio file
imports through the REAL POST /api/meetings/import (multipart, the
hub's own suffix routing mirrored in glassDrop.ts); driven live on
the staged hub — the veil armed, release-sync-followup.vtt became
meeting 121c29ff (2 segments), and archive.zip refused BY NAME
("Can't import .zip — transcript (.vtt .srt .txt) or audio only").
(2) OBJECTS IN — the GL engine's onUp hands a drop landing on a
[data-glass-accept] DOM well through the glass (CustomEvent
desk:glass-drop) and the object returns home (startU captured at
drag start; handed over, never consumed); GroundingSection is the
first well — it lights while an object drag is in flight
(draggingId) and adds the dropped object to the ask/steer/chat
grounding through the same fetch-priced path (contract vitest: event
in → resource added). (3) CHIPS OUT — the printed ask answer drags
out; released over the desk world it fires the SAME keep verb (the
minted artifact files itself). Vitests 310/310; tsc clean; veil +
imported shots in assets/hs-101-03/.

### B9 — summary (the owner's mid-build ask)

The agent panes and the delivery rails wear the canon. The PANE
reads like a SCRIPT: `.desk-session-pane` (shared by the steering
pull-out AND the delivery terminal window) left its bordered box for
the well tone — tonal separation per the HS-99 depth ladder, inset
like a screen, no chrome around the material; the asked question
already floats in aerogel since B1. The DELIVERY list wears the
scale: the item is the material at the primary step, kind/freshness
recede to metadata, the section title is a caption — scoped so the
desk's own Files table keeps its grammar. ⌘3 → Delivery reaches it
(shot in assets; the staged world has no rails configured and the
board says so honestly).

THE SURVEY, recorded: ~/dev/code/delivery-workbench now sits at
phase 25 against this repo's phase-16 rails — live ledger streaming
(WLA-25-05), agent nudges under grant authority (WLA-25-04),
durable operator notification (WLA-25-06), SCM fact observation
(WLA-25-02), and a neutral seam that drives Claude Code itself
(WLA-25-07). Adopting that dw and wiring the desk's rails surfaces
to the live ledger + nudge contracts is ITS OWN PHASE — recorded as
the standing rider from this story; the local `.githooks/dw` (1.12
+ phase 16) stays the rails truth here until that phase.

### Captured run — 2026-07-19T23:02:27Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** ac4cb4a4ee45febfafa31c0fbfc1c1996677cee8

```text
ssssssssssssssssssssss...ssssssssss..................................... [  1%]
........................................................................ [  3%]
...F..s................................................................. [  5%]
.....................................................ss................. [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
....................................................F................... [ 12%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 27%]
..................................................................F..... [ 29%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
..F..................................................................... [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
...F.................................................................... [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
.....................................................                    [100%]
=================================== FAILURES ===================================
_____________________ test_journal_card_has_replay_action ______________________

persistent_db = <holdspeak.db.core.Database object at 0x14c136c10>

    def test_journal_card_has_replay_action(persistent_db: Database) -> None:
        """The Replay action + before/after styles ship in the page/bundle."""
        client = _client(persistent_db)
        body = client.get("/dictation").text
        assert '<div id="root"></div>' in body
        source = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/DictationCore.tsx").read_text()
        assert "/replay" in source and "replayResult" in source
>       assert "Preview only" in source and "Copy result" in source
E       assert ('Preview only' in "// HS-95-05 — the Dictation surface's core, hosted anywhere.\n// HS-98-02 — re-crafted native on the window material..../>\n      <Memory />\n      <Knowledge />\n      <Runtime />\n      <Hooks />\n      <Nudges />\n    </div>\n  );\n}\n")

tests/integration/test_dictation_journal_replay.py:181: AssertionError
___________________ test_dictation_page_includes_journal_tab ___________________

test_client = <starlette.testclient.TestClient object at 0x14c90c590>

    def test_dictation_page_includes_journal_tab(test_client: TestClient) -> None:
        assert '<div id="root"></div>' in test_client.get("/dictation").text
        source = (Path(__file__).resolve().parents[2] / "web/src/pages/cores/DictationCore.tsx").read_text()
        # HS-100-07: the Journal is a head wing of Speak.
        assert '{ id: "journal", label: "Journal" }' in source
        assert "/api/dictation/journal" in source
>       assert "Search journal" in source and "Clear journal" in source
E       assert ('Search journal' in "// HS-95-05 — the Dictation surface's core, hosted anywhere.\n// HS-98-02 — re-crafted native on the window material..../>\n      <Memory />\n      <Knowledge />\n      <Runtime />\n      <Hooks />\n      <Nudges />\n    </div>\n  );\n}\n")

tests/integration/test_web_dictation_journal.py:141: AssertionError
_________________ test_committed_manifest_matches_the_live_app _________________

committed = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...web.routes.activity.enrichment', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': []}}
live = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...web.routes.activity.enrichment', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': []}}

    def test_committed_manifest_matches_the_live_app(committed, live) -> None:
>       assert committed["routes"] == live["routes"], (
            "the committed API-surface manifest drifted from the live app/call "
            "sites — regenerate: uv run python scripts/gen_api_surface.py"
        )
E       AssertionError: the committed API-surface manifest drifted from the live app/call sites — regenerate: uv run python scripts/gen_api_surface.py
E       assert [{'consumers'...ations'}, ...] == [{'consumers'...ations'}, ...]
E         
E         At index 141 diff: {'path': '/api/dictation/blocks/from-template', 'methods': ['POST'], 'module': 'web.routes.dictation.blocks', 'consumers': ['ios']} != {'path': '/api/dictation/blocks/from-template', 'methods': ['POST'], 'module': 'web.routes.dictation.blocks', 'consumers': ['ios', 'web']}
E         Use -v to get more diff

tests/unit/test_api_surface.py:52: AssertionError
_____________________ test_no_dialog_takeovers_on_the_desk _____________________

    def test_no_dialog_takeovers_on_the_desk() -> None:
        for name, text in _tree(DESK).items():
            assert "aria-modal" not in text, f"dialog takeover pattern in {name}"
>           assert 'role="dialog"' not in text, f"dialog takeover pattern in {name}"
E           AssertionError: dialog takeover pattern in web/src/desk/components/DeskWindow.tsx
E           assert 'role="dialog"' not in '// The desk...,\n  );\n}\n'
E             
E             'role="dialog"' is contained here:
E               et"
E                     role="dialog"
E                     aria-label="Keyboard shortcuts"
E                     onPointerDown={(e) => {
E                       if (e.target === e.currentTarget) onClose();...
E             
E             ...Full output truncated (19 lines hidden), use '-vv' to show

tests/unit/test_desk_locks.py:33: AssertionError
_______ test_product_components_do_not_mutate_global_dom_or_inject_html ________

    def test_product_components_do_not_mutate_global_dom_or_inject_html() -> None:
        offenders = []
        for path in sorted(ROOT.rglob("*")):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            text = path.read_text()
            for pattern in (r"document\.(?:querySelector|querySelectorAll)\s*\(", r"\.innerHTML\s*=", r"insertAdjacentHTML\s*\("):
                if re.search(pattern, text):
                    offenders.append(str(path.relative_to(ROOT)))
>       assert not offenders, f"Selector/HTML-owned product state: {sorted(set(offenders))}"
E       AssertionError: Selector/HTML-owned product state: ['desk/surface/__tests__/stream.test.tsx']
E       assert not ['desk/surface/__tests__/stream.test.tsx']

tests/unit/test_web_null_read_guard.py:17: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
FAILED tests/integration/test_dictation_journal_replay.py::test_journal_card_has_replay_action
FAILED tests/integration/test_web_dictation_journal.py::test_dictation_page_includes_journal_tab
FAILED tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
FAILED tests/unit/test_desk_locks.py::test_no_dialog_takeovers_on_the_desk - ...
FAILED tests/unit/test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html
5 failed, 4117 passed, 37 skipped in 967.44s (0:16:07)
```

### Captured run — 2026-07-19T23:22:10Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0e6a1c7d2724e828abe2b42c47f1435e61b3cfd5

```text
ssssssssssssssssssssss...ssssssssss..................................... [  1%]
........................................................................ [  3%]
......s................................................................. [  5%]
.....................................................ss................. [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
.....................................................                    [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
4122 passed, 37 skipped in 927.39s (0:15:27)
```
