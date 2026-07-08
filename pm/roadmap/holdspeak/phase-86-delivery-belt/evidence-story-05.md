# Evidence - HS-86-05

- **Story:** HS-86-05 - The live walk + docs + closeout
- **Status:** done
- **Date:** 2026-07-07

## The walk — this story crossed its own belt

One hub (`scripts/screenshot_hs86_walk.py`), one page session, never
reloaded; every act between shots was real (CLI, git, gh); the hub's
mission-control access log recorded in-process. Beats, each committed
under `./screenshots/`:

1. `walk-1-story-in-progress.png` — HS-86-05 riding the belt
   in-progress (flipped by `dw story status` before launch; the belt
   read it from receipts).
2. `walk-2-evidence-station.png` — `dw evidence capture` ran mid-walk
   (the 29-test module run above IS that capture); the evidence tick
   appeared on the chip with **no reload**.
3. `walk-3-gate-refusal.png` — a REAL refusal: `git commit` attempted
   with no contract; the gate blocked (`contract-missing`) and the
   holdspeak lane's gate light wore the rule within the next belt
   read. The probe never landed (`git log` unchanged).
4. `walk-4-pr-and-ci-lights.png` — the phase's real PR
   (karolswdev/HoldSpeak **#303**) opened mid-walk; the lane lit
   `⛓ 1` with the amber pending CI dot, and the ticker led with the
   refusal, then the evidence capture, then the flip — the walk
   narrating itself.

Zero belt-side writes, mechanically shown: `walk-access-log.json`
records every `/api/missioncontrol*` request the hub served during
the walk — 12 requests, methods `{GET}` only (the script asserts it
and fails otherwise). The merge beat happens after this commit: the
PR merges on green CI, and the close station (final-summary present,
phase segment dimming to closed) is visible on the live desk — the
one beat a commit cannot photograph of itself.

## Docs (this commit)

- `docs/USER_GUIDE.md` — "Mission Control On The Desk": what the belt
  is, that it renders receipts only, that the one act rides
  propose/approve/execute with the repo's gate keeping final say.
- `docs/SECURITY.md` — egress row for mission-control receipts
  (`gh pr list` through the operator's own CLI; GET-only,
  fitness-tested; typed absence).
- `docs/ARCHITECTURE.md` — the belt read path (three contract
  documents + gh, byte-honest relay, `scope:"belt"` frames on the
  one bus, contained evidence reads).
- BACKLOG row U → shipped (B1); roadmap README row/pointer/headline;
  the phase's final-summary.md.

## Verification artifacts

```text
$ uv run python scripts/screenshot_hs86_walk.py
W1: in-progress on the belt
W2: evidence tick, no reload
W3: the gate refused; the belt wears it
W4: PR + CI lights lit
access log: 12 mission-control requests, all GET
```

```text
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3312 passed, 37 skipped, 2 warnings in 254.23s (0:04:14)
```

## Acceptance criteria — re-checked

- [x] Beat-by-beat captures exist; every state shown derives from a
      receipt recorded here (the flip, the capture, the refusal, the
      PR are all in the rail log / GitHub).
- [x] Access-log excerpt: 12 requests, all GET
      (`walk-access-log.json`, asserted in-script).
- [x] Docs updated in canon voice; guards green in the suite run
      below.
- [x] final-summary.md written; suite green; the PR merges on green
      (the merge conclusion is checked before merging, recorded in
      the phase's final summary).

### Captured run — 2026-07-08T02:32:12Z

- **Command:** `uv run pytest -q tests/unit/test_web_routes_missioncontrol.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3dc56324c21a45e356ffa2daf789221884495061

```text
.............................                                            [100%]
29 passed in 0.86s
```

## Deviations from plan

The story planned the refusal via "an honest unchecked contract"; the
walk used the even-simpler honest case (no contract at all) — the
same rule family, the same real refusal.

## Follow-ups

B2 (the nod, beyond the story-flip leg Phase 82 already carries), B3
(the factory), B4 (the DeskOS belt) stay future phases per the RFC;
recorded in the final summary's handoff.
