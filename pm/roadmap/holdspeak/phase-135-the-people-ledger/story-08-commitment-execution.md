# HSEGHS001HS104-135-08 — Commitments become evidenced work

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** 135-03, 135-04, 135-07
- **Unblocks:** durable relationship follow-through and project-grounded delegation
- **Owner:** primary adjudicator

## Problem

A People commitment can appear in Follow-through but cannot be opened, delegated,
linked to an output, or explained historically. Project context also has no stable
place in the relationship model.

## Scope

- **In:** in-place commitment inspector; send to an existing Workbench; linked
  Workbench status/result; explicit satisfaction with evidence snapshot and rationale;
  append-only commitment history and counts; stable Project link/unlink on a
  relationship; project basics/resources carried into Workbench grounding; Project
  Memory deep link.
- **Out:** automatic agent execution, automatic satisfaction, new Workbench lifecycle,
  automatic project/person inference, cross-person productivity comparisons.

## Acceptance criteria

- [ ] Clicking a commitment opens an in-place inspector rather than doing nothing.
- [ ] Sending to Workbench creates one idempotently linked item through the existing
  Workbench authority and preserves the relationship commitment as lifecycle owner.
- [ ] Workbench output/status hydrates back into the inspector; satisfaction records
  rationale and available Workbench evidence without being automatic.
- [ ] History shows accepted/open/satisfied/evidenced counts plus the append-only
  timeline and survives reopen.
- [ ] Relationships can link existing Projects; delegation grounds the item with
  project basics and resource refs and opens Project Memory in-world.

## Test plan

- Focused People service and HTTP flow: project link → request → commitment →
  Workbench item → result → satisfaction → history → reopen.
- Focused PeopleCore interaction: open inspector, see delegation/satisfaction verbs,
  inspect history and Project concepts.
- TypeScript and API-surface drift checks.
- Static authority review: Workbench executes; People decides satisfaction; neither
  duplicates the other's lifecycle.
