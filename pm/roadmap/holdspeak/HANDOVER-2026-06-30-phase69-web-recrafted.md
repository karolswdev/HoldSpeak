# HANDOVER — 2026-06-30 — Phase 69, Web Re-crafted (read me first)

An honest map for the next agent of the web-convergence work that landed this
session: what shipped, where it lives, the traps that will bite you, and what is
deliberately left. No spin.

---

## 1. The headline

**Phase 69 — Web, Re-crafted: CLOSED (12/12), merged to `main` (PR #202)**, plus a
follow-up (**PR #203**, also merged). The web flagship caught up to the iPad's
"Signal" felt craft — no re-theme, no framework swap (Astro + Alpine + vanilla ES
modules; the token foundation was already byte-identical across both surfaces).

Final suite: **`uv run pytest -q --ignore=tests/e2e/test_metal.py` → 3045 passed,
37 skipped.** Everything is on `main`; nothing left local.

This was the **delivery half of the web/iPad convergence**: Phase 68
(`phase-68-web-convergence/parity-map.md`) mapped the gap; Phase 69 applied + ported
it. The "EQUILIBRIUM" spirit — every primitive felt-equal on both surfaces.

---

## 2. The disequilibrium Wave A reconciled (why this mattered)

Before any feature work, a real PMO/cadence mess was fixed:

- The Phase-69 **substrate** (the `.signal-card` primitive, gradient/hairline
  tokens, `hs-materialize`, the egress badge, the Queue HUD) had already been
  written — but it landed **inside a mixed MOBILE checkpoint commit** (`f64d80d
  HSM-14-19`) with **no per-story evidence** — a gate violation, already merged.
- The desktop README "Current phase" pointer was **stale at Phase 67** (Phases 68
  and 69 didn't appear).

Wave A recorded the debt honestly, fixed the pointers, and resumed the program
under the gate. Lesson for next time: substrate/UI work for the *desktop* roadmap
must commit on the *desktop* cadence, not get swept into a mobile checkpoint.

---

## 3. What shipped — the 12 stories + the follow-up

All under `pm/roadmap/holdspeak/phase-69-web-recrafted/` (story-NN + evidence-NN +
screenshots/ + final-summary.md). Each was its own gated commit with screenshot
proof; the theater also has a **real-`.43`-metal** proof.

| Story | What | Key files |
|---|---|---|
| **01** | Egress badge across the cockpit (not just `/presence`) | `web/src/styles/global.css` (`.egress-badge`), `web/src/scripts/egress-badge.js` |
| **02** | `.signal-card` made **composable** (`--signal-card-surface`) + broadened to `/desk` + `/activity` | `global.css`, `web/src/pages/desk.astro`, `activity.astro`, `web/src/scripts/activity-app.js` |
| **03** | Gradient + hairline tokens | `web/src/styles/tokens.css` (`--accent-gradient`, `--bg-gradient`) |
| **04** | `hs-materialize` arrival motion | `global.css` |
| **05** | Premium confirm **sheet** (grab handle, glyph chip, top-lit hairline, tinted-glow backdrop, pill buttons) | `web/src/components/ConfirmDialog.astro` |
| **06** | Qlippy dock + cards **into the cockpit** (extracted to a shared component) | NEW `web/src/components/Qlippy.astro`; `web/src/layouts/AppLayout.astro`; `presence.astro` (slimmed 385→144) |
| **07** | The app-wide Queue HUD (pill → live ledger) | `web/src/scripts/runtime-bus.js`, `queue-hud.js`, `web/src/components/QueueHud.astro` |
| **08** | Reactive mic **waveform** on an **additive `audio_level` WS frame** | NEW `web/src/components/Waveform.astro` + `web/src/scripts/waveform.js`; `holdspeak/web_runtime.py` (`_emit_audio_level`); `holdspeak/runtime/meeting_glue.py` |
| **09** | The generation **theater** (orb + constellation), driven by live intel frames | NEW `web/public/theater/theaterorb.png` (reused from `apple/App/`), `GenerationTheater.astro`, `web/src/scripts/theater.js` |
| **10** | Node canvas **foundation** — the new `/workbench` | NEW `web/src/pages/workbench.astro`, `web/src/scripts/workbench/model.js` + `canvas.js`; route in `pages.py`; TopNav |
| **11** | Node canvas **wiring + inspector + palette** | extends `canvas.js` + `workbench.astro` |
| **12** | `/companion` → **the Agent Desk** | `web/src/pages/companion.astro` (rewritten), NEW `web/src/scripts/companion-desk.js` |
| **follow-up** | **Cloud intel streaming** (PR #203) — endpoint intel now streams `intel_token` (was buffered) | `holdspeak/intel/engine.py` (`_chat_completion_stream`) |

### The waveform's additive backend (HS-69-08)
The recorders already computed a 0..1 level per chunk; the callbacks were thrown
away by stub lambdas. `web_runtime._emit_audio_level(level, source)` throttles to
~15 Hz, clamps, and `self.server.broadcast("audio_level", {...})`. Wired into the
dictation recorder (`web_runtime.py`) + both meeting channels (`meeting_glue.py`).
The frontend subscribes on the shared `runtime-bus`. This is the **only** backend
behaviour change in the presentation phase (an explicit additive exception).

### The node canvas (HS-69-10/11) — the marquee
- `/workbench` renders the canonical **linear `Workflow`** (`source → steps →
  output`, byte-compatible with the iPad's Codable form) as a node graph.
- **Pure-vanilla**, no graph lib: SVG bezier cables + HTML `.signal-card` nodes in
  ONE transformed "world" layer (`canvas.js`). Pan (drag canvas) / zoom (wheel
  about the cursor) / node drag (live cable re-layout) / **drag-to-wire** with
  type-compatibility (green = compatible, danger = not) / an **inspector** drawer
  (tap a node → edit its prompt) / a **palette** (add a node).
- Cable math is the iPad's exact `max(46, |dx|·0.45)` horizontal-tangent cubic.
- Port colours = the web-wins status palette (text→`--accent`, findings→`--ok`,
  signal→`--info`). Layout/edges/prompts persist to `localStorage` under the iPad's
  `hs.workflows.v1` key.

### The cloud-streaming follow-up (PR #203) — the owner's ".43" catch
The generation theater's "thinking" pulse (and the Queue HUD heartbeat) were dark
for **endpoint** intel — the common path. Root cause was the **engine**, not the
endpoint: `MeetingIntel._analyze_stream` short-circuited the cloud provider to a
single `_analyze_once` call (zero `intel_token` chunks); only local GGUF streamed.
Fixed with `_chat_completion_stream` (streams BOTH providers; forwards the
OpenAI-compatible endpoint's `delta.content`). **Proven on real `.43`: 125 streamed
chunks + the snapshot, RESULT PASS** (`scripts/theater_realmetal_proof.py`).

---

## 4. Traps that WILL bite you (hard-won this session)

1. **Astro scoped CSS never reaches JS/`innerHTML`-injected DOM.** The default
   `scopedStyleStrategy` is `'attribute'` (`.foo[data-astro-cid-…]`), and
   runtime-injected nodes don't carry the cid. This is why **every Phase-69
   primitive is `<style is:global>`**, and why `/activity`'s scoped `.rule-item`
   styles never applied to its `innerHTML` cards (a latent bug HS-69-02 fixed via
   the global primitive). When a class compiles into the bundle but doesn't paint,
   this is almost always why — screenshot-verify, don't trust the class.
2. **A new web page needs THREE registrations**, or it 404s / isn't swept:
   (a) the `.astro` page, (b) a route in `holdspeak/web/routes/pages.py`, (c) an
   entry in `tests/e2e/test_route_preflight.py` `PAGE_ROUTES` (a coverage guard
   *requires* it). Missing (b) → the page 404s under the real server (caught me on
   `/workbench`).
3. **Canvas pan stole palette/inspector clicks.** A `pointerdown` handler that
   calls `setPointerCapture` on the viewport steals events from interactive
   children inside it. Guard: `if (e.target.closest('.wb-palette,.wb-inspector,
   .wb-node')) return;` before capturing.
4. **Alpine factories load via `?raw` + `new Function`, NOT ES `import`.** The
   factory file is a plain `function X() {…}` (NO `export`); the page does
   `const fn = new Function(src + "; return X;"); window.X = fn(); Alpine.start();`
   (see `profiles.astro`, `companion.astro`).
5. **The built bundle (`holdspeak/static/_built/`) is GITIGNORED.** Edit
   `web/src`, then `cd web && npm run build`; commit source only. Never commit
   `_built/`.
6. **PMO gate specifics:** a contract (`.tmp/CONTRACT.md`, 7 `[x]`) per commit;
   **≤1 story-flip per commit**; a `story-NN-*.md` flipping to `- **Status:** done`
   must ship its `evidence-story-NN.md` in the SAME commit. The reverse also fires:
   **you cannot stage an `evidence-story-NN.md` without a story-NN flip in that
   commit** (the "orphan evidence" check) — so post-hoc corrections to an
   already-shipped story's evidence belong in `final-summary.md` (hook-free), not
   the evidence file. The `Co-Authored-By` + `Claude-Session` footer IS used (the
   recent commits carry it).
7. **`.43` vs `.13` for real-metal intel.** `.13` (the clean Mac llama-server) was
   **down** this session; `.43` (Qwythos-9B) is up and **does stream** — use it.
   LAN is unreachable from sandboxed Bash; use `dangerouslyDisableSandbox` to hit
   it. (Memory notes `.43` can force a `{"line":...}` grammar, but it produced
   clean intel here.)

---

## 5. Build / run / verify (do this exactly)

- **Tests:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` (exclude the
  mic-bound file). Current: 3045 passed.
- **Web UI:** edit `web/src`, then `cd web && npm run build` (17 pages incl.
  `/workbench`). The bundle is gitignored.
- **Run the hub:** `holdspeak web` (loopback only; **it picks a RANDOM free
  port** and does not reliably print the URL — find it with
  `lsof -nP -iTCP -sTCP:LISTEN | grep -i python` then `curl` for `server: uvicorn`).
  Dictation/meeting capture need mic permission. **A live instance is running now
  at `http://127.0.0.1:59665/`** (background process from this session; stop with
  `pkill -f "holdspeak web"`).
- **Screenshot proofs:** `scripts/screenshot_phase69_*.py` (seed a temp DB + boot
  the real `MeetingWebServer` + Playwright). Pattern: `route`-mock `/api/*` to
  show states without real data.
- **Real-metal intel proof:** `scripts/theater_realmetal_proof.py` (tries `.13`
  then `.43`; needs the sandbox bypass for LAN).

---

## 6. What is NOT done / honest follow-ups

- **The Workbench is read/author only** — you can build + wire a graph, but
  there's no "Run" yet. The natural next epic: POST the `graph_json`/`Workflow`
  to the runtime and drive **run-pulses on the canvas** from the `intel_status` /
  `intel_token` WS frames (the bus + the theater already consume them).
- **The mic waveform's real-mic e2e** isn't exercised (the metal test is
  excluded); the level math is the recorders' existing computation.
- **The egress badge on history/proposal cards** needs a backend egress field
  (skipped by design — no data to show).
- **The Agent Desk** delivers the surface + the real agents + the awaiting link;
  the deeper iPad CompanionBoard **live-session interactions** (select / pin /
  inject into a live coder, which `/api/companion/select|pin|dismiss` already
  back) are a follow-up.
- `evidence-story-09.md` on `main` still carries the at-close "buffered" caveat
  (the historical record); the correction lives in `final-summary.md` + PR #203.
- The **mobile** Equilibrium program (`holdspeak-mobile/EQUILIBRIUM.md`, Phases
  18–23) is a separate track and largely remains.

---

## 7. What I'd do next (suggestions, not orders)

1. **Owner play-walk of the web**, especially `/workbench` (drag, zoom, wire a
   port — green-glow compat — tap to inspect, add from the palette) and the Agent
   Desk at `/companion`.
2. **Make the Workbench runnable** (the run-pulse epic above) — it's the obvious
   next convergence step and reuses the WS bus that's already there.
3. **Stabilise the hub port** (a config/env for a fixed port) so "run it locally"
   has a memorable URL.
4. Reconcile/resume the **mobile Equilibrium** phases if cross-surface contract
   parity is the next priority.

Durable context is in the memory index ([[project_phase69_web_recrafted]] and the
`feedback_*` rules). Read it before acting.
