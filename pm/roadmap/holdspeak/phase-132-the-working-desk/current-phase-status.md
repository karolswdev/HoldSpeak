# Phase 132 — The Working Desk

**Status:** in-progress (13/14).

**Last updated:** 2026-08-16.

## Owner mandate

Recorded 2026-08-15, verbatim intent: the consolidation era (Phases 129–131,
"One Grammar", "One Truth", "One Admission Path") is closed; the machine now
points back at the functional side of the product. This phase supersedes the
previously announced "One Owner Per Decision" slot for Phase 132 by owner
direction; the remaining issue #450 Wave 1/2 web-ownership and
product-language items move to the backlog for a later slice.

## Goal

Every daily verb works when touched, every signal the hub already emits lands
on the desk, and every receipt and control tells the truth. This phase repairs
what a six-pillar functional-reality audit (2026-08-15, six Opus auditors,
file:line evidence throughout) proved broken in the product a user actually
operates — and brings the regression net back to green so it stays repaired.

## The evidence base

Audit run `wf_912aff0f-e3c` (six parallel pillar audits on main @ `89259d4f`,
551 tool calls; full structured reports archived in the phase assets). The
one-line verdicts:

- **Routing honesty:** 4 of 5 issue-#450 defects genuinely fixed with named
  regression tests; the survivor is a receipt/manifest layer that still names
  a model the run never loaded (reproduced live: executed `local-A.gguf`,
  receipt printed the cloud model id).
- **Dictation:** desktop hold-to-talk is healthy end to end; the browser
  streaming path double-runs the DIR pipeline, drops its audio floor after
  30 s, throws away a full Whisper pass every 600 ms, and collapses every
  named refusal into "Dictation did not finish".
- **Meetings/realtime:** persistence is healthy (413 scoped tests green);
  realtime is not — 6 broadcast frame types have zero consumers, 7 subscribed
  types have zero emitters, live action-item triage 404s, and stopping a
  non-live meeting kills the hub process.
- **Web desk flows:** 811 web tests green, architecture sound; the breakage is
  the feedback layer — silent write failures across ~13 verbs, a keystroke-
  eating Workbench editor, a Brief whose two verbs persist nothing, and an
  Intelligence board that can falsely read ALL CLEAR.
- **Test reality:** 5542 passed / 71 failed / 17 errors; 87 of the 88 red
  names are byte-identical to the pre-130 inherited ledger. Only ~5 are
  product defects; ~49 are stale tests grep-ing decomposed monoliths, 17 are
  environment, 21 exercise a fake DB the app no longer consults. CI "Tests"
  has been red on main for 8+ consecutive merges.
- **Parked value:** #450 Wave 0 fully discharged; the durable parked blocks
  are Wave 2 product-language consolidation, the web-ownership slice, and
  never-started backlog candidates (JIRA sync, Notion/Docs, merge actuator,
  onboarding) — all explicitly out of this phase.

## Scope

### In

- Meeting stop/conflict route repairs (a mis-bound callback that can shut the
  hub down; a missing import that turns honest 409s into 500s).
- Live in-meeting action-item triage restored through the active session.
- The desk consumes the realtime streams the hub already emits (intel tokens,
  intel completion, bookmarks, queue state, workbench run frames) with a
  frame-vocabulary registry and an orphan guard on both sides.
- One pipeline run per utterance; speak-to-fill separated from
  dictate-for-delivery.
- Streaming-mic honesty: floor heartbeat, named refusals surfaced, retained
  audio recovery real or removed, partials real or removed.
- Desk write verbs report their failures through one shared receipt channel.
- Workbench editing repairs (local draft, honest disabled states, honest drop
  targets, honest Get Info rename).
- Intelligence truth: navigation-owned filters, persisted Brief triage, a
  meetings collector for Changed, aftercare visible without the mascot.
- Receipt/model-name honesty completed for Ask, Recipe chat, the hub manifest,
  and the meetings placement dial, with an executable receipt-honesty fence.
- The Cadence reply route.
- The regression net: stale tests re-pointed or retired, harness seams fixed
  or tests honestly rebuilt, environment errors converted to skips, canon
  guards green — exit is a green CI "Tests" on main.
- Roadmap record truth: contradictory phase headers corrected, the
  never-committed Phase 120 record landed honestly, missing final summaries.
- A committed screenshot walk (1440 + 393) covering this phase's surfaces and
  the outstanding Phase-130 Article IX.2 IOU, plus a live `.43` proof of
  receipt honesty.

### Out

- Issue #450 Wave 2 (Daily Brief merge, Follow-through as the only
  obligations board, Decision/Receipt model convergence) — backlog.
- The web ownership slice (Workbench skill-binding override, Get Info
  placement hand-off, one target spec API) — backlog, next slice.
- Net-new features: JIRA Desk Sync, Notion/Docs connectors, merge actuator,
  first-run onboarding, workbench manipulation verbs — backlog.
- Any Swift/iPad/iPhone work (standing direction: web desk is the spec).
- Destination-deletion repair sweep (honest refusal already exists) — backlog.
- Changes to the Constitution.

## Constitutional grounding

- **Article II (honest product):** controls that do what they say; a desk that
  cannot silently no-op. Silent write failures, the ALL CLEAR lie, the dead
  Rename, and the wrong-model receipt are Article II violations in shipped UI.
- **Article V.2 (every attempt leaves a receipt):** desk verbs that swallow
  failures leave no receipt at all; the shared write-receipt channel restores
  the article at the UI layer.
- **Article IX (real-runtime proof):** the phase closes on a screenshot walk
  at real sizes and a live `.43` receipt-honesty proof, and it discharges the
  Phase-130 Article IX.2 screenshot IOU.
- **Article XI.3 (immutable admission identity):** the receipt must name the
  admitted deployment's model — the last surviving describer that answers
  from mutable config instead of the resolved deployment is retired.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-132-01 | Stopping a meeting never stops the hub | done | [story-01](./story-01-meeting-stop-and-conflicts.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-132-02 | The live meeting is a living board | done | [story-02](./story-02-live-action-item-triage.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-132-03 | The desk hears intelligence live | done | [story-03](./story-03-realtime-frames-land.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-132-04 | One utterance, one pipeline | done | [story-04](./story-04-one-pipeline-run.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-132-05 | The streaming mic is honest | done | [story-05](./story-05-streaming-mic-honesty.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-132-06 | Desk writes report their failures | done | [story-06](./story-06-write-receipts.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-132-07 | Workbench edits hold | done | [story-07](./story-07-workbench-editing.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-132-08 | Intelligence tells the truth | done | [story-08](./story-08-intelligence-truth.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-132-09 | The receipt names what loaded | done | [story-09](./story-09-receipt-model-honesty.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-132-10 | One meetings placement dial | done | [story-10](./story-10-one-placement-dial.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-132-11 | Cadence answers land | done | [story-11](./story-11-cadence-reply.md) | [evidence-story-11](./evidence-story-11.md) |
| HS-132-12 | The regression net comes back green | done | [story-12](./story-12-green-net.md) | [evidence-story-12](./evidence-story-12.md) |
| HS-132-13 | The roadmap tells the truth | done | [story-13](./story-13-roadmap-truth.md) | [evidence-story-13](./evidence-story-13.md) |
| HS-132-14 | The walk | done | [story-14](./story-14-the-walk.md) | [evidence-story-14](./evidence-story-14.md) |

The ask each story answers, in one line: 01 — a stale Stop cannot kill my
runtime and a resolved conflict answers 409, not 500; 02 — I can mark an
action item done while the meeting is still running; 03 — streams the hub
already emits render on the desk, no orphan frames either way; 04 — speaking
in the Speak room is processed once, journaled once; 05 — long dictation
keeps the floor and failures are named; 06 — a failed create/drop/keep/
dismiss names itself instead of doing nothing; 07 — typing in an item keeps
my characters, disabled and drop states say why; 08 — no false ALL CLEAR,
Brief triage persists, a recorded week shows in Changed; 09 — receipts and
the manifest name the executed model, always; 10 — one placement control
that shows what actually decides; 11 — Send reply delivers instead of 404;
12 — CI "Tests" is green on main and a new break is visible again; 13 —
orientation tools report reality and Phase 120's record exists in git;
14 — the screenshot walk at both widths plus the live `.43` proof.

## Suggested order

01 → 02 → 03 (meetings spine, serialized) in parallel with 04 → 05 (dictation)
and 06 → 07 → 08 (desk feedback layer); 09 → 10 (honesty pair) any time;
11 free-floating; 12 after all product stories land (quiet tree); 13 any
time; 14 last, cannot be waived.

## Held owner questions

1. **Egress vocabulary ruling.** In yolo posture the GitHub/webhook companion
   receipts say `per_action_decision` / `authorization_required` where the
   tests contract `control_posture` / `refused`
   (`holdspeak/operation_policy.py:271-338`). Product regression or
   intentional rename that left the tests behind? HS-132-12 needs the ruling
   to know which side to fix.
2. **Streaming partials.** HS-132-05 carries a design beat: make per-chunk
   partial transcription real (progressive fill in the target field) or delete
   it and pay one Whisper pass per utterance. Orchestrator default: delete;
   owner may overrule.
3. **Subagent model alias.** The harness's `opus` alias resolved this
   session's audit fleet to `claude-opus-5[1m]`, not the ruled
   `claude-opus-4-6[1m]`; the repo `opus-worker` agent definition pins the
   exact string for future sessions. Flagged for the sitting.

## Exit criteria (evidence required)

- [ ] Stopping with no live meeting refuses honestly; the hub process
  survives; sync-conflict branches answer 409/400 by name.
- [ ] An action item surfaced mid-meeting can be completed, dismissed,
  reviewed, and edited before the meeting ends.
- [ ] `intel_token`/`intel_complete`/`bookmark`/`runtime_queue` render live on
  the desk; `workbench.*` frames are emitted and consumed; a guard test fails
  on any frame type orphaned on either side.
- [ ] One DIR pipeline run and one journal row per spoken utterance; field
  mics fill fields without journaling.
- [ ] A >30 s streaming dictation retains the audio floor; every server
  refusal reaches the user by name.
- [ ] Every desk write verb surfaces its failure with a named, retryable
  receipt.
- [ ] Workbench item body editing is draft-buffered and loses no keystrokes.
- [ ] The Intelligence board can never render ALL CLEAR while commitments
  exist; Brief acknowledge/defer survive reload.
- [ ] Readiness model == executed model == receipt model == advertised
  manifest model for every destination kind, held by an executable fence.
- [ ] Meetings placement is one user-facing control that surfaces
  `placement_source` and names an overridden provider intent.
- [ ] Cadence reply delivers (2 red tests green).
- [ ] CI "Tests" workflow is green on main; environment-dependent tests skip
  by name; the canon guards pass.
- [ ] Phase headers 113/114/118/121/124 match their story tables; the Phase
  120 record is committed with an honest evidence note.
- [ ] The walk: committed harness, 1440 + 393 screenshot walk over the phase's
  surfaces (including the Phase-130 IOU surfaces), live `.43` receipt-honesty
  proof captured through `dw evidence capture`.

## Where we are

13/14 done in one day (2026-08-15/16). All twelve product stories shipped
through the gate; HS-132-12 closed with the full backend suite at
5703 passed / 0 failed / 0 errors / 47 named skips (~3.5 min parallel) and
the web suite 917/917 — plus five extra product fixes found by the net
burn-down, the 75-minute suite wedge root-caused (mermaid npx into fresh
HOMEs) and made impossible (300s per-test timeout law), per-xdist-worker
HOME isolation, and the owner's disk crisis traced and cleared. Held owner
question #1 (egress vocabulary) closed as no-drift. Only HS-132-14 — the
walk — remains.
