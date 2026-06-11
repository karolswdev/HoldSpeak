# HS-59-04 — Closeout: real-metal dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 59
- **Status:** done
- **Depends on:** HS-59-01..03
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
"It speaks your language" is a claim about real audio; only real speech
proves it.

## Scope
- **In:** real-metal dogfood: a real non-English utterance (macOS `say`
  with an installed international voice; probe `say -v '?'` first)
  through real Whisper with the language pinned (and once on auto, for
  the honest comparison); the spoken-symbol dictionary through the real
  pipeline; the defaults-byte-identical proof. Full suite; build clean;
  `final-summary.md`; BACKLOG **K** flipped; README CLOSED + index row;
  PR to `main` merged on green CI.
- **Out:** new feature work (findings go back to their story).

## Acceptance criteria
- [x] Dogfood transcript committed: real German (`say -v Anna`) through
      real Whisper pinned to `de`, near-verbatim (auto shown honestly);
      the dictionary fired through the real settings round-trip
      (`std::vector`, `x → y`); defaults byte-identical.
- [x] Full suite green (2683 passed, 17 skipped); build clean; 0
      `_built/` tracked.
- [x] `final-summary.md` + this story's evidence in the same commit.
- [x] README + BACKLOG (K shipped; O queued-next with conditions)
      updated in the same commit; PR merged on green.

## Test plan
- The dogfood + the full suite; CI green on the PR.
