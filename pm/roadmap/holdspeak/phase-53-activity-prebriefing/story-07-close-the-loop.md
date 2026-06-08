# HS-53-07 — Close the loop: the selection actually feeds the model

- **Project:** holdspeak
- **Phase:** 53
- **Status:** done
- **Depends on:** HS-53-03, HS-53-04
- **Owner:** unassigned

## Problem
Chasing a real-metal proof for the closeout (HS-53-06) exposed that **"Dictate
with this" did not actually change what the model wrote.** The loop was open in
two places:

1. **The live dictation path never read the pin.**
   `dictation_runner.run_dictation_pipeline` called
   `build_activity_context(limit=20, refresh=False)` with no `selected_record_id`,
   and the "Dictate with this" button only wrote a `localStorage` pin — nothing
   carried it to the backend.
2. **The rewriter never consumed activity records.** `project_rewriter.py`'s
   prompt builders read only `activity["target"]` and `activity["agent"]`; a
   `grep` for `records`/`selected`/`entity` returned nothing. So even when
   HS-53-03 pinned the selected record at `records[0]`, nothing downstream used
   it.

HS-53-03 unit-tested the *pinning*; this story makes the pin *do something* — and
proves it against a live LLM (the `.43` Q6 endpoint).

## Scope
- **In:**
  - A server-side **one-shot selection pin** (`holdspeak/dictation_selection.py`):
    process-local, recency-bounded, consumed once. Mirrors the
    `get_recent_awaiting_agent_session` recency lookup the agent-reply path uses.
  - **`run_dictation_pipeline` consumes the pin** and passes
    `selected_record_id` to `build_activity_context`, so the selected record is
    pinned at `records[0]` of the bundle the rewrite stage sees. No pin -> `None`
    -> byte-identical default.
  - **The project-rewriter names the selected record to the model**
    (`_selected_activity_context`): a one-line, source-cited reference injected
    into both the draft and refine prompts, plus a rule to ground the rewrite in
    that issue/PR/page. Empty string (byte-identical prompt) when nothing is
    selected.
  - **Two routes** (`POST /api/activity/nudges/select`,
    `POST /api/activity/nudges/select/clear`) and the **frontend wiring** so
    "Dictate with this" parks the selection server-side and "Clear" drops it. The
    select route validates the id against the real ledger (unknown -> 400).
  - **A real-LLM dogfood** proving the closed loop: the same generic dictation,
    run with and without a selected `github_issue`, on the `.43` endpoint.
- **Out:** running the rewriter without `.hs` project context (the rewrite stage
  is `.hs`-gated by design; the selected record augments an existing rewrite).

## Acceptance criteria
- [x] The live dictation path consumes a parked selection and folds the record
      into the rewrite context; no pin -> byte-identical default. (unit)
- [x] The project-rewriter names the selected record in the draft + refine
      prompts; no selection -> byte-identical prompt. (unit)
- [x] `select` / `select/clear` routes set + clear the pin; unknown id -> 400.
      (integration)
- [x] A real-LLM dogfood on the `.43` endpoint shows the selection
      **demonstrably changes the model output** (treatment references the issue;
      control does not). (`dogfood-real-llm-transcript.txt`, RESULT: PASS)
- [x] Full suite green; `npm run build` clean; 0 `_built/` tracked.

## Test plan
- Unit: `test_dictation_selection.py` (the pin),
  `test_dictation_selected_record_prompt.py` (the prompt grounding).
- Integration: `test_web_activity_nudges_api.py` (the select/clear routes).
- Real metal: `dogfood_real_llm.py` against `192.168.1.43:8080`.

## Notes / open questions
- The rewrite stage only runs in an `.hs` project (the DIR-01 design). The
  selected record augments that rewrite; it does not force a rewrite where one
  would not otherwise happen. The dogfood runs in the `.hs` demo fixture, the
  realistic surface for "dictate a reply with this issue as context".
- The too-long guard (`_rewrite_too_long`, ~4x the input) is real: a very short
  dictation caps the draft length. The dogfood uses a realistic-length dictation
  so the grounded output fits — exactly how the feature behaves in product.
