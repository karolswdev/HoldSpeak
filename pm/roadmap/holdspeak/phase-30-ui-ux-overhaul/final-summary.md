# Phase 30 — UI/UX overhaul ("Signal"): Final Summary

**Opened:** 2026-06-01 (scaffolded) · first ship 2026-06-01 (HS-30-01).
**Closed:** 2026-06-02.
**Chunks shipped:** 9 / 9 (HS-30-01 … HS-30-09).

## Goal — was it met?

> Take HoldSpeak's interface to a genuinely professional level by retiring the
> Workbench aesthetic and shipping **"Signal"** — a bold, distinctive, dark-first
> identity … a full UX overhaul, not a re-skin.

**Met.** The Amiga Workbench look (saturated-blue desktop, VT323 pixel font, hard
four-colour hairlines) is gone. Every one of the five routes — runtime, dictation,
history, activity, companion — plus the shared shell and component library now
renders **Signal**: a near-black layered surface, off-white text, a signature
orange accent reserved for the primary/live/focus moment, real depth + radius +
motion, and a Space Grotesk / Inter / JetBrains Mono type system. The work was
audit-led (HS-30-01 IA spec) and skill-derived (`ui-ux-pro-max`), not ad-hoc.

## Exit criteria (re-run against evidence)

- [x] UX audit + IA spec — `evidence/ux-audit.md`, `evidence/ia-spec.md` (HS-30-01).
- [x] "Signal" design language, skill-derived + signed off — `evidence/design-language-signal.md`, `signal-preview.png` (HS-30-02).
- [x] `tokens.css` + `global.css` Signal; fonts swapped; galleries render — (HS-30-03).
- [x] Shell + every component restyled — (HS-30-04 nav + Settings drawer, HS-30-05 components).
- [x] All five routes redesigned, before/after screenshots — (HS-30-06/07/08; `after-hs0*`).
- [x] Accessibility AA verified (contrast harness), focus rings, reduced-motion — (HS-30-09).
- [x] No backend regressions: `2062 passed, 14 skipped` every commit.
- [x] `final-summary.md` (this file).
- [x] **Zero `--wb-*` Workbench tokens repo-wide** (shim deleted at HS-30-08).

## Stories shipped

| ID | Title | Evidence |
|---|---|---|
| HS-30-01 | UX audit + IA redesign | evidence-story-01.md |
| HS-30-02 | "Signal" design language + sign-off | evidence-story-02.md |
| HS-30-03 | Foundation: tokens + global + fonts | evidence-story-03.md |
| HS-30-04 | Navigation + layout shell (Settings drawer) | evidence-story-04.md |
| HS-30-05 | Component library re-skin | evidence-story-05.md |
| HS-30-06 | Dashboard (`index`) redesign | evidence-story-06.md |
| HS-30-07 | Dictation redesign (two-tier tabs) | evidence-story-07.md |
| HS-30-08 | History + Activity + Companion + shim deletion | evidence-story-08.md |
| HS-30-09 | A11y + motion + polish + exit | evidence-story-09.md |

## Stories cut or deferred

None cut. **One follow-up handed off:** History keeps its **Settings** tab — the
full extraction of Settings *content* into the global shell drawer (HS-30-04) is a
larger `historyApp()` + settings-endpoint refactor. The drawer exists and links to
History → Settings, so settings are globally reachable today; the content move is a
clean next chunk.

## Token migration (the `--wb-*` story)

The plan assumed a token swap would flip everything at once. It couldn't: **108
component/page refs hard-coded `--wb-*`** with context-dependent meaning
(`--wb-white` = text 25 / bg 16; `--wb-black` = border 37 / text 1), so no single
global remap was correct. Resolution: a **temporary `--wb-*`→Signal shim**
(HS-30-03) flipped everything to dark immediately and kept each chunk shippable;
then components (HS-30-05) and pages (HS-30-06/07/08) migrated their refs to
canonical tokens, and the shim was **deleted** (HS-30-08). End state: **0 `--wb-*`
repo-wide.** Lesson for the next themer: a transitional shim is the right tool when
a token rename can't be atomic — but budget the per-surface migration explicitly.

## Accessibility posture

WCAG 2.1 contrast computed for the whole palette (`evidence/a11y-contrast.py`):
all functional pairings **AA or AAA**; the single failing combo (white-on-orange,
2.84) is design-language-forbidden and never shipped. Reduced-motion is honoured
product-wide from one `tokens.css` media block. Accent focus rings on every
interactive element. `--text-faint` (≈4.0–4.7:1) is reserved for non-essential meta.

## Final asset / test posture

- **Routes:** 5/5 redesigned to Signal + the shared shell + 12 components.
- **Tokens:** `tokens.css` is fully Signal (canonical + semantic aliases + scale);
  **zero `--wb-*`**; VT323 + Sora removed; Space Grotesk + Inter + JetBrains Mono in.
- **Tests:** web `npm run build` green; backend full sweep **2062 passed, 14
  skipped** (unchanged from the Phase-29 baseline — UI-only phase, no regressions).
- **Theme:** dark-only (Karol's call); tokens authored so a light variant is a
  later additive layer.

## Handoff to the next phase

- **Available now:** a complete Signal design system (`tokens.css` + the component
  library + the `/design/components` gallery as the living contract), a grouped-nav
  shell with a global Settings drawer, and a reusable headless-Chrome screenshot
  approach for route evidence.
- **Read first:** `evidence/design-language-signal.md` (the system),
  `evidence/ia-spec.md` (the IA).
- **Open follow-ups:** (1) extract History → Settings content into the shell drawer;
  (2) optional command palette (slot reserved, HS-30-04); (3) a light theme if
  desired (additive). None are blocking.
- **Tooling note:** the `ui-ux-pro-max` skill is installed **local-only** under
  `.claude/` (gitignored) — re-vendor it if another machine needs to derive design.
