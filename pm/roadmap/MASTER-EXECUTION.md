# Master Execution List — The Mesh + Web Convergence

**Orchestrator-owned.** This is the single source of truth for executing **Phase 15 (The Mesh,
mobile)** and **Phase 68 (Web Convergence, desktop)**, including the newly-added **Agent Desk**
pillar. The orchestrator owns this file, sequences the work, dispatches **Opus 4.8** subagents on
ready units, and integrates + commits their output under the PMO gate. Updated 2026-06-22.

---

## 0. Pick this up from scratch — read order (do this first)

1. **`CLAUDE.md`** (repo root) — the working agreement: the PMO pre-commit gate, source canon, test
   commands. Non-negotiable.
2. **The two roadmaps:**
   - Desktop: `pm/roadmap/holdspeak/README.md` + `phase-68-web-convergence/current-phase-status.md`.
   - Mobile: `pm/roadmap/holdspeak-mobile/README.md` + `phase-15-the-mesh/current-phase-status.md`
     + the mobile `HANDOVER-2026-06-22-craft.md` (build/deploy/show loop, gotchas).
3. **Source canon** (`docs/internal/`): `POSITIONING.md` (one copilot, two modes; the egress badge,
   **no privacy novels**; honest named-competitor voice), `PLAN_PHASE_DICTATION_INTENT_ROUTING.md`,
   `PLAN_PHASE_MULTI_INTENT_ROUTING.md`, `docs/ARCHITECTURE.md`.
4. **The grounding** (already done; §2 below summarizes) — read it before assuming anything. The hard
   lesson that created this whole effort: **read what each platform already does before planning new
   work. A lot of it is already there.**

---

## 1. The PMO process every unit follows (no exceptions)

- **Commit gate.** Before every commit, write `.tmp/CONTRACT.md` per `pm/roadmap/PMO-CONTRACT.md`,
  honestly check every box, then commit (the pre-commit hook validates + deletes it). A stale or
  unchecked contract is rejected. **The orchestrator owns the contract** (it attests to *verified*
  work) — subagents implement + test; the orchestrator verifies, fills the contract, and commits.
- **Operating cadence (every shipping commit):** update the story header status, the phase's
  `current-phase-status.md` (story-status row + "Where we are"), the roadmap README "Last updated",
  and any canon doc the story touches.
- **Tests are real.** Run the relevant tests and read the output before flipping a story to done.
  Desktop: `uv run pytest -q` (exclude `tests/e2e/test_metal.py` — it hangs without a mic). Mobile:
  `swift test` from `apple/` (UI is proven by Simulator screenshots + live on the iPad, not unit
  tests). Type-check is **not** validation.
- **Show it.** Mobile UI work is proven with committed **Simulator screenshots** AND installed live
  on the iPad. Backend/plumbing is not a deliverable; the felt product is.
- **Proof on real metal.** LLM-shaped behavior is proven against the real `.43` endpoint / a real
  agent in tmux, not a no-LLM plumbing pass (a plumbing pass can hide a silently-broken feature).
- **Voice guard.** Shipped `docs/*.md` + README forbid prose-dashes / AI-vocab / HS-IDs. Keep HS-IDs
  in `pm/roadmap/` files only. Roadmap files themselves are not voice-guarded.
- **Commit footer.** Desktop (`holdspeak`): **no** `Co-Authored-By`. Mobile (`apple/`): the footer in
  the mobile HANDOVER is authorized by the hook. Phases close via **PR to main** when CI is green.
- **Design bar (owner, termination-level):** premium/native/"oozes awesomeness"; no prose in the
  product (the egress badge, tight chips — never narration); PixelLab for bespoke assets; deliver,
  don't checkpoint; the mesh **never acts without the user's nod**; the headline proof is air-gapped.
- **Load-bearing principle — the iPad is a full peer, never a thin client.** On-device is first-class
  and **complete**: capture, transcription, intelligence, AND **every Workbench workflow** run locally,
  air-gapped (flight mode → meeting → heaven). The mesh (Your Mac / endpoint / the Agent Desk) is
  **additive, never a dependency**; default `RUNS ON` is on-device; mesh-only actions degrade honestly
  offline and never block the local core. Every Phase-15 build unit is checked against this.

---

## 2. The grounded picture (exists vs. genuine deltas)

**Desktop already ships (reuse, do not reinvent):** the dictation pipeline (DIR-01) +
`POST /api/dictation/remote` → `_deliver_remote_dictation` → `tmux send-keys` / `TextTyper`
(`runtime/dictation_capture.py`, `tmux_transport.py`); the **agent-hook loop** (the coder reports its
own pane + question via `agent_context/sessions.py` + `hooks.py`; `awaiting_response`,
`last_assistant_text`); `GET /api/companion/status` + select/pin/dismiss (`web/routes/system.py`); the
**one** actuator approval/egress contract (`plugins/actuator_executor.py` 5-gate +
`web/routes/meetings.py`); two job queues (`activity/plugin_jobs.py`, `intel_queue.py`); OpenAI-compatible
LLM seams (`intel/engine.py`, `intel/providers.py`; `.43` = `provider=cloud` + `meeting.intel_cloud_base_url`).

**Web already ships:** Astro + Alpine + vanilla ES modules, built `cd web && npm run build` →
`holdspeak/static/_built/` (gitignored), served by `web/routes/pages.py`. A **mature "Signal" token
system** (`web/src/styles/tokens.css`, Phase 30) — same accent `#FF6B35`, top-lit hairlines, settle
motion — **under-applied**. Broad surfaces (`/`, `/history`, `/dictation`, `/settings`, `/activity`,
`/commands`, `/companion`, `/welcome`, `/setup`, `/presence`). Live WS streaming + Qlippy (stranded on
`/presence`) + the egress badge.

**Genuine deltas (the actual new work):** (1) free-typing remote-dictation target (deliver to a
focused Mac app without an awaiting agent session); (2) a generic "run a capability on your Mac &
return the result" RPC; (3) one aggregated in-flight + pending-approval inbox; (4) decouple the
approval ledger from `meeting_id`; (5) **the Agent Desk + proactive presence** (surface, not plumbing
— the hook loop + `/api/companion/status` exist); (6) the iPad flagship surfaces; (7) the web pattern
ports (node canvas, Queue HUD, generation theater, Qlippy-in-cockpit, the motion pass); (8) the
air-gapped Proof.

---

## 3. The work units

Type: **D**=design/research doc · **B**=build · **P**=proof · **X**=docs. Owner: **O**=orchestrator ·
**A**=Opus-4.8 subagent (orchestrator integrates + commits).

| Unit | Title | Type | Where to look | Depends on | Proof | Owner |
|------|-------|------|---------------|------------|-------|-------|
| HS-68-01 | Cross-platform design-pattern catalog | D | `apple/App/MeetingCaptureApp.swift`; `web/src/styles/tokens.css` + `components/` | — | traced doc, both sides | A |
| HS-68-02 | Two-way parity map + ordered delivery backlog | D | both UIs; §2 grounding | HS-68-01 | the backlog → scaffolds Phase 69 | A |
| HS-68-03 | Web technical design (node canvas / Queue HUD / theater / Qlippy-in-cockpit / motion) in Astro+Alpine+vanilla | D | `web/src/`, `web/astro.config.mjs` | HS-68-01 | a de-risked build approach | A |
| HSM-15-04 | One mesh runner — pure `WorkflowRunner` (on-device/endpoint path; Your-Mac dispatch behind the seam) | B | `apple/Sources/RuntimeCore/Workbench/`; the Workbench graph model in `MeetingCaptureApp.swift` | — | `swift test` green | A |
| HSM-15-01a | Desktop free-typing dictation target (deliver to focused app w/o an awaiting agent) | B | `runtime/dictation_capture.py`, `web/routes/dictation/pipeline.py`, `typer.py` | — | `uv run pytest` + LAN | A |
| HSM-15-01b | iPad dictation flagship surface (over `/api/dictation/remote`) | B | `apple/App/MeetingCaptureApp.swift`; `HTTPDesktopClient` | HSM-15-01a | Simulator + LAN trace | O+A |
| HSM-15-08 | The Agent Desk (surface over `/api/companion/*`) | B | `apple/App/…`; `web/src/pages/companion.astro` | HSM-15-04n/a | Simulator + LAN | O+A |
| HSM-15-09 | Proactive agent presence (watcher + HUD lane + nudge + notify) | B | the Phase-15 `QueueHUD`/`RunQueueStore`; `/api/companion/status` | HSM-15-08 | Simulator + LAN | A |
| HSM-15-02/03/05 | Workbench mesh targets · mesh queue · approval-ledger decouple | B | §2 deltas 2/3/4 | a "run capability" RPC | LAN | O+A |
| HSM-15-06 | The air-gapped Proof + launch narrative | P | the whole mesh | most of 15 | owner-driven session | O |
| HSM-15-07 / HS-68 docs | Docs catch-up (both) | X | READMEs, getting-started | features land | voice guard green | A |
| Phase 69 | Web delivery (the ports) | B | from HS-68-02 backlog | HS-68-02/03 | per-story | A |

---

## 4. Waves (sequence)

- **Wave 1 (ready now, parallel, no cross-deps):**
  - **HS-68-01** — the design-pattern catalog (doc). → Opus 4.8 agent.
  - **HSM-15-04** — the pure `WorkflowRunner` + host tests (RuntimeCore; no UI, no device — the
    cleanest possible delegate). → Opus 4.8 agent.
- **Wave 2 (after wave 1):** HS-68-02 (parity map, needs the catalog) + HS-68-03 (web tech design,
  needs the catalog) + HSM-15-01a (desktop free-typing delta) — all parallel.
- **Wave 3:** HSM-15-01b (iPad dictation surface, needs 01a) + HSM-15-08 (Agent Desk) + scaffold
  Phase 69 from HS-68-02's backlog.
- **Wave 4:** HSM-15-09 (proactive presence), the web ports (Phase 69), the mesh deltas (02/03/05).
- **Wave 5:** docs (15-07, 68 docs) → the air-gapped Proof (15-06, owner-driven) → close via PR.

---

## 5. Dispatch protocol (how the orchestrator runs each agent)

- **Model:** every implementation/design subagent is **Opus 4.8** (`model: "opus"`).
- **Brief template (stellar, from-scratch):** every dispatch includes — the repo + working dir; the
  read-order (§0); the **grounded facts** relevant to the unit (§2, with file:line); exactly **where to
  look**; the **acceptance + the proof required**; the **PMO constraints** (§1) that apply; and an
  explicit **"do NOT commit — implement, run the tests, write the deliverable file(s), and return a
  precise summary (files changed, test output, open questions) for orchestrator review."** The
  orchestrator integrates, verifies, fills `.tmp/CONTRACT.md`, and commits.
- **Output discipline:** design agents write their doc into the **phase dir** (not `docs/*.md` — avoids
  the voice guard until the orchestrator promotes it). Build agents implement + run tests + report;
  they do not touch the roadmap status files (the orchestrator does, per the cadence).
- **Integration loop:** orchestrator reviews each return against the acceptance + the design bar,
  reconciles cross-unit decisions, updates the roadmap, and commits. Failures/uncertainty come back as
  the next unit, not a silent pass.

---

## 6. Live status

- **2026-06-22 — list created; Agent Desk pillar scoped into Phase 15 (HSM-15-08/09); Phase 68 opened.**
- **2026-06-22 — WAVE 1 COMPLETE + integrated (both Opus 4.8, orchestrator-verified).**
  - **HSM-15-04** — the pure `WorkflowRunner` is built (`apple/Sources/RuntimeCore/Workbench/`):
    on-device/endpoint via injected `ILLMProvider`, `{input}` substitution, `keepIf` pure filter, a new
    `FailurePolicy` (retry→park / fallback / skip) with injectable backoff + resume-from-cache; the
    `dispatchToMac` seam stubbed (additive). Aligns with the iPad-full-peer principle (on-device by
    default). `swift test` re-run by orchestrator: **250 / 6 skipped / 0 failures.** Not committed.
  - **HS-68-01** — the design-pattern catalog is authored
    (`phase-68-web-convergence/design-pattern-catalog.md`): 9 patterns mapped, foundation byte-identical,
    port-priorities set. **Open owner decision:** the status palette diverged (iPad vs web) — catalog
    recommends web-wins (WCAG). Not committed.
- **2026-06-22 — palette decision: WEB-WINS** (owner-approved). The web status colors
  (`ok #34D399 / warn #FBBF24 / danger #F87171 / info #56C7F5`) are canonical for both platforms; the
  iPad re-tunes `Sig.ok/warn/bad/local` to match — a small follow-up unit on the MOBILE roadmap
  (**MOBILE-RETUNE-PALETTE**, not yet scheduled). Recorded in the Phase 68 status.
- **2026-06-22 — WAVE 2 dispatched (both Opus 4.8, background):** HS-68-02 (two-way parity map +
  ordered Phase-69 backlog) + HS-68-03 (web technical design for the marquee patterns). Both honor
  web-wins + the iPad-full-peer principle.
  - **HS-68-02 DONE + integrated** (`parity-map.md`): **11 ordered Phase-69 stories** (HS-69-01…11,
    egress-badge first → node-canvas epic last) + the iPad-gains-breadth list for the mobile roadmap.
    **Two owner-calls surfaced:** (a) companion-portal direction; (b) whether the web needs the full
    node canvas vs a lighter pipeline view (HS-68-03 informs this). Held for owner.
  - **HS-68-03 DONE + integrated** (`web-technical-design.md`): per-pattern build approach in the
    Astro+Alpine+vanilla stack. **Design foundations are now COMPLETE** (catalog + parity map + tech
    design). Orchestrator decisions recorded (owner may override): node canvas = pure-vanilla SVG,
    linear-renderer-first (resolves the full-canvas-vs-pipeline-view owner-call — they converge);
    waveform = a small server `audio_level` WS frame; Queue HUD = derived from existing WS frames via
    a shared `runtime-bus.js`. Substrate-first order: `.signal-card` + tokens + `hs-materialize` first.
- **2026-06-22 — owner green-light ("yeas").** Companion-portal decision: web `/companion` **becomes
  the Agent Desk** (added as HS-69-12). **Phase 68 design foundations COMPLETE** (catalog + parity map
  + tech design) and **Phase 69 — Web, Re-crafted** scaffolded (`phase-69-web-recrafted/`, 12 stories,
  substrate-first) → Phase 68's last exit criterion met; Phase 68 ready to close (via PR).
- **2026-06-22 — WAVE 3 dispatched (Opus 4.8, background):** the web Signal **substrate**
  (HS-69-02 `.signal-card` primitive + HS-69-03 gradient/hairline tokens + HS-69-04 `hs-materialize`
  motion) — additive CSS that lifts every surface; agent build-verifies (`npm run build` + global-scope
  check), orchestrator does the visual before/after screenshots + commit. Next after integration:
  HS-69-01 (egress badge → cockpit) + the surface ports, then the node canvas last; and the first iPad
  mesh surface (Agent Desk HSM-15-08 / dictation HSM-15-01b).
- **2026-06-22 — WAVE 3 integrated + visually verified.** Web Signal substrate shipped
  (`.signal-card` primitive + gradient/hairline tokens + `hs-materialize`); `npm run build` green,
  global-scoped. Orchestrator ran `holdspeak web` locally + headless-chromium-shot the settings panel
  → confirmed it renders as a raised signal-card. **The web show-it loop is proven** (run server →
  headless chromium → verify). Phase 69 HS-69-02/03 done, HS-69-04 built (visual pending seeded data).
- **2026-06-22 — WAVE 4 dispatched (3 Opus 4.8 agents, parallel, non-colliding codebases):**
  - **HS-69-01** (web/src) — egress badge → the cockpit cards (reuse the existing `{scope,label}` badge
    stranded on `/presence`).
  - **HSM-15-08** (apple/) — the iPad Agent Desk surface + a `HS_DEMO_AGENTDESK` sim seed + a committed
    Simulator screenshot.
  - **HSM-15-01a** (holdspeak/) — the desktop free-typing dictation target (`target: focused`) + pytest;
    the "answer the coder" path stays byte-identical.
  Orchestrator integrates + screenshot/test-verifies each on return, then keeps rolling the backlog
  (HS-69-05/06/07 web; HSM-15-09 presence; HSM-15-01b iPad dictation surface).
- **2026-06-22 — WAVE 4/5 integrated (all Opus 4.8, verified):**
  - **HS-69-01** egress badge → cockpit (built, dashboard intel card; honest-skip where no egress data).
  - **HS-69-07** web Queue HUD (built; caught live — the "1 working" pill on the seeded cockpit).
  - **HSM-15-08** the iPad Agent Desk (built + Simulator-proven, `agentdesk.png`).
  - **HSM-15-01a** desktop free-typing dictation (`target_mode:focused`; 18/18 + 372 sweep, re-verified).
  - **HSM-15-04 wiring — THE WORKBENCH NOW EXECUTES on the iPad** (`PatchModel.lowerToWorkflow()` →
    `WorkflowRunner` on-device; canvas nodes light + Queue HUD shows live `StepOutcome` jobs;
    Simulator-proven `wb-exec.png`). The masterful builder is a working engine.
  - Integration fix: `FailurePolicy` unified into RuntimeCore (was colliding); iPad build green.
  - **A reusable web screenshot harness** built (isolated-HOME seeded instance + headless chromium) —
    the web show-it loop is now on tap.
- **2026-06-22 — WAVE 6 dispatched:** HSM-15-01b (the iPad "Dictate to your Mac" surface, over the
  built 01a delta). Then: Agent Desk live wiring, proactive presence (15-09), the mesh-inbox, more web.
- **2026-06-22 — WAVE 6/7 integrated (all Opus 4.8, verified):** HSM-15-01b iPad dictation surface
  (`dictate-surface.png`, suite 250/6/0); HSM-15-09 proactive presence (`presence-hud-lane.png`, 7
  watcher tests + 83 ProvidersTests); HSM-15-10 the Connect place END-TO-END — desktop advertises
  `_holdspeak._tcp` + `/api/mesh/info` (12 + 2205 tests), iPad `ConnectView` Bonjour discovery + pair
  (`connect-surface.png`). Integration fix carried: `FailurePolicy` unified into RuntimeCore.
  Fully-integrated iPad tree: `gen && swift test` exit 0.
- **MILESTONE: the Mesh forward map is essentially realized on the iPad** — Workbench executes ·
  Agent Desk · proactive presence · dictation surface · the Connect place · Queue HUD (+ web: substrate,
  egress badge, Queue HUD). Remaining: live-on-metal proofs (real agent/Mac over LAN — owner-gated),
  the mesh-inbox + pairing-code slices, and the rest of the web ports (HS-69-05/06/08/09/10/11).
- **READY TO COMMIT (the clean checkpoint).** Proposed per-area branch + commits, all verified green:
  (1) `apple/` engine+surfaces (runner, executing Workbench, Agent Desk, presence, dictation, Connect,
  FailurePolicy unify); (2) `holdspeak/` (free-typing dictation `target_mode`, mesh Bonjour+`/api/mesh/info`);
  (3) `web/` (Signal substrate, egress badge, Queue HUD); (4) `pm/roadmap/` (Phases 15/68/69 + master list).
  Awaiting the owner's word.

- 2026-07-04 — holdspeak Phase 82 (Mission Control — the Desk conveyor) OPENED 0/5: the
  Delivery Workbench counterpart phase (their Phase 13 substrate is shipped; their WLA-13-05
  joint exit exam waits on HS-82-05). Bridge → belt → live layer → approval leg, all consuming
  the three frozen documents per their docs/mission-control.md §5.
