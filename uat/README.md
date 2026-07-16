# HoldSpeak UAT — the rig

A web-based UAT framework that puts HoldSpeak through its paces and captures
per-step human feedback. The **conductor** hosts HoldSpeak as an isolated,
managed subprocess (booting it with a chosen configuration, good or
deliberately bad, seeding the desk, spawning mesh nodes, restarting it between
scenarios); the **guided site** walks you through a pack beat by beat and lands
every verdict in a run database; a sitting ends in a **debrief packet** you and
an agent triage together into `pm/roadmap/holdspeak/BACKLOG.md`.

The governing acceptance policy is [`CHARTER.md`](./CHARTER.md). For physical
iPhone/iPad work, use the short [`DEVICE-RUNBOOK.md`](./DEVICE-RUNBOOK.md). The
latest evidence-backed readiness audit is [`REVIEW-2026-07-09.md`](./REVIEW-2026-07-09.md).
The owner-facing execution order, bootstrap rules, usability bar, and stop gates
are in [`FUNCTIONAL-PASS.md`](./FUNCTIONAL-PASS.md).

Protocol v2 records every verdict as `implementation target × form factor`.
`cli_python:local_shell` identifies terminal protocols; `web_react` is the
React product; `ios_flagship_swift`,
`ios_companion_swift`, and `ios_classic_swift` are separate installed Swift
roots. `desktop`, `ipad_browser`, `iphone_browser`, and `tablet_viewport` are
web environments; native `ipad` and `iphone` are physical app form factors.
Viewport resizing never proves native behavior. React Desk and Swift Desk are
separate campaign legs, and parity is joined only after both legs were run.

---

## The owner's functional runbook

```bash
cd /Users/karol/dev/tools/HoldSpeak
git pull                                 # the merged framework
uv run python -m uat.conductor           # opens the UAT site; note the URL it prints
```

Then, in the browser (it prints `http://localhost:8799`):

1. Start **1 · React Web Desk foundation — desktop**. The twelve numbered owner
   campaigns are the execution protocol; ordinary packs remain below them as
   reference/diagnostic material. Campaigns 10–12 are the Phase 93/94
   physical-proof legs (BACKLOG candidate Y): 10 is production-Web owner
   evidence, 11 is the flagship pass on physical devices (TestFlight build 12+),
   12 is the Delivery Runtime on real metal (second machine, iPad, tailnet
   HTTPS).
2. Walk the beats: each says *do this*, *expect this*. Use **Open the product**
   to jump to the right screen. Cast a verdict only for the displayed
   **target/form-factor slot**. Campaign 1 is React desktop; Campaign 5 is the
   independent flagship Swift Desk/native pass on physical devices. Then jot a
   note (type it or **speak it** — every note field has a 🎤 that rides
   the run's own transcribe route, local Whisper, no egress), drop a screenshot.
3. Finish and triage one campaign before starting the next. Campaign cards show
   the time, preflight, and split between automatic, assisted, and hands-on
   bootstrap. Campaigns 2–4 add `.43`, mic, audio, and tmux only where needed.
   Campaign 5 is the physical flagship pass.
4. Read the **debrief** at sitting end (score per execution slot, coverage %,
   every non-pass finding with its log slice). Triage the findings with an agent per
   [`TRIAGE.md`](./TRIAGE.md); each `fix` becomes a BACKLOG row.

If anything is broken or pending, it is named honestly under **Known state**
below.

Campaigns 1–9 contain 90 scenarios and 327 direct observations: 54 are fully
automatic, 27 are recipe-staged plus a real-world preflight, and 9 begin at a
genuinely hands-on boundary. Exact meeting/action/proposal fixtures remove
model wording and manual setup from UI-mechanics tests; live inference stays
in the scenarios that judge intelligence itself. Campaigns 10–12 add 20
scenarios that are deliberately hands-on: they exist to capture the owner and
physical-device evidence the Phase 93/94 closes parked, so most beats start at
a human boundary (real microphones, real devices, a second machine).

---

## The port map

| Port | What | Note |
|---|---|---|
| `8799` | the conductor (this site + API) | `UAT_PORT` overrides |
| `8788`+ | the product under test | one per run; auto-bumps if busy |
| `8765` | your real hub | **untouched** — a sitting runs beside your live desk |

`UAT_HOST=0.0.0.0 uv run python -m uat.conductor` binds the site LAN-wide for a
device sitting. Also enable **Device sitting** on the pack picker; that LAN-binds
the isolated product run and preserves its pairing token across deck changes.

## How a sitting flows

1. Pick a pack → the conductor boots an **isolated run** (a fresh HOME under
   `uat/_runs/<run_id>/home/`, so your real `~/.config/holdspeak` is never
   touched; model caches are symlinked in so nothing re-downloads).
2. For each scenario, the conductor **stages** its state recipes (deck + seeds +
   actions) and verifies each through the product's own routes.
3. You walk the steps; every verdict writes to the run DB the moment cast, keyed
   `(scenario, step, target, form factor)`. A refresh or a crash **resumes** at
   the first unanswered slot.
4. At the end the **debrief packet** (`uat/_runs/<run_id>/debrief/debrief.md` +
   `.json`) generates.

For a multi-campaign release gate, run:

```bash
uv run python scripts/uat_closeout.py phase-92
```

The closeout is a read-only, fail-closed join over debrief packets. It selects
the newest required campaign result only for the repository's exact clean
commit, rechecks the current scenario/slot/measurement matrix, enforces metric
thresholds and physical-device attestations, and names every missing
prerequisite. It never writes evidence or changes a story/phase status. The
same report is available at `GET /api/closeouts/phase-92`; policies live under
`uat/closeouts/` so future releases can reuse the primitive.

Each sitting snapshots its normalized scenarios, ledger, recipe/deck asset
hashes, and git commit into `protocol-snapshot.json`. Debrief coverage means
**executed** coverage; authored pack coverage is reported separately.

## Where things land

- Runs, logs, screenshots, the run DB: `uat/_runs/` (gitignored).
- Debrief packets: `uat/_runs/<run_id>/debrief/`.
- Decks: `uat/decks/`. Seeds: `uat/seeds/`. Recipes: `uat/recipes/`.
- Scenarios: `uat/scenarios/<pack>/`. The feature ledger: `uat/features.yaml`.
- Multi-campaign gate policies: `uat/closeouts/` (reports are computed, never
  persisted as evidence by the conductor).

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

## Device sittings (Swift on iPad / iPhone)

The guided site is usable from a device browser: `UAT_HOST=0.0.0.0`, then open
the LAN URL the conductor prints. That browser is the recorder, not automatically
the product target. Open the separately installed Swift app for a native step
and pair it to the isolated product URL/token.

Before a native verdict, register the exact target/form-factor device session:
device name, OS, bundle ID, build number, installation source, and explicit
pairing verification. The harness locks the slot unless that attestation matches
the scenario. It is a durable human attestation, not cryptographic device proof.
A result cast in React Safari on the iPad is `web_react:ipad_browser`, never
`ios_flagship_swift:ipad`.

Some device-local states (a sideloaded GGUF, airplane mode, mic permission)
cannot be induced from the LAN; those are hand-staged in the device pre-flight
and the harness refuses the beat rather than faking it.

## Building the site

The built site (`uat/web/dist`) is **committed**, so the wake-up runbook works
after a plain `git pull` — no npm step. To rebuild after editing `uat/web/src`:

```bash
npm --prefix uat/web install
npm --prefix uat/web run build
```

## Known state (kept truthful)

- **The `web_react:desktop` loop is complete and proven** end to end (conductor →
  induction → contract → guided site → debrief), including live on `.43` for the
  meeting-intel and mesh recipes.
- **Physical Swift verdicts are the owner's.** Every native slot starts locked
  and unanswered until a matching pairing-verified device attestation exists.
  React browser and Swift app evidence remain distinct even on the same glass.
- **The first live human sitting (HSU-1-06) is pending the owner.** The rig is
  built up to the sitting; the sitting itself cannot be delegated — that is the
  point of the project.
- **Native targets are distinct.** `ios_flagship_swift`,
  `ios_companion_swift`, and `ios_classic_swift` are separate execution
  targets. The current inventory still
  contains claims that must be reclassified after on-glass verification; see
  `CHARTER.md` "Current release blockers."
- **The Phase-2 formal device verification + joint ranking** are not done; the
  directory is a model's reading of the record, used here as scenario source.

## Testing

- `uv run pytest -q tests/uat/` — the harness suite (the `.43`-gated tests
  self-skip without the LAN).
- `npm --prefix uat/web test` — the site's store tests.
- `uv run python scripts/uat_site_walk.py` — a Playwright drive of the real site
  (UI smoke only; it is not a human sitting or a device-parity proof).

## Drive it ad-hoc (no sitting)

To induce a world and poke it — create a KB, a zone, a meeting; boot a broken
deck; spawn a mesh node — without running a full sitting:

```bash
uv run python -m uat.stage --list                       # what you can invoke
uv run python -m uat.stage --recipe seeded-desk         # boot + seed, stays up
uv run python -m uat.stage --seed desk-zones-demo --deck golden-local
```

It prints the run's product URL to open. See [`AUTHORING.md`](./AUTHORING.md)
§"Drive the harness ad-hoc" for the CLI and the equivalent conductor-API calls.

See [`AUTHORING.md`](./AUTHORING.md) to add a scenario, deck, seed, or recipe.
