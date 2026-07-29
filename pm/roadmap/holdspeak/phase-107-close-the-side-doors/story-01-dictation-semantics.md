# HS-107-01 - Dictation's commit boundary — semantics before rerouting

- **Project:** holdspeak
- **Phase:** 107
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-107-02
- **Owner:** unassigned

## The thesis (the bar)

Dictation is the crux of the census and the path the owner uses most.
`holdspeak/runtime/dictation_capture.py` holds **six** of the ten
typing debt sites — five TextTyper calls (D01-D05) and the
dictation-to-agent tmux call (T03) — which means it is the one file
that appears in two families at once.

RFC §7 rung 5 is explicit: **define dictation's commit-boundary
semantics FIRST, then reroute.** Dictation is migrated once, with
settled authority semantics, never twice. This story reroutes
**nothing**. It answers the question that a reroute would otherwise
answer by accident.

The bar: after this story, anyone can say exactly where dictation's
consequential boundary is — which act is the effect, what authority
covers it, and what a receipt for it contains — and can point at a
test that pins the answer.

## Problem

Dictation today types directly. Five call sites reach `TextTyper`
and one reaches `send_text_to_pane`, each with its own idea of when
the act is committed. Route them through the kernel without settling
the semantics first and the boundary gets defined implicitly, by
whichever site was migrated first — and then it gets re-defined when
the next one disagrees. That is the double migration the RFC forbids.

## The question this story answers

For the hold-key path: **the owner holds a key, speaks, releases, and
text lands in the focused application.** Which part of that is the
consequential operation?

- Capture, transcription, punctuation and rewrite are **computation**
  — Article XI clause 5 exempts them, and RFC §12 keeps them on the
  low-latency path permanently. Audio frames are never journaled.
- The final typing is **the effect**. It is the only part that owes
  the kernel anything.
- The owner's hold gesture **is the approval** — Article XI clause 4
  says consent is not a second confirmation of what the owner just
  did. `operation_policy.py` already models this as a distinct
  authority basis (direct gesture vs. scoped grant vs. posture).

The five paths differ and the story must state each one's boundary
explicitly: ordinary typing, preview-before-commit, voice command,
remote dictation, and dictation-to-agent (which types into a *pane*,
not the focused app, and is therefore closer to `process.input` than
to a desktop type).

## Recipe

1. **Write the contract.** A short, precise document — not prose —
   naming for each of the five paths: what the effect is, when it is
   committed, what authority basis covers it, what the receipt
   records, and what is exempt computation.
2. **Pin it as tests** against today's behaviour, with no rerouting.
   The tests describe what dictation does now and what the boundary
   will be; they must pass before and after HS-107-02.
3. **Measure the baseline.** Hold-key latency on real metal, before
   any migration: capture → transcribe → type. Print the numbers.
   HS-107-02 has to match them.
4. **Name the authority basis per path** against
   `operation_policy.py`'s existing descriptors — do not invent a new
   one. Where a path has no honest basis today, say so; that is a
   finding.
5. **Decide the dictation-to-agent case explicitly.** T03 types into
   a tmux pane. It probably belongs to `process.input` (already
   migrated and proven) rather than a desktop typing operation. State
   the choice and the reason.

## Out of scope

- Any rerouting. Zero call sites change. Zero register entries move.
- Changing what dictation does.
- The other four typing sites (wake, macros) — they ride in
  HS-107-02 once the boundary is settled.

## Acceptance

- The contract exists and covers all five paths plus
  dictation-to-agent, each with effect, commit point, authority
  basis, receipt content, and exemptions.
- Tests pin the boundary and pass against **unmodified** dictation.
- Baseline hold-key latency measured on real metal and printed.
- The register is unchanged — 36 entries, byte-identical. A story
  that settles semantics must not quietly move a site.
- Every claim about authority cites `operation_policy.py` by line.

## Test plan

- **Unit:** the boundary contract as executable assertions against
  current behaviour.
- **Live (evidence):** real hold-key dictation on real metal, latency
  printed, all five paths exercised where reachable.
- **Census:** register byte-identical before and after.

## Chef's notes

- The temptation is to "just migrate the obvious one while we're
  here." Don't. The whole point of this story is that no site moves
  until the boundary is written down.
- If the honest answer for a path is "this has no clear authority
  basis today," that is the most valuable output this story can
  produce. Write it plainly; HS-107-02 needs to know.
- Watch the preview path especially — preview-before-commit is the
  one place where the commit point is genuinely ambiguous, because
  the user sees text before it lands.
