# Phase 30 — UI/UX overhaul: retire Workbench, ship the "Signal" identity

**Last updated:** 2026-06-02 (HS-30-08 shipped — in-progress, 8/9. **History +
Activity + Companion migrated to Signal and the `--wb-*` shim is DELETED — zero
Workbench tokens repo-wide.** Behaviour-preserving ref inlining + eyebrow headers;
the whole product is now Signal end-to-end. Build green; backend 2062 passed.
History Settings-tab extraction deferred to a follow-up — drawer links to it).

> **Phase status: IN-PROGRESS (8/9).** This is the live pickup doc; it is
> mutable until the phase closes.

> Lineage note: Phases 10 → 12 built the current web look — a design-token
> system (`web/src/styles/tokens.css`) and an Amiga **Workbench-evoking**
> palette + VT323 pixel font ("Workbench voice"). It was a deliberate,
> well-systematized identity, but in daily use it **doesn't work**: the
> saturated-blue desktop, the pixel display font, and the hard four-colour
> hairline grammar read as a retro gimmick that fights a calm, trustworthy,
> local-first productivity tool — poor readability, high-contrast eye strain,
> no depth. This phase replaces it wholesale. Because the token layer is the
> single source of truth and the component tree is plain Astro + scoped CSS,
> the redesign is a **clean swap**, not a migration.

## Goal

Take HoldSpeak's interface to a genuinely professional level by retiring the
Workbench aesthetic and shipping **"Signal"** — a bold, distinctive, dark-first
identity (near-black canvas, off-white text, a signature orange accent, real
depth and motion, Space Grotesk / Inter / JetBrains Mono). This is a **full
UX overhaul, not a re-skin**: a UX audit drives an information-architecture
redesign first, then a skill-derived design system, then the foundation
(tokens + fonts), the navigation shell, the component library, and a
per-page redesign of every route, closing on an accessibility + motion pass.
After this phase every screen looks and feels like one confident product.

The design system is derived with the **`ui-ux-pro-max`** skill
(`.claude/skills/ui-ux-pro-max/`), not invented ad-hoc.

## Scope

### In

- **UX audit + IA redesign** of all five product routes (`index` dashboard,
  `dictation`, `history`, `activity`, `companion`) and the navigation model —
  an audit doc + an IA spec (`pm/roadmap/holdspeak/phase-30-ui-ux-overhaul/
  evidence/ux-audit.md` + `ia-spec.md`).
- **Design language "Signal"** — a written design-language doc derived from the
  `ui-ux-pro-max` skill (style, palette, type scale, depth, motion, density),
  signed off by Karol before any token is written.
- **Foundation rewrite** — `web/src/styles/tokens.css` + `global.css` rebuilt to
  Signal; fonts swapped to Space Grotesk (display) / Inter (UI) / JetBrains Mono
  (data) via `@fontsource`; the `/design/check` + `/design/components` galleries
  prove the foundation.
- **Navigation + layout shell** — `AppLayout.astro` + `TopNav.astro` rebuilt to
  the IA from HS-30-01 (nav structure, responsive shell, optional command entry).
- **Component library re-skin** — every component in `web/src/components/`
  (Button, Panel, Pill, ListRow, Toolbar, EmptyState, InlineMessage,
  ConfirmDialog, CommandPreview, LocalPill, AppMark, HoldMark) restyled to Signal
  with real depth, radius, and motion.
- **Per-page redesign** — new layouts for the dashboard (`index`), `dictation`,
  and the secondary trio (`history`, `activity`, `companion`), each grounded in
  the IA spec, not just recoloured.
- **Accessibility + motion pass** — WCAG AA contrast on the dark surfaces
  (accent-on-dark verified), visible focus rings, keyboard nav, `prefers-reduced-
  motion` honoured; a phase `final-summary.md`.
- Evidence per story is **screenshots of the rebuilt route(s)** + a green
  `npm run build` + a green backend sweep (no Python regressions).

### Out

- Backend / API changes — the Astro front-end is served pre-built under `/_built`;
  no `web_server.py` route or Python behaviour changes (UI-only phase).
- New product features or pages beyond the five existing routes.
- A light theme — Signal is dark-first; a light variant is a possible follow-on,
  tracked as deferred, not shipped here.
- Plugin / meeting-intelligence work (Phases 16 → 29 closed that rollout).
- Hardware / companion-device firmware (Phases 15 / 24 / 25).

## Exit criteria (evidence required)

- [x] UX audit + IA spec exist and name concrete problems + the new IA per route.
      (HS-30-01 — `evidence/ux-audit.md`, `evidence/ia-spec.md`.)
- [x] "Signal" design-language doc exists, is skill-derived, and is signed off
      before HS-30-03 lands. (HS-30-02 — `evidence/design-language-signal.md` +
      `evidence/signal-preview.png`; Karol approved 2026-06-01.)
- [x] `tokens.css` + `global.css` carry the Signal system (no VT323/Sora, no
      saturated-blue desktop); galleries render the foundation; `npm run build`
      green. (HS-30-03 — `tokens.css`'s only `--wb-*` is the temporary shim §3,
      deleted in HS-30-05; backend 2062 passed.)
- [x] Nav + layout shell (HS-30-04) **and every** component in `web/src/components/`
      (HS-30-05) restyled to Signal; component `--wb-*` refs = 0. (Shim deletion
      lands with the last page, HS-30-08.)
- [x] All five routes redesigned to Signal with before/after screenshots
      (HS-30-06 dashboard, HS-30-07 dictation, HS-30-08 history/activity/companion).
      The `--wb-*` shim is deleted — **zero Workbench tokens repo-wide**.
- [ ] Accessibility: AA contrast verified on the dark palette, focus rings
      visible, keyboard-navigable, reduced-motion honoured. (HS-30-09.)
- [ ] No backend regressions: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green across the phase.
- [ ] `final-summary.md` records the before/after and the (deferred) light-theme
      handoff. (HS-30-09.)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-30-01 | UX audit + IA redesign | done | [story-01-ux-audit-and-ia.md](./story-01-ux-audit-and-ia.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-30-02 | "Signal" design language + skill-derived system + sign-off | done | [story-02-design-language-signal.md](./story-02-design-language-signal.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-30-03 | Foundation: tokens + global CSS + fonts + design galleries | done | [story-03-foundation-tokens.md](./story-03-foundation-tokens.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-30-04 | Navigation + layout shell | done | [story-04-nav-and-layout-shell.md](./story-04-nav-and-layout-shell.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-30-05 | Component library re-skin | done | [story-05-component-library.md](./story-05-component-library.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-30-06 | Dashboard (`index`) redesign | done | [story-06-dashboard-redesign.md](./story-06-dashboard-redesign.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-30-07 | Dictation redesign | done | [story-07-dictation-redesign.md](./story-07-dictation-redesign.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-30-08 | History + Activity + Companion redesign | done | [story-08-secondary-pages-redesign.md](./story-08-secondary-pages-redesign.md) | [evidence-story-08.md](./evidence-story-08.md) |
| HS-30-09 | Accessibility + motion + polish + phase exit | backlog | [story-09-a11y-motion-exit.md](./story-09-a11y-motion-exit.md) | — |

## Where we are

**In-progress, 1/9.** Direction locked by Karol: **bold + distinctive, dark-only**
("Signal"), as a **full IA + visual redesign** (not a token-only swap). The
`ui-ux-pro-max` skill is installed at `.claude/skills/ui-ux-pro-max/` (engine + 30
CSVs, smoke-tested) and seeds the design system — its top recommendation for this
product class ("Modern Dark" / "Real-Time Monitor", best-for dev-tools / pro
productivity) matches the chosen Space Grotesk / Inter / JetBrains Mono pairing.

The work is strictly ordered so each chunk is independently verifiable by
rebuild + screenshot: **audit/IA → design language (sign-off gate) → foundation
→ shell → components → pages → a11y/exit**. The token layer
(`web/src/styles/tokens.css`, 276 lines) is the single source of truth and every
component reads from it, so HS-30-03 flips the whole product at once and the
later stories restyle structure on top of the new foundation.

**HS-30-01 shipped.** The UX audit (`evidence/ux-audit.md`) names 12 problems —
saturated-blue/white/pixel/hairline grammar with no hierarchy, a flat ungrouped
nav, **global Settings buried as tab 6 of 6 in History**, fragmented action-items,
duplicated ops surfaces, and Dictation's 7 flat tabs. The IA spec
(`evidence/ia-spec.md`) answers each with a grouped nav (Live / Review /
Configure + a global status cluster + a Settings drawer), one shared
header/panel/rail/empty-loading-error system, and per-route layout intentions —
all **without adding routes**. "Before" screenshots of all five routes +
the component gallery are in `evidence/before/`.

**HS-30-02 shipped.** "Signal" is fully specified + signed off (see
`evidence/design-language-signal.md`, `evidence/signal-preview.png`).

**HS-30-03 shipped — the Signal foundation is live and the whole product renders
dark.** `tokens.css` rewritten to the §9 map (canonical Signal tokens + legacy
semantic aliases repointed + real radius/depth/motion); `global.css` → dark canvas
+ off-white text; fonts swapped to Space Grotesk/Inter/JetBrains Mono (VT323+Sora
removed); galleries render Signal; build green; backend **2062 passed, 14 skipped**.
Verified on the running build (`evidence/after-hs03/`). **Discovery:** 108 component
refs hardcode `--wb-*` context-dependently, so a single clean swap was impossible —
the foundation flips them via a **temporary `--wb-*`→Signal shim** (tokens.css §3),
plus a bounded fix retargeting 16 `--wb-white` backgrounds + 2 `#f5f5f5` footers to
`--surface-2` so the result is clean dark, not light boxes.

**HS-30-04 shipped.** The shell is rebuilt to the IA spec (`evidence/after-hs04/`):
`TopNav` is a grouped nav (Live | Runtime · Review | History, Activity · Configure
| Dictation, Companion) with a dual-encoded active state (accent-tint fill +
weight + accent underbar + `aria-current`); the brand is Space Grotesk with a
glowing mark; the tail holds the status slot + a **⚙ Settings drawer** (lifted out
of History per IA §2 — slide-over, accessible, `#settings` deep-link, interim
content linking to History → Settings until HS-30-08 migrates it); below 880px the
groups collapse behind a menu toggle. Wired vanilla (Alpine is per-page). Command
palette **deferred** (no dead control shipped).

**HS-30-05 shipped.** Every component in `web/src/components/` is restyled to
Signal (`evidence/after-hs05/components.png`): eyebrow panel headers, `--elev-1` +
`--radius-lg` cards, primary `--glow-accent`, flat-grey disabled (hatch retired),
selected rows with an inset accent marker. All 30 component `--wb-*` refs migrated
to canonical tokens (components now 0). The shim stays for the 59 page refs.

**HS-30-06 shipped.** The runtime dashboard is redesigned to the IA spec
(`evidence/after-hs06/dashboard.png`): the page's local Workbench CSS (panels,
hero, buttons, pills) is migrated to Signal — raised cards, eyebrow headers, hero
accent-glow on active, primary glow; the rail is grouped under **Intelligence /
Work / Operations** eyebrow labels; transcript stays dominant. Page `--wb-*` 8→0.
No Alpine binding touched (CSS + inserted label divs only).

**HS-30-08 shipped.** History, Activity, and Companion are migrated to Signal
(`evidence/after-hs08/`) and the **`--wb-*` compat shim is deleted — zero Workbench
tokens repo-wide.** Ref migration was a behaviour-preserving inline of the shim's
mapping + an eyebrow-header tweak (activity); no JS hook touched. The whole product
is now Signal end-to-end. **Deferred:** the full extraction of History's Settings
*tab* content into the shell drawer (a larger `historyApp()` refactor) — the drawer
exists + links to it; flagged for a follow-up.

**Next:** HS-30-09 — accessibility (AA contrast verify on the dark palette), motion
+ `prefers-reduced-motion`, a cross-route polish pass, and the phase exit
(`final-summary.md`).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Dark palette fails AA contrast (esp. orange-on-dark, muted text) | medium | Pick accent/text ramps for AA at design-language time; verify in HS-30-09 with a contrast check, not by eye. | Any primary text/affordance < 4.5:1 (3:1 large) → adjust the token, don't ship. |
| "Full IA redesign" balloons scope | medium | IA spec (HS-30-01) fixes the surface before any page story starts; page stories restyle, they don't add features. | A page story grows new product features → cut to a later phase. |
| Token swap leaves orphaned Workbench styles in scoped component CSS | medium | HS-30-05 sweeps every component; HS-30-03 exit asserts zero `--wb-*` / VT323 references repo-wide. | `grep -r "wb-\|VT323"` finds live references after HS-30-05 → not done. |
| Front-end has no automated visual tests; "build passes" ≠ "looks right" | high | Evidence is **screenshots per route** via the dev server, plus `npm run build`; the `/design/components` gallery is the component contract. | A route ships without a screenshot in evidence → contract violation. |

## Decisions made (this phase)

- 2026-06-01 — **Retire the Workbench aesthetic entirely** (no nostalgic nod kept)
  in favour of a bold, dark, distinctive identity. — author: Karol.
- 2026-06-01 — **Dark-first ("Signal")**: near-black canvas, off-white text,
  signature orange accent (`#FF6B35`, evolving the heritage Workbench orange),
  Space Grotesk / Inter / JetBrains Mono, real depth + motion. — author: Karol.
- 2026-06-01 — **Full IA + visual overhaul**, not a token-only re-skin: a UX
  audit and IA redesign precede the visual work. — author: Karol.
- 2026-06-01 — **Derive the system with the `ui-ux-pro-max` skill**, signed off
  before tokens are written, rather than inventing a palette ad-hoc. — author:
  Karol + agent.
- 2026-06-01 — **Treat the UI as greenfield** (no backwards-compat ceremony for
  the old token names): the old look is replaced, not deprecated-in-place. —
  author: agent (per project note: the product is not yet really released).
- 2026-06-01 — **Dark-only** for this phase (no light theme): ship Signal dark,
  author tokens so a light variant is a later additive layer. — author: Karol.
- 2026-06-01 — **Lift global Settings out of History** into a shell-level Settings
  drawer (not a new route), per the IA spec — fixes the worst discoverability
  failure without growing the route set. — author: agent (HS-30-01 finding).
- 2026-06-01 — **Temporary `--wb-*`→Signal shim in tokens.css §3** (HS-30-03):
  108 component refs hardcode `--wb-*` context-dependently, so a clean one-shot
  removal was impossible. The shim flips them to dark now; HS-30-05 migrates the
  refs and deletes §3. Still greenfield — a two-story transition aid, not shipped-
  user compat. — author: agent (HS-30-03 discovery).

- 2026-06-01 — **Command palette deferred** (HS-30-04): the IA reserved a `⌘`
  slot; shipping a non-functional control is worse than none, so no ⌘ button
  ships. The concept stays reserved; revisit once the page surfaces stabilize. —
  author: agent (HS-30-04 decision).

## Decisions deferred

- A **command palette / quick-switcher** — reserved concept; revisit after the
  page redesigns (HS-30-06/07/08) settle the surface inventory. Default if never
  picked up: ship without one.
