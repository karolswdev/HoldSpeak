# HS-88-05 — The walk, the docs, the close

- **Project:** holdspeak
- **Phase:** 88
- **Status:** done
- **Depends on:** HS-88-02, HS-88-03, HS-88-04
- **Owner:** unassigned

## Problem

The thesis — the rails are desk-native material — is proven by
grounding a REAL open story into a REAL run and watching the model use
it, and by the observer journaling a REAL flip, live, on camera. The
close consolidates the phase and hands the seam forward.

## Scope

- In: the walk (below), each beat captured; a mechanical-rules pass
  (the no-markdown-scrape grep test extended to every rails path, the
  one-hydration parity assertion, the observer-is-read-only
  invariant); docs — USER_GUIDE "Ground the rails / the rails
  journal", SECURITY.md the observer + rails-read rows, ARCHITECTURE.md
  a rails-as-material paragraph; BACKLOG/README cadence; final summary
  with the B3/B4 + remote-grounding handoff.
- Out: new capability; performance work beyond the existing caps.

## The walk (each beat a capture)

1. Ground: pick THIS phase's open story into an ask; the answer uses
   its content (control vs treatment).
2. Ground a steer: the same open story ridden into a Phase-87 steer
   into a real pane; the composed text carries the rail block.
3. Receipt, not scrape: show the grounded block is the dw-named file,
   provenance-headed; a bad ref refuses by name.
4. Observer on: flip a real story; the journal entry appears, naming
   the events it saw, summarized by the local model.
5. Observer restraint: the observer's suggested action is a PROPOSAL,
   approved by a human, the dw gate keeping say.
6. Reach: a remote (two-process) flip reaches the journal, the node
   named; the node goes quiet and the stream reads stale.
7. The journal grounded: open the journal, ground IT into a run.

## Acceptance criteria

- [ ] All beats captured against real rails + a real model; zero
      mocked frames; every claim backed by a receipt (a dw-named path,
      a journal entry, an audit/proposal row).
- [ ] The no-scrape grep test covers every rails hydration path; the
      one-hydration parity test is green; the observer-read-only
      invariant holds.
- [ ] Docs shipped in canon voice; voice/docs/api-surface guards
      green; suite green (read from the output file).
- [ ] final-summary.md with the handoff (what remote grounding, B3,
      and B4 inherit from the rails-as-material seam).

## Test plan

- Unit: the mechanical rules (scrape census, hydration parity,
  observer-read-only).
- Integration: the walk itself.
- Manual / device: the owner replays beats 1–5 from the docs alone.

## Implementation direction

- **Walk rig:** extend the Phase-87 pattern (`scripts/steer_walk_hs87.py`
  + `scripts/steer_grounding_proof.py`) — one hub, a real `dw context`
  against this repo, a real model on `.43`, real acts between captures;
  the observer beat flips a real story and reads the journal back.
- **Control vs treatment:** the Phase-53 pattern again — a question the
  bare model cannot answer, answerable only from the grounded open
  story (e.g. an acceptance criterion's exact wording).
- **The docs** lead with the receipt rule (the rails are read through
  your own `dw`, never scraped) and the consent rule (the observer is
  read-only, off by default) — the no-reassurance canon: say what
  refuses and when.
- **Self-reference:** grounding THIS phase's own story into the walk's
  run is the Phase-86/87 recursion again — keep it; it sells the seam.
