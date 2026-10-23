# Surface modernization and the in-desk reference

Source: `62358b67189cf39de78be7395c7730c56231092e` (#1427).
Audit by Astra, 2026-10-22. Read-only product inspection; no product changes.
**Design recommendations: UNCHECKED — awaiting Muad'Dib.** This record is
not a new canon, implementation authorization, or owner aesthetic acceptance.

The owner likes the modernization direction but asks whether the whole app,
its layouts, shared components, compositor and documentation support it. He
also proposes a golden-record design page inside the desk. The Tuesday test:
can he recognize the job, read what matters, act, and recover without learning
a different interface in each window? The shared foundation helps; this audit
does not establish that result across all windows.

## Findings

| Area | What exists | Remaining work |
| --- | --- | --- |
| Shared material | Token source and generated CSS/TS, common controls, frame material, illustrated icon sources. | Material changes propagate broadly, but do not establish interior hierarchy, reading width or task clarity. |
| Components | A substantial surface library with real form, state, ledger, source, reading and composer consumers. | Higher-level composition is less uniform than the low-level controls. An export or specimen is not proof of live adoption. |
| Layout | Shared sections, rows, columns, form sheets, readers and container reflow. | Reconcile grouping, spacing, metadata, action placement and scroll ownership across real task families. Avoid forcing every task into one layout. |
| Compositor | Common frame, live planes, placement, motion, resize and compact behavior. | Front-window derivation, mounting and scroll policy still cross several registries and family-specific seams. No rewrite is justified by this audit. |
| Documentation | Useful API contracts, tokens, owner rulings and bounded journey records. | Current guidance and historical material/process instructions are intermixed. Following an older imperative can recreate the rejected style. |

Source anchors:

- `web/src/desk/surface/index.ts`: actual exported library, including later
  reading, conversation, state and object patterns.
- `web/src/pages/cores/ComponentsCore.tsx:120`: production control specimens;
  `:192` local composer; `:261` ledger; `:295` empty/error; `:299` state family.
- `web/src/desk/components/DeskWindow.tsx:853`: frame front state uses
  compositor planes; `components/window/Dock.tsx:374` derives its own front
  from the store order/open list. This is a maintenance seam, not an observed
  focus failure in this audit.
- `web/src/desk/compositor/useCompositor.ts`, `live.ts`, `hubWindows.ts`,
  `web/src/desk/store/compositorSlice.ts`, and `windowRegistry.ts` split live,
  persisted and remote-open responsibilities. Document the authority of each
  before consolidating anything.
- `web/src/features/project-room/review/ReviewPosture.tsx` and its CSS retain
  feature-owned form/action composition; Ask uses shared `ComposerWell` and
  `desk/surface/patterns/conversation.css`. These are contrasting consumers
  to inspect, not a mandate to put every editor into a conversation layout.

## Golden record: develop the existing Components window

The existing application manifest registers **Components** as a desk window
(`web/src/desk/applications.ts:320`); `/design/components` also resolves to it.
Its current catalogue is a useful seed. It is not yet a complete pattern
reference: controls and notices work, but many specimens are isolated parts,
and some example actions are no-ops.

Proposed next slice: a bounded reference for **editing and recovering a form**,
using the actual shared controls and window host. Show ordinary, dirty,
invalid, saving, failed/retry and saved states, including a long value and a
narrow window. Use explicit local specimen state. Carry the same composition
into two appropriate real consumers, such as Settings and an Automation
editor; record the exact consumers and the remaining differences. Do not
count the gallery itself as production adoption.

Then add complete examples for reading a result with sources, choosing an
item in a list and viewing its detail, conversation, and long-running work.
Each should demonstrate:

- clear identity, useful grouping, reading width and one leading action;
- empty, populated, busy, unavailable and recovery states where relevant;
- keyboard/focus behavior, narrow reflow, one declared main scroller and
  reachable actions with long content;
- its production component imports and named live consumers, with proposed,
  parked and gallery-only examples clearly distinguished in the author map;
- the desk's existing per-window feedback entry, so the owner can report on
  the reference in the same way as any other window.

Use the common implementation. A copied demonstration with independent CSS
will drift. The existing Buttons/controls catalogue can remain a separate
section inside Components; no second design app or framework is needed.
Publish an example as the reference only after it is actually implemented,
observed in its named consumers and reviewed on the owner's running desk.

## Documentation reconciliation

Keep responsibilities short and distinct:

| Home | Responsibility |
| --- | --- |
| Constitution / UX-CANON | Owner principles and interaction obligations. |
| DESIGN_SYSTEM / token source | Current material, type, spacing, control geometry and semantic tokens. |
| Surface contract / barrel | Supported component and pattern APIs, composition and import rules. |
| Components window | Executable reference examples using those APIs. |
| `web/README.md` | One author map, including compositor/frame versus interior ownership. |
| Existing release records / tracker | What shipped, which consumers were observed, and what remains open. |

Repair these specific contradictions, preserving historical owner quotes and
compatible token/class names:

- `surface/contract.md:21` still specifies 10px chip text; source uses the
  12px label token. `:170` still prescribes the full Steel bevel.
- `DESIGN_SYSTEM.md:109` describes a default 44px Button; current painted
  desktop size is 32px, with 44px narrow target ownership. Its gadget matrix
  at `:172` still prescribes square bevel/mono-uppercase material despite
  the modern shell amendment at `:33`.
- `surface/contract.md:1029` still calls every verb a 28px Steel plate.
- `UX-CANON.md:92` should describe its list as core species and link to the
  actual contract/barrel, rather than imply the older list is exhaustive.
- TWO-BRAINS and ORCHESTRATION retain imperative premerge/DW passages. Link
  their current-flow entry to `CLAUDE.md:6` and clearly label superseded
  process history. Screenshots before merge and owner aesthetic acceptance
  are distinct; do not introduce an owner approval gate.

Update documentation **in the same change** when material meaning, component
API, interaction behavior or ownership changes. Update the matching executable
specimen with the component; record actual adoption where it changes. A local
spacing correction need not rewrite the canon. Retire contradictory guidance
from current instructions while retaining its history. Existing October 14–17
surface/flagship records remain evidence for their named revisions, not proof
that today's entire product has been visually accepted.

## Verification and limits

Fresh isolated runs on the frozen #1427 source/build:

`tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences`, filtered to
`room`, `conductor`, `surface-components`, `automation`, and `needs`, at both
1440 and 393. Collection: **10/110 cases**; run: **10 passed in 19.38s**.
Run used the test lock, isolated HOME, and `DESK_SWEEP_SHOTS=1`. Astra viewed
all ten resulting images under
`/Users/karol/dev/tools/wt-richer-icons-20261022/.tmp/evidence-shots/desk-sweep/`.
No owner desk data was used by this rig.

Observed composition examples: the narrow Room splits the question input,
answer mode and unavailable-engine choice across several rows; Agents retains
outlined connection groups while Automation uses a sentence-led setup and
boxed results. These are real differences to judge and reconcile, not proof
that every difference is a defect. Components is a long specimen catalogue,
not a task-oriented reference. Passing fit/geometry checks does not establish
beauty, clarity or all-state behavior.

The #1427 full tape is complete and **not green**: 13 Python failures and nine
browser failures across its shards; web baseline and Firefox timing pass.
This audit did not attribute those failures to a particular merge. The
betterment tracker's 115/117 merged slices are implementation accounting,
not a percentage of modernized or owner-accepted interfaces. No exhaustive
live-owner journey or aesthetic acceptance is claimed.

Review provenance: three read-only Luna audits supplied component, compositor
and documentation findings; Astra checked the key source seams and all ten
shots. These are audit inputs, not Muad'Dib's check. Setup MCP
`agent.start_helper` returned `launch_only` / 403, “only a launched agent has
helpers,” for this owner-started session. No credential bypass was attempted.
Recommendations therefore remain unchecked; current canon and product code
were not changed.
