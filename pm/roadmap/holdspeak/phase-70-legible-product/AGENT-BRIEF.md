# Phase 70 — Agent Brief (read this first)

**Phase 70 — The Legible Product (Out-of-the-Box).** Opened on owner
direction, in the owner's own words: *"I literally am confused myself about
the product, and IMO, that's a VERY, very bad sign."* The mission is to make
HoldSpeak's web flagship legible enough that a brand-new user — and the
person who built it — can say what it is and what to do first, in one breath,
within ten seconds of the screen.

## 0. Mission

Reconcile the web surface to the story. The **story** is settled and crisp:
`docs/internal/POSITIONING.md` — *"one local copilot, two modes: dictation
and meetings."* The **surface** has sprawled to **16 top-level pages**
(`index, welcome, setup, dictation, history, activity, cadence, commands,
desk, workbench, profiles, companion, presence, settings, design, docs`)
presented as a flat list of ~14 co-equal destinations with visible
redundancy (three first-run surfaces, three canvas surfaces, two ambient
surfaces). That gap — between a two-sentence product and a fourteen-door
control panel — is the confusion. Phase 70 closes it.

## 1. The one thing you must not get wrong

**Do not re-label the sprawl — actually simplify the mental model.** A nav
rename that still leaves fourteen equal doors is a failure. The test is
behavioral: sit a fresh person (or the owner) in front of a freshly-launched
hub and they can, unprompted, (a) say what HoldSpeak is, (b) name the two
modes, and (c) take a first action that produces a win — with the power
features present but never *confronting* them. If they can't, the phase isn't
done, no matter how clean the diff.

Corollary: **no route may 404.** Every retired/moved/renamed route keeps a
redirect (bookmarks, the CLI launch nudge, docs links, and the route
pre-flight guard all point at real URLs). This is presentation + IA, not new
backend features — behavior is byte-identical except where a consolidation
deliberately changes it, and every such change is called out in evidence.

## 2. The two load-bearing decisions (owner-confirmed, not up for relitigating)

The owner made these two calls at scaffold (2026-06-30) via a direct choice:

- **Decision A — Bold reorg + consolidate** (over an additive front-door).
  Restructure the nav to the two modes; merge and retire redundant surfaces
  (three first-run pages → one, dictation + its journal/learning/nudges made
  whole, meetings + import + archive + aftercare made whole). Fewest
  destinations, clearest story. Pages get demoted or absorbed, not preserved
  for their own sake.

- **Decision B — Tuck the power features into a "Studio" tier** (over
  elevating them to a third pillar, and over hiding them entirely). Workbench,
  Agent Desk, Cadence, Commands, Profiles, and Presence stay fully built, but
  live behind one collapsed **Studio** group so a first-run user is not
  confronted by them. Discoverable when ready, invisible when not.
  POSITIONING's "two modes" stays canon; Studio is the advanced tier below it.

## 3. The target information architecture

```
HoldSpeak
├─ Home        what is this + your next action
├─ Dictation   voice typing + the journal + the learning digest + pre-briefing
├─ Meetings    capture / import + the archive + aftercare
└─ Studio ▾    (collapsed, advanced — not a front-door concern)
      Workbench · Agent Desk · Cadence · Commands · Profiles · Presence
   Settings
```

Four primary destinations + Settings, not fourteen. The route→home map (the
consolidation intent — see the stories for the exact per-route disposition):

| Today's route | Phase-70 home |
|---|---|
| `/` (data dashboard) | **Home** — reframed as "what is this + your next action" |
| `/welcome`, `/setup` | **one** first-run path (wizard teaches the two modes → lands on Home); the survivor's health/model bits fold into Settings |
| `/dictation` | **Dictation** |
| `/activity` (pre-briefing/nudges) | folded into **Dictation** (nudges feed "Dictate with this") |
| `/history` (the archive) | **Meetings** |
| `/cadence`, `/workbench`, `/companion` (Agent Desk), `/commands`, `/profiles`, `/presence` | **Studio** tier (collapsed) |
| `/settings` | **Settings** |
| `/design`, `/docs/*` | not primary nav (dev/reference; unchanged) |

## 4. Rules (the standing set)

PMO gate (fresh `.tmp/CONTRACT.md`, ≥7 `[x]`, one story-flip per commit with
its `evidence-story-NN.md` in the same commit); cadence per shipping commit
(story header + this `current-phase-status.md` row/Last-updated/"Where we
are" + the project `README.md` phase row/Last-updated/Current-phase);
branch `phase-70-legible-product`, one PR per slice, merged on green CI; full
suite via `uv run pytest -q --ignore=tests/e2e/test_metal.py`. The recent
commits carry the `Co-Authored-By` + `Claude-Session` footer — match the
current convention (the older "no trailer" note is superseded; verify against
`git log` before your first commit).

## 5. Gotchas that WILL bite (carried from the Phase-69 handover)

- **Astro scoped CSS never reaches JS/`innerHTML`-injected DOM.** New
  primitives are `<style is:global>`; screenshot-verify, don't trust that a
  class compiled into the bundle.
- **A new/renamed page needs THREE registrations** or it 404s / isn't swept:
  (a) the `.astro` page, (b) a route in `holdspeak/web/routes/pages.py`,
  (c) an entry in `tests/e2e/test_route_preflight.py` `PAGE_ROUTES`. When you
  retire a route, add its **redirect** here too and update the guard.
- **The built bundle (`holdspeak/static/_built/`) is GITIGNORED.** Edit
  `web/src`, then `cd web && npm run build`; commit source only.
- **Alpine factories load via `?raw` + `new Function`, NOT ES import** on the
  older pages (`profiles.astro`, `companion.astro`); the dictation cockpit is
  real ES modules (Phase 54). Know which surface you're touching.
- **The hub picks a RANDOM free port** and doesn't reliably print the URL;
  find it via `lsof -nP -iTCP -sTCP:LISTEN | grep -i python`. LAN `.43` is
  unreachable from sandboxed Bash (use `dangerouslyDisableSandbox`).

## 6. What this phase is NOT

- Not new product features. No new mode, no new connector, no new plugin.
- Not a re-theme. Phase 69 already brought the felt craft; this is
  organization, arrival, and naming on top of that craft.
- Not a mobile-roadmap change. The iPad DeskOS/Primitive-Framework paradigm
  is a separate track; Phase 70 does not port the diorama to web. (If the
  owner later wants the Desk paradigm ON web, that is a distinct, larger
  phase — flagged as a follow-up, not smuggled in here.)
- Not a Studio rebuild. The power features keep working as-is; they are
  grouped and framed, not re-implemented.

## 7. Definition of done (phase-level)

- The nav is Home · Dictation · Meetings · Studio▾ · Settings, everywhere.
- Home answers "what is this + your next action"; it is not a data dashboard.
- One first-run path (no user meets three arrival surfaces); it teaches the
  two modes and lands the first win.
- Dictation and Meetings each cleanly contain their whole mode.
- Studio is one collapsed, clearly-secondary tier; a first-run user never
  gets dumped into it.
- Every primary surface has a guiding empty state (no scary blanks).
- Naming is canonical; POSITIONING records the IA + the "Studio" name; the
  README front door reflects Home + two modes + Studio.
- No route 404s (redirects for everything moved); full suite green; a
  first-run play-walk (launch → Home → one dictation win) is screenshot-proven.
