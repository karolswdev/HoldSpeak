# Phase 102 — The Refit

**Status:** IN PROGRESS (2/7, 2026-07-22). Chartered by the owner's
direct order after the round-9 reflex round merged: *"I really want
us to create another phase, a phase where we will do exact, direct
and precise refactorings to a variety of things."* Six named
targets, two with screenshots; the owner's words per target are
quoted verbatim in each story.

**Last updated:** 2026-07-22 (HS-102-02 done; HS-102-03 next).

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
| HS-102-03 | Ask AI — the composer refit | backlog | [story-03-ask-ai](./story-03-ask-ai.md) | — |
| HS-102-04 | The Meetings wings — Outcomes / Record / Artifacts | backlog | [story-04-meetings-wings](./story-04-meetings-wings.md) | — |
| HS-102-05 | The selection mark yields to open | backlog | [story-05-selection-mark](./story-05-selection-mark.md) | — |
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
