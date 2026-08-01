# HS-111-07 - System chrome

- **Project:** holdspeak
- **Phase:** 111
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

Dropdown menus (Desk/Object/Go), context menus, the search palette
(Cmd+K), the shortcut sheet, and popovers are the OS's own voice —
they appear over every program. The bar: **system chrome speaks pure
Workbench 2.0: opaque rectangular menus with 1px bevels, full-width
highlight bands, mono labels; the palette is a command console, not
a Spotlight clone.**

## Method (phase canon)

1. **Audit.** An agent opens every menu, the palette, the shortcut
   sheet, and each popover; files every macOS-ism and SaaS-ism.
2. **Rethink.** Propose the native treatment against the phase
   question — one menu grammar for all of them.
3. **Implement** in `web/src`.
4. **Prove** with live screenshots on the real desk, 1440 and 393.

## Test plan

- Menus are opaque, 2px-cornered, beveled; hover is a full-width
  band, not a rounded chip.
- The Cmd+K palette renders in the same grammar (sunken input well,
  ledger results).
- The shortcut sheet and popovers share the treatment; no
  backdrop-filter anywhere in chrome.
- Screenshot walk at both viewports.
