# Shared picker lane

HOLD FOR SHIP. Product source frozen; no staging, commit or push by worker.
Root owns production walks, combined quick check and shipping.

## Result

CycleGadget and legacy Signal Select share WorkbenchSelect. The visible
native select owns the accessible label, focus, value, form membership,
default/reset behavior, required validation and native events. The library
draws its popup with chrome Button rows, a checked current choice and a
separate blue active choice. Unavailable choices cannot commit.

Pointer and keys suppress native opening. Arrows/Home/End/typeahead move
the active row without saving; Enter/Space/row press commits a changed
choice through one input/change event pair. Escape cancels before window
Escape; Tab and outside pointer preserve normal destination behavior.
Blur, ancestor scroll, resize, disable and external value/roster changes
close the popup. The popup's own scroll stays usable. Placement chooses
available space above or below; labels wrap and lists scroll. Portal styles
carry computed custom properties from the owner. Device targets use the
existing global 420px device rule.

The Button implementation moved unchanged to Button.tsx and Signal
re-exports it. This prevents Signal → picker → Signal import cycles.
Native multiple/sized list controls retain their native list behavior;
the adoption census found no active picker consumer that uses those modes.

## Owned files

- New: `web/src/components/signal/Button.tsx`
- New: `web/src/components/signal/WorkbenchSelect.tsx`
- New: `web/src/components/signal/WorkbenchSelect.css`
- New: `web/src/components/signal/WorkbenchSelect.test.tsx`
- Updated: `web/src/components/signal/Signal.tsx`
- Updated: `web/src/desk/surface/gadgets.tsx`
- Updated: `web/src/styles/global.css` (exact device target rule only)
- Updated: `web/src/desk/surface/contract.md`
- Updated: `docs/internal/DESIGN_SYSTEM.md` (picker species sentence)
- Updated: `scripts/ux_canon_scan.py` (two exact library implementation paths)
- Updated: `tests/unit/test_ux_canon_ratchet.py` (focused exact-path assertions)
- New: this KIT.md and `canvas/{README.md,index.html,main.tsx,canvas.css,vite.config.mjs}`

`gadgets.css` has one incidental removed blank line, with no material
change; root may restore that blank line. No product face files changed
by this lane. Adoption owns ThreadPullout and its tests.

## Scoped proof

All runs used `.tmp/workbench-pickers/locked.py`, the machine test lock,
isolated HOME, Node 22 and `--maxWorkers=2`. Only these files ran:

```text
src/desk/surface/gadgets.test.tsx
src/components/signal/Signal.test.tsx
src/components/signal/WorkbenchSelect.test.tsx
```

Collection: `vitest list` exit 0, final 41 named cases in
`.tmp/workbench-pickers/kit-lifecycle-collect.log`.

Before implementation (`kit-red.log`):

```text
Test Files  1 failed | 2 passed (3)
     Tests  9 failed | 29 passed (38)
  Duration  1.48s
```

After implementation and two additional boundary cases (`kit-final.log`):

```text
test_lock: acquired after 5 s
Test Files  3 passed (3)
     Tests  40 passed (40)
  Duration  1.85s
```

The 12 new cases cover native pointer suppression/label/form ownership;
active-vs-saved/Escape; exact native events; controlled keyboard commit;
missing and unavailable choices; Home/End/typeahead; Tab/outside action;
disable/unmount/scroll; default/external-form/reset/producer change;
option label/disabled group; edge placement/portal theme; external
value/resize closure. Existing gadget and Signal tests remain unchanged.

Independent review found that React child identity changes could close an
unchanged roster when a parent polls or raises a window. The final core
compares the actual native selected index and option value/label/disabled
snapshot. A new regression keeps the popup and active row through an
unrelated parent render; the existing snapshot test also changes the real
option roster and proves closure. Final proof:

```text
Before lifecycle fix: 1 failed | 40 passed (41)
After lifecycle fix: 3 files passed; 41 passed (41); duration 1.64s
```

Logs: `.tmp/workbench-pickers/kit-lifecycle-{collect,red,green}.log`.
There are now 13 new picker cases. Root authorized this bounded correction
after independent review; product source is frozen again.

The final diagnosed extraction seam also ran only
`tests/unit/test_ux_canon_ratchet.py`, under the same isolated HOME/lock:

```text
Collection: 7 tests collected in 0.06s
Before registry fix: 2 failed, 5 passed in 1.22s
After registry fix: 7 passed in 1.13s
```

Proof logs: `.tmp/workbench-pickers/kit-scanner-{collect,red,green}.log`.
The two parametrized cases prove the actual Button and WorkbenchSelect
implementation paths are valid while matching basenames under face
directories and prefix/suffix lookalikes stay flagged.

## Limits and integration note

Worker ran no product browser walk, build, full suite or owner-state
operation. Browser touch, focus and actual saved-value proof belong to
root. Corrected canvas shots and root's pre-build settlement are recorded
in `canvas/README.md`.

The canon scanner now recognizes the exact genuine library implementation
paths `components/signal/Button.tsx` (A1) and
`components/signal/WorkbenchSelect.tsx` (B). Root authorized this final
diagnosed seam after the source freeze. No ceiling or waiver changed.

Tuesday: each existing value writer keeps its interface; the owner picks
a choice in the desk's material without a browser menu interrupting it.
