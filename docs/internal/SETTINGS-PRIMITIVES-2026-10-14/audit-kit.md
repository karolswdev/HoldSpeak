# Settings primitives — kit build

Status: implemented, focused checks green, holding for SHIP. Root reviewed
the canvas direction. Owner acceptance and production glass verification
remain pending.

Worktree: `/Users/karol/dev/tools/wt-settings-primitives-20261014`.
Branch: `feat/settings-primitives-20261014`, base `22de063e3`.

## Delivered

The current surface kit now owns the reviewed inset control-sheet material,
aligned label/value rows, bounded group actions, a visible native On/Off
checkbox, narrow table field labels, and equal preference columns. Settings
continues to own its existing values and update callbacks.

| Change | Source |
| --- | --- |
| Named `GadgetGroup` sections, opt-in inset material, block content and sibling action footer | `web/src/desk/surface/gadgets.tsx:26` |
| `GadgetRow.controlWidth` and block slots for opt-in rows | `web/src/desk/surface/gadgets.tsx:58` |
| Native `CheckGadget` state variant with On/Off | `web/src/desk/surface/gadgets.tsx:98` |
| Head-derived field labels in `GadgetTable.layout="fields"` | `web/src/desk/surface/gadgets.tsx:580` |
| Exported semantic `GadgetDivider` | `web/src/desk/surface/gadgets.tsx:51`, `index.ts:43` |
| `SurfaceColumns.variant="preferences"` | `web/src/desk/surface/Surface.tsx:304`, `surface.css:318` |
| Paper sheet, native targets and responsive geometry | `web/src/desk/surface/gadgets.css:1156` |
| API contract | `web/src/desk/surface/contract.md:36` |

The preference composition is bounded at 960 px, with equal columns and a
24 px gap. It stacks at 920 px or less, bounded at 620 px. The desktop row
label column is 118–160 px and the value cap is 190 px. The narrow cap is
172 px. Fields and row actions have native 44 px narrow targets. The full
row selector explicitly overrides the inset row at both widths.

The checkbox input owns the complete check-and-word label. Decorations pass
pointer events through to it. The native checkbox supplies keyboard behavior,
checked state and disabled state. The visual On/Off word is hidden from the
accessibility tree to preserve one accessible control name.

Default group, row, checkbox, table and column faces retain their existing
material. Table row keys, armed delete, custom verb slots, and native editor
key guards remain in place. The worker changed only the seven shared kit
files assigned in the brief and the canvas/design record. No Settings files,
install, broad suite, product build, staging, or commit were performed.

## Focused proof

Every invocation ran through `.tmp/settings-primitives/locked.py`, which
creates an isolated HOME, uses Node 22 and serializes through the repository
test lock. Vitest 4 uses the `list` subcommand for collection.

```text
.venv/bin/python .tmp/settings-primitives/locked.py kit-collect-final --web ./node_modules/.bin/vitest list src/desk/surface/gadgets.test.tsx --maxWorkers=2

src/desk/surface/gadgets.test.tsx > gadget kit > inset groups name their section and keep actions after block content
src/desk/surface/gadgets.test.tsx > gadget kit > state checks expose one named checkbox and a visible On or Off value
src/desk/surface/gadgets.test.tsx > gadget kit > disabled state checks retain their value and reject pointer and keyboard changes
src/desk/surface/gadgets.test.tsx > gadget kit > field tables derive repeated visible labels from the supplied heads
src/desk/surface/gadgets.test.tsx > gadget kit > field tables keep editing keys native and preserve an armed row action across reorder
src/desk/surface/gadgets.test.tsx > gadget kit > preference columns retain the two content slots and leave the default unmarked
```

The six new cases plus nineteen existing cases were collected. Before kit
implementation, the RED run failed five new API cases; the preservation case
and the existing cases passed:

```text
.venv/bin/python .tmp/settings-primitives/locked.py kit-red --web ./node_modules/.bin/vitest run src/desk/surface/gadgets.test.tsx --maxWorkers=2
Test Files  1 failed (1)
Tests       5 failed | 20 passed (25)
Duration    1.13s
```

The first GREEN attempt had two test interaction failures because
`user-event` rejects a direct click on a decorative span whose pointer events
pass through. The tests now click the owning label. The same corrective pass
fixed the full-width CSS override noted above. The single corrective run
passed:

```text
.venv/bin/python .tmp/settings-primitives/locked.py kit-green-corrected --web ./node_modules/.bin/vitest run src/desk/surface/gadgets.test.tsx --maxWorkers=2
RUN v4.1.9 /Users/karol/dev/tools/wt-settings-primitives-20261014/web
Test Files  1 passed (1)
Tests       25 passed (25)
Start at    22:57:33
Duration    1.36s (transform 302ms, setup 88ms, import 471ms, tests 438ms, environment 280ms)
```

Full logs: `.tmp/settings-primitives/kit-collect-final.log`, `kit-red.log`,
`kit-green.log`, `kit-green-corrected.log`.

## Final review correction

`REVIEW.md` found that the standard direct StringGadget width selector had
specificity `(0,5,0)`, while the later full-width control selector had
`(0,4,0)`. The full row grid spanned correctly, but the text well still kept
the 190/172 px standard cap. The shared CSS now repeats the non-stepper
StringGadget qualification on the full-width override. Its `(0,5,0)`
specificity matches the standard rule and its later position wins, at both
widths. The standard cap remains in place for ordinary rows.

The same bounded CSS pass restores `flex-wrap: wrap` on opt-in gadget slots.
Rows retain minimum heights and grow with wrapped content, including a
boolean plus address and credential count, an engine plus action, or a read
failure plus Retry. Default rows receive no new rule.

This correction changed only `gadgets.css` and this record. No additional
tests or builds ran: the existing unit cases do not prove CSS geometry.
Root owns the browser re-check of full versus standard text wells at both
widths and the populated Remote access row. Product source is frozen again,
holding for SHIP. The original review remains the record for the final
re-check; no owner acceptance is claimed.

The root then measured clipping of `AFTER EVERY MEETING` in the 172 px
narrow CycleGadget. The same opt-in selector now uses `letter-spacing: 0`.
The 12 px mono font, native select, options and default CycleGadget remain
unchanged. Root will measure the selected text against its available width
at both sizes. This added one CSS property and this record, with no tests
or builds. Product source is frozen again for the final re-check.

## Tuesday and unknowns

The designed first sheet puts the hold key, language, preview and commands
together, with labels beside their values. The symbol dictionary keeps field
names visible at phone width and Add symbol has a bounded home in either
state. This meets Tenets 3 and 5 in the composition and Tenet 6 in material.

Unit checks verify semantics and native interaction behavior. They do not
prove browser geometry, physical pointer ownership, production width shots,
or the owner's live acceptance. Root owns those checks and the final done
call. This record makes no claim that they have passed.
