# Phase 46 — Documentation Excellence & the 10-Second Hook

**Status:** CLOSED ✅ (6/6). Opened 2026-06-06 on user direction ("a dedicated
phase that will guide us through scaffolding/updating documentation … the main
README is too low on cool facts of the app, and slightly too large and
repetitive. People love the graphics, so that stays … other documentation files
probably also need a big lift").

**Last updated:** 2026-06-07 (**Phase 46 CLOSED ✅ (6/6)** — HS-46-06 closeout:
`final-summary.md` written; before/after captured (README **205 → 157**, index
list → map, a guide gains a real screenshot + footer); invariants re-asserted
(all 6 graphics kept; honesty; doc-drift + link + plugin-count + image-ref guards
8 passed; `npm run build` ✓; 0 `_built/`; docs-only — full suite **2365 passed,
17 skipped**, after confirming a 2-test Playwright flake passes in isolation); PR
to `main` opened. Project-KB product/UX legibility handed to **Phase 47**. Prior:
**HS-46-05 — Coverage & discoverability: DONE**. A
**feature → doc matrix** in the audit doc maps 16 user-facing capabilities →
guide home → README hook → index journey: **no orphan features, no orphan docs**.
Gaps closed: the index now names **actuators**, and the user-reported **"project
KB" confusion** is fixed in the docs (a plain definition on first use + a gloss on
`kb-enricher` + a `DOCS_STYLE.md` glossary entry) — its deeper **product/UX
legibility teed up as new Phase 47**. No stale residue. Guards 8 passed; full
suite 2365/17. Next: HS-46-06 (closeout + PR). Prior: **HS-46-04 — Visual lift:
DONE**. A repeatable
`scripts/screenshot_docs.py` (boots a real server over seeded state — no mic/LLM —
and writes `welcome.png` / `journal.png` / `history.png` to
`docs/assets/screenshots/`) + three real UI shots embedded with alt+caption: the
journal in the **README** ("See it learn"), the welcome wizard in **Getting
Started**, the `/history` artifact cards in **Meeting Mode**; Intelligent Typing
already carried 9 from Phases 40/41/45. A new **image-ref guard**
(`test_all_embedded_image_refs_resolve`) now validates `<img src>` + markdown
images across the README + docs. Pixellab art kept (additive); `npm run build` ✓; 0
`_built/` tracked. Guards 8 passed; full suite 2365/17. Next: HS-46-05 (coverage
matrix) → HS-46-06 (closeout + PR). Prior: **HS-46-03 — Docs voice & structure +
elevated index: DONE**. A style guide (`docs/internal/DOCS_STYLE.md`: voice + the standard
page skeleton + privacy callout + cross-link/anchor rules); a **uniform `## See
also` footer across all 13 docs** (renamed the two strays, added the missing ones);
and `docs/README.md` rebuilt as a **journey map** (Start here · Dictate · Meet ·
Extend · Operate & Trust), in lockstep with the README's "Where to go next".
Voice+structure, not a rewrite — reference docs kept their depth. A guard catch
(example links in a code fence) fixed honestly. Guards 7 passed; full suite
2365/17. Next: HS-46-04 (visual lift — real UI screenshots) + HS-46-05 (coverage
matrix). Prior: **HS-46-02 — The README, reimagined: DONE**. The
README went spec-sheet → product pitch: a 10-second hook ("Hold a key. Speak. It
types — anywhere. 100% local. And it learns you.") + a "Why it's different"
cool-facts strip (the journal/replay "it learns you" story above the fold), every
pixellab graphic kept, the 52-line plugin table + 22-line AIPI prose cut to
teasers+links, the raw config block linked out, pre-release stated once —
**205 → 152 lines** (26%). Honest per the HS-46-01 audit (every cool fact true;
install extras + anchors verified). Guards 7 passed; full suite 2365/17. Next:
HS-46-03 (voice & structure) + HS-46-04 (visual lift). Prior: **HS-46-01 — Doc
truth audit & drift fix: DONE**.
`docs/internal/DOC_AUDIT_2026-06.md` inventories all 18 live user-facing/root
docs with a Fresh/Minor-drift/Stale verdict against a code-verified canonical-facts
table. 4 drift findings fixed across 6 docs: presence is config-backed not
env-var-only [README, ITG §11, GETTING_STARTED]; the phantom `intel_cloud_timeout_seconds`
config key removed [MEETING_MODE_GUIDE]; the missing `pipeline` connector kind added
[CONNECTOR_DEVELOPMENT]; the stale `Listening...`/`Thinking...` device pushbacks
removed [DEVICE_PROTOCOL]. A new guard pins the README plugin count to the registry.
The deep-link anchors flagged by an auto-pass were verified *correct* and left
alone. Suite 2365 passed, 17 skipped. Next: HS-46-02 the README reimagining.)

## The thesis — why this phase

**The product outgrew its docs.** Thirteen phases shipped since the last
dedicated documentation pass (Phase 33, OSS readiness) — the journal + replay,
the moment-of-truth, actuators I/II, desktop presence, the first-run wizard, the
config cockpit, persistent memory. The README and guides have accreted, not been
composed. Verified against the live tree:

- **The README sells like a spec sheet, not a product.** 205 lines that open
  with a competent one-liner and then list features. No 10-second hook, no "why
  this is different," and the best stories (it *learns you*; your **voice** now
  gets the afterlife your **meetings** do; 14 real LLM plugins; 100% local) are
  buried or missing. The user's read: *too low on cool facts.*
- **It repeats itself.** "What it does", "Intelligence Pipeline", and "Meeting
  intelligence plugins" re-describe overlapping ground; the pre-release status is
  stated twice; the AIPI-Lite companion gets two long paragraphs for an optional
  device. The user's read: *slightly too large and repetitive.*
- **The graphics are great — and underused.** The pixellab art (logo, workflow
  map, operator-loop GIF, AIPI device) is a genuine asset. **It stays.** But the
  *app itself* is never shown — there are zero real UI screenshots in the README
  or guides, despite a beautiful journal, `/history`, cockpit, and presence HUD.
- **The guides have drifted + lack one voice.** 4,677 lines across 13 docs
  (`PLUGIN_AUTHORING` 808, `INTELLIGENT_TYPING_GUIDE` 668, `MEETING_MODE_GUIDE`
  601, …), written across many phases with different tone, structure, and
  freshness. Some claims likely drifted from live code; the index
  (`docs/README.md`, 64 lines) is a list, not a map.

This phase gives the documentation the same lift the product got: a README that
**hooks in ten seconds** (cool facts up, graphics kept, repetition cut, depth
linked out), real **screenshots of the actual app**, one consistent **voice +
structure** across every guide, and a **truth pass** so nothing is overstated or
stale.

## Goal

Make the documentation worthy of the product: a README that hooks in ten seconds
and sells what's genuinely cool (honestly), and a docs set that is **accurate,
consistent, visually rich, and easy to navigate** — every shipped capability
discoverable and represented, the graphics kept, the bloat gone.

## Scope

- **In:** a **doc truth audit** + drift fix (claims vs live code); a **bold
  README reimagining** (10-second hook · cool-facts highlights · all graphics
  kept · capability matrix · 60-second start · depth linked out · materially
  shorter); a **docs voice & structure system** (a short style guide + the
  standard page skeleton applied across every guide) + an elevated, scannable
  **docs index**; a **visual lift** (real UI screenshots across the guides via
  the existing Playwright scripts + a repeatable capture home); a **coverage &
  discoverability** sweep (a feature → doc matrix; every shipped capability —
  journal/replay/actuators/presence/wizard — sold and linked); a **closeout**
  (link-check + doc-drift green, before/after, `final-summary.md`, PR).
- **Out:** code/feature changes (docs only — if a doc reveals a real bug, file
  it, don't fix it here); new pixellab asset generation (reuse the existing art +
  real screenshots); reference-doc rewrites beyond voice/accuracy unless trivial;
  translating docs; a hosted docs site.

## Exit criteria (evidence required)

- A doc audit lists every live doc with its drift findings; the factual errors
  are fixed; counts/flags/keys/route-names match live code. (HS-46-01)
- The README hooks in ten seconds (a real hook + a cool-facts highlights strip),
  keeps **every** existing graphic, cuts the repetition, links depth out, and is
  **materially shorter** (target ~130–150 lines); before/after captured. (HS-46-02)
- A docs style guide exists and the standard page skeleton is applied across the
  user-facing guides; `docs/README.md` is a scannable journey-grouped map. (HS-46-03)
- Real UI screenshots of the actual app appear in the README + the key guides,
  captured by a repeatable script under `docs/assets/screenshots/`. (HS-46-04)
- A feature → doc matrix proves every shipped capability is documented + linked;
  no shipped feature is undiscoverable; nothing overstated. (HS-46-05)
- Doc-drift + dangling-link guards green; before/after; `final-summary.md`;
  phase CLOSED; PR to `main`. (HS-46-06)

## Invariants

- **Honest, not hype.** Cool facts must be *true* — pre-release status stays
  clear; no cloud-sync / always-on claims that contradict the local-first
  posture; "100% local" only where literally true (the LLM endpoint you point at
  is yours). Bold framing, accurate substance.
- **Graphics stay.** The pixellab art is an asset and is preserved; screenshots
  are additive.
- **Docs only.** No source/behavior changes; the suite is incidental (doc guards
  + link-check + a clean `npm run build` for any screenshot capture).
- **Grounded.** Every claim is checked against live code (the repo's standing
  doc-truth rule); the audit (HS-46-01) is the foundation the rest builds on.
- **Reproducible visuals.** Screenshots come from a committed capture script (no
  hand-pasted one-offs), so they can be refreshed when the UI changes.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-46-01 | Doc truth audit & drift fix | done | [story-01-doc-truth-audit.md](./story-01-doc-truth-audit.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-46-02 | The README, reimagined (the 10-second hook) | done | [story-02-readme-reimagined.md](./story-02-readme-reimagined.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-46-03 | Docs voice & structure system + elevated index | done | [story-03-voice-and-structure.md](./story-03-voice-and-structure.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-46-04 | Visual lift — real screenshots across the guides | done | [story-04-visual-lift.md](./story-04-visual-lift.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-46-05 | Coverage & discoverability (feature → doc matrix) | done | [story-05-coverage-discoverability.md](./story-05-coverage-discoverability.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-46-06 | Closeout — before/after + guards + PR | done | [story-06-closeout.md](./story-06-closeout.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Where we are

**Phase CLOSED ✅ (6/6).** Accurate spine, one voice, the real app on screen, proven
coverage, and a verified closeout: README 205 → 157 with a hook + cool-facts strip
(every graphic kept), a uniform `## See also` footer (13/13) + a journey-map index,
real screenshots from a repeatable script, a feature → doc matrix (no orphans), and
a truth audit pinning the headline facts with guards. **PR to `main` opened.** The
project-KB *product/UX* legibility lives on in scaffolded **Phase 47**.
_(Earlier — HS-46-01 → 05:)_

**HS-46-01 → 05 done** — accurate spine, one voice, the real app on screen, *and*
proven coverage. A feature → doc matrix shows no orphan features or docs; the index
names actuators; the user-reported "project KB" confusion is fixed in the docs (the
product/UX side spun out as **Phase 47**). Only **HS-46-06 (closeout + PR)** remains.
_(Earlier — HS-46-01 → 04:)_

**HS-46-01 → 04 done** — accurate spine, one voice, *and* the real app on screen.
The README hooks in ten seconds (HS-46-02: 205 → 152 lines), the guides clear a
shared skeleton with a uniform `## See also` footer (13/13) + a journey-map index
(HS-46-03), and **real UI screenshots** now appear in the README, Getting Started,
and Meeting Mode — captured reproducibly by `scripts/screenshot_docs.py` (welcome /
journal / history) and guarded by a new image-ref check (HS-46-04). Pixellab art
kept throughout. Suite green (2365/17). **Next: HS-46-05** (feature → doc coverage
matrix; prove nothing shipped is undiscoverable and nothing is overstated) →
**HS-46-06** (closeout + PR). Sequence: ~~01~~ → ~~02~~ → ~~03~~ → ~~04~~ → 05 → 06.

---

_Earlier — HS-46-01 (the accuracy foundation):_ `docs/internal/DOC_AUDIT_2026-06.md`
is the map: a canonical-facts yardstick + a per-doc verdict for all 18 live docs,
with 4 drift findings fixed (presence enablement, a phantom config key, a missing
connector kind, a self-contradicting protocol example) and a new README-plugin-count
guard. The "verified-correct" anchors note keeps the next pass from regressing the
deep links. Suite green (2365/17). **Next: HS-46-02** — the bold README reimagining,
built on the now-accurate picture (10-second hook + cool-facts strip, every graphic
kept, repetition cut, depth linked, ~130–150 lines). Sequence: ~~01~~ → (02, 03) →
(04, 05) → 06.

## Active risks

- **Over-selling a pre-release.** Bold framing can drift into hype. Mitigation:
  the honesty invariant + the truth audit gate; keep the pre-release banner.
- **Screenshot staleness.** Hand-captured screenshots rot. Mitigation: a
  committed capture script (reuse the `scripts/screenshot_*.py` pattern) so
  visuals are reproducible.
- **Scope creep into a rewrite of everything.** 4,677 lines of docs. Mitigation:
  the truth pass is accuracy + voice + structure + visuals — not a line-by-line
  rewrite of reference material; deep rewrites are out unless a doc is actively
  misleading.
- **Doc↔feature drift recurring.** Mitigation: the feature → doc matrix
  (HS-46-05) + the existing doc-drift guard; consider extending the guard.

## Decisions made (this phase, from user)

- **README: bold reimagining** — lead with the wow / cool facts, cut hard for
  punch (~130–150 lines), keep every graphic, move depth (the plugin table, the
  AIPI prose, the config block) to linked docs.
- **Visuals: real UI screenshots** — add live product screenshots via the
  existing Playwright scripts; reuse the pixellab art as-is (no new generation).
- **Scope: README + a truth/voice pass on all docs** — comprehensive: fix drift,
  unify voice/structure, elevate the index across the whole user-facing set.

## Decisions deferred

- **Cool-facts home** — README hero highlights vs a dedicated `HIGHLIGHTS`/"Why
  HoldSpeak" doc vs both; settle in HS-46-02/05 (default: a README highlights
  strip + the index map; a dedicated doc only if it earns its place).
- **Reference-doc depth** — how far the voice/structure pass goes into the
  dev/reference docs (`PLUGIN_AUTHORING`, `CONNECTOR_DEVELOPMENT`,
  `DEVICE_PROTOCOL`); settle in HS-46-03 (default: accuracy + a consistent
  skeleton, not a rewrite).
