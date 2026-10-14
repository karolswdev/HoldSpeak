# Deep usability pass — 2026-10-14

Owner correction: Send was an example. The job is to discover pressing issues
across HoldSpeak through actual use, then repair the affected jobs together.
Release: [#1202](https://github.com/karolswdev/HoldSpeak/pull/1202).
Base: main eb9a3266e (#1201). Three bounded Sol xhigh audit/build lanes; root
owns source/shot checks, integration, verification and one release.

## What the deeper pass found

| Job | Observed problem | Settled repair |
|---|---|---|
| Write Knowledge | Body PUT returns200 and a saved receipt; after Save/reload the written text is gone. Canonical Knowledge is a member collection. | Correct name/member editor; remove unsupported body authoring; explicit retained-text recovery as a Note. |
| Finish an edit | Cancel has already saved the changes. Save can close after a refused write. | Truthful autosave, actual receipt, Done/Close flush fence, retained failure and Retry in both hosts. |
| Edit a Workflow | A supported prompt-only Workflow has no prompt editor; linear step controls and prompt extend beyond the frame. | Existing prompt field, stacked step layout, library controls; preserve branching graphs. |
| Read a report's context | Four setup forms precede saved notes; phone note text clips without an opener. | Readable saved context first, note composition on request, folded link setup. |
| Keep a Person note draft | Context→Prep→Context empties Topic and Note. | Existing per-person desk drafts, restored on return/reload and cleared only after accepted Add. |
| Correct project work | A refused Save & confirm closes the editor, loses text/owner/date and hides the refusal. | Keep correction and cause in the same well; retry; close only after acceptance. |
| Compose Workbench work | Close/reopen discards the instruction; an unbound Workbench leads with agent configuration. | Keep the composition per Workbench; work/composer lead, configuration on request. |
| Find created work | Workbench Add succeeds while its original app still says No workbenches yet. | Reread the authoritative list through the existing desk-change signal. |
| Return to a recurring schedule | Recurring/cron/90min returns as Once/60min with the old title. | Preserve the whole existing schedule draft, restore without scheduling. |
| Keep accepted work through a failed read | Aggregate503 can replace known item buckets with empty arrays and hide a saved Workbench. | Retain only explicitly classified transient buckets; successful empty reads and401/403 remain authoritative. |
| Choose Ask sources | Controlled component reproduction shows reverse-order reads dropping one of two choices; inputs are nested in raw buttons. | Merge current choices, keep one existing checkbox control per row; actual Ask selection walk follows. |

These are job, content and action-authority defects. Styling and composition
follow the corrected job. [Settled implementation](IMPLEMENTATION.md) names
exact ownership, acceptance, focused checks and scope. Independent review also
found an awaited Schedule creation erasing newer edits; submitted-snapshot
acknowledgement now covers both the mounted and reopened form.

## Coverage, with its boundaries

- [Work](work.md): actual People Context/Prep/History and Room correction,
  refusal, confirmation and existing action/decision paths at1440/393.
- [Create](create.md): actual Knowledge creation/edit/cancel/refusal/reload;
  Agent and Workflow editing/return, supported prompt-only Workflow; Artifact
  view; Thread rename/draft/engine-refusal. The matrix names phone selector
  gaps instead of treating them as dead actions. Directory remains parked.
- [Operate](operate.md): actual Workbenches chooser/creation/inlet/return/Add,
  empty Runs/Memory where reached, phone recurring-schedule return, Repo file/
  directory/PR/issue reads and Roadmap Timeline/Stories/Health. Populated runs,
  real execution and a successful Delivery dossier remain outside observation.
- [Root](root.md): supplementary desktop Settings Voice/Accounts Add/People
  poses, source and controlled shared-context reproduction, independent reading
  of the pressing before shots. Actual Search → Ask source selection then passed
  separate production graph walks at1440/393. The supplementary Settings phone
  audit remains unobserved.

Seeded data and actual UI actions are recorded separately. Each audit had at
most two capture setup attempts. No general sweep verdict is used as approval
of an unseen editor, inner object or operation. No new audit framework or
nightly suite was created. Every walk/check uses isolated HOME/DB and the
machine lock. The owner's runtime is not an audit target.

## Composition checks

Native canvases precede product edits. Root read Work Context393/Addnote1440/
Room refusal393; Operate empty393/draft1440/schedule393; Create Knowledge393/
Workflow1440/failure393/recovery393. They use production components with
synthetic data and are direction checks, not action proof. Work and Operate
canvases live under phase17/canvas/deep-*; Create's canvas lives in this record
folder. Workers build those compositions, retain real privacy/authority and
hold for SHIP. Current delivery follows CLAUDE's October12 fast cycle; these
records are not a historical premerge Muad'Dib gate or a claimed Muad'Dib check.

## Delivery proof

Implemented-screen and action checks are complete for the repaired jobs at
1440/393. They include retained Person drafts and refused Room corrections;
accepted correction plus failed reread; Workbench body/priority/source draft,
phone source choice, accepted Add plus failed list and Retry; recurring
schedule return/reload; normal-motion editor Close refusal and Retry; real
Knowledge member editing and seeded legacy-text → real Note/member recovery;
Agent close flush; Workflow graph/prompt editing and actual title-bar Edit;
and two resolved Ask source choices. Source reads, controlled failures,
seeded legacy data and actual UI-produced data are distinguished in each record.

Focused unit checks passed in each lane. Their overlapping counts must not be
summed: Work75, Operate50 before its final Schedule6, Create40/35/21/9/5,
shared reads16, root Grounding19 and Note close40. Logs are named in the lane
records. Production TypeScript and capability documentation generation passed.
Final combined quick check **GREEN**: **3717 web tests /407 files**, **550
Python checks**, **107 desktop/phone sweep cases** with2 existing xfails,
and **15 canon guards**. Production build and frozen-source TypeScript passed.
Release logs: `.tmp/deep-usability/quick-release/`; console
`.tmp/deep-usability/quick-release-console.log`. Final corrected-definition
Ask graph cases passed separately at both widths; see root.md. The first
combined run exposed metadata failures, all fixed and rerun, not waived.

[Independent review](review.md) found the Schedule custody defect and prompted
the bounded fix and deferred-request regressions. The independent fix recheck
returned RATIFY with no remaining review conditions. The initial review's Create
desktop/recovery and Ask phone evidence gaps are now closed by independent
production captures and the two graph walks. No Muad'Dib check or Astra
postmerge review is claimed.

Open audit tails: existing Workbench item-body timer/unmount custody; compact
Grounding summary truncation/zero count; Settings phone inner poses; populated
Workbench Runs/Memory and successful Delivery dossier. Each is recorded as
unobserved or source/shot evidence, rather than silently called usable.
Owner judgment, real model/agent/terminal/microphone execution, external
account/delivery actions and physical-device use are not established by these
isolated observations or by a component test.
