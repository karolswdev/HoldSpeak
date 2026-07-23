# HS-103-05 - A provable steering demo — the flagship feature, on demand

- **Project:** holdspeak
- **Phase:** 103
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The research finding (the bar)

The independent Desk-OS audit (2026-07-22) could not verify HoldSpeak's
most ambitious surface — attaching to and steering a live coding
agent's terminal from the desk — because the seeded desk it staged
(`uat.stage --recipe seeded-desk`) has no live coder session: "Agents
reads 'No one is waiting on you' and the steer/attach path is
unreachable. I can confirm the code exists and is large; I cannot
independently confirm it works." That's a fair limitation of the
harness, not a defect in the feature — but it means the roadmap's own
"live-walked" claims on this surface are currently unverifiable by
anyone who doesn't already know the exact UAT incantation.

Investigation for this story found the missing piece already exists in
two separate places that have never been combined: `uat/recipes/agent-pane-armed.yaml`
(spawns a real tmux pane via the product's own `/api/coders` factory
route and arms it — `deck: golden-local`, no desk seeding) and
`uat/recipes/seeded-desk.yaml` (a populated desk — notes, KBs, zones —
`deck: golden-local`, no live pane). Nobody has to invent tmux-spawning
machinery; it's sitting in `uat/conductor/induction/steering.py`
already. The gap is purely that no recipe combines the two, so no
single `uat.stage` invocation gives an auditor both a desk worth
looking at AND a live, armed, steerable session to click into.

## Problem

There is no one-command way to stand up a HoldSpeak instance that
demonstrates the full "steer a live coding agent from the desk" story
end to end — populated desk, real armed pane, ready to screenshot.
This makes the most ambitious shipped feature the hardest one to prove,
audit, or demo.

## Scope

- In: a new UAT recipe (e.g. `uat/recipes/seeded-desk-steering.yaml`)
  that composes the existing `seeded-desk` seed with the existing
  `agent-pane-armed` spawn+arm actions (reuse
  `uat/conductor/induction/steering.py`'s `spawn`/arm primitives — do
  not reimplement tmux spawning), so `uv run python -m uat.stage
  --recipe seeded-desk-steering` boots one instance with both a
  populated desk and a live, armed, awaiting-input pane reachable from
  the desk's Agents surface. Document the recipe (title/description
  per the existing YAML convention) so a future auditor or the owner
  can find and use it without archaeology.
- Out: changing the steering feature's actual implementation
  (`holdspeak/coder_steering.py` and friends — untouched, this is a
  harness/tooling story, not a product story); a scripted end-to-end
  Playwright walk of the steering UI itself (a natural follow-up once
  the recipe exists, but not required for this story — the recipe
  being drivable by hand or by a future walk script is the bar).

## Acceptance criteria

- [ ] `uv run python -m uat.stage --recipe seeded-desk-steering` boots
      successfully and prints a working localhost URL.
- [ ] The booted instance shows a populated desk (the same seeded
      notes/KBs/zones as `seeded-desk`) AND the Agents surface shows a
      live, armed coder pane (matching `agent-pane-armed`'s probe:
      `grant_live: coder`, `audit_min: 1`).
- [ ] Driven live (headed or headless Playwright) at 1440 and 393: open
      the desk, find the armed pane via the Agents surface, attach and
      send a real key/keystroke, observe it land in the pane — screenshot
      each step as evidence that the flagship feature works end to end,
      not just that the harness boots.
- [ ] The recipe's probe block (matching the existing recipe-verify
      convention) asserts both the desk-seed and the armed-pane
      conditions, so `uat.stage`'s own verification catches drift if
      either half breaks later.
- [ ] `uv run python -m uat.stage --list` shows the new recipe in its
      catalog output (confirms it's properly registered, not a
      one-off script).

## Test plan

- Unit: n/a — this is a UAT-harness composition, not application code.
- Integration: the recipe's own probe block, run via `uat.stage`
  itself, is the integration test.
- Manual / device: the live drive described in acceptance criteria —
  screenshots are the evidence artifact for this story.

## Notes / open questions

Check whether `uat/conductor/induction/recipes.py`'s recipe format
supports `includes:` combined with a `seeds:` list directly (the
existing `agent-pane-armed.yaml` uses `includes: [agent-pane-awaiting-input]`
for action composition; `seeded-desk.yaml` uses `seeds: [dogfood-desk]`
for data seeding) — if both compose cleanly in one YAML, this story is
almost entirely declarative. If they don't compose cleanly, that's a
real finding to report in evidence, not something to route around with
a bespoke Python script outside the recipe system.
