# Evidence — HSM-17-05: AI-drafted answers (approve-then-inject)

**Date:** 2026-07-04. **Proof style:** unit-pinned assembly + a LIVE endpoint
draft against the LAN model, grounded and correct; the composer's Draft
affordance simulator-shot. The on-device (air-gapped) draft on the iPad Air M4
walks in HSM-17-06 with the phase's other device beats, as the story planned.

## What shipped

- **`CoderAnswer.draftPrompt` / `draft` (RuntimeCore)** — the fourth input into
  the 17-04 composer. The coder's question is the `[TASK]`; dropped-context
  grounding rides as a cited `[CONTEXT — <source>]` block (bounded at 6k chars);
  the model is told to write AS the user, first person, reply-text only. One
  `ILLMProvider.complete` call — **the draft API cannot reach the desktop
  client by construction** (test-pinned): drafting composes, only the human's
  Send injects.
- **The composer action** — a violet "Draft with AI / Re-draft" button with its
  OWN egress chip (`.local` on-device / `.cloud("endpoint")`) distinct from the
  send row's `Local + your desktop`: where the draft RUNS is not where the
  answer GOES. Drafting state, honest inline error (the composer keeps the
  human's text on failure), the draft lands editable in the reply editor,
  re-draft reuses the (possibly trimmed) grounding. The stage resolves a FRESH
  provider per call via the desk's `callLLM` (the Mode-A KV rule); the seeded
  demo drafts offline so the flow stays drivable without a model.

## The live endpoint proof (opt-in test, run against the LAN box)

`CoderDraftLiveTests` (skipped unless `HS_LIVE_DRAFT_ENDPOINT` is set — the
Python suite's opt-in e2e posture). Run against the LAN llama.cpp
(Qwythos-9B), question: *"Should the sync queue retry failed pushes
automatically, or surface them for manual retry?"*, grounding: the mesh-queue
design decision (durable-first, per-workflow failure policy). The draft, in
0.52s:

> The sync queue should surface failed pushes for manual retry. We already
> handle retries per workflow, so auto-retrying here would bypass our
> intentional failure policies.

First person, decisive, and **grounded** — it argued FROM the attached
context, which is the whole point of the gesture.

## The composer (screenshots/hsm-17-05-composer-draft.png)

The seeded answer composer showing every affordance in one frame: THE QUESTION
block, the type-or-speak editor with the mic, **Draft with AI** with its
**On device** egress chip, the **Local + your desktop** send badge, Cancel /
Send — the glaring waiting coder visible behind.

## Acceptance vs. delivered

- Draft from question + dropped context via the resolved provider — shipped;
  endpoint path **live-proven**; the on-device air-gap run is an HSM-17-06
  device beat by the story's own criteria.
- Draft lands editable; never sent without explicit approval — the API cannot
  inject (pinned), the button only fills the editor; re-draft works.
- Approve injects via the 17-04 path — unchanged, live-proven in 17-04.
- Egress-honest — the draft's chip reflects the engine; the send's badge stays
  the LAN crossing.

## Tests + builds

- `CoderAnswerTests` +6 (prompt shape, cited grounding, runaway-grounding
  bound, one-call trim, **draft-never-touches-the-client**, failure surfaces);
  `CoderDraftLiveTests` (opt-in, live-run above). Full SPM suite
  **465 passed / 9 skipped / 0 failures**; simulator app build **SUCCEEDED**.
