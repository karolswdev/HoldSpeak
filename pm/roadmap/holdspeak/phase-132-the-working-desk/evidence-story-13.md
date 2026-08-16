# Evidence - HS-132-13

- **Story:** HS-132-13 - The roadmap tells the truth
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:14:57Z

- **Command:** `.githooks/dw check holdspeak`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 420485ee90c186ad7600dcbb261fb7ee4baca3d3

```text
ERROR pm/roadmap/holdspeak/phase-101-the-native-innards/evidence-story-04.md: evidence exists but matching story is not done
```

## Orchestrator notes

- Exit 1 is the honest expected end state: the single remaining ERROR is
  phase-101's evidence-story-04.md, held out of `done` by standing owner
  direction until the Phase-101 sitting — exempt per this story's
  acceptance criteria. Before this story the check reported 21 errors.
- Corrections verified against git history, per file:
  - 113: stories 01-11 shipped via PRs #437-#440 with per-story commits
    (each evidence file names its commit); 12-15 saved in-flight in
    068f36ff, left backlog with a re-audit note.
  - 114: zero HS-114 commits ever; six in-progress rows downgraded to
    backlog; header notes the audit's absorption findings.
  - 118: waves 6522739b/ab3acb44/28cda81a on main = 9/10; header corrected
    from "backlog (0/10)"; story-10 walk stays the open IOU.
  - 121: no HS-121 commits — record kept chartered with an absorption
    note (kit shipped via later phases).
  - 124: whole phase in 416f0828 (PR #442); header corrected from
    "chartered (0/10)" to done; 10 evidence files as commit pointers.
  - 120: record landed in git for the first time; 11 evidence-debt files;
    final summary names the debt.
  - Final summaries written retroactively for 115/116/119/120/122/123/
    124/125/126/127, each pointer-based, never re-certifying.
- web/test-results/ gitignored.
