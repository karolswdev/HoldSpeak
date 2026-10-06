# Web UI contract and audit

This page is for contributors.
It states the rules that keep the HoldSpeak web controls consistent, and it explains how to check them.
It covers the web app only. Browser screenshots are not evidence for the native iPad app.

The owner rulings for faces are in `docs/internal/UX-CANON.md`.
The component contract is in `web/src/desk/surface/contract.md`.
Those two files win when they differ from this page.

## Rules

1. **One component, one contract.** A shared component sets the size and states of a control. A page sets only placement.
2. **Use the library.** Every verb is the library `Button`. Do not add a raw `<button>` to a face. Build a face from the species in `web/src/desk/surface/`. See `UX-CANON.md`, section B.
3. **Show state, not debug text.** Show a status only when it confirms a finished task, explains a block, or offers a recovery. Do not repeat a count that the screen already shows. Do not show raw HTTP status, route names, or polling output.
4. **A label stays visible.** Every field has a visible label. A placeholder is not a label.
5. **Align an action with its control.** An action beside a field lines up with the field, not with its label.
6. **Match the control to the choice count.** Use direct choices for a few options, a select for a moderate list, and a searchable combobox for a long or remote list.
7. **Keep native semantics.** Use real inputs, buttons, labels, and disclosure elements. Styling must not remove keyboard or screen reader support.
8. **Show where data goes.** Put the egress chip on the row that leaves the machine. Never show a secret.
9. **A state uses more than color.** Use an icon and text. The closed state set is `idle`, `active`, `working`, `success`, `warning`, `failure`, and `unreachable`.
10. **Use tokens.** Spacing, type, color, and motion come from `web/design-tokens.json`. Do not use raw values.

## Status messages

Show a message when the user needs new information. Examples:

- `Connected to Office server.` after an explicit connection test.
- `No models were reported. Enter a model manually.` with a recovery action.
- `Could not reach the server.` with the reason and a retry control.
- `Saving…` and `Saved` when the save is not otherwise clear.

Do not show a message that repeats a visible fact, such as `Found 1 model.` under the selected model.

## Shared controls

| Control | Where it lives |
| --- | --- |
| Button (primary, ghost, dense) | `Button` in `web/src/components/signal/Signal.tsx` |
| Text, number, and URL fields | `Field`, `TextInput`, `TextArea` (`Signal.tsx`), and `StringGadget` (`desk/surface/gadgets.tsx`) |
| Select | `Select` and `.hs-select` |
| Checkbox | `CheckGadget` |
| Choice cards | `ChoiceCard` and `ChoiceCardGroup` |
| Disclosure | `Disclosure` |
| Notice | `ActionNotice` and `StateChip` |

The component gallery is at `/design/components`.
It opens the **Components** window.
Show every new reusable pattern there.

## Run the audit

`scripts/web_ui_audit.py` opens each web route at 1440 by 1000 and at 430 by 932 pixels.
It reports controls that are smaller than 24 or 44 pixels, controls with no name, native selects, mixed style signatures, horizontal overflow, and console errors.

1. Start the hub.
2. Run `uv run python scripts/web_ui_audit.py --base-url http://127.0.0.1:8788 --out <directory>`.
3. Read the JSON report and the screenshots in the output directory.

The script names its narrow viewport `compact_web`. It never names it iPad or iOS.

## Before you merge a control change

1. Show a new reusable pattern in `/design/components`.
2. Build the web app and run the tests that cover the change.
3. Run the audit against a live hub.
4. Add no raw native select, unnamed control, control smaller than 24 pixels, or console error.
5. Check a Swift change on the native target separately.

## See also

- `docs/internal/UX-CANON.md`
- `docs/internal/DESIGN_SYSTEM.md`
- `docs/internal/DESK_GRAMMAR.md`
