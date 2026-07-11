# The Inventory Directory — what to look at, what to expand

> **Historical inventory axis:** The web/iPad/iPhone columns below describe what
> the phase record claimed, not executable implementation identity. Protocol v2
> maps each claim to `web_react` or an exact Swift root plus form factor before
> UAT can award evidence. Compact width is never native proof by itself.

**Derived 2026-07-08** by an 8-agent parallel sweep (Opus 4.8) of the whole
phase record — HoldSpeak desktop phases 0–90, HoldSpeak Mobile 1–27, and the
public docs corpus read as promises. **255 capabilities** enumerated. This is
the *starting map* Phase 2's sweeps refine on real glass; it is not yet the
verified ledger.

This directory is the answer to the owner's ask: *a directory of what's to be
looked at and what needs to be expanded upon.* The four domain files below are
the "what to look at"; the surface columns and the expansion callouts are the
"what needs expanding."

## The four files

| File | Domain | Capabilities | Feeds |
|---|---|---|---|
| [10-input-and-intelligence.md](./10-input-and-intelligence.md) | dictation, learning loop, wake word, languages, macros, activity, on-device models, onboarding, presence | 76 | HSU-2-02 |
| [20-meetings.md](./20-meetings.md) | capture, import, the 14 plugins, artifacts, aftercare, proposals, archive | 42 | HSU-2-03 |
| [30-desk-mesh-agents.md](./30-desk-mesh-agents.md) | the desk, workbench, ask, runtime profiles, the mesh edge, the belt, steering/factory, sync, handoff arcs | 113 | HSU-2-04 |
| [40-trust-and-egress.md](./40-trust-and-egress.md) | every egress point + every consent gate (cross-cut) | 24 | all three sweeps |

Sibling docs: [../PROTOCOL-NOTION.md](../PROTOCOL-NOTION.md) (how a sitting is
shaped), [../RECIPE-WORKLIST.md](../RECIPE-WORKLIST.md) (the state recipes to
build), [../PHASE-3-PLAN.md](../PHASE-3-PLAN.md) (the coverage-pack plan — the
output that IS Phase 3's input).

## The headline finding: the iPhone parity is unverified

The parity claim is three surfaces — web desk, iPad, iPhone. The record proves
the first two and is nearly silent on the third:

| Surface | Record says present (✅) | Record says absent (—) | **Unknown (❓)** |
|---|---|---|---|
| web desk | 221 | 18 | 16 |
| iPad | 142 | 15 | **98** |
| **iPhone** | **25** | 17 | **213** |

**213 of 255 capabilities have no record-level answer for the iPhone.** That is
not a claim the phone is broken — it is that the phone was never the surface a
phase *proved itself on* (the diorama is iPad-first; HSM-20 is the lone compact-
width phase). This is the single largest thing UAT exists to find out, and it is
why nearly every scenario must be sat on the phone even where the record shrugs.
An `❓` that the owner resolves to `✅` on the phone is a parity win banked; one
that resolves to `—` is a roadmap gap the sitting surfaced.

## How to read a row

Each row is one capability: a priority, the three surface marks, a one-line
title, the stable ledger key, the shipping phase(s), and the state recipe(s) a
scenario for it would need. The marks are the **record's** claim with an
evidence pointer in the source rows (`inv_rows.json`); the sweep's job is to
turn ❓ into ✅/— by opening the real surface, and to catch a ✅ the record
asserts but the live product no longer honors (later phases retired earlier UI
more than once — the web was re-crafted in phases 69–73, the IA collapsed to
four doors in 70).

## What needs expanding (the sweep worklist, by signal)

- **The whole iPhone column.** 213 ❓. HSU-2-02/03/04 each carry an explicit
  "verify on iPhone" pass; where a capability genuinely has no compact-width
  surface, the row becomes `—` *with a reason*, and that reason is reviewable.
- **iPad ❓ on the input side (dictation depth).** The dictation cockpit, blocks,
  KB, journal, learning loop, correction memory are all ✅ on web and ❓ on
  device — the device may mirror, partially mirror, or defer to the hub. 30-odd
  rows to resolve.
- **The handoff arcs are the parity claim at its most end-to-end** and the
  thinnest-tested: author-on-iPad → run-on-hub → read-on-web, steer-a-machine-
  from-the-phone, record-on-iPad → intel-on-hub → review-on-web. Enumerated as
  their own rows (search `handoff` / `cross_machine` / `mesh.handoff` /
  `sync.` keys) — each needs a two-device sitting.
- **The trust cross-cut is must-test-heavy (15/24) and easy to under-test.**
  Every egress badge, the loopback-token gate, the steering arming grant, the
  key allow-list, "no telemetry," "the key never syncs" — these are the promises
  a stranger's hands must not be able to break. They get their own honest-failure
  beats (see PROTOCOL-NOTION).
- **Record-vs-product discrepancies flagged by the sweep** (204 rows carry an
  `expand_notes` in the source) — most are "verify this survived the re-craft."
  The sweep resolves each to confirmed / retired / changed.

## Provenance & honesty

- Raw rows (with per-surface evidence pointers and full scenario hints):
  `inv_rows.json` in the run scratchpad; the sweep may re-run the fleet to
  refresh.
- The marks are a **model's reading of the record**, not a device test. Nothing
  here is a verdict. The verdict is the human sitting; this is the script that
  sends them to the right screens.
