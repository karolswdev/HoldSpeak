# HS-140-04 — A desk worth opening

- **Project:** holdspeak
- **Phase:** 140
- **Status:** backlog
- **Depends on:** 140-01
- **Unblocks:** 140-05, 140-06
- **Owner:** delegated Terra worker; orchestrator adjudicates

## Problem

Progressive disclosure cannot reveal an empty toy. The current packaged seed
creates only two empty drawers (`Inbox`, `Work`), five unconfigured profiles,
and a Workbench. It creates no useful notes or attachable context collection.
Public Getting Started copy claiming six drawers and two starter notes is stale.

## Scope

- **In:** evolve `holdspeak/seeds/fresh-desk.yaml` and the existing seed applier
  into a useful default pack; six directories named Inbox, Personal, Work,
  Meetings, Decisions, Reference; a Start here note; editable About me, Current
  priorities, How I like help, People & vocabulary, and Meeting preferences
  notes; one Everyday context KB containing those five context notes; one
  plain Context choice available through the existing Ask picker and Agent
  editor `kb_id`; file notes into sensible drawers; extend seed application to
  honor KB membership; remove the five unconfigured placeholder profiles and
  starter Workbench from the regular-user seed; keep deterministic IDs and
  sync-compatible records.
- **Out:** a new context/drawer model, fabricated personal facts, automatic
  cloud/model enrollment, agents that pretend to work without a ready target,
  demo meetings/decisions, new schema/API/MCP surface.

## Acceptance criteria

- [ ] Fresh seed creates exactly the six named drawers, Start here, five
  editable context notes, and Everyday context with deterministic `hs-seed-*`
  IDs; it creates no Agent, model profile, provider endpoint, or Workbench.
- [ ] Everyday context contains the five context notes through the canonical KB
  membership seam; Ask can explicitly pick it and an Agent can select it through
  the existing Context/`kb_id` field; both hydrate edited note contents.
- [ ] Starter text asks useful questions and gives terse examples but asserts
  no owner name, employer, role, relationship, preference, or current goal.
- [ ] Start here states that context is not automatically included in an AI
  request and enters one only when attached; it states that ordinary Desk sync
  still follows existing device pairing; no Constitutional Context is populated.
- [ ] Ordinary seed creates only starter IDs that have never existed: rerunning
  it preserves changed text, names, membership, filing, and AI attachment, and
  does not resurrect a tombstoned starter object.
- [ ] Explicit Reset to seed still tombstones clutter and deliberately restores
  the packaged defaults through an explicit force-restore mode; its confirmation
  says existing Desk objects will be tombstoned and furnished defaults restored.
- [ ] Existing owner-created objects and configured destinations are untouched
  by ordinary seeding. Reset retains its explicitly destructive Desk sweep.
- [ ] The seeded objects edit, rename, move, delete, sync, ground, and open
  through existing primitive paths; no seed-only rendering branch exists.

## Test plan

- **Python:** exact manifest shape; ordinary apply twice; edit every starter
  field then reapply without mutation; tombstone then ordinary apply without
  resurrection; explicit Reset force-restores defaults; KB membership hydrates;
  Ask/recipe grounding receives edited seeded context; no invented-fact guard.
- **Web:** default drawers/notes/Knowledge arrive through ordinary store refresh,
  edit through existing windows, and are explicitly selectable in Ask.
- **Local browser:** inspect the furnished Floor and explicitly attach/switch
  Everyday context in Ask and an Agent at both widths without opening Settings.

## Notes

“Context drawer” is owner language for the experience, not permission to merge
directory placement with semantic grounding. One note may be filed in a drawer
and simultaneously belong to Everyday context through the existing two seams.
Implement ordinary and force-restore as explicit seed modes; do not infer mode
from whether a row happens to be deleted.
