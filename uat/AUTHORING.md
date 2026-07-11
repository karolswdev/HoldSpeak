# Authoring UAT content

How to add a scenario, a deck, a seed manifest, or a state recipe. Everything
here is YAML validated by the contract — a malformed file fails loudly, naming
the file and field.

## The four building blocks

```
uat/decks/<name>.yaml       # a config posture the run boots with
uat/seeds/<name>.yaml        # desk/context state applied through public routes
uat/recipes/<name>.yaml      # deck + seeds + actions, closed by a verify probe
uat/scenarios/<pack>/*.yaml  # the human script: steps × execution slots × verdicts
uat/features.yaml            # the ledger every scenario cites (generated)
```

## Add a deck

A deck is a **sparse** config overlay — state only the delta; the product's
`Config.load` fills the rest.

```yaml
# uat/decks/my-deck.yaml
title: My deck
description: One line on what posture this induces.
requires: []            # [intel] if it needs the .43 LAN endpoint
config:
  config_version: 1
  meeting: { intel_enabled: false }
```

Every deck is round-tripped through the product's `Config.load` in
`tests/uat/test_decks.py` so it can't rot. Add yours to `REQUIRED_DECKS` there
if it's load-bearing.

## Add a seed manifest — create any desk primitive

A seed manifest creates desk state through the product's own public routes, so a
seeded object is indistinguishable from a user-made one. It covers **every
primitive type the product exposes a create route for**. Every item carries a
**deterministic `id`** so re-applying upserts in place (no duplicate desk).

```yaml
# uat/seeds/my-seed.yaml
notes:                    # -> POST /api/notes
  - id: uat-seed-my-note
    title: A note
    body_markdown: "…"
    tags: [uat-seed]
kbs:                      # knowledge blocks -> POST /api/kbs   (alias: knowledge_blocks:)
  - id: uat-seed-my-kb
    name: My KB
directories:              # the desk ZONES -> POST /api/directories   (alias: zones:)
  - id: uat-seed-my-zone
    name: My zone
    member_ids: [uat-seed-my-note]   # files primitives into the zone
recipes:                  # desk recipe primitives -> POST /api/recipes
  - id: uat-seed-my-recipe
    name: Summarize like a PM
    system_prompt: "Summarize as decisions, owners, risks."
chains:                   # -> POST /api/chains          (steps: [...])
workflows:                # -> POST /api/workflows        (prompt:, graph_json:)
profiles:                 # runtime profiles -> POST /api/profiles   (kind:, node:)
  - id: uat-seed-my-profile
    name: Local profile
    kind: onDevice
meetings:                 # transcript import -> POST /api/meetings/import
  - transcript: dogfood/transcripts/pylon-incident.vtt
    title: My meeting (UAT seed)
    tags: [uat-seed]
```

Each item's fields are passed straight through to its route, so any field the
route accepts works. `uat/seeds/desk-zones-demo.yaml` is the worked example.

## Add a state recipe

A recipe names a world and closes with a **verify probe** read back through the
product's own routes. Idempotency is the contract: applying it twice converges
to the same verified state.

```yaml
# uat/recipes/my-world.yaml
title: My world
deck: golden-local        # the boot posture (default golden-local)
requires: []              # [intel] gates it on .43
includes: []              # other recipes' seeds/actions fold in (cycles refuse)
boot: { link_caches: true }
seeds: [my-seed]
actions:                  # optional: spawn_node / kill_node / create_profile /
  - wait: 2               # process_intel / sync_meeting / propose_github_card /
                          # dispatch_run / steering verbs / wait
probe:                    # assertions read back through GET routes
  - notes_min_count: 1
  - note_exists: uat-seed-my-note
```

Probe kinds: `notes_empty|notes_min_count|note_exists`, the `kb*` equivalents,
`meeting_with_open_actions`, `meeting_actions_are`,
`runtime_endpoint_unreachable`, `setup_not_ready`,
`setup_reachable`, `egress_scope_is`, `proposal_egress_names_target`,
`mesh_node_live|mesh_node_offline`, `doctor_names_dead_endpoint`.
A recipe that cannot verify itself raises `RecipeVerifyError` naming the missed
assertion.

`sync_meeting` stages deterministic meeting/action state through
`POST /api/sync/push` (the product's device ingress); pair it with
`propose_github_card` to create an unapproved aftercare card without touching
the product DB or firing a connector. `uat/recipes/egress-cloud-card.yaml` is
the worked local→cloud, probe-first example. It also accepts an `action_items`
list when a test needs exact pending/accepted states; see
`functional-aftercare-review.yaml`.

## Compose an owner campaign

Campaigns under `uat/campaigns/` are executable packs that reference canonical
scenarios without copying them. Use a campaign to define human execution order,
preflight, duration, and an exit gate; keep behavior instructions in the source
scenario.

```yaml
title: "1 · My functional pass"
purpose: The user journey this sitting proves.
sequence: 1
tier: core                 # core | extended | conditional
estimated_minutes: 45
prerequisites:
  - A real-world fact the conductor cannot create.
exit_gate:
  - The user-visible condition required before moving to the next pass.
scenarios:
  - pack-desk/desk-seeded-reads-back
  - {pack: pack-c-dictation-grounding, id: c-hold-to-talk}
```

The conductor loads those source files in manifest order, rewrites their pack
identity for the sitting snapshot, and still hashes the canonical source assets.
Unknown pack/ID references and duplicate scenario IDs fail validation.

## Add a scenario

Protocol v2 separates implementation from shape. `execution_target` identifies
the code/root under test; `form_factors` identifies the environment or physical
device running it. The valid pairs are:

| Target | Form factors |
|---|---|
| `cli_python` | `local_shell` |
| `web_react` | `desktop`, `ipad_browser`, `iphone_browser`, `tablet_viewport` |
| `ios_flagship_swift` | `ipad`, `iphone` |
| `ios_companion_swift` | `ipad`, `iphone` |
| `ios_classic_swift` | `ipad`, `iphone` |

`tablet_viewport` is responsive React evidence only. It is never an alias for
`ios_flagship_swift:ipad`. A physical iPad browser is
`web_react:ipad_browser`; the flagship app on that same glass is
`ios_flagship_swift:ipad`. Those are distinct scenarios and verdicts.
`ios_unclassified_swift` exists only to quarantine unresolved historical
protocols; it cannot produce acceptance evidence or appear in an owner campaign.
`legacy_unqualified` preserves old snapshots and is likewise invalid evidence.

```yaml
# uat/scenarios/<pack>/NN-slug.yaml
id: my-scenario                 # unique within the pack
title: A short human title
execution_target: web_react
form_factors: [desktop]         # explicit; never inferred/defaulted
features: [desk.ask-ai.grounded-on-pile]   # ≥1 ledger key that EXISTS
recipes: [my-world]                         # ≥1 recipe that stages the world
steps:
  - do: The instruction to the human.
    expect: The honest pass bar (see the voice rule below).
    verifies: [desk.ask-ai.grounded-on-pile]  # exact claim(s) this beat proves
    where: /                    # optional product route to open
    form_factors: [desktop]     # optional subset of scenario form_factors
    after:                      # optional mid-run conductor actions
      - apply_recipe: mesh-node-just-died
```

### Hand-staged protocols (`manual_setup`)

A must-do protocol the harness **can't auto-stage** (a device-local state, a live
capture, a connector needing real credentials) is still a real protocol — it's
staged by hand. Give it a `manual_setup` list instead of (or alongside)
`recipes:`; the guided site shows those as a checklist ("stage this by hand →
continue") before the walkthrough, and the person still casts a verdict per
execution slot.

```yaml
id: mesh-cross-machine-steer
title: Steer a coder on a second machine
execution_target: ios_flagship_swift
form_factors: [ipad]
features: [steering.cross_machine]
manual_setup:                 # human staging — no recipe can induce this
  - Pair a second Mac as a steering node (`holdspeak mesh serve` on it).
  - Start a coder session on that node awaiting input.
recipes: []                   # empty is fine when manual_setup is present
steps:
  - do: From this desk, arm and steer the remote coder.
    expect: The far node writes its own audit row; the local one does not.
```

A scenario needs **≥1 recipe OR a non-empty `manual_setup`** — never neither.

`after` runs only after every applicable execution slot has verdicted the current
step, and establishes the world for the **next** step. It is durable,
server-executed, and blocks progress if it fails. Do not put the treatment
recipe on the treatment step; put it on the preceding control step. Initial
recipes must not span different decks—use one composite recipe with `includes`
when prerequisites must be true simultaneously.

Native scenarios must name the exact installed Swift application target. A
native target forces LAN/device mode, requires a matching pairing-verified
device attestation, and replaces the misleading React Web Desk deep-link with a
prompt to use that app. The attestation records target, form factor, device/OS,
bundle/build, and installation source. It is structured human provenance, not
cryptographic identity.

One scenario has one implementation target. If a workflow crosses React and
Swift, split it into target-specific scenarios or explicit handoff legs. Do not
put a web form factor on a Swift target, do not put `ipad`/`iphone` on
`web_react`, and do not copy web routes/control names into a native script.
Parity is computed only after the independently executed legs exist.

Use `verifies` whenever a scenario cites more than one feature. Once any step
uses it, every scenario feature must be mapped to at least one step. Authored and
executed per-slot coverage then credits only the mapped beat, rather than every
feature merely because some unrelated step was answered. Legacy scenarios
without `verifies` retain scenario-level accounting until migrated.

Rules the contract enforces (named errors):

- **Cite real keys and recipes.** Every `features` key must exist in
  `uat/features.yaml`; every recipe must exist. Unknown → validation error.
  A scenario with no recipe must carry `manual_setup`.
- **The execution slot is explicit.** Both `execution_target` and a non-empty
  `form_factors` list are required; there are no all-surface defaults. Legacy
  `surfaces` is forbidden. Step form factors, when present, must be a subset of
  the scenario form factors.
- **Target/form-factor pairs are validated.** Browser factors belong only to
  `web_react`; native `ipad`/`iphone` belong only to an exact Swift target.
- **A step needs `do` and `expect`.**
- **Initial recipes cannot fight over decks.** Multiple initial recipes are
  allowed only when they share one deck; otherwise validation requires a
  composite recipe or an `after` transition.

## The honest-`expect` voice rule

`expect` lines are the pass bar, written against POSITIONING canon — honest,
checkable, never marketing:

- Good: "the badge reads local", "doctor names the dead endpoint", "the digest
  names what is still open and by whom".
- Bad: "the experience is delightful", "it just works", "blazing fast".

For non-deterministic LLM output, judge **structurally**: assert the right
*type* rendered (an action-item list, a decision or an open question) and judge
it on substance — did it surface the decision / owner / risk — never on literal
wording.

## The one rule that ties a pack together

**No pack is all-green-happy-path.** Open with a staging-verify beat and close
with an honest-failure or control beat. If a pack has no beat that could fail
loudly, it is a demo, not a test.

## Drive the harness ad-hoc (no sitting)

The conductor + guided site are for a *sitting*. To just **induce a world and
poke it** — create a KB, a zone, a meeting; boot a broken deck; spawn a mesh
node — use the staging CLI:

```bash
# See everything you can invoke (decks, recipes, seeds)
uv run python -m uat.stage --list

# A seeded desk on golden-local; opens a product URL you can poke, stays up
uv run python -m uat.stage --recipe seeded-desk

# Create specific things: apply one or more seeds (KBs, zones, notes, …)
uv run python -m uat.stage --deck golden-local --seed desk-zones-demo

# A real meeting with open actions (needs .43), then tear down at once
uv run python -m uat.stage --recipe meeting-just-ended-open-actions --once

# Bind LAN so an iPad/iPhone can pair with the run
uv run python -m uat.stage --recipe seeded-desk --lan
```

It boots an isolated HoldSpeak, applies the recipes/seeds, prints the run's
product URL (and token, if LAN), and holds the run up until Ctrl-C.

**Or drive it over the conductor API** (same verbs the site uses) — start
`uv run python -m uat.conductor`, then:

```bash
RUN=$(curl -s -XPOST localhost:8799/api/runs -d '{"deck":"golden-local"}' | jq -r .id)
curl -s -XPOST localhost:8799/api/runs/$RUN/recipes/seeded-desk        # apply a recipe
curl -s -XPOST localhost:8799/api/runs/$RUN/seeds/desk-zones-demo      # create zones/KBs/…
curl -s -XPOST localhost:8799/api/runs/$RUN/nodes -d '{"name":"w1"}'   # spawn a mesh node
curl -s localhost:8799/api/runs/$RUN                                    # pairing facts + status
curl -s -XDELETE localhost:8799/api/runs/$RUN                           # tear down
```

`GET /api/decks`, `GET /api/recipes`, `GET /api/seeds` enumerate what's available.

## Validate before you commit

```bash
uv run python -m uat.tools.build_ledger --check   # ledger is in sync
uv run pytest -q tests/uat/test_scenarios.py tests/uat/test_smoke_pack.py
```

Or load a pack directly: `GET /api/packs/<pack>` returns the scenarios,
coverage, and any `validation_errors`.

## Author a multi-campaign closeout

A file in `uat/closeouts/<id>.yaml` can join independent campaign debriefs
without weakening their target identity. Name every required campaign and its
exact execution slots, then give every required scenario measurement a policy:
`present`, `eq`, `lte`, or `gte`. Policy loading fails when a required prompt
has no rule or a rule no longer belongs to any prompt; this turns scenario drift
into an explicit contract error.

Closeout evaluates only the newest packet for each campaign on one clean Git
commit. It requires the complete current verdict matrix, protocol-v2 hash,
executed journey coverage, permitted verdict/triage states, numeric thresholds,
and configured physical-device attestations. Repository prerequisites can name
a relative file plus an exact line prefix/required substring. Paths are confined
to the repository root. Do not use a closeout to generate evidence or mutate PM
state; it reports readiness and gaps only.

```bash
uv run python scripts/uat_closeout.py <id>
uv run python scripts/uat_closeout.py <id> --json
curl -s localhost:8799/api/closeouts/<id> | jq
```
