# HS-119-03 — Seed revision

- **Project:** holdspeak
- **Phase:** 119
- **Status:** backlog
- **Depends on:** HS-119-02 (regression sweep confirms schema stability)
- **Unblocks:** HS-119-04 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The current seed dumps 15+ demo objects onto the desk: sample meetings,
fake notes, placeholder zones with invented content. This is seeded
flattery. A new user opens the desk and sees a busy surface that looks
like someone else's workspace. Nothing is theirs. Nothing is real.

Article VI is explicit: "No demo state, no seeded flattery, no fallback
that hides a failure." The seed should create a toolkit — the minimum
set of objects a user needs to start configuring their own workspace.
Honest at zero, ready to configure.

When this ships, the seed button on the empty desk creates:

- **Inference target profiles:** the named configurations a user
  points their workbenches at. Not preconfigured endpoints — profiles
  with placeholder credential fields the user fills in.
- **A starter workbench:** pre-wired to the local resolver profile
  so voice drawer resolution works out of the box.
- **One or two starter zones:** "Inbox" and "Work" (or similar) —
  empty containers ready to receive content, not prefilled with
  demo data.

That's it. No sample meetings, no fake transcripts, no placeholder
notes, no invented content. The desk starts quiet and ready.

**Articles served:** VI (honest by construction — no demo state, no
seeded flattery; counts are honest at zero), II (everything is a
primitive — seeded objects are real DeskPrimitives, not demo
fixtures), IV (voice as input — the resolver profile is pre-wired so
voice works immediately), I (the Desk is the operating surface — the
seed creates a usable desk, not a showroom).

## Deliverables

1. **Inference target profiles.** The seed creates these named
   profiles:

   - `local-4B-resolver` — for voice reference resolution
     (HS-118-05). Points at the local 4B model. Pre-wired as the
     resolver profile on the starter workbench.
   - `local-intelligence-small` — for lightweight agent tasks.
     Points at a local small model. Placeholder endpoint.
   - `local-intelligence-medium` — for heavier agent tasks.
     Points at a local medium model. Placeholder endpoint.
   - `cloud-openai` — OpenAI API profile. Placeholder API key
     field. Egress badge: cloud.
   - `cloud-anthropic` — Anthropic API profile. Placeholder API
     key field. Egress badge: cloud.

   Each profile is a real DeskPrimitive with the correct schema.
   Placeholder fields are visibly empty — not filled with fake
   values. The egress badge (Article III) is set correctly:
   local profiles show "local", cloud profiles show "cloud".

2. **Starter workbench.** The seed creates one workbench:

   - Name: "Workbench" (or similar neutral name).
   - Resolver profile: wired to `local-4B-resolver`.
   - No items, no schedule, no grounding. Empty and ready.
   - The workbench is functional: the user can drop objects onto
     the inlet, type instructions, and run — provided they have
     a model endpoint configured.

3. **Starter zones.** The seed creates one or two zones:

   - "Inbox" — a general-purpose receiving zone.
   - "Work" — a project-oriented zone.
   - Both are empty. No prefilled content. No demo items.

4. **Remove the current noisy seed.** The existing seed function
   (wherever it lives) is replaced, not extended. The old demo
   objects — sample meetings, fake notes, placeholder content — are
   removed entirely. If the old seed data lives in fixture files,
   those files are deleted or archived.

5. **Seed button behavior.** The seed button on the empty desk
   creates this baseline in one action. After seeding, the desk
   shows the inference profiles, the workbench, and the zones —
   all empty, all real, all ready to configure.

6. **Idempotence.** Running the seed on a desk that already has
   objects does not duplicate or overwrite. The seed checks for
   existing objects by kind/name and skips creation if they exist.

## What NOT to do

- Do NOT seed sample meetings, transcripts, or notes. Those are
  demo state.
- Do NOT fill placeholder fields with fake values (fake API keys,
  fake endpoints). Empty is honest.
- Do NOT create more than the minimum toolkit. The seed is a
  starting point, not a tour.
- Do NOT remove the seed button itself. An empty desk still needs
  a way to bootstrap the toolkit.

## Test plan

- `uv run pytest -q tests/ -k seed` — existing seed tests pass
  (or are updated to match new seed content).
- New test: seed creates exactly the expected profiles (5),
  workbench (1), and zones (2). No other objects.
- New test: seed on an empty DB produces valid DeskPrimitives
  (schema validation passes).
- New test: seed on a desk that already has objects is idempotent —
  no duplicates.
- New test: inference profiles have correct egress badges
  (local for local profiles, cloud for cloud profiles).
- New test: starter workbench has the resolver profile wired to
  `local-4B-resolver`.
- New test: no demo content exists after seeding — no sample
  meetings, no fake notes.
- Visual at 1440: seed on empty desk, verify the desk shows
  profiles + workbench + zones, all empty, all openable.
