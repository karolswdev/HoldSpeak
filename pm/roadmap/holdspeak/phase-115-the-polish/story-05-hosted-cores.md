# HS-115-05 - Hosted cores

- **Project:** holdspeak
- **Phase:** 115
- **Status:** done
- **Depends on:** HS-115-01
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

The 13 hosted surface cores (Speak, Meetings, Settings, Workbench,
Agents, etc.) all render as proper Desk material inside their host
windows. The Workbench graph canvas resizes with its window. Legacy
card/glow styling is replaced with Signal Workbench bevel material.
JSON dumps are behind RAW disclosure. Typography uses the shared
surface tokens. When this ships, no hosted core looks like a web
page dropped into a window.

**Articles served:** I (no feature-owned pages), VII (quiet chrome),
VIII (native-grade craft).

## Ground (from the audit)

| Rule | File | Violation |
|------|------|-----------|
| L3 | react-app.css:223 | Workbench canvas enforces min 600px height, can't shrink |
| M3 | WorkbenchCore.tsx:349 | Workflow nodes use legacy card treatment |
| M3 | react-app.css:256 | Nodes use large radii, gradients, glow |
| M4 | react-app.css:313 | Palette is elevated rounded card, not hairline band |
| D3 | react-app.css:221 | Separate dark graph-canvas system |
| C1 | WorkbenchCore.tsx:230 | Workflow receipt exposes raw invocation ID |
| C1 | DictationCore.tsx:935 | Raw trace renders complete API JSON |
| C1 | HistoryCore.tsx:627 | Body-less artifacts expose row JSON |
| C1 | HistoryCore.tsx:737 | Routing receipts expose timeline JSON |
| C1 | LiveCore.tsx:315 | Route-preview renders complete API response JSON |
| C1 | ProcessCore.tsx:79 | Raw principal, placement, head, reference fields |
| C1 | ProjectMemoryCore.tsx:91 | Superseded label exposes raw successor ID |
| L2 | surface.css:133 | Surface rows truncate with no fallback |
| L2 | surface.css:1271 | Ledger primary forced to one ellipsized line |
| C2 | SetupCore.tsx:155 | Next step panel uses explanatory sentences |
| C3 | desk.css:1914 | AskBar uses ad-hoc typography |

## Deliverables

1. **Workbench canvas resize.** Remove the min-height floor from
   `react-app.css:223`. Let the canvas fill its host window.

2. **Workbench material migration.** Replace legacy node styling
   (large radii, gradients, glow) with Signal Workbench bevel
   material. Palette becomes a hairline-separated control band.

3. **JSON → RAW fold.** Wrap all raw JSON dumps in DictationCore,
   HistoryCore, LiveCore, and WorkbenchCore inside a `<details>`
   RAW disclosure fold.

4. **ProcessCore sanitization.** Raw principal, placement, head,
   reference → human-readable labels via the label map from
   story 02.

5. **Surface row overflow.** Add `title` attributes to ellipsized
   surface rows. Consider two-line treatment for ledger primary
   material.

6. **SetupCore labels.** Replace explanatory sentences with terse
   action verbs and state labels.

7. **AskBar typography.** Use `--font-mono` and
   `--desk-surface-label-size` for the selection status.

## Test plan

- `npx vitest run` — all frontend tests pass.
- Open Workbench → resize the window smaller → canvas must shrink
  with it, no content escape.
- Open Speak → run a dictation → Raw trace must be behind a fold.
- Open Meetings → artifacts with no body must not show JSON.
