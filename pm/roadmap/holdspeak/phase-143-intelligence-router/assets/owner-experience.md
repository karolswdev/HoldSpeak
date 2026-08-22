# Phase 143 owner experience — Model Library and Assignments

**Status:** normative product contract.

## The two jobs

Settings has two peer destinations:

1. **Model Library** answers “What intelligence is available?” It downloads,
   detects, verifies, connects, and tests models/providers. Adding something to
   the library changes zero assignments.
2. **Assignments** answers “Which intelligence does each HoldSpeak job use?” It
   edits ordered compatible model chains with explicit fallback boundaries.

Never combine these into `Download & use`, `Connect & use`, or `Use model` once
the library exists. The lawful commands are `Download`, `Add to library`,
`Connect`, and `Add model`. Success says: **Added to the Model Library.
Assignments are unchanged.** A quiet **Choose where to use it** may open
Assignments.

A fresh hub with no assignment says **No default model** and offers **Choose
default**. Adding the first model does not change that. A server-projected
starter bundle may be applied only through one explicit **Apply setup** action
that previews every group and boundary. An upgrade preserves each valid legacy
primary as a one-leg assignment; missing/dangling targets remain named issues.

## Model Library

The compact task-first picker remains the library foundation:

```text
Model Library                         7 ready · 1 needs attention
All (10) | This device (3) | Connected (4) | Available (3)

○ Quick Qwen             Fast everyday model.       2.5 GB · 8K
● Balanced Qwen          General reasoning.          6.0 GB · 16K
○ Deep Qwen              Harder reasoning.          17.0 GB · 32K

Balanced Qwen
Local · 6.0 GB · 16K
Strong Thought interviews and everyday writing.
                                             Download
```

Detected, installed, downloadable, and connected models—including Anthropic,
OpenRouter, private, paired, and mesh-backed models—share one row grammar.
Full names wrap; only route summaries may truncate. Rows are flat separators,
not large cards. Details holds filenames, revisions, quantization, source proof,
runtime, and technical compatibility. A broken configured model stays visible
with one repair.

**Add model** opens four entries: **Download from catalog**, **Connect hosted
model**, **Define endpoint**, and **Use model file**. Each returns to this one
library inventory and changes no assignment. Providers is a focused disclosure
for endpoints, secrets, and readiness. It is
not another assignment surface. OpenRouter, Anthropic, custom
OpenAI-compatible, private, paired, and future providers use the same canonical
profile/binding application service.

The sole action follows selected truth: downloadable **Download**; existing
file **Add to library**; hosted profile **Connect**; custom endpoint **Add
model**; active **Ready** as status, not a command. A connection check is quiet
and synthetic. Failure keeps the draft/key in the focused form and offers one
exact **Try again** or repair. Success clears secrets only after durable
confirmation and says assignments are unchanged.

## Assignments overview

The default page height is bounded even if the registry grows to 100 jobs:

```text
Assignments                                      1 issue
Default for AI work       Quick Qwen → Deep Qwen
Thoughts & notes          Uses default · Quick Qwen → Deep Qwen
Writing & dictation       Tiny Qwen → Quick Qwen
Speech recognition        This device
Meetings                  This device → Deep Qwen
Agents & tools            Uses default · Quick Qwen → Deep Qwen
Background                Uses default · Quick Qwen → Deep Qwen
Show task overrides
```

The roster is exactly those seven assignment rows. Each summary is one 48–56 px row: owner-facing group label, effective named
chain, and at most one actionable status. Show the first two models plus `+N`.
Never show a select in every row. Issues sort to the top with one **Fix**.

**Show task overrides** opens capability leaves whose default filter is
**Overrides & issues**. **All tasks** reveals the complete owner-visible registry,
grouped under Thoughts, Writing & dictation, Speech recognition, Meetings,
Agents & tools, and Background. Adding a capability never adds permanent
default-screen chrome.

## Assignment editor

Clicking any summary opens one side sheet on desktop and one full-width sheet
on narrow screens:

```text
Writing & dictation

○ Use default   Quick Qwen → Deep Qwen
● Custom

1  Tiny Qwen                         Ready      ⋯
2  Quick Qwen       Fallback         Ready      ⋯
   Add fallback

Fallbacks run only after the failure types shown in Details.
Cancel                                  Save assignment
```

The model chooser reuses Model Library rows but the server filters compatible
choices for the exact capability revision. Reordering supports drag and
accessible Move up/Move down. The owner edits a draft and performs one atomic,
revision-checked **Save assignment**. There is no fallback toggle and no
per-slot autosave.

Adding a cloud leg shows one line adjacent to it: **Fallback 2 can send this
Note and attached context to OpenRouter.** The material noun changes for the
capability. Incompatible or newly broken saved entries remain in place,
with a specific repair. Raw IDs, filenames, target/profile terminology, and
deployment revisions stay in Details.

## Inheritance on product surfaces

Workbench, Thoughts, Agents, Recipes, and Projects reuse the same summary and
editor contract:

```text
Model   Uses Thoughts default · Quick Qwen + 1 fallback     Change
```

`Use default` always names the resolved chain. It never displays opaque
`Automatic` or `Default`. Changing an override affects the next reservation;
the in-flight receipt remains frozen and the UI labels the new chain **Next
run**. No feature builds a private target selector.

Before **Use default** clears a leaf/subject override, the sheet previews the
effective chain and retry behavior for that exact capability. Group/global rows
show server-projected compatibility issues across their member capabilities;
the browser never guesses that one chain or retry policy fits the group.

## Runtime truth

Exact copy follows durable controller state:

* `Quick Qwen failed. Trying Deep Qwen (2 of 3)…`
* `Deep Qwen completed this after Quick Qwen failed.`
* `All 3 models failed. This task didn’t complete.` only when all three made a
  physical attempt and failed; skipped entries use distinct copy.
* `Quick Qwen refused this run. No fallback was attempted.`
* `Cancelled. No fallback was attempted.`
* `We can’t confirm whether Quick Qwen ran. No fallback was attempted.`
* `Quick Qwen can’t run right now. No model was started.`
* `Deep Qwen needs an OpenRouter key.`
* `Hammer can’t run Thought development yet.`

The UI never claims fallback before a later leg is durably reserved. A fallback
that actually completed is always disclosed. A preflight-unavailable primary
does not imply fallback unless the saved server policy explicitly permits that
disposition.

## 1440 and 393 composition

At 1440, Model Library uses a list plus 320 px detail pane. The selected row,
details, and sole command seat all intersect the visible Desk working band
without scrolling under the dock. Assignments uses the bounded summary list;
its editor is a side sheet. At 393, initial `scrollTop` is zero; title, library
status, source tabs, and at least three model rows intersect the viewport before
scrolling. Both sheets reserve footer space, keep the selected action above the
Desk dock with zero overlap, and meet the same intersection law at 200% zoom.
The assignment sheet shows name, order, readiness, boundary warning, and Save
without horizontal scrolling. Every target is at least 44 px and close restores
exact focus.

## Keyboard and accessibility

* Model lists and assignment choices are labelled radiogroups; arrows move
  selection and selection never executes.
* Reorder exposes Move up/down commands and announces the new ordinal.
* Escape closes chooser/editor and restores exact focus.
* Mod+Enter invokes the sole primary only in the focused surface.
* Status/progress uses semantic live regions with coarse updates.
* Reduced motion, 200% zoom, screen-reader names, and full keyboard operation
  preserve all authority truth.

## Rejection criteria

Reject the implementation if any is true:

1. Capabilities and models become two permanently visible matrix axes.
2. Adding the twentieth capability increases the default page height.
3. Adding/downloading/connecting a model silently changes an assignment.
4. A feature owns a duplicate model selector instead of the shared editor.
5. A saved entry is hidden merely because it became unavailable.
6. A browser infers compatibility, readiness, or fallback eligibility.
7. Order changes autosave one slot at a time.
8. `Default` or `Automatic` appears without the effective named chain.
9. A local-to-cloud boundary crossing is silent.
10. Success/error copy misstates whether fallback occurred.
11. Raw IDs, paths, endpoints, or secrets appear on ordinary glass.
12. There is more than one visible primary in a library/editor state.
