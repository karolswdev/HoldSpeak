# The Equilibrium — bringing every surface into contract parity

> The program chart. Grounded in [`PARITY-AUDIT-2026-06-27.md`](./PARITY-AUDIT-2026-06-27.md)
> (50-agent flotilla, 22 features, 70 verified gaps, 17 high). Authored 2026-06-27.
>
> **The design layer:** [`EXPERIENCE-VISION-2026-06-27.md`](./EXPERIENCE-VISION-2026-06-27.md) —
> a 16-agent design flotilla reframed these gaps as experiences and designed them masterfully across
> web + iOS (iPad and iPhone as one adaptive app). It is the *how it should feel* to this program's
> *what it must do*; every phase below has a matching per-experience direction there. Build against
> the vision, not the checklist.

## What "equilibrium" means

A feature is in **equilibrium** when its contract is honored on every surface it belongs
to (desktop hub, web flagship, iPad desk, iPhone/compact), with honest `n/a` where a
surface genuinely cannot host it. The desktop hub is the execution and persistence center;
web and iPad are authoring ports; iPhone is the same Apple codebase at compact width.

The audit found the imbalance is not random. It is six systemic patterns. This program is
six phases, one per pattern, sequenced so the load-bearing contracts land before the
surfaces that depend on them.

## The six patterns → six phases

| Phase | Pattern (audit theme) | The one-line goal |
|-------|------------------------|-------------------|
| **18 — The iPad joins the dictation contracts** | The iPad is a tourist for dictation (theme 2/3) | Real Swift clients for the dictation pipeline, voice macros, language, symbols, activity nudges |
| **19 — The iPad joins the meeting contracts** | The iPad is a tourist for meetings (theme 2/3) | Aftercare, faceted archive, import, artifact provenance, proposals review, learning-loop review |
| **20 — One app, every size** | iPhone is layout debt, not capability debt (theme 1) | A real `horizontalSizeClass` pass across every Apple surface, proven on metal |
| **21 — Honest everywhere** | Honesty drift in trust + names (theme 4) | Real egress per primitive, the `.mixed` scope, banned-copy guard, web connector configs |
| **22 — The graph travels** | The Workbench graph cannot leave the iPad (theme 5) | A `graph_json` serializer + Save/sync; the hub honors the graph; web can author one |
| **23 — Mesh-safe storage** | Mobile schema safety lags desktop (theme 6) | iPad refuse-newer + backup-then-apply + a doctor panel; sync integrity |

## Sequencing

```
18 ─┐                      (the iPad earns its dictation client)
19 ─┴─► 20 ─► 21           (then the meeting client; THEN the iPhone size pass over both,
22 ─────────► 23            because you cannot lay out at compact width what does not exist yet)
```

- **18 + 19 lead** and can run in parallel (disjoint client surfaces: `dictation` vs
  `meetings`). They build the missing iPad clients the hub already serves.
- **20 (the iPhone pass) follows 18/19** on purpose. Theme 1's own finding: most iPhone
  gaps are "the same finding twice" (the feature is absent on Apple, so there is nothing to
  lay out). Size-class work over a surface that does not exist is wasted. Build the surface
  in 18/19, then make it reflow in 20.
- **21 (honesty)** can land any time after 18 begins (it touches egress + copy that 18/19
  also pass through); slot it right after the surfaces exist so the badges have something
  real to describe.
- **22 (the graph bridge)** is independent of the iPad-client work; it can run in parallel
  with 18/19. It is the keystone the cross-surface workflow story waits on.
- **23 (schema safety)** is the safety net for everything sync touches; do it before the
  mesh grows more newer-DB peers. Independent; schedule against capacity.

## How this is built

Each phase opens with its `current-phase-status.md` (the why, the design call, the story
table). Story files are authored when a phase opens, per the established cadence — except
the lead phase (**18**), whose stories ship with this chart so the program has an executable
front. Every story carries the audit's `file:symbol` pointers as its starting evidence, so
no story begins from a blank page.

**Standing rules** (carry from the rest of the roadmap and the audit caveats):
- Prove iPad/iPhone work on real metal, not seeded Simulator screenshots
  ([[feedback_verify_on_device_not_seeded]]). Every "size pass" cell stays a forward
  constraint until walked on a device.
- No modals on the desk; edit in-world ([[feedback_no_modals_in_world]]).
- A speak-to-fill mic on every text field ([[feedback_voice_mic_every_input]]) — a
  cross-cutting line carried into each phase's new screens, not a one-off.
- Honest egress badge, never reassurance prose ([[feedback_no_privacy_novels]]).
- The desktop hub is the contract; the audit graded it as a baseline, not independently
  verified — Phase 22 and 23 re-audit the two real hub holes it filed as footnotes (the
  linearizer dropping `failure_policy`/`runs_on`; push-inbox-vs-live-merge sync).

## Not in this program (deliberately deferred)

- On-device journaling / the full learning loop on iPad (Phase 9 territory; 19 ships the
  read-first review client only).
- An iPad wake word and on-device dictation injection into other apps (iOS sandbox `n/a`;
  documented, not built).
- The per-primitive matrix explosion the audit critic recommended (Note/KB/Directory/Agent/
  Chain/Workflow each graded separately) — a chart refinement, folded into 23's sync-integrity
  story rather than its own phase.

## Wave log

Equilibrium gaps land in waves (a build flotilla of worktree-isolated agents, one disjoint
gap each, integrated + full-suite-verified together). Stories stay the canonical unit; the
waves are how the backlog drains in parallel.

### Wave 1 (2026-06-27) — hub + web, 6 gaps

| Gap | Phase | What landed |
|-----|-------|-------------|
| Graph node policy/target | 22 | the linear runner carries + applies per-node `failure_policy` (skip/fallback continue, retry/unset fail fast) + `runs_on`, surfaced in the run steps; honestly documents what the hub does not yet enforce |
| Banned copy + guard | 21 | "intelligent typing" replaced with canonical names in web product copy; the voice guard now scans `web/src/**/*.astro` so a reintroduction fails CI |
| Web connector configs | 21 | the hub reads/writes `companion_webhook_url` + `companion_github_repo` (Slack-parity validation); the web settings page exposes them |
| Sync live-merge | 23 | `POST /api/sync/push` live-merges pushed meeting + artifact content into their real tables (was a JSON inbox), so they are immediately queryable like the other kinds |
| Workflow run signals | 22 | the web run UI surfaces the hub's honest `warning` (ran linear, branches skipped) + the per-node `steps` trail; `primitives.ts` `graphJson` type corrected |
| Intent-timeline + plugin-runs | 19 | the web meeting-detail consumes the two persisted read routes (an intent-timeline strip + a plugin-run table) that had no consumer |

Integrated + verified together: full Python suite **2924 passed**, web build green.

### Wave 2 (2026-06-27) — finish the honesty ban + more web, 4 gaps

| Gap | Phase | What landed |
|-----|-------|-------------|
| Rename the guide + global ban | 21 | `docs/INTELLIGENT_TYPING_GUIDE.md` → `DICTATION_PIPELINE_GUIDE.md` (all refs + the verbatim test updated); `_BANNED_NAMES_DOCS` collapsed back so "intelligent typing" is now banned EVERYWHERE (docs + web). Closes the Wave 1 follow-up. |
| Web proposals egress | 19 | the proposals review surface already existed (Phase 37); the real gap was its egress being a guard SENTENCE, replaced with the structured egress badge ({scope,label}) per canon |
| Web linear graph builder | 22 | the web Desk authors a real minimal LINEAR `graph_json` (was hardcoded `{}`), in the exact shape `workflow_graph.linearize()` + the iPad Blueprint speak, so a web-authored chain round-trips |
| Web ambient trust chip | 21 | an ambient egress/trust chip + a readiness line from `/api/setup/status` on the web Desk (reusing the egress component, never prose) |
| Index page null-guard (bonus) | 21 | a pre-existing latent bug the integrated preflight caught: `index.astro` route-preview `x-text` read `routePreview.active_intents` un-guarded and threw on load when null; fixed with optional chaining (CI skips this e2e without Chromium, so it had hidden) |

Integrated + verified together: full Python suite green (route-preflight included, locally with Chromium), web build green. Cherry-pick note: the graph-builder + trust-chip both edited `desk.*` but git auto-merged them (additive, different regions).

See [[project_primitive_framework]], [[project_phase15_the_mesh]], [[project_phase17_agent_sync]].
