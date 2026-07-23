# HS-103-03 - Grounding verification — does the artifact say what the source says

- **Project:** holdspeak
- **Phase:** 103
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-103-06
- **Owner:** unassigned

## The research finding (the bar)

A research pass over `ViuGiaLai/researchmind` (an unrelated academic
research-assistant repo, MIT-licensed, examined for carry-over ideas
only — not code to vendor) found one genuinely transferable mechanism:
claim-decomposition + citation-entailment grounding verification
(`backend/chat/claim_decomposition.py` + `backend/chat/citation_entailment.py`
in that repo — an atomic-claim splitter feeding a deterministic,
dependency-free lexical `entailment_score()` that labels each claim
`entailed` / `partial` / `unsupported` against its cited source
passage, with an *optional* local NLI model as an upgrade path that
silently falls back to the lexical scorer if unavailable — no extra
network call either way).

HoldSpeak already hydrates references into prompts (`holdspeak/grounding.py`)
and ships cited output (meeting artifacts with transcript-moment
citations, Ask-AI answers with source receipts) — but nothing today
checks that the GENERATED claim is actually supported by what it
cites. A citation currently asserts provenance ("this came from
somewhere"), not support ("this is actually true of what it cites").
Given HoldSpeak's whole positioning is "quiet trust" (egress badges,
`learned-from-N` chips, honest receipts, never a raw wire dump — see
`docs/internal/POSITIONING.md`), a per-claim support signal is directly
on-brand: it's the same trust posture applied one level deeper, from
"here's where this came from" to "here's whether this is actually
backed by where it came from."

## Problem

Meeting-artifact bullets and Ask-AI answers can drift from their cited
source with no detection — an unsupported or hallucinated claim looks
identical to a well-grounded one. Add a cheap, local, deterministic
check that flags claims whose text isn't actually supported by the
transcript/source span they cite, surfaced as a quiet, honest signal —
never a hard verdict (a lexical checker will false-flag legitimate
paraphrase, so it must read as "possibly unsupported, worth a look,"
not "this is wrong").

## Scope

- In: a small, dependency-free lexical entailment scorer (adapt the
  researchmind pattern — token-overlap / claim-to-passage support
  scoring, no model call) applied as a post-generation check on (a)
  the meeting-artifact synthesis path (`holdspeak/plugins/` — wherever
  artifacts carry a transcript-moment citation today) and (b) the
  Ask-AI answer path. Surface the result as a quiet per-claim chip in
  the existing chip/badge vocabulary (alongside `learned-from-N`,
  egress badges) — something like a low-key "unverified" mark on a
  bullet whose support score falls below a documented threshold, never
  blocking or altering the underlying content.
- Out: any network/model call for entailment (must stay local and
  free, matching the egress posture — no cloud NLI); rewriting or
  blocking generation based on the score (this is a signal, not a
  gate); the rest of researchmind's RAG-hardening surface
  (context-compression, claim decomposition beyond what's needed to
  feed the scorer) — port only the entailment check itself, not the
  surrounding machinery; retrofitting every historical artifact (apply
  going forward / on next synthesis, not a backfill migration — this
  project's posture is greenfield/aggressive, no migration ceremony).

## Acceptance criteria

- [ ] A pure, testable `entailment_score(claim, source_text) -> float`
      (or equivalent) function exists with unit tests covering clearly
      supported, clearly unsupported, and ambiguous/paraphrase cases —
      the ambiguous case's expected behavior (partial/uncertain, not a
      hard fail) is explicitly asserted.
- [ ] At least one real generation path (meeting artifacts OR Ask-AI —
      pick the cheaper integration first) runs every generated claim
      through the scorer and attaches a support flag to the response.
- [ ] The UI shows the flag as a quiet, existing-vocabulary chip (not a
      new banner/warning pattern) on claims below threshold; verified
      live that a deliberately unsupported test claim gets flagged and
      a well-grounded one does not.
- [ ] No new network egress introduced — confirm via the existing
      egress-scope guard/tests that this path stays local-only.
- [ ] A named regression test (interior-canon or a dedicated test file)
      pins that the flag never blocks or mutates the underlying
      generated content — it's additive metadata only.

## Test plan

- Unit: a new `tests/unit/test_grounding_entailment.py` (or similar)
  covering the scorer function directly with supported/unsupported/
  paraphrase fixtures.
- Integration: whichever generation path is chosen (meeting-artifact
  synthesis or Ask-AI) gets an end-to-end test asserting the flag
  appears on a deliberately unsupported fixture claim.
- Manual / device: a live drive on a staged hub with a real (or
  fixture) transcript, showing an artifact with a genuinely unsupported
  bullet flagged and a genuinely supported one not — screenshot both.

## Notes / open questions

Pick ONE integration point for this story (meeting artifacts or
Ask-AI), not both — extending to the second surface is a natural
follow-up story once the pattern is proven, not a reason to double this
story's scope. Threshold tuning (what score counts as "flag it") should
be a named constant with a comment explaining the choice, not a magic
number — expect to revisit it once real usage data exists.
