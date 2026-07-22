# Phase 102 — The Refit

**Status:** IN PROGRESS (5/7, 2026-07-22). Chartered by the owner's
direct order after the round-9 reflex round merged: *"I really want
us to create another phase, a phase where we will do exact, direct
and precise refactorings to a variety of things."* Six named
targets, two with screenshots; the owner's words per target are
quoted verbatim in each story.

**Last updated:** 2026-07-22 (HS-102-05 done; HS-102-06 next).

## Why this phase exists

Phase 101 ratified the interior canon and rebuilt the worst innards;
round 9 made the desk's object primitives behave. But the owner's
eyes found six working surfaces still composed as web forms wearing
window chrome — and named them, one by one, with screenshots for the
worst. This phase is the refit: not a new canon, not new
capabilities — the EXISTING canon applied exactly, surface by
surface, to the rooms where work actually happens.

The design authority is already gated: the interior canon
(DESIGN_SYSTEM.md §"The interior canon (HS-101)") was approved by
the owner at HS-101-02 ("Well, merge it in for me, and then keep
going...") and amended at that gate (aerogel not accent rails;
fluidity is canon). Nothing here invents design law — every story
cites the rule it applies. Constitution: Article VI (honesty — raw
wire dumps in the glass are dishonesty by laziness), Article VII
(the interface serves the person), Article VIII (native-grade
craft), Article IX.4 (the felt verdict outranks every green suite).

## The method (per story — the round-9 shape, now the law here)

1. **Hands first.** Operate the surface HEADED on a staged hub —
   1440 AND 393 — and write the defect ledger from what the hands
   and eyes find, not from the code. The owner's verbatim words and
   screenshots seed each ledger; the ledger may grow, never shrink.
2. **Recompose at the cause**, citing the canon rule each change
   applies. Wire contracts stay byte-identical unless a story says
   otherwise.
3. **Prove with hands**, headed, both viewports: drive the real
   flows (create, edit, record, ask, review), screenshot every
   state, READ every screenshot. Machine guards ride along (token
   gate, vocabulary, interior canon, geometry walk, vitest).
4. One story flips per gated commit; before/after evidence in the
   story's evidence file.

## Scope

- In: the six named refits (Runs on, Live Meeting, Ask AI, the
  Meetings wings, the selection mark, Speech Settings) and the walk
  legs / guards that pin their behavior.
- Out: new capabilities or routes; canon changes (ratified at
  HS-101-02); launcher/chrome/window-grammar (ratified); iPad parity
  (consumes this after). The HS-101-04 sitting loop stays open in
  parallel — its remainder inventory feeds future rounds, not this
  scope.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-102-01 | Runs on — destinations easy as heck | done | [story-01-runs-on](./story-01-runs-on.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-102-02 | Live Meeting — a working face | done | [story-02-live-meeting](./story-02-live-meeting.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-102-03 | Ask AI — the composer refit | done | [story-03-ask-ai](./story-03-ask-ai.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-102-04 | The Meetings wings — Outcomes / Record / Artifacts | done | [story-04-meetings-wings](./story-04-meetings-wings.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-102-05 | The selection mark yields to open | done | [story-05-selection-mark](./story-05-selection-mark.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-102-06 | Speech Settings — one composed face | backlog | [story-06-speech-settings](./story-06-speech-settings.md) | — |
| HS-102-07 | Closeout — the owner's sitting | backlog | [story-07-closeout](./story-07-closeout.md) | — |

## Where we are

Scaffolded from the owner's six-target order (2026-07-20), the same
day round 9 (the reflex round, PR #365) merged. HS-102-01 is ready;
each build story starts with its hands-first ledger. The phase
closes on the owner's sitting over the assembled chain
(HS-102-07), per Article IX.4.

**2026-07-21 — each build story (01-06) gained a "Design direction"
section**, grounded in a live headed drive against a fresh staged
instance (not the spec prose): the exact raw-wire fields, form
stacks, and stat strips the owner's words convicted, confirmed
current and unfixed, plus the specific existing kit component each
story must reuse (`RuntimeDestination`, `SurfaceBay`, `SurfaceLibrary`,
`Material`, `SurfaceStream`, `SurfaceGroup`/`SurfaceSettingRow`,
`EditInPlace`) so the six refits converge on ONE kit rather than six
independent near-misses. HS-102-07 grew a matching acceptance bullet:
the sitting checks shipped surfaces against their story's direction,
not just the walk legs, and refuses a second implementation of any
named component.

**2026-07-22 — HS-102-01 (Runs on) shipped.** Live-drive ledger
confirmed the exact form-stack the story convicted; the fix reused
`RuntimeDestination`'s choice-bay pattern and closed the
`SurfaceBay` expand-slot gap the design direction named (now a kit
piece, not a local fork). One real defect caught mid-drive and fixed
before evidence capture: `Checkbox` (self-labeling) double-rendered
its text inside a `SurfaceSettingRow` that also carried the label —
swapped for the bare `SurfaceToggle` `RuntimeDestination` itself
uses. Proven live at 1440 and 393 (create via the switchboard's own
ghost bay, edit-in-place, inline URL refusal before save, make
default, two-step delete); `/api/profiles` wire untouched. New guard:
`test_profiles_core_never_regresses_to_a_field_stack`. Full vitest
(312/312), tsc, token gate, and the interior-canon + vocabulary
guards green. Next: HS-102-02 (Live Meeting).

**2026-07-22 — HS-102-02 (Live Meeting) shipped.** The live drive
confirmed the room even lacks a reachable "before recording" state in
normal use (the Record chip both opens and starts) — the stat strip,
Bookmark form, Intent routing preset, Preview-route textarea, and
Deferred-plugin-jobs dump all rendered at the FIRST instant of a live
meeting. `LiveCore.tsx` gained the same `door`/`doorOpen` gear split
`DictationCore.tsx` already uses (Intent routing/Preview
route/Deferred jobs/Devices moved behind "Configure meeting");
`MetricStrip` is gone, replaced by one `SurfaceFacts` line; the
transcript now rides `SurfaceStream`/`SurfaceStreamEntry`; Bookmark is
a `+ Bookmark` verb opening a transient inline composer (the wire only
accepts a label at creation, so the POST defers to commit rather than
firing empty). Proven live: start → real captured segment → bookmark
→ configure door → stop, both viewports, `RecordOrb` entry point at
393px. New guard: `test_live_core_never_regresses_to_a_stat_strip`.
Full vitest (312/312), tsc, token gate, interior-canon + vocabulary
guards green. Next: HS-102-03 (Ask AI).

**2026-07-22 — HS-102-03 (Ask AI) shipped.** `AskPanel.tsx`
recomposed to the one-well grammar `PersonaChat.tsx` and the
capability-card composer already use (`desk-chat-well` /
`desk-chat-composer` / `desk-chat-well-foot`) — mic + question + verb
inline, `RunsOnPicker`/`GroundingSection`/`RailsPicker` folded into
the well's foot as captions (a scoped CSS rule strips their
bordered-card chrome only in that context, leaving PersonaChat's own
placement untouched). `desk-pullout-md`'s raw-markdown `<pre>` is
gone; the printed answer renders through `Material` (HS-101 round
8's renderer, reused not reinvented). Proven live end to end,
including a REAL grounded ask against the LAN model at `192.168.1.43`
(registered as a `Runs on` destination through the unchanged
`/api/profiles` wire): selected a note → picked the destination →
asked → a correct, `Material`-rendered answer with an honest egress
badge and receipt → Keep minted a real desk artifact. (A first pass
of the evidence wrongly claimed the LAN model was unreachable from
this sandbox and deferred that leg to HS-102-07 — the owner caught
it; corrected same day, the deferred bullet on HS-102-07 removed.)
New guard: `test_ask_panel_never_regresses_to_a_pre_box_or_section_stack`.
Full vitest (312/312), tsc, token gate, interior-canon + vocabulary
guards green. Next: HS-102-04 (the Meetings wings).

**2026-07-22 — HS-102-04 (the Meetings wings) shipped.** Artifacts:
the `Disclosure`+`SurfaceCode` dump replaced by `SurfaceLibrary`/
`SurfaceLibraryTile` — the SAME components Blocks already uses —
artifact body as the tile FACE via `Material`, an Open verb to the
round-9 object card. Outcomes: `SurfaceRow` gained a `quiet` prop (kit
addition); the meetings rail sorts needs-you (error/warning tone)
rows first, settled rows read quieter. Record: a leading "Record
meeting" verb + quiet caption sit above the existing round-7 drop
well. Proven live with REAL data, not fixtures: a transcript imported
through `/api/meetings/import`, run through the real plugin chain
(`holdspeak intel --reroute`) against the LAN model at `192.168.1.43`
— 4 real synthesized artifacts, correctly library-composed at both
viewports. One defect caught and fixed mid-drive: plugin artifact
bodies self-title with a heading matching their own name, duplicating
against the tile spine — stripped before render. `meetingflow` walk
leg grown and run live (populated, not just empty): budget still 3
interactions, artifacts wing confirmed `.surface-library`. New guard:
`test_history_core_artifacts_wing_is_the_library`. Full vitest
(312/312), tsc, token gate, interior-canon + vocabulary guards green.
Next: HS-102-05 (the selection mark yields to open).

**2026-07-22 — HS-102-05 (the selection mark yields to open) shipped.**
A click-grammar fix, not a surface recompose: opening a card (mouse
double-click, touch tap-open, the world context menu's Open, and the
a11y activation layer — all four paths through `openPullout`) now
calls the store's existing `setSelected([])` right after opening,
clearing the ring + "N selected · Ask AI" bar in the same frame the
card appears. Guarded by `if (!state.askOpen)` throughout so the Ask
composer's held selection rope (the HSM-16-04 carve-out) is never
stripped mid-compose — verified live: select → open Ask AI → double-
click a different object → Ask AI keeps its original context while
the second object's card opens alongside it. `openAsk()`'s comment
("the selection stays visible behind the panel") reworded to name the
carve-out explicitly, since it no longer describes every open.
`web/src/desk/gl/engine.ts` (`onUp`'s two open branches) and
`web/src/desk/gl/WorldStage.tsx` (context-menu Open + the a11y
layer) — four call sites, one mechanism, no new store action.
`__hsWorldProbe()` grew a `selected` field so the walk can assert
ring state without a DOM proxy. Proven live on a real seeded desk
(`uat.stage --recipe seeded-desk`) at 1440 and 393: mark-then-open
screenshots show the ring/bar present after a single click and gone
the instant the card opens. `scripts/desk_gl_walk.py`'s `smoke()` leg
grew three assertions on the existing tap-open path (marked before,
unmarked + bar-gone after) and passed live: `smoke: tap-open ok, drag
ok (330px), lasso bar=1, zone drag 319px`. Full vitest (312/312), tsc,
build, token gate, interior-canon + vocabulary guards green. No new
interior-canon guard — this story's regression coverage is the grown
walk leg, not a raw-wire-dump pattern. Next: HS-102-06 (Speech
Settings).
