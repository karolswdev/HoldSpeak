# Settings primitive adoption audit — 2026-10-14

**DRAFT — input to the settled design; UNCHECKED — awaiting Muad'Dib.**

Bounded source audit at `22de063e32edf21db5eb43bae7b63b6dc94c6b1f` in
`wt-settings-primitives-20261014`. Anchors below can drift. No product files
changed; no tests, installs, staging, or commits performed. The existing
untracked `web/node_modules` was left alone.

The smallest useful change is a panel treatment and local footer on the
existing `GadgetGroup`, plus explicit control layout on `GadgetRow`. The
controls and persistence already exist. Tenet 5 calls for this shared seam;
tenets 2 and 3 favor keeping the owner's ordinary choices visible. Workbench
material remains the design constraint (tenet 6).

## Adoption sites

All paths in this table start at `web/src/pages/cores/`.

| Face | Exact sites | Shared adoption and behavior to preserve |
| --- | --- | --- |
| Voice | `SettingsCore.tsx:1783` columns; `:1795` Transcription; `:1798` Typing; `:1811` Spoken symbols; `:1861` Wake word; `:1877` Advanced | Panel groups around current gadgets. One local **Add symbol** footer for both empty and populated dictionary. Keep no empty table header. Keep symbol patches, append defaults, and armed FORGET. Hotkey is its own group in `settingsBespoke.tsx:78`; its listening/cancel behavior stays there. |
| Meetings | `SettingsCore.tsx:2081` Summary; `:2098` Recording; `:2133` Calendar; `:2219` Export; `:2248` Advanced | Compact boolean/pick/value rows; stretch text and ranges. Engine value + egress + Change engine are one wrapping row. Calendar stays a `SurfaceLedger` inside the common panel body; keep edit wells, identities, counts, source egress, and failed Save drafts. Add calendar/Add feed/Import image belong to its local footer (`:2198`), with snapshot egress beside Import image. |
| Rhythm | `SettingsCore.tsx:2333` columns; `:2335` Cadence; `:2360` Morning brief; `:2368` Telegram; `:2374` Advanced | Common panels and compact rows; preserve numeric units/bounds and existing setting paths. No new action or Save button is needed. |
| Sounds | `SettingsCore.tsx:1936` columns; `:1938` Sounds; `:1953` Presence; `settingsTts.tsx:79` loading/failure, `:85` absent install, `:97` installed | Same panel grammar across loading, read failure, absent model, and ready states. Desk sounds must still call both `update` and `toggleSfx` (`SettingsCore.tsx:1946`). Put model download/receipt/error in a group-local footer; keep Hugging Face egress adjacent to Download (`settingsTts.tsx:107`). |
| People | `SettingsCore.tsx:2474` columns; `settingsPeople.tsx:76` You; `:137` Agents | Stretch name/alias rows. Agent access remains the existing `FilterTokens` with effective value and disabled state when the environment holds it (`:150`). Preserve its separate endpoint, failure refresh, and operation receipt. Name blur flush and alias Enter/comma/Backspace/blur behavior are independent of Settings' writer. |
| System | `SettingsCore.tsx:702` columns; `:955` Remote access; `settingsPrefs.tsx:307` Desk; `SettingsCore.tsx:613` Diagnostics; `:715` Mesh; `:2461` Device | Common outer panels; preserve remote credential/grant ledger, one-time token well, and local state. Issue credential (`:1225`) is a panel action; Issue/Cancel (`:1215`) remain inside its edit well. Reset desk is the existing armed `ConfirmVerb` plus receipt (`settingsPrefs.tsx:310`). Diagnostics/mesh/device remain under Advanced. |

## Minimal library seam

`gadgets.tsx:26` and `:44` are presentation wrappers. A backward-compatible
proposal is `GadgetGroup` with an optional panel variant and `footer` node,
and `GadgetRow` with an explicit compact/stretch control layout. Keep `wide`,
`highlight`, `fact`, and children. Exact prop names belong to the settled
design. Group owns the header/body/footer material, wrapping, spacing, and
intrinsic action size; it must not own values, validation, writes, or drafts.
Use a block body/control wrapper if the slot accepts ledgers or wells.

Existing value species cover the job: `CheckGadget` (boolean), `CycleGadget`
(closed set, including unknown stored values), `StringGadget` (text with mic),
`StepperGadget` (bounded number + unit), `PropGadget` (range + value),
`FilterTokens` (People's established choice strip), and ordinary text for
observed facts. `GadgetRow.fact` is a token, not helper prose.

`SurfaceSection.actions` already supplies section header actions
(`surface/Surface.tsx:109`). There is no current group-local footer slot.
`SurfaceFooter` is the window footer: it portals into the frame
(`surface/SurfaceFooter.tsx:142`), and Settings already owns one through
`settingsPrefs.tsx:639`. Do not put a `SurfaceFooter` inside each panel.
Reuse library `Button`/`ConfirmVerb` in the new local slot.

The two Add paths differ today: populated dictionary uses GadgetTable's raw
button (`surface/gadgets.tsx:634`, full-width `.gadget-table-add` at
`surface/gadgets.css:643`); empty dictionary renders a Button directly in
the stretching column sheet (`SettingsCore.tsx:1859`, `.gadget-sheet` at
`gadgets.css:8`). A single external footer can omit `GadgetTable.onAdd`
without changing the table API.

## Local compensation to absorb

All anchors below are in `web/src/pages/cores/settings.css` unless named.

- Group and row overrides are layered at `:194`–`:208`, then again at `:314`
  through `:325`: margins, heading type, label width, 44 px row height,
  padding, wrapping, and control gaps. Panel/row geometry should live in
  the library rather than these descendant overrides.
- `:327`–`:330` changes String/Stepper widths and number input size;
  `:371`–`:379` infers stacking from descendant `:has` selectors and caps
  selects. Explicit control layout should replace these heuristics.
- `:360` makes checkbox paint ignore pointer events; `:382` expands narrow
  checkbox targets. If retained, these are shared checkbox ownership fixes,
  not Settings presentation. Preserve real input hit ownership at 393.
- `:333` overrides `settingsSurfaceRepair.css:3`–`:8` for the summary's
  multiple controls. Shared wrapping must preserve the row's full target
  height. Grant-receipt footer corrections in that file (`:13`) concern the
  window footer, not panel footers.
- `.prefs-reset-controls` (`:334`), calendar action bars (`:197`), and
  `.prefs-text-field` (`:390`) are local versions of action wrapping/stretch
  behavior. The grid/column composition (`:310`–`:312`, `:364`) is also
  repeated at all six adoption sites; the design worker is settling its
  shared container. Keep ledger-specific calendar identity layout separate.

## Risks that a visual adoption must preserve

1. **Drafts and save races:** `SettingsCore.tsx:1336`–`:1503` holds the 700 ms
   writer, exact-path pending patches, revision reconciliation, refusal
   retry, and pagehide flush. Keep bindings `:1625`–`:1738` and their stable
   path keys; do not define new components inside render (`:1614`). A panel
   remount must not replace the writer or steal focus.
2. **Independent edit protocols:** calendar draft fields save atomically
   and close only on success (`:2040`); owner-name blur flush is at
   `settingsPeople.tsx:84`; `desk/firstrun/OwnerAliasField.tsx:10` owns the
   incomplete alias draft. People access, remote access, reset, and TTS
   download use separate operations. A common Save/Cancel form would change
   their behavior.
3. **Accessibility and keyboard:** preserve real checkbox/select/range/
   number/text inputs and accessible names. GadgetRow's visible span is
   not the input label. Keep StringGadget's mic and inputProps, hotkey Esc,
   table roving focus, and armed delete (`gadgets.tsx:587`). Symbols use
   index row identity today; do not imply stable IDs were added. Give panel
   sections a heading association if named; never make a whole panel one
   click target around its controls.
4. **Honest state and egress:** keep environment-held access disabled,
   pending/refused receipts and Retry visible, hidden zero counts, and
   egress on the action/row that leaves the machine. A panel heading does
   not substitute for an action's egress chip.

## Focused existing coverage (read, not run)

- `web/src/desk/surface/gadgets.test.tsx`: real input species, off-roster
  cycles, numeric bounds, row facts, table verbs/armed delete, disclosures.
- `web/src/desk/__tests__/settings.app.test.tsx`: navigation and one footer;
  name/aliases (`:325`); Meetings groups, calendar, empty symbols (`:348`,
  `:422`); refusal/retry and newer drafts (`:475`); System remote/grants
  (`:622`, `:754`); Sounds (`:726`). Column and `.gadget-table-head`
  assertions are composition-coupled (`:426`, `:438`).
- `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`: edit/add/remove,
  failed Save, native/snapshot identity, per-action egress.
- `web/src/pages/cores/__tests__/settingsPeople.test.tsx` and
  `settingsTts.test.tsx`: environment locks, receipts/read retry, model
  installation/download and browser support.
- `web/src/pages/cores/__tests__/SettingsCore.test.ts`,
  `settingsLeave.philo17.test.tsx`, and `settingsWriters.test.ts`: patch
  reconciliation, leave sends, canonical writer ownership.
- `tests/e2e/test_settings_glass.py`: summary target geometry at both
  widths, pressed/held state, remote/grant control ownership. Its summary
  test still searches for the old “Capture + export” heading (`:110`), and
  held-strip test uses removed `settings-more` (`:264`); inspect these stale
  selectors before treating a failure as a regression. No green claim.

Tuesday: the owner can reach ordinary Voice/Meetings choices directly; the
shared panel should bind each value and local action into a recognizable
group without adding a new step. Visual fit, hit ownership, and live drafts
were not verified by this source audit.
