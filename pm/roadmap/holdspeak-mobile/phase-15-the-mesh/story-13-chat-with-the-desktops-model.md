# HSM-15-13 — Chat with the desktop's model (the manifest becomes a front door)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** scaffolded — 2026-07-06, owner ask in the same session as 15-12 (*"this
  mac hosts a nice model, and it has its own definition of it... we should be able to
  simply choose to have a chat with that model on our Mac"*). 15-11 lets an AGENT run
  on a hub model; this makes the model itself a person you can open.
- **Depends on:** [[story-11-agents-on-your-desktops-models]] (the `desktop` profile
  kind + the `callLLMTurn` seam + `/api/ask` model pinning), the synced mesh manifests
  (`meshModelsJSON`), [[story-12-the-context-envelope]] (the chat's grounding rides
  free once the chat exists).
- **Owner:** unassigned

## Problem

The phone already KNOWS what the Mac can run — the sync pull caches every desktop
manifest row, and the hub allow-lists model pinning on `/api/ask`. But that knowledge
only surfaces inside RunsOnPicker, two menus deep in an agent's builder. There is no
way to do the obvious first thing: see the Mac's model on the connect surface and just
talk to it. The manifest is a capability card with no front door.

## The design — a model row is a chat you can open

- **The models live on the connect surface.** The desk's connect card (paired state)
  gains a "Models" section: one row per remote manifest (hub first), each wearing the
  node that holds it. One tap = chat.
- **A model chat IS a recipe chat.** Opening a model synthesizes a transient
  `RecipeRecord` (id `modelchat:<node>:<name>`, name = the model's name, profileId =
  the desktop profile pinned to that model) and opens the existing `DioRecipeChat` —
  the thread persists under that id like any agent thread, the reply path funnels
  through `callLLMTurn`'s desktop branch, and the printed egress is whatever the hub
  reports for the run. No parallel chat surface.
- **Grounding rides free.** Because it is the same chat, the 15-12 "Ground this ask"
  picker works on a model chat unchanged — grounding refs ship to the hub, the hub
  hydrates. "Chat with the Mac's model about these two meetings" is one motion.
- **Honest when unreachable.** The mesh vocabulary (15-02/15-03 grammar) carries:
  unpaired hides nothing (rows wear the blocked state), an unreachable peer fails the
  turn with the named cause and the one-tap "Run on this device" fallback stays out
  (a model chat has no local twin — the failure names the peer instead).

## Acceptance criteria

- [ ] **The front door:** on a paired desk, the connect card lists the desktop's
      models by name; tapping one opens a chat titled with the model's name.
- [ ] **The turn is real:** a message in that chat executes on the hub pinned to THAT
      model (`/api/ask` `model` override); the reply renders in the thread and the
      run's egress is the hub-reported one.
- [ ] **The thread persists:** closing and reopening the model chat keeps the
      conversation (same `agentChats` persistence as recipes).
- [ ] **Grounded model chat:** the 15-12 picker attaches meetings to a model chat and
      a desktop turn ships grounding refs.
- [ ] **Unpaired honesty:** unpaired, the section shows the blocked state (never
      disappears); an unreachable peer fails the turn naming the cause.
- [ ] **The proof:** real-metal — a model chat turn against the live hub prints the
      hub-reported model name in the thread's badge/egress.

## Build plan

1. **The synthesized persona:** `modelChatRecipe(manifest:)` — transient
   `RecipeRecord` pinned to `InferenceConfigStore.desktopProfile(model:)`; open it
   through the existing `openAgent` path (thread key `modelchat:<node>:<name>`).
2. **The connect card section:** paired card lists remote manifests (hub row first)
   with a chat affordance per row; blocked state when unpaired.
3. **Sim seeds + screenshots** (the 15-10 rig): paired-with-models card, the model
   chat open, a grounded model chat.
4. **Real-metal proof** against the live hub (the 15-11 desktoprun rig pattern).

## Test plan

- Host (Swift): the synthesized persona mapping (id/name/profileId) — pure function.
- Sim: build + the three screenshots.
- Real metal: one live turn through the paired hub, egress printed.

## Notes

- Sibling of [[story-11-agents-on-your-desktops-models]] and
  [[story-12-the-context-envelope]]: 15-11 gave agents the hub's models, 15-12 gave
  asks your records, this gives the models themselves a door.
