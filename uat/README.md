# HoldSpeak UAT — the rig

A web-based UAT framework that puts HoldSpeak through its paces and captures
per-step human feedback. The **conductor** hosts HoldSpeak as an isolated,
managed subprocess (booting it with a chosen configuration, good or
deliberately bad, seeding the desk, spawning mesh nodes, restarting it between
scenarios); the **guided site** walks you through a pack beat by beat and lands
every verdict in a run database; a sitting ends in a **debrief packet** you and
an agent triage together into `pm/roadmap/holdspeak/BACKLOG.md`.

---

## The owner's wake-up runbook

```bash
cd /Users/karol/dev/tools/HoldSpeak
git pull                                 # the merged framework
uv run python -m uat.conductor           # opens the UAT site; note the URL it prints
```

Then, in the browser (it prints `http://localhost:8799`):

1. Pick **Pack D — Honest Failure** first (needs no LAN). Watch the rig stage
   the world (each recipe verified, or the failure with the product's own log
   tail — never a spinner).
2. Walk the beats: each says *do this*, *expect this*. Use **Open the product**
   to jump to the right screen. Cast a **verdict per surface** (web now;
   iPad/iPhone when you have a device in hand — see "Device sittings" below),
   jot a note (type it or **speak it** — every note field has a 🎤 that rides
   the run's own transcribe route, local Whisper, no egress), drop a screenshot.
3. If `.43` is up, **Pack A — Meeting Aftercare** and **Pack C — Dictation
   Grounding** put the intelligence through its paces too.
4. Read the **debrief** at sitting end (score per surface, coverage %, every
   non-pass finding with its log slice). Triage the findings with an agent per
   [`TRIAGE.md`](./TRIAGE.md); each `fix` becomes a BACKLOG row.

If anything is broken or pending, it is named honestly under **Known state**
below.

---

## The port map

| Port | What | Note |
|---|---|---|
| `8799` | the conductor (this site + API) | `UAT_PORT` overrides |
| `8788`+ | the product under test | one per run; auto-bumps if busy |
| `8765` | your real hub | **untouched** — a sitting runs beside your live desk |

`UAT_HOST=0.0.0.0 uv run python -m uat.conductor` binds the site LAN-wide for a
device sitting.

## How a sitting flows

1. Pick a pack → the conductor boots an **isolated run** (a fresh HOME under
   `uat/_runs/<run_id>/home/`, so your real `~/.config/holdspeak` is never
   touched; model caches are symlinked in so nothing re-downloads).
2. For each scenario, the conductor **stages** its state recipes (deck + seeds +
   actions) and verifies each through the product's own routes.
3. You walk the steps; every verdict writes to the run DB the moment cast, keyed
   `(scenario, step, surface)`. A refresh or a crash **resumes** at the first
   unanswered slot.
4. At the end the **debrief packet** (`uat/_runs/<run_id>/debrief/debrief.md` +
   `.json`) generates.

## Where things land

- Runs, logs, screenshots, the run DB: `uat/_runs/` (gitignored).
- Debrief packets: `uat/_runs/<run_id>/debrief/`.
- Decks: `uat/decks/`. Seeds: `uat/seeds/`. Recipes: `uat/recipes/`.
- Scenarios: `uat/scenarios/<pack>/`. The feature ledger: `uat/features.yaml`.

## Prerequisites per deck

| Deck | Needs `.43`? | Used by |
|---|---|---|
| `golden-local` | no | seeded/fresh desk, the demo-without-the-LAN path |
| `bad-endpoint` | no | `intel-endpoint-dead` (honest failure) |
| `no-model` | no | `first-run-no-model` (first-run truth) |
| `golden-43` | **yes** | `meeting-just-ended-open-actions` (real intel) |
| `mesh-node` | yes (for real work; liveness is local) | the mesh recipes |

`.43` = the LAN llama.cpp at `http://192.168.1.43:8080`. Pack D needs none of it,
so **the rig demos without the LAN**. Packs A and C need `.43` up.

## Device sittings (iPad / iPhone)

The site is fully usable from a device browser: `UAT_HOST=0.0.0.0`, then open
the LAN URL the conductor prints on the device. The run is shared, so a verdict
cast from the iPad shows up on the Mac's open view. The **product** under test is
reachable from the device the way it pairs with the real hub — each run reports
its pairing facts (LAN URL + its own per-run token). Some device-local states
(a sideloaded GGUF, airplane mode, mic permission) cannot be induced from the
LAN; those are hand-staged in the device pre-flight and the harness refuses the
beat rather than faking it.

## Building the site

The built site (`uat/web/dist`) is **committed**, so the wake-up runbook works
after a plain `git pull` — no npm step. To rebuild after editing `uat/web/src`:

```bash
npm --prefix uat/web install
npm --prefix uat/web run build
```

## Known state (kept truthful)

- **The web surface loop is complete and proven** end to end (conductor →
  induction → contract → guided site → debrief), including live on `.43` for the
  meeting-intel and mesh recipes.
- **Physical iPad/iPhone verdicts are the owner's.** The device legs are built
  (LAN-reachable site, per-surface verdict slots, `n/a`-with-reason), but every
  device-surface verdict starts unanswered — never faked. The live device
  cross-view (a verdict cast from a real device, seen on the Mac) awaits the
  owner's sitting.
- **The first live human sitting (HSU-1-06) is pending the owner.** The rig is
  built up to the sitting; the sitting itself cannot be delegated — that is the
  point of the project.
- **The Phase-2 formal device verification + joint ranking** are not done; the
  directory is a model's reading of the record, used here as scenario source.

## Testing

- `uv run pytest -q tests/uat/` — the harness suite (the `.43`-gated tests
  self-skip without the LAN).
- `npm --prefix uat/web test` — the site's store tests.
- `uv run python scripts/uat_site_walk.py` — a Playwright drive of the real site.

See [`AUTHORING.md`](./AUTHORING.md) to add a scenario, deck, seed, or recipe.
