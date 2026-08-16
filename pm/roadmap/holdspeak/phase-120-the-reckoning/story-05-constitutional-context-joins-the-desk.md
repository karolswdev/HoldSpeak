# HS-120-05 — Constitutional context joins the desk

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

ConstitutionalContextCore is built entirely with inline `style={{}}`
objects — 15+ inline style blocks covering layout, colors, fonts,
borders, and spacing. It uses a raw native `<select>` for version
picking and a raw `<textarea>` for the context body. No hero slot, no
receipt bar, no SurfaceVerbs, no wings — none of the surface primitives
every other core uses. Hardcoded fallback colors (`#f87171`, `#fbbf24`,
`#34d399`, `orange`) appear in styles. It looks like a prototype from a
different app.

When this ships, the constitutional context editor is a proper desk
core:

1. Version picker uses `CycleGadget` instead of native `<select>`.
2. Context body uses `PadGadget` or `DeskEditor` instead of raw
   `<textarea>`.
3. Status indicators use `LampGadget` / `SurfaceState` / `desk-chip`
   with tone tokens.
4. All colors come from CSS custom properties (tokens), zero hardcoded
   hex values.
5. Layout uses CSS classes, zero inline `style={{}}` objects.
6. Hero slot, receipt bar, and surface section structure match other
   cores.

## Acceptance criteria

- [ ] Zero inline `style={{}}` objects in ConstitutionalContextCore.
- [ ] Zero hardcoded hex colors.
- [ ] Zero raw `<select>` or `<textarea>` elements.
- [ ] Uses CycleGadget, PadGadget/DeskEditor, LampGadget, SurfaceSection.
- [ ] Visual parity with other desk cores (SettingsCore, CadenceCore).

## Test plan

- Visual: open the constitutional context core, verify it matches the
  desk material language.
- Grep: `style={{` in ConstitutionalContextCore.tsx returns zero hits.
- Grep: `#[0-9a-fA-F]{3,6}` in the same file returns zero hits.

## Files in scope

- `web/src/pages/cores/ConstitutionalContextCore.tsx`
- Possibly a new CSS file if substantial styling is needed.
