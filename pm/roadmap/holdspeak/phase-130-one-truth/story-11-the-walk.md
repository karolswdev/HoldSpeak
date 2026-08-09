# HS-130-11 — The walk

- **Project:** holdspeak
- **Phase:** 130
- **Status:** done
- **Depends on:** HS-130-01, HS-130-02, HS-130-03, HS-130-04, HS-130-05, HS-130-06, HS-130-07, HS-130-08, HS-130-09, HS-130-10
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The exit story re-runs the verification methodology against the finished
product and proves the one claim this phase exists to make: **for every run,
readiness, badge, doctor output, and the receipt name the same deployment, and
every placement control states its scope and its inherited source.** It cannot
be closed by unit tests alone and cannot be waived (ORCHESTRATION §The walk).
It is also where the owner's simplicity mandate is judged: can a person answer
"where will this run / what did it use / which setting owns the default"
without knowing the implementation?

### What changes

1. A reusable harness in `scripts/` drives: a `this_machine` run, a named
   on-device run, an Ask run with an explicit target, a Workbench run, and a
   meeting run — capturing readiness, the engine's actual model, the badge, the
   doctor line, and the receipt for each, and **asserting all name the same
   deployment**.
2. **On real metal (.43):** a LAN endpoint run proves `private_network` end to
   end (badge + doctor + receipt), and control-vs-treatment confirms the
   boundary is derived from the executed deployment, not defaulted.
3. **The exfiltration regression** (HS-130-02) is exercised live: a
   punctuation-colliding profile cannot read another's key.
4. **The settings race** (HS-130-07) is exercised: two surfaces, concurrent
   edits, no loss.
5. **Placement provenance:** every placement control (Default / Workbench /
   Run this / Retry) is shown reporting its scope and, when unset, its
   inherited source (HS-130-01).
6. Before/after pairs against the audit evidence (the four egress lies, the
   A/B model split, the double-create) — the phase's before-pictures next to
   its afters, for the owner's sitting.
7. The full check chain (backend suite + web tests + typecheck) captured
   through `dw evidence capture`; the inherited-ledger classification
   (HS-130-10) attached.

## Acceptance criteria

1. For every run family exercised, readiness == executed model == badge ==
   doctor == receipt (deployment identity), proven by the harness with
   assertions, not by inspection.
2. The LAN case reports `private_network` on real metal; no run names a host
   it did not contact; no "Local only" over a mesh route.
3. The credential-collision and settings-race regressions are demonstrably
   closed live.
4. Every placement control shows scope + inherited source; unset never means
   "this device" by accident.
5. The full suites are green or every non-green is accounted for by the
   HS-130-10 ledger with a named home; the reproduction is read from file
   before the flip.
6. The harness is checked into `scripts/` and re-runnable.

## Test plan

- Walk: the `scripts/` harness across the five run families at both the LAN
  and local boundaries; before/after screenshot pairs; assertions captured.
- Metal: .43 for the LAN-boundary and control-vs-treatment legs.
- Full check chain via `dw evidence capture`; ledger attached.

## Out of scope

- Anything kernel-admission (Phase 131) — the walk proves *receipt truth*, not
  *admission*.
- The owner sitting itself (this story produces the exhibit; the sitting is
  the owner's).

## Amendment (2026-08-09, orchestrator — owner may overrule at the sitting)

Two legs were adapted to what this environment can reach; both amendments are
visible here and in the phase decision log:

1. **Live metal (.43) — DONE, and better than chartered.** The `.43` LAN
   endpoint (`http://192.168.1.43:8080/v1`, serving Qwen3.6-35B) was reached
   live and driven through the harness: it classifies **private_network
   end-to-end** — the badge, the DeploymentIdentity boundary, and the receipt
   boundary all agree, `owner=you`, with no fabricated cloud host. Control:
   `api.openai.com` classifies `cloud`. This is the HS-130-04 control-vs-
   treatment proven on real hardware. Output: `assets/hs-130-11/walk-output.txt`.

2. **The live Playwright screenshot-walk (1440+393) — DEFERRED to the owner's
   sitting.** This job has no browser and no built web bundle (`web/dist`
   absent, `playwright` not installed), so the before/after UI shot pairs
   cannot be produced here. The BACKEND/CLI truth the phase exists to establish
   is proven live (19/19 assertions, incl. real `.43`); the reusable harness
   `scripts/walk_one_truth.py` is checked in so the owner runs the whole proof
   with one command (`HS_WALK_LAN=… .venv/bin/python scripts/walk_one_truth.py`).
   The UI screenshot-walk rides the owner's sitting on a machine with the built
   hub, per the standing screenshot-walk rule.

Nothing in the phase's truth claim rests on the deferred leg — placement,
egress, deployment identity, secret slots, and settings versioning are all
asserted live. The screenshot pairs are a presentation artifact, not the proof.
