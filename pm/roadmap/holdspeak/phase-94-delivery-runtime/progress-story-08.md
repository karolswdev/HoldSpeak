# HS-94-08 progress record — Delivery work inhabits the Web Desk

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (the owner-observed
north-star walk is BACKLOG candidate Y; every invariant and the
production walk are machine-verified).

## What shipped

- `web/src/desk/delivery.ts`: a read-model projection store that holds NO
  authority — association/target/policy/grant/status all come from the
  server snapshot; the only persisted state is a view-focus preference.
  A heuristic association is coerced to exact:false; unknown source status
  to unavailable; economical ETag/304 polling keeps the last coherent frame.
- Delivery objects render through the existing Desk grammar: a Delivery
  board window lists Sources (freshness chip + per-state recovery),
  Projects/Phases (dossier buttons), current Stories, Active work (attempts
  naming Story/association/node/branch/worktree/lifecycle/freshness/target),
  and discovered Coder-session targets, with a voice-fillable Launch
  composer showing destination + consequence. Story and Phase dossiers open
  in a desk window (no route change) with pass/fail captured runs and
  manifest-bound asset links. Delivery rows join the HS-93-08 semantic List
  view.
- The terminal window subscribes by the server-issued immutable target
  (target_id + generation); an open target cannot be reinterpreted (no
  setter exists); commands carry no authority/policy block (the hub derives
  them); a different node/worktree is a different target/subscription.
- Freshness/recovery states (stale/offline/incompatible/unauthorized/
  unavailable and the terminal absences) each render a distinct,
  non-fabricated affordance. The belt keeps working via a compat projection.

## Verification

19 new Vitest cases (no-authority, immutable-target no-reinterpret,
authority-free commands, freshness distinctness, list inclusion, ETag
economy, belt compat); full Web gate green (architecture guard 130 sources,
typecheck, 38 files / 217 tests, build); desk source-lock/copy 15 passed. The
production evidence runner registers this repo as a live Source and drives
board → attempt → dossier-in-window → immutable-target terminal (live 200
subscription) plus an iPad-width pass with zero failed API responses; the
board renders HS-94-08's OWN Work attempt as an exact starting attempt.
Captured at close in [evidence-story-08](./evidence-story-08.md).
