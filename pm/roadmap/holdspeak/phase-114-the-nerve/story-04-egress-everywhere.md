# HS-114-04 - Egress on every inference path

- **Project:** holdspeak
- **Phase:** 114
- **Status:** in-progress
- **Depends on:** HS-114-01
- **Unblocks:** HS-114-05, HS-114-07
- **Owner:** unassigned

## The thesis (the bar)

Every surface that invokes LLM inference shows a LampGadget egress
readout in its instrument footer — before, during, and after the
call. The readout sits in the same row as the RunsOnPicker, reading
cause (control) to effect (state) in one scan line. Article III:
the decision-time egress badge must state local, LAN, or cloud.

## Ground (from the applicability study + design instruction)

- 10 of 14 AI surfaces invoke LLM inference without an egress
  indicator. (`AskPanel` and `PersonaChat` have EgressChip in the
  title bar; 12 others have nothing.)
- The design instruction (2026-08-02) establishes: egress inside
  surfaces is a LampGadget readout, not an EgressChip. The chrome
  bar keeps its EgressChip as the global posture badge.
- LampGadget: 8px square dot, 5px gap, 10px/600 mono uppercase,
  .06em tracking. Tones: `ok` = local (green), `warn` = LAN/private
  (amber), `fail` = cloud/external (red).
  (`web/src/desk/surface/gadgets.css:632-660`)
- `InferenceTarget.boundary` maps directly to tones:
  `same_device` → ok, `private_network`/`paired_device` → warn,
  `external_service` → fail. (`holdspeak/inference_targets.py:72-108`)
- EgressChip sits in AskPanel title bar `actions` slot.
  (`web/src/desk/components/AskPanel.tsx:316-328`)

## Method

### Design rule (from the design instruction)

Egress is a LampGadget readout in the instrument footer, not a
chip in the title bar. Two homes, one species:

- **Chrome bar:** EgressChip stays (global posture, clicks into
  Privacy & Trust).
- **Inside surfaces:** LampGadget in the instrument footer row.

Tones:
- `● LOCAL` (ok/green) — data stays on this machine
- `● LAN` (warn/amber) — private network, off-machine
- `● CLOUD` (fail/red) — external service
- `● NO MODEL` (fail/red) — no inference target configured

Position: last item in the footer row, after RunsOnPicker. Optional
detail suffix in `--text-faint`: target name.

### Surfaces to remediate

1. **AskPanel:** Move egress from title `actions` to instrument
   footer row (`desk-chat-well-foot`), after RunsOnPicker. Use
   LampGadget, not EgressChip. Derive tone from the selected
   target's boundary.

2. **PersonaChat:** Same move — egress from title to footer row.

3. **Pullout run (recipe/workflow):** Add LampGadget to the run
   footer, after RunsOnPicker.

4. **Editor AI bar:** Add RunsOnPicker (CycleGadget) and egress
   LampGadget to the Rewrite/Expand/Continue strip. When no target
   configured: `● NO MODEL`, actions disabled.

5. **Workbench workflow run:** Add RunsOnPicker + egress lamp to
   the run toolbar.

6. **Meeting intel state line:** Add compact egress lamp inline.

7. **Cadence / Decision / Delivery drafting:** Add inline receipt
   lamp after response.

8. **Dictation pipeline:** Add egress lamp to the recovery row.

9. **Traffic turn receipts:** After HUB> content, inline lamp +
   target name + model + latency.

## Acceptance

- Every one of the 14 AI surfaces shows an egress readout when
  inference is configured.
- Egress inside surfaces uses LampGadget, not EgressChip.
- Chrome bar EgressChip unchanged.
- Egress lamp is visible BEFORE the call, not only after.
- Tones map correctly: local=green, LAN=amber, cloud=red.
- `● NO MODEL` shows when no target configured.
- Editor AI bar: actions disabled when no model.

## Test plan

- `npx vitest run` (all web tests)
- Screenshot walk: each remediated surface showing the lamp.
