# Phase 70 — The Legible Product (Out-of-the-Box)

**Status:** IN PROGRESS (3/9) — 2026-06-30. Read [`AGENT-BRIEF.md`](./AGENT-BRIEF.md) first.

**Last updated:** 2026-06-30 (**opened + scaffolded** on owner direction, in the owner's own words:
*"I literally am confused myself about the product, and IMO, that's a VERY, very bad sign."* Phase 69
brought the web flagship to the iPad's felt craft; Phase 70 fixes what craft can't: the surface has
sprawled to **16 top-level pages** presented as ~14 co-equal doors, while the story is two sentences
("one copilot, two modes"). The two load-bearing calls are owner-confirmed at scaffold: **A — bold
reorg + consolidate** (not an additive front-door), **B — tuck the power features into a "Studio" tier**
(not a third pillar, not hidden). Nine stories authored; branch `phase-70-legible-product` on open.)

## The thesis

The confusion the owner feels is the **information architecture diverging from the story.** The story
is settled and crisp (POSITIONING: *one local copilot, two modes — dictation and meetings*). The web
surface is a flat list of fourteen destinations with visible redundancy (three first-run surfaces,
three canvas surfaces, two ambient surfaces). Phase 70 reconciles the surface to the story so a
first-time user — and the person who built it — can say what HoldSpeak is and what to do first, in one
breath, within ten seconds. This is not craft (Phase 69 did that) and not features; it is arrival,
organization, and naming.

## The target information architecture (owner-confirmed)

```
HoldSpeak
├─ Home        what is this + your next action
├─ Dictation   voice typing + the journal + the learning digest + pre-briefing
├─ Meetings    capture / import + the archive + aftercare
└─ Studio ▾    (collapsed, advanced) Workbench · Agent Desk · Cadence · Commands · Profiles · Presence
   Settings
```

Four primary destinations + Settings, not fourteen. Per-route disposition is in the AGENT-BRIEF §3 map.

## Decisions carried in (owner, 2026-06-30)

- **A — Bold reorg + consolidate.** Restructure the nav to the two modes; merge/retire the redundant
  surfaces (three first-run pages → one; dictation + journal/learning/nudges made whole; meetings +
  import + archive + aftercare made whole). Pages get demoted or absorbed, not preserved for their own
  sake. (Rejected: an additive guided front-door that leaves the sprawl underneath.)
- **B — Tuck the power features into a "Studio" tier.** Workbench, Agent Desk, Cadence, Commands,
  Profiles, Presence stay fully built but collapse behind one Studio group so a first-run user is not
  confronted by them. "Two modes" stays canon; Studio is the advanced tier below it. (Rejected:
  elevating them to a third pillar / changing the positioning canon; hiding them entirely behind a flag.)

## Scope

- **In:** the nav reframe (spine), a Home that orients, one consolidated first-run, Dictation and
  Meetings each made whole, the Studio tier, guiding empty states, naming + positioning coherence, and
  a closeout that proves no dead doors + a clean arrival.
- **Out:** new product features (no new mode/connector/plugin); a re-theme (Phase 69 did the craft);
  porting the iPad DeskOS/Primitive-Framework paradigm to web (a distinct, larger phase if ever — a
  flagged follow-up, not smuggled in); re-implementing any Studio tool (they are grouped and framed,
  not rebuilt). Behavior is byte-identical except where a consolidation deliberately changes it.

## Exit criteria (evidence required)

- [ ] Nav is Home · Dictation · Meetings · Studio▾ · Settings, everywhere; Studio collapsed by default
      (HS-70-01).
- [ ] Home answers "what is this + your next action"; it is not a data dashboard; both mode cards are
      co-equal and unmistakable (HS-70-02).
- [ ] Exactly one first-run arrival surface (no user meets three); it teaches the two modes and lands
      the first win on Home; retired first-run routes redirect (HS-70-03).
- [ ] Dictation contains typing + journal + learning + corrections + pre-briefing; `/activity` folds in
      (HS-70-04). Meetings contains capture/import + archive + aftercare with entry actions promoted
      (HS-70-05).
- [ ] Studio is one collapsed, clearly-secondary tier; off-by-default tools shown off; a first-run user
      never lands there (HS-70-06).
- [ ] Every primary surface has a guiding empty state; load-vs-empty distinct; no-prose copy (HS-70-07).
- [ ] Naming canonical; POSITIONING records the IA + the "Studio" name; README/index/Getting Started
      reflect the new front door; voice guard green (HS-70-08).
- [ ] No route 404s (redirects for everything moved); full suite green; the launch→Home→first-win
      play-walk screenshot-proven; the 10-second legibility read-test recorded (HS-70-09).

## Stories

| Story | Title | Priority | Status | Depends on |
|-------|-------|----------|--------|------------|
| HS-70-01 | The IA spine: nav reframe to two modes + Studio | HIGH | **done** (TopNav → `Home · Dictation · Meetings · Studio▾`; Studio is a native `<details>` tier of the 7 browsable advanced surfaces, auto-open on an active route; `Route` union + 4 page slugs updated; Activity parked in Studio, Presence excluded as a nav-less overlay; 4 nav states screenshot-proven, route pre-flight 2 passed; see [evidence](./evidence-story-01.md)) | owner A+B |
| HS-70-02 | Home: "what is this + your next action" | HIGH | **done** (`/` reframed from the meeting-runtime dashboard into an orientation Home: identity + a `/api/setup/status`-fed next-action band + the two modes as co-equal cards with guiding subtitles + a quiet Studio link; the 1378-line live dashboard moved to `/live`; empty + seeded screenshot-proven; see [evidence](./evidence-story-02.md)) | 01 |
| HS-70-03 | One arrival: consolidate the three first-run surfaces | HIGH | **done** (`/welcome` is the single arrival — guard + CLI nudge route new users there, it teaches both modes and lands on Home; `/setup` demoted from a second "Welcome" to the "Setup & health" surface and surfaced from Settings; screenshot-proven; 13 tests + full suite green; see [evidence](./evidence-story-03.md)) | 01, 02 |
| HS-70-04 | Dictation mode, made whole (folds `/activity`) | MED | **todo** | 01 |
| HS-70-05 | Meetings mode, made whole (`/history` → Meetings) | MED | **todo** | 01 |
| HS-70-06 | The Studio tier: power features framed + contained | MED | **todo** | 01 |
| HS-70-07 | Guiding empty states everywhere (no scary blanks) | MED | **todo** | 02 |
| HS-70-08 | Naming + positioning coherence (the docs story) | MED | **todo** | 01–07 |
| HS-70-09 | Closeout: no dead doors, one clean arrival, proven | HIGH | **todo** | 01–08 |

Suggested build order (cheapest-high-impact-first, spine early): **01 → 02 → 03** (the arrival trio
that fixes the confusion outright) → **04 → 05 → 06** (each mode/tier made whole) → **07** (empty
states) → **08** (docs/naming lock) → **09** (closeout). 04/05/06 are parallelizable after 01.

## Where we are

**2026-06-30 — HS-70-03 done (one arrival).** Three first-run surfaces became one arrival. `/welcome` is
the single canonical first-run surface: the HS-70-02 guard sends every first-run user there, and the CLI
launch nudge already did (`test_cli_nudge_points_first_run_user_at_the_wizard`); verified it already
teaches both modes (hero + the Done step's "Dictate anywhere" / "Run a meeting" cards) and lands on Home
(`href="/"`), so the wizard needed no change. `/setup` was the confusing part — a second "Welcome to
HoldSpeak" cockpit. Its hero eyebrow was retitled to "Setup & health", demoting it to the returning-user
health/fix-it surface, and a "Setup & health check →" link was added to the Settings aside so it is
discoverable from Settings. Decision recorded: demote-and-retitle over delete/redirect, because many
returning-user paths (Home's next-action band, the Desk readiness chip, the CLI nudge, the wizard's
troubleshoot link) rely on `/setup` as a calm fix-it cockpit — redirecting them into the full-screen
wizard would degrade that. The arrival is genuinely one surface; `/setup` is no longer an arrival.
Screenshot-proven (`welcome-arrival` / `setup-health` / `settings-health-link`); setup + welcome +
preflight 13 passed; full suite 3045 passed, 37 skipped. Next: HS-70-04 (Dictation mode made whole —
fold `/activity` in).

**2026-06-30 — HS-70-02 done (Home).** The front door now orients instead of dumping a dashboard. `/`
was the 1378-line live-meeting runtime (Alpine hero + capture); it moved verbatim to `/live`
(`current="meetings"`, registered in pages.py + PAGE_ROUTES) and `/` became a focused Home: the
positioning one-liner as identity, a next-action band fed by `/api/setup/status` (surfaces the server's
`primary_action` until the user is set up, hidden after), the two modes (Dictation / Meetings) as
co-equal `.signal-card`s with white-on-gradient glyph chips, one-line what-it-does, dynamic subtitles,
and action buttons, plus a quiet dashed Studio link that never outshouts the modes. Dynamic subtitles
fill pre-rendered `textContent` only (no injected DOM → scoped CSS holds). Empty state guides ("Nothing
yet. Hold your key and speak." / "…Capture or import your first meeting.") rather than blanking — a
down payment on HS-70-07. Proven both ways: `home-empty.png` (fresh DB: NEXT band + guiding subtitles)
and `home-seeded.png` (a seeded meeting + journal entry fill `Last: …`). Route pre-flight 2 passed
(Home + `/live` swept); full suite 3045 passed, 37 skipped. Next: HS-70-03 (consolidate the three
first-run surfaces into one arrival that lands on Home).

**2026-06-30 — HS-70-01 done (the IA spine).** The nav now states the story: `TopNav.astro` went from
three inline groups (Live / Review / Configure, ~14 co-equal doors) to `Home · Dictation · Meetings ·
Studio ▾ · Settings`. Studio is a native `<details>` disclosure (zero JS, keyboard-native) holding the
seven browsable advanced surfaces (Workbench, Desk, Agent Desk, Activity, Cadence, Commands, Profiles)
behind an "ADVANCED" eyebrow; it auto-opens when the active route lives inside it, and the summary
carries a subtle "you are here" tint. The `Route` union moved in lockstep (AppLayout + TopNav;
`runtime`→`home`, `history`→`meetings`, `+cadence`) and four page `current=` slugs were retargeted
(`index`, `history`, `design/check`, `cadence` — the last previously had no `current`, so its nav item
never lit). Two transitional calls recorded: Activity is parked in Studio pending its HS-70-04 fold into
Dictation; Presence is excluded from the nav (a nav-less HUD overlay would be a dead-end) and stays in
Settings, with the HS-70-06 Studio index free to card it. No routes moved or added. Proven: `npm run
build` green (17 pages), route pre-flight 2 passed (every route served/listed/swept for zero page errors
under the new nav), and four nav states screenshot-verified (wide collapsed / wide expanded /
`/workbench` auto-open+active / mobile inline) — not just class-in-bundle. Next: HS-70-02 (reframe `/`
into a Home that answers "what is this + your next action").

**2026-06-30 — opened + scaffolded.** Authored from the Phase-69 web handover's "what is NOT done"
(§6) plus the owner's confusion signal. Grounding pass confirmed the real surface: 16 pages in
`web/src/pages/`, a flat `TopNav.astro`, three overlapping first-run surfaces (`/welcome` + `/setup` +
the `/` guard), two ambient surfaces (`/activity` + `/cadence`), three canvas surfaces (`/desk` +
`/workbench` + `/companion`). POSITIONING is the fixed story to reconcile to. The two load-bearing
calls (reorg-aggression + power-feature disposition) were put to the owner and answered (A + B above),
so every story is grounded, not speculative. Next: an agent starts HS-70-01 (the nav spine) on branch
`phase-70-legible-product` under the PMO gate.
