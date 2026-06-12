# HS-61-04 — Closeout: the real POST + final-summary + PR

- **Project:** holdspeak
- **Phase:** 61
- **Status:** done
- **Depends on:** HS-61-01, HS-61-02, HS-61-03
- **Unblocks:** phase exit
- **Owner:** unassigned

## Problem
Fakes prove the seams; the phase only closes when a real approval drives
a real HTTP POST whose body is byte-equal to the preview, and when the
unconfigured path is proven invisible.

## Scope
- **In:** a live run: a real meeting record → the real export route →
  the real proposal → approval through the real flow (dashboard or
  Qlippy card) → the REAL `build_webhook_connector` POSTs to a REAL
  local incoming-webhook-shaped receiver; assert the received
  `{"text": ...}` body byte-equal to the stored preview; assert nothing
  was received before the approval. The off-proof: unconfigured →
  no buttons + 400. A wrong-host probe: the connector refuses before
  egress. Full suite; `final-summary.md`; BACKLOG L flipped to shipped;
  project README cadence; PR `phase-61-send-to-slack` merged on green
  CI; the phase memory file.
- **Out:** posting to real Slack infrastructure (a local receiver is
  the proof; the wire format is Slack's documented contract).

## Acceptance criteria
- [x] The live trace ships in evidence: proposal recorded → nothing
      received → approval → exactly one POST → body byte-equal to the
      preview. (14/14, real browser + real receiver + real transport.)
- [x] The off-proof and the wrong-host refusal ship in evidence (the
      wrong-host probe ran with the REAL transport; refused before any
      socket opened).
- [x] Full suite green (`--ignore=tests/e2e/test_metal.py`): 2768
      passed, 17 skipped.
- [x] final-summary.md written; BACKLOG row L flipped; README cadence
      done; PR merged on green; memory recorded.
      See `evidence-story-04.md`.

## Test plan
- A dogfood script driving the live loop against a local HTTP receiver;
  the full suite as regression.
