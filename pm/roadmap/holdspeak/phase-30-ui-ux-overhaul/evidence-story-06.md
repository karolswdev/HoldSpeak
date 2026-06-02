# HS-30-06 Evidence — Dashboard (`index`) redesign

**Date:** 2026-06-02.
**Story:** [story-06-dashboard-redesign.md](./story-06-dashboard-redesign.md).

## Implementation Evidence

The flagship runtime dashboard (`web/src/pages/index.astro`) is redesigned to the
IA spec on the Signal system, **without touching any Alpine binding**.

- **Local Workbench CSS → Signal.** The page carries its own copies of `.panel`,
  `.hero`, `.btn`, `.pill` CSS (it renders `class="panel"` markup directly, not the
  Panel component). Migrated all of it: panels are raised `--surface-1` cards with
  `--radius-lg` + `--elev-1` and **uppercase-eyebrow** headers (matching
  `Panel.astro`); the hero is a rounded card that gains an **accent glow** in the
  active state; primary buttons get `--glow-accent`; danger → white-on-`--danger-fill`.
  The page's **8 `--wb-*` refs → 0**.
- **Rail grouped per IA.** The 8 rail panels are now organised under three eyebrow
  group labels — **Intelligence** (live intel · Intelligence · Topics · Summary),
  **Work** (Action items), **Operations** (Deferred plugin jobs · intent routing) —
  with dividers, so the rail reads as a coherent secondary region instead of a
  stack of equal boxes. Implemented as **inserted non-Alpine `<div>` labels + CSS**
  — zero changes to `x-data`/`x-show`/`x-text`/`x-for`.
- The board grid keeps the transcript **dominant** (`1fr`) over the rail (≤400px).

## Tests

```bash
grep -cE -- '--wb-' web/src/pages/index.astro      # 0  (was 8)
cd web && npm run build                            # green, 8 pages
uv run pytest -q --ignore=tests/e2e/test_metal.py  # 2062 passed, 14 skipped
```

## Live evidence

`evidence/after-hs06/dashboard.png` (1440) — the idle runtime: rounded hero with
the glowing Start-meeting button, the dominant **TRANSCRIPT STREAM** panel, and the
rail under INTELLIGENCE / WORK / OPERATIONS labels. Compare
`evidence/before/before-runtime.png` (the blue Workbench original).

Binding safety: the redesign changed only CSS + added label divs, so the live
transcript append / copy-on-click / export / bookmark + metadata modals are
unaffected; the idle render confirms the page mounts and Alpine evaluates. A full
idle→active→stopping walk against a live meeting is folded into HS-30-09's manual pass.

## Result

The flagship reads as one designed Signal surface. **Next: HS-30-07** — the
dictation page (7 tabs → two tiers), continuing the page migrations.
