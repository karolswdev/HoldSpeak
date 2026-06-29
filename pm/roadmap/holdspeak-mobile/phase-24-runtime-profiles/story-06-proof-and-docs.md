# HSM-24-06 — Cross-surface parity proof + the docs story

- **Status:** done (2026-06-28) — the cross-surface never-sync proof (a key from EITHER ingress, sync
  push or REST body, never reaches ANY read surface; the served shape is field-for-field the agreed
  schema) + the entry-point docs (README, docs/MODELS.md "Runtime profiles", docs/SECURITY.md §5 key
  custody). Evidence: [evidence-story-06.md](./evidence-story-06.md). Full `uv run pytest` 3040 passed;
  voice guard green. **Phase 24 closes with this story.**

## Problem

Equilibrium isn't "it builds on each surface" — it's "the contract is honored on each surface, or
honest `n/a`." This story is the proof gate + the docs (every phase gets its own docs story).

## The design

- **The parity proof:** one named profile authored once, observed in equilibrium:
  - Create a "Claude" OpenAI-compatible profile on the iPad (key → Keychain).
  - It appears (shape only) on the desktop hub and on web via sync; **no surface ever received the
    key** (assert on each serializer/payload).
  - Assign an agent to it on each surface; run the agent; confirm it hits the right backend, with
    each surface sourcing the key from its own custodian (iPad Keychain / hub secrets).
  - An `.onDevice` GGUF profile renders honest `n/a` on web.
  - The egress badge reads each profile's scope on each surface.
- **The never-sync invariant** gets a dedicated cross-surface assertion (the security crux).
- **Docs:** update the entry points — README (the "where intelligence runs" story: basic vs
  advanced), `docs/` model/runtime page, and the iOS/web settings help — plus a short
  `SECURITY`-style note that keys are device/hub-custodial and never sync.

## Scope

- The cross-surface proof script/checklist (real metal where applicable).
- The never-sync cross-surface test.
- Entry-point docs + the security note.

## Test plan

- The full suites green (`swift test`, `uv run pytest`, web smoke).
- The proof walked: one profile, three surfaces, key never crosses; agents run on their assigned
  backends; `n/a` honest.

## Done when

Profiles are demonstrably in equilibrium across desktop / iPad / iPhone / web, the key never syncs
(proven), and the entry-point docs + security note ship in the same closing commit.
