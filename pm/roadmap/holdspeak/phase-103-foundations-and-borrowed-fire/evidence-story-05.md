# Evidence - HS-103-05

- **Story:** HS-103-05 - A provable steering demo — the flagship feature, on demand
- **Status:** done
- **Date:** 2026-07-22

## Proof

### Captured run — 2026-07-23T04:29:07Z

- **Command:** `bash -c uv run python -m uat.stage --list && uv run pytest -q tests/uat/test_recipes_parse.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c0472cb5cfebc6f88fd599bc7e85f545460ee36

## Investigation (per the story's own open question)

Confirmed `includes:` and `seeds:` compose cleanly in one recipe
(`uat/conductor/induction/recipes.py`'s own docstring: "``includes:``
other recipes (their seeds/actions/probes fold in)"). One real
wrinkle, not a blocker: `RecipeEngine.apply()` treats "the combined
probe is the TARGET's own probe" (line 201-203 of `recipes.py`) —
included recipes' individual probe blocks do NOT auto-merge (by
design: a child recipe's probe can describe an earlier lifecycle stage
that no longer holds once composed further, e.g.
`agent-pane-awaiting-input`'s own `keys_refused_unarmed` assertion
would be FALSE once `agent-pane-armed` arms it). So the new recipe
restates its own complete probe — the union of `seeded-desk`'s
assertions plus `agent-pane-armed`'s own two (`grant_live: coder`,
`audit_min: 1`) — exactly mirroring how `agent-pane-armed` itself
already handles composing on top of `agent-pane-awaiting-input`. This
was purely declarative, no bespoke Python needed.

## The recipe

`uat/recipes/seeded-desk-steering.yaml` — `includes: [seeded-desk,
agent-pane-armed]`, `deck: golden-local`, its own 9-assertion probe.
Reuses `uat/conductor/induction/steering.py`'s existing spawn/arm
primitives verbatim (via the include) — no tmux-spawning code was
written for this story.

## Live proof — both halves, then the flagship feature end to end

`uv run python -m uat.stage --recipe seeded-desk-steering` (staged on
:8791): confirmed via direct API calls that BOTH halves are real in
the same instance — `GET /api/notes` returned the 3 seeded notes
(`uat-seed-note-decisions`, `-standup`, `-glossary`); `GET
/api/coders/steering/panes` listed a run-scoped `uat-<runid>-coder`
tmux session; `GET /api/coders/steering/grants` showed a live grant on
its pane. `--once` re-run afterward: `probe ok=True` (idempotent,
matching the recipe-verify convention), clean teardown confirmed (no
leftover process, port, or tmux session).

Then drove the ACTUAL flagship feature through the real desk UI
(headed Playwright, 1440 + 393 — screenshots in
`assets/story-05/hs103-05-{desktop,compact}-*.png`):
1. Opened the search/tools shelf (⌘K) and its "Panes" drawer — the
   real discovery path (`uat-*-coder` is a launcher, not a static dock
   button; found via `DeskToolShelf.tsx`'s `matchingDrawers`).
2. Clicked the recipe's spawned pane → attached (`SessionPullout`
   opened on `pane:%577`).
3. The recipe's 300s TTL had lapsed by click-through time (test walk
   naturally took a few minutes) — the UI itself offered "Arm pane
   %577 for 15 minutes"; clicked it, re-armed live through the real
   arm route, not a fixture.
4. Typed a real marker string (`hs103-05-live-proof`) into the steer
   composer and clicked Send.
5. The marker landed VERBATIM in the live tmux pane's rendered output
   (`.desk-session-pane`), with a printed receipt
   ("✓ Receipt steering:2 · %577" / "steering:3" on the second
   viewport's run) — proof the keystroke actually reached the real
   pane through the real product route, not a mock.

Note on the story's own wording: acceptance criteria says "the Agents
surface" — investigation found the actual UI path is the dock's
search-shelf "Panes" drawer (`DeskToolShelf.tsx` / `PanePicker` in
`SessionPullout.tsx`), not `CompanionCore`'s "Agents" tab (which reads
a DIFFERENT registry — real Claude/Codex CLI hook sessions via
`agent_sessions.json` — and would never show a synthetic UAT tmux
pane). Drove and screenshotted the real, correct surface instead of the
loosely-named one.

```text
Decks:
  bad-endpoint     Bad endpoint — intel pointed at a dead port
  cloud-egress     Cloud egress selected — named endpoint, execution still closed
  golden-43        Golden .43 — real intelligence on the LAN llama.cpp (needs .43)
  golden-local     Golden local — fully local, no LLM
  mesh-node        Mesh node — a hub that can consume a local mesh worker (needs .43)
  no-model         No model — a first-run desk with no transcription model
  pack-g-actuators-on Actuators governance ON — master switch + allow-list open (needs .43)
  pack-g-slack-configured Send-to-Slack configured — the URL half of the double opt-in (needs .43)

Recipes (named worlds, deck + seeds + verify probe):
  agent-pane-armed                 -> deck golden-local
  agent-pane-awaiting-input        -> deck golden-local
  agent-pane-awaiting-input-43     -> deck golden-43 (needs .43)
  agent-pane-mesh                  -> deck mesh-node (needs .43)
  desk-primitives                  -> deck golden-local
  desk-primitives-43               -> deck golden-43 (needs .43)
  dict-groundless-43               -> deck golden-43 (needs .43)
  dict-symbols-43                  -> deck golden-43 (needs .43)
  egress-cloud-card                -> deck cloud-egress
  first-run-no-model               -> deck no-model
  fresh-desk                       -> deck golden-local
  functional-aftercare-review      -> deck golden-local
  functional-proposal-review       -> deck golden-local
  functional-qlippy-queue          -> deck golden-local
  intel-endpoint-dead              -> deck bad-endpoint
  learned-correction-taught        -> deck golden-local
  meeting-just-ended-open-actions  -> deck golden-43 (needs .43)
  mesh-node-alive                  -> deck mesh-node (needs .43)
  mesh-node-just-died              -> deck mesh-node (needs .43)
  mesh-run-on-worker               -> deck mesh-node (needs .43)
  mesh-run-ready                   -> deck mesh-node (needs .43)
  pack-a-import-endpoint-dead      -> deck bad-endpoint
  pack-a-mixed-topic-meeting       -> deck golden-43 (needs .43)
  pack-a-two-meetings              -> deck golden-43 (needs .43)
  pack-b-pane-steered              -> deck golden-local
  pack-c-byo-backends              -> deck golden-local
  pack-c-journal-ready             -> deck golden-local
  pack-c-wake-word-ready           -> deck golden-local
  pack-g-actuators-armed           -> deck pack-g-actuators-on (needs .43)
  pack-g-slack-armed               -> deck pack-g-slack-configured (needs .43)
  profile-key-never-syncs          -> deck golden-local
  seeded-desk                      -> deck golden-local
  seeded-desk-43                   -> deck golden-43 (needs .43)
  seeded-desk-mesh                 -> deck mesh-node (needs .43)
  seeded-desk-steering             -> deck golden-local

Seed manifests (desk primitives to create):
  desk-primitives
  desk-zones-demo
  dict-symbol-dictionary
  dogfood-desk
  mesh-authored-run
  pack-a-ledgerline-meeting
  pack-a-questline-meeting
  pack-c-byo-backends
  pack-c-journal-context
  pylon-incident-meeting

Seed a manifest with any of: notes, kbs (knowledge blocks), recipes,
chains, workflows, directories (zones), profiles, meetings. See uat/AUTHORING.md.
...........                                                              [100%]
11 passed in 0.27s
```
