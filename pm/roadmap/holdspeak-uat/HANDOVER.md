# HANDOVER — Build the HoldSpeak UAT Framework (overnight, autonomous)

> **Historical specification:** This document preserves the framework-build
> brief as executed. Its web/iPad/iPhone “three surfaces” model is superseded by
> protocol v2 in `uat/CHARTER.md`: implementation target and form factor are
> separate, responsive React is never Swift evidence, and parity joins
> independently executed target-specific legs.

> **You are the next agent. This is your goal, not a suggestion.** Read this
> whole file, then the linked roadmap, then start building. You are expected to
> **design, dig deeper, plan, and EXECUTE** — end to end, unattended, through
> the PMO gate — and to leave a *running web-based UAT framework* behind you.
> The owner is asleep. They will wake up, run one command, and sit through a
> real UAT of HoldSpeak. Make that true.

---

## 1. THE GOAL (the thing the owner wakes up to)

A **web-based UAT framework** that puts HoldSpeak through its paces and captures
per-step human feedback. Concretely, when the owner wakes up, this must work:

```bash
cd /Users/karol/dev/tools/HoldSpeak
uv run python -m uat.conductor          # serves the guided UAT site on a pinned local port
```

They open the site in a browser and:

1. **Pick a pack** (start with the smoke pack; real scenario packs exist too).
2. The rig **stages the world** in front of them — boots an *isolated* HoldSpeak
   under its own HOME, applies a config deck, induces a named state (a seeded
   desk, a just-ended meeting, a dead endpoint), and shows the staging succeed
   honestly (or fail with the log tail — never a spinner).
3. They **walk the pack beat by beat** — each beat says *do this*, *expect this*;
   an "Open the product" button deep-links to the right screen; they cast a
   **verdict per surface** (pass / fail / partial / skip), jot a note, drop a
   screenshot.
4. At the end they get a **debrief** — a per-surface score, coverage against the
   feature ledger, and every non-pass finding with its note, screenshot, and a
   **slice of the product's own log** around that moment.
5. They (with an agent later) **triage** the findings into fix / won't-fix /
   by-design, and the `fix`es become `pm/roadmap/holdspeak/BACKLOG.md` rows.

**That is done.** If the owner can do all five of those against the real product
on the web surface, you have delivered the framework. Everything below is how to
get there and how far to push.

### The bar, stated plainly
- It **runs** (not a plan, not scaffolding — a program that boots and guides).
- It **stages real state** and verifies it through the product's own routes.
- It puts the **real application** through its paces (real scenarios from the
  Phase-3 plan, not just plumbing checks).
- It **captures feedback** durably (per-surface verdicts + notes + shots in a DB).
- It **produces a debrief** the owner and an agent can act on.
- It is **honest** — no faked sittings, no green-washing, device legs it cannot
  prove are marked pending, not pretended.

---

## 2. WHAT ALREADY EXISTS — read in this order, do not redo

The design and inventory are **done**. You are executing a specified thing, not
inventing one. Read:

1. **[`README.md`](./README.md)** — the project: four principles (harness stands
   outside the product; coverage enumerated not remembered; three surfaces =
   web desk / iPad / iPhone are the claimed parity set; states are induced by
   idempotent recipes with verify probes). Glossary of every term you'll use.
2. **[`phase-1-the-mechanics/`](./phase-1-the-mechanics/)** — **this is your
   build spec.** Six stories, each a full scope + acceptance criteria + test
   plan:
   - `story-01-the-conductor.md` — the standalone process, isolated runs, LAN
     reachability, logs, restart-with-a-different-deck. **Subprocess-only: the
     conductor must never import the `holdspeak` package (grep-enforced).**
   - `story-02-the-induction-engine.md` — decks, seed manifests, **state recipes
     with verify probes + idempotency**.
   - `story-03-scenario-contract-and-coverage.md` — the scenario YAML contract,
     the surface axis, `uat/features.yaml`, coverage math, the smoke pack.
   - `story-04-the-guided-site.md` — the React+Vite walkthrough, per-(step,
     surface) verdicts, crash-safe resume, usable from a device browser.
   - `story-05-the-debrief.md` — the packet (md+json, per-surface scores, log
     slices), findings lifecycle, `uat/TRIAGE.md`, the BACKLOG feed.
   - `story-06-docs-and-first-sitting.md` — `uat/README.md` + `uat/AUTHORING.md`,
     dogfood supersession, and the closing sitting (**owner-gated — see §6**).
3. **[`phase-2-the-inventory/directory/`](./phase-2-the-inventory/directory/)** —
   **the 255-capability directory** (input & intelligence, meetings,
   desk/mesh/agents, trust/egress), each row with per-surface applicability,
   needed recipes, priority, phases. This is your scenario source material.
   `_raw-inventory-rows.json` is the machine-readable form.
4. **[`phase-2-the-inventory/PROTOCOL-NOTION.md`](./phase-2-the-inventory/PROTOCOL-NOTION.md)**
   — **how a sitting is shaped** (beat spine, control-vs-treatment, honest-failure
   close, structural verdicts, per-surface capture). Build the site and the
   scenarios to this shape.
5. **[`phase-2-the-inventory/RECIPE-WORKLIST.md`](./phase-2-the-inventory/RECIPE-WORKLIST.md)**
   — **the recipes to build, ranked by demand** (`seeded-desk` ×125,
   `mesh-node-alive` ×48, `meeting-just-ended-open-actions` ×37, …). Build the
   top ~8; the long tail is later.
6. **[`phase-2-the-inventory/PHASE-3-PLAN.md`](./phase-2-the-inventory/PHASE-3-PLAN.md)**
   — **the five coverage packs** (Aftercare / Steering / Dictation Grounding /
   Honest Failure / Mesh Edge), grouped by shared staged world. Author real
   scenarios from these — see §5.

---

## 3. THE SOURCE SEAMS YOU'LL BUILD ON (don't re-discover these)

The harness drives the product through its existing surface. Verified pointers:

- **Boot the product**: `holdspeak web --no-open` (entry `holdspeak/main.py`;
  web runtime `holdspeak/web_runtime.py`). Pin the port with `HOLDSPEAK_WEB_PORT`;
  bind LAN with `HOLDSPEAK_WEB_HOST=0.0.0.0` (rides the Phase-25 non-loopback
  auth-token guard — the run gets its own token per HOME via
  `holdspeak/web_auth.py`).
- **Route registration pattern** (if you ever need to read how the product wires
  routes): `holdspeak/web_server.py` `app.include_router(build_*_router(ctx))`;
  route modules under `holdspeak/web/routes/`. **You do not add routes to the
  product** — the conductor is separate code under `uat/`.
- **Seed through public routes**: `/api/desk/*` (notes, KB, recipes — under
  `holdspeak/web/routes/primitives/`), transcript/audio import under
  `holdspeak/web/routes/meetings.py` (Phase-55/57 import seam). A seeded object
  must be indistinguishable from a user-made one.
- **Config**: `holdspeak/config.py` — `Config.load(path)` / `.save()`. A **deck**
  is a sparse overlay you merge over defaults and write as the run HOME's
  `config.json` before boot. Round-trip every deck through `Config.load` in a
  test so it can't rot.
- **Isolated HOME substrate**: `dogfood/` — `setup.sh`, `env.sh`, `_home/`,
  `make_fixtures.py`, committed transcripts under `dogfood/transcripts/`, three
  mock repos with `.hs/` context under `dogfood/repos/`. **Reuse this** (the
  project supersedes dogfood — see §6). The `.43` wiring lives here too.
- **The walks to mimic**: `scripts/walk_hs85_live.py`, `scripts/rails_walk_hs88.py`,
  `tests/e2e/test_spoken_meeting_e2e.py`, and `HSM-16-06-WALK.md` — the staging
  preambles and beat structure you're productizing. Read at least one before
  writing the recipe layer.
- **Doctor / health**: `holdspeak doctor` (`holdspeak/commands/doctor.py`) — your
  honest health probe for `intel-endpoint-dead` / `no-model` recipes.
- **The LAN LLM**: `.43` = `http://192.168.1.43:8080` (llama.cpp). Needed for
  `golden-43` and any recipe that produces real intel output. **The sandboxed
  Bash tool cannot reach the LAN — use `dangerouslyDisableSandbox: true` for any
  `curl`/run that must hit `.43`.** If `.43` is down, fall back to the fully-local
  recipes and say so; do not block the whole build on it.

---

## 4. BUILD ORDER — slice first, then broaden (always keep it running)

Do **not** build all six stories to completion in order and only integrate at the
end. Get one thin thing end-to-end working first, prove it, then widen. Suggested
execution:

**Slice 0 — the walking skeleton (highest priority).** The smallest thing that is
the whole loop: conductor boots one isolated `golden-local` run → applies
`seeded-desk` and verifies its probe → serves a 3-beat hardcoded scenario → the
site casts one web verdict per beat into a sqlite run DB → a minimal debrief.md
drops out. When this works and is merged, the framework *exists* and everything
after is breadth. Prove it with an integration test that drives the whole loop.

**Then widen, roughly along the stories:**
- HSU-1-01 to full: log capture, restart-with-deck, teardown (no orphans),
  LAN-bind + pairing facts, the no-import grep test.
- HSU-1-02: the five decks (incl. `bad-endpoint`, `no-model`), the top ~8 recipes
  from the worklist with verify probes + idempotency, local `mesh serve` spawn/kill.
- HSU-1-03: the real scenario contract + loader + validation + the surface axis;
  `uat/features.yaml` seeded **from the directory's `_raw-inventory-rows.json`**;
  coverage math; the smoke pack.
- HSU-1-04: the real React+Vite site — per-(step,surface) verdicts, notes,
  screenshots, crash-safe resume, staging view with log tail, device-browser
  reachable.
- HSU-1-05: the debrief packet (per-surface scores, log slices), findings +
  triage states, `uat/TRIAGE.md`, the BACKLOG-block generator.
- HSU-1-06: `uat/README.md` (with the **owner wake-up runbook** at the top),
  `uat/AUTHORING.md`, dogfood supersession pointer.

**Each story ships as its own PR through the PMO gate, merged on green CI**
(§7). Flip its story status + evidence in the same commit. Update
`phase-1-the-mechanics/current-phase-status.md` and the project README per the
operating cadence.

---

## 5. PUT THE APPLICATION THROUGH ITS PACES (real scenarios, not just plumbing)

The owner said "put the application through the paces." A rig with only a smoke
pack does not do that. After the engine works, **author real scenario packs from
[`PHASE-3-PLAN.md`](./phase-2-the-inventory/PHASE-3-PLAN.md)**, web-surface legs
first (device legs get `n/a`/pending — §6). Priority order for overnight:

1. **Pack D — Honest Failure & Trust** first: it is **fully local** (needs no
   `.43`), must-test-heavy, and proves the product is honest when broken — the
   highest-value, lowest-dependency pack.
2. **Pack C — Dictation Grounding** and **Pack A — Meeting Aftercare**: these
   need `.43`; author them, run their web legs if `.43` is up, mark
   `.43`-blocked beats clearly if not.
3. **Pack B (Steering)** and **Pack E (Mesh Edge)**: need tmux / a second worker;
   author them, stage what you can locally, mark the rest pending.

Author scenarios to the **PROTOCOL-NOTION** shape: every pack opens with a
staging-verify beat and closes with an honest-failure or control-vs-treatment
beat. **No pack is all-green-happy-path.**

---

## 6. HONEST BOUNDARIES — what you CAN and CANNOT finish overnight

Be ruthless about this. The framework's whole ethic is resistance to
self-deception; do not violate it to look finished.

**You CAN and MUST fully deliver:**
- The entire engine (conductor, decks, recipes, contract, site, debrief).
- The **web surface** loop, proven end to end by integration tests **and** a
  Playwright drive of the real site. Verdicts you cast in those tests are
  **harness self-tests, clearly labelled as such — they are NOT a sitting.**
- Real scenario packs (§5) with their web legs runnable.

**You CANNOT finish (leave staged + clearly marked pending):**
- **A real human sitting.** Only the owner sits. Do not fabricate human verdicts
  to close HSU-1-06's sitting; that story's live sitting is the owner's, at their
  desk. Build everything up to the sitting and stop at the sitting.
- **Physical iPad / iPhone verdicts.** You have no device in hand and cannot cast
  a device verdict. **Build the device legs anyway** (LAN reachability, per-surface
  verdict slots, `n/a`-with-reason where a surface lacks a capability) so the
  owner can extend to the phone/iPad when they sit — but every device-surface
  verdict starts unanswered, never faked.
- **The formal Phase-2 device verification + joint ranking.** The directory is a
  model's reading of the record. Use it as scenario source, but do not mark the
  Phase-2 sweeps `done` — that needs the owner on real glass.
- **Anything `.43` if the LAN is unreachable from where you run.** Degrade to
  local recipes, log the gap.

**When you hit a real fork you cannot resolve reversibly**, pick the sensible
default, record the decision in `current-phase-status.md` "Decisions made", and
keep moving. Do not stop and wait — the owner is asleep.

---

## 7. THE AUTONOMY CONTRACT (how to work unattended without breaking main)

- **PMO gate every commit.** Stage → `.githooks/dw contract new` → honestly flip
  every box → `git commit`. Never `--no-verify`. Roadmap-status commits and code
  commits both pass the gate. (`CLAUDE.md` has the full contract.)
- **One story per PR.** Branch, build, test, push, open PR, **watch CI**
  (`gh pr checks <n> --watch`), **merge only on green**, pull main, next story.
- **Commit footer (holdspeak desktop):** NO `Co-Authored-By`. End commits with the
  `Claude-Session:` line. PR bodies end with the Generated-with line. (See the
  repo's git rules.)
- **Tests are real.** `uv run pytest -q`; put UAT tests under `tests/uat/`. Read
  the output before flipping a story done. Exclude `tests/e2e/test_metal.py`
  (hangs without a mic). Type-check is not validation.
- **Watch the api-surface guard.** If you ever touch product routes/consumers,
  regenerate: `uv run python scripts/gen_api_surface.py` (this exact test left
  main red twice this week). The `uat/` conductor is separate code, so it should
  not trip it — but if you add anything the guard scans, regenerate.
- **`uv run` works**; the toolchain is uv-managed CPython 3.13. Prefer it.
- **The new site's build**: decide the build posture and document it. (The
  product's web bundle is gitignored and built from `web/src`; your `uat/web/`
  is new — pick commit-source-only or commit-built, state it in `uat/README.md`.)
- **Keep the roadmap honest** every shipping commit: story header status, the
  phase `current-phase-status.md` (row + "Where we are"), the project README
  "Last updated". `.githooks/dw check holdspeak-uat` must stay green.

---

## 8. DEFINITION OF DONE (check every box before you consider it finished)

Engine:
- [ ] `uv run python -m uat.conductor` serves the site on a pinned local port.
- [ ] A run boots an isolated HoldSpeak (own HOME under `uat/_runs/`), health-
      checked, logs captured, torn down with no orphan processes.
- [ ] The conductor never imports `holdspeak` (grep test passes).
- [ ] ≥5 decks incl. `bad-endpoint` + `no-model`; each round-trips `Config.load`.
- [ ] Top recipes apply, **verify via probe through product routes**, and are
      idempotent (applied twice = same verified state, no dupes): at minimum
      `fresh-desk`, `seeded-desk`, `intel-endpoint-dead`, `first-run-no-model`,
      `mesh-node-alive`, and `meeting-just-ended-open-actions` (real if `.43` up).
- [ ] Scenario contract + loader + validation; surface axis enforced (`n/a` needs
      a reason). `uat/features.yaml` seeded from the directory.

Experience:
- [ ] The guided site walks a pack; per-(step,surface) verdict + note + screenshot
      persist to the run DB the moment cast; crash-safe resume works.
- [ ] Staging failure renders honestly with the log tail (retry/abort, no spinner).
- [ ] The debrief packet (md + json) generates with per-surface scores, coverage
      %, and a product-log slice per non-pass finding; `uat/TRIAGE.md` exists;
      the BACKLOG-block generator works.

Paces (real coverage):
- [ ] Pack D (Honest Failure) fully authored and its web legs runnable with no LAN.
- [ ] Packs A and C authored (web legs; `.43` legs runnable if up).
- [ ] The whole loop self-proven by `tests/uat/` integration tests **and** a
      Playwright drive of the real site (labelled harness self-tests).

Ship & docs:
- [ ] `uat/README.md` (with the owner wake-up runbook up top) + `uat/AUTHORING.md`.
- [ ] `dogfood/PROTOCOL.md` points here as the way UAT is now run.
- [ ] Every story shipped via its own PR, CI green, merged; roadmap statuses +
      evidence updated. `dw check holdspeak-uat` green.

Explicitly NOT done (leave for the owner, clearly marked):
- [ ] The real human sitting (HSU-1-06's live beat).
- [ ] Physical iPad/iPhone verdicts; the Phase-2 device verification + ranking.

---

## 9. THE OWNER'S WAKE-UP RUNBOOK (put a copy at the top of `uat/README.md`)

When the owner wakes up, this is their first five minutes:

```bash
cd /Users/karol/dev/tools/HoldSpeak
git pull                                 # your merged work
uv run python -m uat.conductor           # opens the UAT site; note the URL it prints
```

Then, in the browser: pick **Pack D — Honest Failure** (needs no LAN), watch the
rig stage the world, walk the beats, cast a verdict per surface (web now; iPad/
iPhone when they have devices in hand), and read the debrief at the end. If `.43`
is up, Pack A and Pack C put the intelligence through its paces too. The findings
are theirs to triage with you into `BACKLOG.md`.

If anything is broken or pending, they will find it named honestly in
`uat/README.md` §"Known state" — which you keep truthful as you go.

---

**Now go build it. Leave a running framework, an honest one, and a debrief the
owner can act on the moment they wake.**
