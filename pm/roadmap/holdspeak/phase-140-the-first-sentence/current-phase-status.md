# Phase 140 — The First Sentence

**Status:** active (0/6).

**Last updated:** 2026-08-18.

## Owner mandate

HoldSpeak has become too complex for the value it asks a new person to find.
The owner ordered the cut. The proposed Dashboard Door is cancelled: adding
TODO, calendar, and scheduling furniture would deepen the problem before the
first useful act is clear.

## Goal

Make a fresh HoldSpeak open on one obvious job—dictate one sentence—carry that
sentence through edit, Copy, or Keep as Note, then reveal a robust furnished
default without exposing the system's internal vocabulary.

## Evidence base

[`first-value-audit.md`](./first-value-audit.md) records three independent
read-only Terra audits: a cold fresh-HOME walk, a visible-complexity census,
and a Tuesday-question product ruling. All three reached the same conclusion:
the first-value machinery exists, but the front door hides it.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-140-01 | One obvious door | ready | [story-01](./story-01-one-obvious-door.md) | — |
| HS-140-02 | The sentence becomes useful | backlog | [story-02](./story-02-the-sentence-becomes-useful.md) | — |
| HS-140-03 | Recovery stays here | backlog | [story-03](./story-03-recovery-stays-here.md) | — |
| HS-140-04 | A desk worth opening | backlog | [story-04](./story-04-a-desk-worth-opening.md) | — |
| HS-140-05 | The quiet return | backlog | [story-05](./story-05-the-quiet-return.md) | — |
| HS-140-06 | The cold walk | backlog | [story-06](./story-06-the-cold-walk.md) | — |

## Where we are

The phase is chartered. No implementation story has begun. HS-140-01 is the
only ready story and must land first: move the existing `FirstWords`
composition to the Chair's fresh-owner state and suppress competing first-run
chrome without deleting advanced capability.

## Risk register

| Risk | Guard | Stop signal |
|---|---|---|
| Simplicity forks the product | reuse `FirstWords`, Chair, and onboarding state | a new welcome app, wizard, or capture path appears |
| Hiding becomes capability loss | suppression is conditional on `arrival_required`; Continue later exits it | a normal-Chair path is unreachable after exit |
| Receipt claims success too early | success remains bound to a non-empty transcript | milestone changes on mic open or capture start |
| Recovery becomes a scavenger hunt | errors stay in place; Setup appears only for an exact fix | generic configuration copy or multiple recovery destinations |
| Local happy path secretly needs cloud | exercise fresh HOME with no API key | first sentence requires Models administration or a cloud key |
| Starter content becomes fake biography or demo clutter | prompts/examples only; blank facts remain unknown | seed asserts a name, employer, preference, or relationship the owner never supplied |
| Re-seeding destroys customization | ordinary mode creates never-seen IDs only and does not resurrect tombstones; Reset is explicit force-restore | ordinary seed changes or resurrects an existing starter object |

## Decision log

- 2026-08-18 — Chartered by owner order: “okay, cut it.” Dashboard Door is
  cancelled in favor of The First Sentence.
- 2026-08-18 — The owner's YOLO/open-throttle ruling is not reopened. This
  phase removes cognitive competition, not capability or authority.
- 2026-08-18 — GitHub CI is not a phase gate by owner ruling. Local focused
  suites, production build, and the fresh-HOME walk are the verification path.
- 2026-08-18 — Owner amendment: progressive disclosure must reveal a “very,
  very, very robust default setup” with useful drawers and editable prefilled
  context that can attach to AIs. HS-140-04 added; phase expanded 5→6 stories.
