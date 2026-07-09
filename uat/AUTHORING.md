# Authoring UAT content

How to add a scenario, a deck, a seed manifest, or a state recipe. Everything
here is YAML validated by the contract — a malformed file fails loudly, naming
the file and field.

## The four building blocks

```
uat/decks/<name>.yaml       # a config posture the run boots with
uat/seeds/<name>.yaml        # desk/context state applied through public routes
uat/recipes/<name>.yaml      # deck + seeds + actions, closed by a verify probe
uat/scenarios/<pack>/*.yaml  # the human script: steps × surfaces × verdicts
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
  - wait: 2               # process_intel / restart / wait
probe:                    # assertions read back through GET routes
  - notes_min_count: 1
  - note_exists: uat-seed-my-note
```

Probe kinds: `notes_empty|notes_min_count|note_exists`, the `kb*` equivalents,
`meeting_with_open_actions`, `runtime_endpoint_unreachable`, `setup_not_ready`,
`setup_reachable`, `mesh_node_live|mesh_node_offline`, `doctor_names_dead_endpoint`.
A recipe that cannot verify itself raises `RecipeVerifyError` naming the missed
assertion.

## Add a scenario

```yaml
# uat/scenarios/<pack>/NN-slug.yaml
id: my-scenario                 # unique within the pack
title: A short human title
features: [desk.ask-ai.grounded-on-pile]   # ≥1 ledger key that EXISTS
recipes: [my-world]                         # ≥1 recipe that stages the world
surfaces:                       # default all-yes; opt out only with a reason
  web: yes
  ipad: yes
  iphone: {n/a: "why this surface genuinely lacks the capability"}
steps:
  - do: The instruction to the human.
    expect: The honest pass bar (see the voice rule below).
    where: /                    # optional product route to open
    surfaces:                   # optional per-step override
      ipad: {n/a: "reason"}
    after:                      # optional mid-run conductor actions
      - apply_recipe: mesh-node-just-died
```

Rules the contract enforces (named errors):

- **Cite real keys and recipes.** Every `features` key must exist in
  `uat/features.yaml`; every recipe must exist. Unknown → validation error.
- **The surface axis is explicit.** Default is all-yes; a surface is opted out
  only with `{n/a: <reason>}`. `n/a` without a reason fails; a step with **every**
  surface `n/a` fails (a step must be walked somewhere).
- **A step needs `do` and `expect`.**

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
