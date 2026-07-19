# Phase 99 — The OS Chrome: final summary

**CLOSED 8/8, 2026-07-18 — scaffolded and shipped the same day**, at
machine-verifiable scope under the standing close directive; the
owner's live verdict rides the next sitting (Campaign 13's
design-polish scenario now walks the bar, the controls, the
scrollbars, and the living dock).

## What this phase was

The owner's live verdict on the staged Phase 98 build: a step, not an
OS — unstyled selects everywhere, windows deserving a huge overhaul —
with a direct study directive: ProzillaOS (MIT), borrow and embrace.
Three source sweeps (window system, skin/controls, desktop shell)
produced [PROZILLAOS_STUDY.md](../../../docs/internal/PROZILLAOS_STUDY.md):
the reference's power is a small set of relentless chrome techniques;
ours was strong machinery wearing no skin.

## What shipped

- **The study as canon + nine chrome tokens** (tonal ladder
  head/rail/well, scrollbar pair, control height, quart/expo/back
  easings) and the chrome-ladder spec, before any consumer.
- **The title bar is a bar**: 40px two-tone head (tone, no border),
  full-height square SVG verbs flush to the edge, red-hover close via
  the variable-override pattern, square corners on maximize, a
  right-click head menu. Two defects caught by proof and pinned: an
  open head menu now absorbs the first Escape (the window survives),
  and a stale surface-window head override (old padding + border) was
  killed when the chrome walk MEASURED the verbs at 26×19 — the
  eyeball had passed what the leg failed.
- **Controls wear the skin**: the real "unstyled selects" were the
  desk's own components shipping raw elements past Signal — bare
  `select`/`textarea`/text-like inputs inside the desk shell now
  inherit the control foundation mechanically (no component can ship
  an unstyled control), with the drawn chevron, surface-toned
  options, accent checkboxes, inverted date indicator, a drawn
  search-cancel glyph, and a Signal file button.
- **Scrollbars and menus**: the drawn pill scrollbar product-wide —
  with two canon gotchas (standard scrollbar properties disable
  webkit styling in modern Chromium, now Firefox-scoped; the headless
  shell suppresses custom scrollbars, so proof is HEADED) — and
  `DeskMenuList`/`DeskMenuItem` as the one menu vocabulary behind the
  room, head, and new dock-chip menus.
- **The dock is alive**: frosted glass over a real blur, a running
  underline per open window (front = wide accent, grows on hover),
  run marks on launchers, glyph swell, chip entry motion.
- **Interior archetypes**: Settings' left rail at wide windows
  (container-driven), Meetings' well-tone status bar with honest
  counts, the verb bar continuing the head tone, the split detail on
  the rail tone.
- **Floors written** into DESIGN_SYSTEM/README/architecture locks.

## Proof

The assembled chain — all twelve legs (smoke, windows, shell, cores,
dictation with real voice, meetings with a real recording, config
round-trip, lastexits, reflow, the six-leg grammar chain, surfaces,
and the new `chrome` leg with its mechanical bar/select/scrollbar/
corner/underline asserts) — green in ONE captured run with zero
failed API responses; storm assembled 8.3ms median / 10.0 p95 on
hardware GL. `npm run check` (291) and the full python sweep captured.

## Riders

- A fully custom select POPUP (browsers cap `<option>` styling) if
  the skinned native still offends.
- The dock chip EXIT animation (width collapse) needs unmount
  orchestration.
- Skin/theme switching: the public-classname seam from the study is
  the recorded path if theming ever lands.
- Dock badges/counts; nested submenus.
- HSM One Grammar on Glass now consumes tokens + grammar + idiom +
  chrome; The Living World (object↔window continuity) remains staged.
