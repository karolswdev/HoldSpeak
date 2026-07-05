# Evidence — HSM-16-04 (the web Astro Desk — the survey-corrected remaining slice)

**Done 2026-07-05.** The two genuinely-open slices shipped: the recipe layer resurrected
(authoring at parity) and the Ask AI atom's full web arc. Plus one latent 16-08 bug found
and fixed on the way.

## The truth-up first (the house discipline)

The resume survey marked this story "substantially pre-paid". The recipe half of that
credit was **false in practice**: the Phase-17 rename (agent → recipe) half-landed on the
web and left the whole recipe layer dead — loader keys (`d.agents` → `items.agent`, both
wrong), world ORDER/glow, lineage resolution, editor/pull-out kind checks, a crashing
"+ Agent" chip, and a desk vitest suite that was already failing on a renamed import.
Recorded loudly in the story header. Lesson (the same one as 16-09's): pre-paid credit is
only real once the surface's code is READ — and this time, once its tests are RUN.

## A second latent bug, found and fixed (HSM-16-08's manifest)

`_hub_model_name` (routes/sync.py) read the intel knobs off the top-level `Config`; they
live on `Config.meeting`. The `except` swallowed the `AttributeError` and every existing
test monkeypatched the helper — so a REAL hub never emitted its live `desktop:intel`
manifest row. Fixed; `test_hub_model_name_reads_the_real_config` now exercises the real
body with a real `Config` (local stem / cloud model id / disabled → "").

## What shipped

### The recipe layer, resurrected + authoring (web)

- `api.ts` reads the hub's real `{recipes: […]}` into `items.recipe` (fetch-stubbed
  regression lock on exactly this mapping).
- `world.ts` / `lineage.ts` / `InlineEditor` / `Pullout` / `DeskChrome` speak `recipe`;
  lineage tolerates the pre-rename `agent` rows on old artifacts and knows the ask via row.
- The in-world recipe editor gained the avatar field; `sprites.js` maps `recipe` to the
  same avatar pool as the pre-rename kind (same id → same face).
- The chrome chip is `+ Recipe` and actually works (was a live crash).

### The Ask AI atom (web parity of 16-09)

- **The gesture**: drag the empty desk to lasso (a dashed rope, `.desk-lasso`), or
  shift/cmd-click; roped objects wear a held selection ring; the bundle bar rises with
  `N selected → ✦ Ask AI`.
- **The composer** (`AskPanel`): docked in-world panel — desk visible and alive behind
  (the 17-08 atelier posture, no scrim, no modal); the iPad's five `RouteLenses` verbatim;
  prompt textarea with the speak-to-fill mic; a RUNS-ON picker (Hub default + profiles)
  whose egress chip is honest pre-run for the PICK.
- **The hub run** (`POST /api/ask`, new): assembles the roped cards' material FROM THE
  CANONICAL STORE (note body / artifact body / meeting intel summary+actions else
  transcript head / kb members; per-ask 6000-char cap, the iPad's number) — the Phase-53
  lesson, and the grounding is asserted in tests (`test_ask_grounds_in_the_canonical_store…`
  checks the content REACHES the engine's user prompt). Runs on the requested profile
  (key custody unchanged) or the hub default. **Persists nothing** — keep/bin is the
  human's judgment.
- **The printed card**: prints into the panel (its own print-in beat — the shared
  `materialize` keyframes are object-anchored and had shoved the card half off-panel),
  wearing the RUN's egress: `☁ Qwen3.5-9B-Q6_K · 192.168.1.43` for a profile run,
  `⌂ <local model>` for a local one — from the RESPONSE, never the app default.
- **Keep** (`POST /api/ask/keep`, new): mints the SAME artifact the iPad's Keep mints —
  `structured_json.provenance` with `via_kind: "ask"`, `context_ids`/`context_titles`/
  `prompt` (ask keys only when present — the golden recipe/chain wire shape untouched),
  `sources` = one `card` row per card read + the `ask` via row, `plugin_id: "web.desk"`,
  origin `run`. Locked byte-for-byte in `test_ask_keep_mints_the_ipad_wire_shape`. The
  kept card lands on the desk wearing the NEW beat.
- **Bin**: closes; nothing stored (asserted).

### Fixed on the way (pre-existing)

- `theater.js` consumed `intel_status` without the `scope: "run"` filter the dashboard
  applies — EVERY desk capability run popped the full-screen meeting "INTELLIGENCE READY"
  theater (caught in this story's first screenshot pass). Filtered.
- The desk's egress badges emitted `egress-<scope>` classes; global.css styles
  `is-<scope>` — the scope tint never applied. Both call sites fixed.

## Proof

- **Hub**: `uv run pytest tests/unit` → **2482 passed** (8 new ask-route tests + the
  manifest-config guard); `contracts/validate.py` → ALL CHECKS PASSED; api-surface
  regenerated (240 routes: `/api/ask`, `/api/ask/keep`).
- **Web**: `npm run test:desk` → **39 passed** (was 1 failing before this story);
  `npm run build` green (17 pages); source-only commit (the bundle stays gitignored).
- **Live** (`scripts/screenshot_hsm16_web_desk.py` — Playwright against the real app,
  scratch DB, engine faked in-process, `/api/ask` + `/api/ask/keep` run for real; the
  script also asserts the lasso count, both egress badges, and the kept row's provenance):
  - `screenshots/hsm-16-04-desk-recipes.png` — Scout floats AND rides the rail.
  - `screenshots/hsm-16-04-recipe-editor.png` — in-world authoring, all fields, no modal.
  - `screenshots/hsm-16-04-ask-selected.png` — the roped ring + the bundle bar.
  - `screenshots/hsm-16-04-ask-compose.png` — lenses, prompt, RUNS-ON naming the LAN
    profile's honest `☁ 192.168.1.43`.
  - `screenshots/hsm-16-04-ask-printed.png` — the printed card, full answer, the run's
    badge naming model · host, Bin/Keep, the desk alive behind the glass.
  - `screenshots/hsm-16-04-ask-kept.png` — the kept artifact on the desk, NEW beat.

## Deviations

- The Mission-Control conveyor is CSS-hidden inside the screenshot harness only (it reads
  this machine's real rails — off-topic and it must not leak local project names into
  committed shots). Nothing app-side changed for it.
- KB "spill its members" from the original criteria was NOT rebuilt here: a KB pull-out
  lists members (pre-paid), the spill-as-objects gesture remains iPad-only. If the owner
  wants it on web it is a small follow-up, not silently claimed.
