# Phase 135 — The Comfy Chair

**Status:** in-progress (7/15).

**Last updated:** 2026-08-17.

## Owner mandate

The Comfy Chair arc, leg one (2026-08-16 reflection + quiz rulings):
fewer doors, one beautiful jobs-first front door — "something that
pleases the user, but also something we can drive independently with
MCP"; "that door needs to be beautiful… Workbench 2.0+ on steroids."
The owner ruled all eleven design questions (recorded in
[assets/design-laws.md](./assets/design-laws.md) and the arc memory);
the law book was drafted within those rulings and RULED by counsel
(assets/design-laws-counsel-ruling.md — ten laws ratified, conditions
folded, three open questions settled). Workers implement the laws
verbatim: the draft + the ruling record together are the contract.

Also chartered here by counsel recommendation: the 59→60 migration P0
surfaced during Phase 134 (the owner's real DB fails to open on
current main) as story 01 — the hub must open its own desk before the
desk gets a new front door.

## Goal

The Chair is HOME: a jobs-first launcher-place in the ratified Signal
Workbench material — four fixed lanes (Brief, Follow-Through, Meetings,
Agents) informing at a glance, every action opening a DeskWindow
(single-instance, focus-not-duplicate), a capture hero with the mic at
its heart (tap records; voice can trigger it; Ask AI one tap away), a
six-sound mechanical palette, and the law-book debts paid (lamp
overflow, wing affordance, sizing tokens, sparse-surface chrome). The
spatial floor stays fully intact one dock-button away. Desktop grammar
only this phase; the narrow shell is Phase 136.

## The evidence base (all in assets/)

- design-laws.md — the RULED ten-law book (L1 depth … L10 sparse).
- design-laws-counsel-ruling.md — ratifications with conditions,
  settled questions (Chair↔Floor dock button; fixed lane order;
  ember-only on the Chair), the five demanded additions, and the arc
  shape this charter follows.
- five-jobs-baseline.md — the stopwatch numbers the Chair must beat
  (Record 1 click / TODO homeless / Ask two-doors / no voice trigger).
- kit-census.md, face-walk.md, design-system-counsel-ruling.md — the
  EXTEND verdict evidence.

## Settled design (implement, don't relitigate)

The owner's eleven rulings + the counsel's settlements: Chair is home
at every width; EVERYTHING-WINDOWS; composite lanes, no new data
model; three button species, no fourth; sound on by default (sfx.ts
module, NOT CSS tokens; 3-instance pool cap; mono OGG; global toggle;
reduced-motion mutes); ember the only interactive accent (kind-tints
categorical only; accent-gradient ONLY on capture hero + Record Orb);
one density law; curated dozens per lane; 960px desktop minimum;
Chair↔Floor = dock button; lane order Brief→Follow-Through→Meetings→
Agents, fixed; single-instance-per-surface (open twice = focus);
the shelf (Cmd+K) remains canonical discovery; TODO-home is Wave-2 —
the Follow-Through lane header carries a forward-compatible
"New commitment" verb slot (hidden until Wave 2 lands).

## Scope

### In

The thirteen stories below: the P0 migration fix; law codification
(L6+L7 CSS fixes, L9 sizing tokens, L10 sparse rule); the Chair shell
+ home routing; the four lanes; the capture hero; the sound palette;
docs + the walk.

### Out

- The narrow shell / tab bar / DeskShellRouter (Phase 136 — depends on
  this phase's Chair surface).
- The TODO primitive / manual commitment creation (Wave 2); the
  Speak-vs-Ask-AI door merge (Wave 2); note auto-save; silent-Deliver
  error surfacing (pipeline-reliability story elsewhere).
- The 393w desktop-shell bugs (dock overflow, menubar clipping) — the
  narrow shell eliminates them by design in 136; the desktop grammar
  declares its 960px floor here.
- Any Swift/iPad work; Constitution changes; virtualization (P2, with
  archives).

## Constitutional grounding

- **Article II (honest product):** lanes render only truthful state;
  the sparse-surface law removes chrome that outweighs data; the lamp
  law ends nowrap text bleeding past windows.
- **Article VI.1 (states its own limits):** the capture hero names what
  a tap does; hidden verb slots stay hidden, not dead.
- **Article IX (real-runtime proof):** the phase closes on a
  screenshot walk at 1440 and 960 plus the five-jobs stopwatch re-run
  — the Chair must move the baseline numbers.
- **Article XI + ledger-not-gate:** every Chair verb opens surfaces or
  fires existing admitted verbs; the door adds zero new side doors.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-135-01 | The hub opens its own desk | done | [story-01](./story-01-migration-fix.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-135-02 | Lamps wrap, wings look pressable | done | [story-02](./story-02-lamp-wing-laws.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-135-03 | The sizing tokens land | done | [story-03](./story-03-sizing-tokens.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-135-04 | Sparse surfaces shed chrome | done | [story-04](./story-04-sparse-surfaces.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-135-05 | The Chair shell | done | [story-05](./story-05-chair-shell.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-135-06 | The Chair is home | backlog | [story-06](./story-06-chair-is-home.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-135-07 | The Brief lane | backlog | [story-07](./story-07-brief-lane.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-135-08 | The Follow-Through lane | done | [story-08](./story-08-follow-through-lane.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-135-09 | The Meetings lane | backlog | [story-09](./story-09-meetings-lane.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-135-10 | The Agents lane | backlog | [story-10](./story-10-agents-lane.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-135-11 | The capture hero | backlog | [story-11](./story-11-capture-hero.md) | [evidence-story-11](./evidence-story-11.md) |
| HS-135-12 | The desk clicks | done | [story-12](./story-12-sound-palette.md) | [evidence-story-12](./evidence-story-12.md) |
| HS-135-13 | Docs and the walk | backlog | [story-13](./story-13-docs-and-walk.md) | [evidence-story-13](./evidence-story-13.md) |
| HS-135-14 | The chrome speaks Workbench | backlog | [story-14](./story-14-chrome-speaks-workbench.md) | [evidence-story-14](./evidence-story-14.md) |
| HS-135-15 | Creation operates | backlog | [story-15](./story-15-creation-operates.md) | [evidence-story-15](./evidence-story-15.md) |

The ask each story answers, in one line: 01 — the owner's real desk
opens on current main; 02 — no system text bleeds past a window and
every tab reads as touchable; 03 — the raw-px hole gets its seven
tokens; 04 — an empty surface shows verbs and an empty well, not
filter chrome; 05 — the Chair exists with its lane contract, capture
hero slot, and single-instance windows; 06 — HoldSpeak opens ON the
Chair, the floor one dock button away; 07-10 — each lane informs at a
glance and opens its window; 11 — the mic hero records on tap, hears
"start meeting", and Ask AI is one tap away; 12 — six mechanical
sounds, on by default, one toggle, reduced-motion silent; 13 — the
docs teach the door and the walk proves it moved the five-jobs
numbers.

## Suggested order

01 and 02-04 in parallel (disjoint); 05 after 03 (tokens first); 06
after 05; 07-10 in parallel after 05 (disjoint lane files); 11 after
05; 12 any time; 13 last, cannot be waived. Waves: {01,02,03,04} →
{05,12} → {06,07,08,09,10,11} → 13.

## Amendments

- **2026-08-17, owner-directed (visible amendment 2):** story 15 added
  on the setup-flows joy audit (57 shots): agent creation is a DEAD
  END (editor never opens — the flow does not operate), Run enabled
  with nothing to run, and a lying empty state. The smallest
  operate-breakers only; the full setup-joy redesign (cadence
  comprehensibility, progressive disclosure, workflow run affordance,
  the Agent/Agents naming collision) charters as the arc's next leg on
  the audit evidence.
- **2026-08-17, owner-directed (visible amendment):** story 14 added
  mid-phase — the system icon family regenerated to Workbench-2.0
  hygiene through a fixed 8-color palette mold via PixelLab
  (assets/icon-palette.png), plus the note-editor mic alignment fix.
  Mandated by the owner with screenshots in hand ("that level of
  hygiene. It was beautiful."). Cadence's deeper UX illegibility goes
  to the setup-flows audit → the arc's next leg, not this story.

## Ledger

- **Wave-one gate (2026-08-17):** 5832 passed, one single-run xdist
  flake (`test_meeting_session.py::test_stop_completes_without_deadlock_during_final_transcription_and_intel`),
  3/3 green serially — fourth distinct timing flake of the arc, all
  ledgered for BACKLOG Candidate Z.
- **Icon style RATIFIED bright** (owner, verbatim: "AMIGA OS
  FOREVER"); the first dark mold rejected ("Too gloomy. This is not
  an RPG"). The bright palette is the assets/icon-palette.png.

## Held owner questions

1. Lane hiding/collapse (deferred by counsel Q2 ruling — future story;
   confirm at sitting).
2. The 59→60 migration fix ships here; the sitting confirms whether
   the tolerant mir_profile fallback (Phase 134 leniency) retires next
   wave per counsel.

## Exit criteria (evidence required)

- [ ] The owner's real DB (schema 59 backup copy) migrates 59→60 clean
  in a test using a COPY — never the live file — and the hub boots on
  it.
- [ ] gadget-lamp text wraps/truncates per L6 (regression test);
  inactive wings carry the L7 treatment (visual + test).
- [ ] The seven L9 tokens exist in design-tokens.json + generated CSS;
  the named highest-traffic raw-px sites migrated.
- [ ] Surfaces under the sparse threshold hide filter chrome and show
  verbs + empty well (L10, tests).
- [ ] The Chair renders with four fixed lanes, curated-dozen bounds,
  capture hero slot, and single-instance window opening (tests +
  shots).
- [ ] `/` lands on the Chair at ≥960px; the Floor dock button swaps to
  the spatial floor and back; the floor is unchanged.
- [ ] Each lane: truthful data from its existing surface, header
  opens the window, one-verb actions work; Follow-Through carries the
  hidden New-commitment slot.
- [ ] Capture hero: tap starts recording (state visible in hero);
  spoken "start meeting" starts recording; Ask AI reachable in one
  tap from the Chair.
- [ ] sfx.ts: six sounds, pool cap 3, global Settings toggle,
  prefers-reduced-motion mutes; sounds on the hero + window
  open/close/land per L4.
- [ ] Docs entry points teach the Chair; the walk: screenshot walk at
  1440 + 960 across Chair + lanes + floor-swap, five-jobs stopwatch
  re-run with numbers vs baseline, zero console errors, full suite
  zero regressions.

## Where we are

HS-135-01 shipped: the 59-to-60 migration P0 fixed. Root cause: SCHEMA_SQL
carried CREATE INDEX idx_mesh_workers_identity referencing node_id before
_migrate_columns added the column. Pre-schema column guard in
_migrate_renames ensures mesh_workers has node_id and credential_generation
before SCHEMA_SQL runs. Orchestrator independently verified the real backup
copy migrates clean (schema 60, 4 meetings and 44 kernel_operations intact).
HS-135-02 shipped: L6 lamp overflow fixed (gadget-lamp truncates with
title tooltip; .is-block variant wraps block system messages; two
settings-models lamps converted to block). L7 wing affordance fixed
(inactive wings: --text-muted + --wash-1; hover escalates to --wash-2;
active untouched). 27 tests green across gadgets + wings suites.
HS-135-03 shipped: L9 sizing tokens landed. Seven tokens in
design-tokens.json semantic layer (--size-touch 40px, --size-key 48px,
--size-chip 27px, --size-btn 28px, --size-icon-sm 16px, --size-icon-md
20px, --size-icon-lg 32px); three rejected duplicates documented in
drift note. Generator updated to handle doc-only entries. 21 raw-px
sites migrated across surface.css (7), gadgets.css (9), chrome-menus.css
(5). Pixel-identity-preserving. 46 vitest + 8 interior canon tests
green.
HS-135-04 shipped earlier: sparse-surface chrome shedding.
HS-135-05 shipped: the Chair shell exists. Chair.tsx renders hero slot +
four fixed lanes (Brief, Follow-Through, Meetings, Agents) via the lane
composition contract (ChairLane: maxItems prop default 12, Surface
primitives only, onOpenInWindow on header + rows, optional footer verb).
300ms all-blank fallback renders one SurfaceState (counsel condition 2).
Ember-only: chair.css uses no --accent-cool or --accent-gradient.
Single-instance-per-surface: the window-opening seam already implemented
the rule (windowFactory.ts:86-94 deduplicates + focusPanel; pullout
opener does the same at compositorSlice.ts:184-188) -- no code change
needed, 5 tests prove the existing behavior. laneContract.ts renamed
from lane.ts to avoid macOS APFS case-insensitive collision with
Lane.tsx. 17 vitest green (12 Chair + 5 window-seam).
HS-135-12 shipped: the desk clicks. Six synthesized mechanical sounds
(key-down 35ms, key-up 25ms, latch 75ms, land 60ms, file 15ms, error
115ms) generated via Python stdlib (wave/struct/math) with filtered
noise bursts + sine ticks, sharp attack/fast decay envelopes, peak 0.25
(quiet). OGG/Opus via ffmpeg + WAV fallback; 16.4KB total (both formats).
sfx.ts: typed SfxName enum, lazy AudioContext, buffer cache, pool cap 3
(oldest dropped), global enable via localStorage + sfx-off CSS class,
prefers-reduced-motion mutes. Wiring: MicButton (key-down/up + error),
windowFactory (latch on open/close), deliveryTerminal + steering (land
on success, error on refusal), DeskFilingStrip (file on toggle, error on
failure). Settings: desk_sounds bool in UIConfig (default true), validated
in settings_service.py, DESK SOUNDS CheckGadget in Appearance module
wired to toggleSfx(). design-tokens.json: "sound" documentation section
(names only, no --sfx-* CSS properties per counsel A.L4). Two honest
caveats: OGG encoded as Opus not Vorbis (local ffmpeg lacks libvorbis;
Opus is a better codec with broad support); the very first sound play
per session misses (buffer loads async) but all six preload in parallel
after the first user gesture. 10 sfx tests + 1003 full vitest + 39
settings tests green.
HS-135-08 shipped: the Follow-Through lane. FollowThroughLane.tsx
composes directly with SurfaceSection/SurfaceRows/SurfaceRow (not
ChairLane) -- a contract-preserving composition choice: ChairLane's
LaneItem places meta inside the onOpen button wrapper, which nests
interactive elements when verbs are buttons; composing with Surface
primitives directly uses the SurfaceRow verbs slot (outside the button
wrapper) for the complete/dismiss actions. Data from
/api/follow-through/board (no new endpoints); order OVERDUE then NOW
then WAITING to the maxItems bound; each item shows owner initials + due
age; complete (done) and dismiss verbs reuse the existing
/api/follow-through/complete action. Header-click opens Intelligence on
the Follow-Through wing via openIntelligence({ view: "follow-through" }).
The counsel-mandated newCommitmentVerb prop exists (typed ReactNode|null,
default null) and renders nothing when null (Article VI: hidden = absent,
not disabled). Registry entry added to lanes/index.ts keyed as
"follow-through" (matching LaneId). 10 lane tests + 12 Chair tests
green (22/22).
