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

## Add a seed manifest

Seeds carry a **deterministic `id`** so re-applying upserts in place (no
duplicate desk). Meetings import a committed transcript.

```yaml
# uat/seeds/my-seed.yaml
notes:
  - id: uat-seed-my-note        # deterministic → idempotent
    title: A note
    body_markdown: "…"
    tags: [uat-seed]
kbs:
  - id: uat-seed-my-kb
    name: My KB
meetings:
  - transcript: dogfood/transcripts/pylon-incident.vtt
    title: My meeting (UAT seed)
    tags: [uat-seed]
```

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

## Validate before you commit

```bash
uv run python -m uat.tools.build_ledger --check   # ledger is in sync
uv run pytest -q tests/uat/test_scenarios.py tests/uat/test_smoke_pack.py
```

Or load a pack directly: `GET /api/packs/<pack>` returns the scenarios,
coverage, and any `validation_errors`.
