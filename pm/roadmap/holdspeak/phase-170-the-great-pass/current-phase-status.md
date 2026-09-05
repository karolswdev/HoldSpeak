# Phase 170 - The Great Pass

- **Project:** holdspeak
- **Status:** ACTIVE 2/7
- **Chartered:** 2026-09-05 off main `f8e2739d` (169 The Streamlined Door MERGED via PR #551 → `27eabf0c`; the handover addendum #552)
- **Canon:** docs/internal/CONSTITUTION.md; docs/internal/DESIGN_SYSTEM.md (the interior canon); web/src/desk/surface/contract.md (the species); **docs/internal/UX-CANON.md (the face canon, born this phase)**; pm/roadmap/holdspeak/THE-TUESDAY-ARC.md (the order of the arc; this phase is its horizontal frame + its 170)

## The charter

The owner's words (2026-09-05), verbatim: **"Brother. Fedaykin need to
make a huge UX pass of everything. Is our canon kerpt?"** — after
merging 169 on trust: "I will trust you on this one… LET'S MERGE AND
DEVISE ADDITIONAL PLANS…" and "Let them be fable-5-1 models. Let's show
Arrakis how much we can push HoldSpeak forward."

The honest answer to "is our canon kept": the supreme canon is; the
FACE canon was not written down — the owner's rulings on faces lived in
memory and handovers. This phase writes it (UX-CANON.md), measures every
face against it (the census), fixes what is species-level in the
library so every face lifts at once (the sweep), makes the canon
mechanical (guards), then applies the 169 treatment — design on the
canvas, his word, build to the artboard, rig, walk — to the Concierge
(the arc's 170, the front door of every intelligent feature) and to the
Tuesday faces the census ranks highest.

The chain: 01 the census → 02 the species sweep → 03 the Concierge ∥ 04
the top faces → 05 his walk → 06 docs → 07 close. Exit: his word on his
desk, face by face — "the module we are both proud of" becoming the
desk we are both proud of.

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-170-01 | The census (every surface shot at 1440 + 393 on an isolated desk; the canon-violation scan across the web tree; one ranked table per face by Tuesday use × canon debt) | done | [story-01-the-census](./story-01-the-census.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-170-02 | The species sweep (library-level fixes that lift every face at once; the canon guards made mechanical) | done | [story-02-the-species-sweep](./story-02-the-species-sweep.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-170-03 | The Concierge — the model front door designed and built to the canon (the Tuesday Arc's 170) | in-progress | [story-03-the-concierge](./story-03-the-concierge.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-170-04 | The top faces re-designed and rebuilt (the Tuesday faces ranked by the census: Settings, Meetings aftercare, People/1:1, the Thread, the shade) | backlog | [story-04-the-top-faces](./story-04-the-top-faces.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-170-05 | The walk (the owner's attended walk of the whole desk on a Tuesday; the stopwatch per face; his verdict) | backlog | [story-05-the-walk](./story-05-the-walk.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-170-06 | The docs (the guide re-shot for every rebuilt face; UX-CANON linked from CLAUDE.md and the design system) | backlog | [story-06-the-docs](./story-06-the-docs.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-170-07 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-07-the-close](./story-07-the-close.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**ACTIVE 2/7.** Branch `feat/the-great-pass` off main `f8e2739d`.
**01 DONE:** UX-CANON.md; 17 surfaces × 2 widths shot; 671 canon
violations located and ranked; the rig re-captured green after the
sweep (the after-census). **02 DONE:** all three sweep lanes
landed (P @3dbe8a82, T @b540dd3a, D @bd47897e) — tree 671 → 222 hits;
raw `<button>` 147 → 6, accent rails 8 → 0, egress misses 1 → 0; vitest
2184 green, zero branch-new; the retired setup wizard parked under
`_parked/`. The scanner's false positives fixed (151 real hits) and the ratchet
guards green (ceiling per rule + per face; hard zeros on rails and
egress). **03 designed:** the Concierge on six
boards, counsel RATIFY-W-C paid (Use these disabled beside WAITING;
Anthropic in FOUND; the cloud `Check` with its cost chip; Adjust under
the set with hosts; the downloading board). **04 designed:** the four
faces on twelve boards (arrival needs-you/quiet/393 · Settings hub
640/393 · Speak idle/landed/unset/393 · Meetings list/detail/393);
counsel reading. **The canvas** (18 boards):
https://claude.ai/code/artifact/3fc26e25-1d5f-4796-b2e9-0d4bae9bff20 —
his word on the Concierge unblocks the 03 build; his word on the four
faces (and the N) unblocks 04. **The wire under both is BUILT and
committed** (`/api/concierge/*`; the meetings intelligence run, the
desk needs-you aggregate, the Settings hub read; MCP 197 tools / 35
families). **Full suite (CI shape, -n auto, 2026-09-05 01:50):** 9392
passed; 9 failed = 6 inherited/environment-bound (zero diff vs main in
every file involved: ask grounding ×2 + ask runner need the owner's
real model file under an isolated HOME; kernel broker fences ×2;
product-copy drift) + 3 xdist-only (green serially). Every
branch-new failure of the first run (106 → 9) was paid: the second
`MeetingSummary`, the archive pause in the sanctioned repo, allow-list
sizes, the AGENTS zero law, the Room rig's midnight seed, the Phase 143
censuses, and the 163 stale-bundle law made universal
(`tests/e2e/conftest.py`).

**Decision (2026-09-05 02:00, under the owner's standing goal «all
phases to 180… do not pause to ask»):** the faces of 03 and 04 are
BUILT NOW to the counsel-ratified artboards; the owner's word moves
from before-build to before-MERGE for this phase (a branch is
reversible, a merge is not). His walk of the built faces on his desk
and his word on the canvas are the merge gate; anything he bounces is
rebuilt to his ruling before the PR.
