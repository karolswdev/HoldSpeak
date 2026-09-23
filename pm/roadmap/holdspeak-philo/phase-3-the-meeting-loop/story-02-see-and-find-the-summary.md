# PHILO-3-02 - See and find the summary

- **Project:** holdspeak-philo
- **Phase:** 3
- **Status:** done
- **Depends on:** none
- **Unblocks:** the meeting loop
- **Owner:** Astra; Muad'Dib checks design and counsels on built
- **Council tag:** A2

## Problem

The central meeting job has no proven completion on the rig, and by source trace the arrival never learns a summary landed: the Chair refreshes once after Run summary (`ChairHome.tsx:756`), only the Live window consumes `intel_complete`/`intel_status` (`LiveCore.tsx:177`), and the drainer emits no `desk_changed`; a retrying job shows QUEUED and FAILED under "Nothing needs you" (`ChairHome.tsx:628,1949`; `intel_queue.py:513`). Import is only ACCEPTED at capture (202, duration 0). Restart retrieval is unverified.

## Scope

- **In:** the owner result below and its closure evidence; the proof repairs the council named for this story.
- **Out:** everything the council deferred (COUNCIL.md, "Deferred, explicitly").

## Edges and states this story closes

edge.face.arrival_run_intel; edge.timer.intel_drainer; edge.cli.restart_hub; states meetings.intelligence.{queued,running,ready,failed}; J4, J5, J6, J7

## Acceptance criteria

- [x] A COMPLETED import with its length and transcript on the row (the case waits for completion).
- [x] One Run; the ACTUAL host and the summary text appear on the arrival without a manual refresh; retrying and failed jobs show their state, actual LAST ATTEMPT host, and the plain LAST ERROR · PROVIDER FAILED cause.
- [x] The same summary is found after a hub restart (the rig's restart step, retained evidence), and the planned host is visible at 393 with nothing covering the control.
- [x] One synthetic architect meeting with planted decisions, owners and actions is the material; the documented install is reproduced in isolation and its result retained (the model client question, D2) before the owner touches it.
- [x] Closure evidence: the end-to-end chain on the rig with retained observations at both widths; technical completion and owner usefulness reported separately.

## Effort (council estimate, not a promise)

2–4 days incl. proof repairs (import wait, one-trigger recipe, a lawful failure reply, retained restart evidence)

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above, run through `scripts/graph_walk.py`, observations retained.
- **Manual / device:** the owner's sitting on the finished chain.

## Lane record

2026-09-23 — **OWNER RULED, counsel round two:** summary open, transcript collapsed by default, word count on its existing fold, one click to open. [Muad'Dib's RATIFY-WITH-CONDITIONS](checks/story-02-built-muaddib.md) identified that the earlier cause claim described a queue wrapper, not a plain cause. Box 2 now names the required displayed facts. The C1 correction, current queue count, refresh continuity and plain read-error facts are paid in the same follow-up; the story remains done and evidence is appended, with no new status flip. Aftercare obstruction and ASR instability are [ledgered, not repaired here](../../../../docs/internal/philo/phase-3/summary/round-2/deferred-ledger.md).

2026-09-23 — **OWNER RATIFIED:** “Ratify, build it.” The corrected Arrival boards in `assets/story-02-canvas/` were published at [the owner canvas](https://claude.ai/artifact/KnASxYRZc4UXkAiFU1z5zX). Seams (c) and (d) now build under that ratification and Muad'Dib's recorded check: existing row grammar, length and words, planned host before Run, actual receipt afterwards, summary/transcript wells, LAST ATTEMPT / LAST ERROR, no new row verb or attempt limit.

2026-09-23: under Muad'Dib's recorded RATIFY-WITH-CONDITIONS, install correction committed first as `794f07ff`, verified by an independent base install from fresh source/HOME/venv. Queue correction committed as `a28c19f9`, after four pre-fix failing producer fences and 77 passing focused tests. [Corrected canvas](assets/story-02-canvas/README.md) goes to Muad'Dib for the owner's ratification before Arrival implementation. [Retained proof and remaining steps](summary-lane-record.md). Acceptance criteria were unchanged and unclosed at that checkpoint.

## Closure — 2026-09-23

Technical A2 is complete under the owner-ratified design. [Lane record](summary-lane-record.md), [captured evidence](evidence-story-02.md), [technical observations](../../../../docs/internal/philo/phase-3/summary/technical-completion.md), [usefulness with omissions](../../../../docs/internal/philo/phase-3/summary/usefulness.md), and [full-suite classification](../../../../docs/internal/philo/phase-3/summary/integration/full-suite-classification.md). Usefulness is partial; the owner has not sat with the chain. This closes the five technical/reporting acceptance boxes, not the phase exit. Muad'Dib counsels on built before merge.
